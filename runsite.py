import flask
import flask_session
import spotifyapi
import os
import authlib
import authlib.integrations
import authlib.integrations.flask_client
import dotenv
import database
import inference
import flask_cors
import openai
import random

if not dotenv.find_dotenv():
    raise RuntimeError("No .env file found")

class EmotionSupport:
    def __init__(self):
        self.emotion = ""
        self.emotion_override = ""


detector = inference.RestDetector('torchscript_model_0_66_49_wo_gl.pth')

dotenv.load_dotenv()

app = flask.Flask(__name__)
flask_cors.CORS(app)

ec = EmotionSupport()



oai = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
flask_session.Session(app)


auth = authlib.integrations.flask_client.OAuth(app)
auth.register(
            "auth0",
            client_id=os.environ.get("AUTH0_CLIENT_ID"),
            client_secret=os.environ.get("AUTH0_CLIENT_SECRET"),
            client_kwargs={
                "scope": "openid profile email",
            },
            server_metadata_url=f'https://{os.environ.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
        )

spapi = spotifyapi.SpotifyAPI(flask.session)

cache_handler = spapi.get_cache_handler()
auth_manager = spapi.get_auth_manager()
sp = spapi.get_spotify()

userdb = database.UserDatabase("users.json")
songdb = database.SongDatabase("songs.json")

def get_emotion_support():
    if 'emotion_support' not in flask.session:
        flask.session['emotion_support'] = EmotionSupport()
    return flask.session['emotion_support']

@app.route("/login")
def login():
    return auth.auth0.authorize_redirect(
        redirect_uri=flask.url_for("callback", _external=True)
        )


@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = auth.auth0.authorize_access_token()

    flask.session["user"] = token

    if not userdb.user_exists(flask.session.get("user")['userinfo']['name']):
        userdb.add_user(flask.session.get("user")['userinfo']['name'],
        {
            "spotify": None,
            "liked_songs": []
        })

    if userdb.user_linked_spotify(token["access_token"]):
        return flask.redirect("/dashboard")
    else:
        return flask.redirect("/link_spotify")

@app.route("/link_spotify")
def link_spotify():
    return flask.redirect(auth_manager.get_authorize_url())

@app.route("/dashboard")
def dashboard():

    if flask.request.args.get("code"):
        auth_manager.get_access_token(flask.request.args.get("code"))
        userdb.modify_user(flask.session.get("user")['userinfo']['name'], {
            "spotify": sp.current_user()["id"],
            "liked_songs": userdb.get_user(flask.session.get("user")['userinfo']['name'])["liked_songs"]
        })
        return flask.redirect("/dashboard")

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return flask.redirect("/link_spotify")

    saved_tracks = spapi.get_all_saved_tracks()


    for track in saved_tracks:
        if track['track']["id"] not in userdb.get_user(flask.session.get("user")['userinfo']['name'])["liked_songs"]:
            userdb.modify_user(flask.session.get("user")['userinfo']['name'], {
                "spotify": userdb.get_user(flask.session.get("user")['userinfo']['name'])["spotify"],
                "liked_songs": userdb.get_user(flask.session.get("user")['userinfo']['name'])["liked_songs"] + [track['track']["id"]]
            })
            emotion = spapi.get_song_emotion(track['track']["id"])

            if emotion == "happy":
                songdb.songs["happy"].append(track['track']["id"])
            elif emotion == "uplifting":
                songdb.songs["uplifting"].append(track['track']["id"])
            else:
                songdb.songs["calming"].append(track['track']["id"])

            songdb.save_db()

    start_playback()
    return flask.render_template("dashboard.html", session = flask.session.get("user"))


@app.route("/emotioninference", methods=['POST'])
def emotioninference():
    print((spapi.get_song_length())/1000)
    print((spapi.check_song_time())/1000)
    print(f"Time left: {(spapi.get_song_length() - spapi.check_song_time())/1000}")

    if spapi.get_song_length() != 0 and spapi.check_song_time() != 0:
        if (spapi.get_song_length() - spapi.check_song_time())/1000 < 10 and (spapi.get_song_length() - spapi.check_song_time())/1000 > 5:
            queue_next_song()


    file = flask.request.files['file']
    emotion = detector.detect_emotion(file)

    if emotion in ["Neutral", "Joy"]:
        ec.emotion = "happy"
    elif emotion in ["Sadness", "Stressed"]:
        ec.emotion = "uplifting"
    else:
        ec.emotion = "calming"

    return flask.jsonify({"emotion": emotion})

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    data = flask.request.get_json()
    user_text = data['text']

    prompt = f"Analyze the following text for simple emotions such as happy, scared, angry. If no real emotion, then neutral: \"{user_text}\""

    response = oai.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You're a emotion therapist."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )

    analysis = response.choices[0].message.content
    emotion_override = "Neutral"
    music = "happy"

    if any(keyword in analysis for keyword in ["sad", "down", "unhappy"]):
        emotion_override = "Sadness"
        music = "uplifting"
    elif any(keyword in analysis for keyword in ["stressed", "anxious", "overwhelmed"]):
        emotion_override = "Stressed"
        music = "calming"
    elif any(keyword in analysis for keyword in ["happy", "joyful", "excited"]):
        emotion_override = "Joy"
    elif any(keyword in analysis for keyword in ["angry", "mad", "furious"]):
        emotion_override = "Anger"
        music = "calming"
    elif any(keyword in analysis for keyword in ["scared", "fearful", "afraid"]):
        emotion_override = "Fear"
        music = "calming"
    elif any(keyword in analysis for keyword in ["surprised", "amazed", "astonished"]):
        emotion_override = "Surprise"
        music = "calming"

    ec.emotion_override = music
    return flask.jsonify({"emotion": emotion_override})

@app.route('/current_track', methods=['GET'])
def current_track():
    current_playback = sp.current_playback()
    if current_playback and current_playback['item']:
        track_info = {
            'cover': spapi.get_cover(),
            'title': spapi.get_title(),
            'artist': spapi.get_artist()
        }
        return flask.jsonify(track_info)
    else:
        return flask.jsonify({'error': 'No track currently playing'}), 404

@app.route('/start_playback', methods=['POST'])
def start_playback():
    # check there is at least one active device
    devices = sp.devices()
    print(devices)

    active_device = False

    for device in devices['devices']:
        if device['is_active']:
            active_device = True
            break

    if not active_device:
        return flask.jsonify({"status": "error", "message": "No active device found"})

    if ec.emotion_override != "":
        songType = ec.emotion_override
    else:
        songType = ec.emotion

    if songType == "happy":
        sp.start_playback(uris=["spotify:track:" + songdb.songs["happy"][random.randint(0, len(songdb.songs["happy"]) - 1)]])
    elif songType == "uplifting":
        sp.start_playback(uris=["spotify:track:" + songdb.songs["uplifting"][random.randint(0, len(songdb.songs["uplifting"]) - 1)]])
    else:
        sp.start_playback(uris=["spotify:track:" + songdb.songs["calming"][random.randint(0, len(songdb.songs["calming"]) - 1)]])

    return flask.jsonify({"status": "success"})

def queue_next_song():

    if ec.emotion_override != "":
        songType = ec.emotion_override
    else:
        songType = ec.emotion

    if songType == "happy":
        print("CALLED", "spotify:track:", "HAPPY")
    elif songType == "uplifting":
        print("CALLED", "spotify:track:", "UPLIFTING")
    else:
        print("CALLED", "spotify:track:", "CALMING")

    if songType == "happy":
        spapi.the_add_to_queue("spotify:track:" + songdb.songs["happy"][random.randint(0, len(songdb.songs["happy"]) - 1)])
    elif songType == "uplifting":
        spapi.the_add_to_queue("spotify:track:" + songdb.songs["uplifting"][random.randint(0, len(songdb.songs["uplifting"]) - 1)])
    else:
        spapi.the_add_to_queue("spotify:track:" + songdb.songs["calming"][random.randint(0, len(songdb.songs["calming"]) - 1)])

    return flask.jsonify({"status": "success"})





@app.route('/')
def index():
    return flask.render_template("homepage.html")


if __name__ == '__main__':
    app.run(debug=True, port=3000)

