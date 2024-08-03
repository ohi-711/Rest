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

if not dotenv.find_dotenv():
    raise RuntimeError("No .env file found")

detector = inference.RestDetector('torchscript_model_0_66_49_wo_gl.pth')

dotenv.load_dotenv()

app = flask.Flask(__name__)
flask_cors.CORS(app)

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

@app.route("/login")
def login():
    return auth.auth0.authorize_redirect(
        redirect_uri=flask.url_for("callback", _external=True)
        )

@app.route("/callback", methods=["GET", "POST"])
def callback():
    token = auth.auth0.authorize_access_token()

    flask.session["user"] = token

    if not userdb.user_exists("test"):
        userdb.add_user("test",
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
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return flask.redirect("/link_spotify")

    if flask.request.args.get("code"):
        auth_manager.get_access_token(flask.request.args.get("code"))
        userdb.modify_user("test", {
            "spotify": sp.current_user()["id"],
            "liked_songs": userdb.get_user("test")["liked_songs"]
        })
        return flask.redirect("/dashboard")

    saved_tracks = spapi.get_all_saved_tracks()

    for track in saved_tracks:
        print("HERE")
        print(userdb.get_user("test"))
        if track['track']["id"] not in userdb.get_user("test")["liked_songs"]:
            userdb.modify_user("test", {
                "spotify": userdb.get_user("test")["spotify"],
                "liked_songs": userdb.get_user("test")["liked_songs"] + [track['track']["id"]]
            })
            emotion = spapi.get_song_emotion(track['track']["id"])

            if emotion == "happy":
                songdb.songs["happy"].append(track['track']["id"])
                print("happy")
            elif emotion == "uplifting":
                songdb.songs["uplifting"].append(track['track']["id"])
                print("uplifting")
            else:
                songdb.songs["calming"].append(track['track']["id"])
                print("calming")

            songdb.save_db()

    return flask.render_template("dashboard.html", session = flask.session.get("user"))

@app.route("/emotioninference", methods=['POST'])
def emotioninference():
    file = flask.request.files['file']
    emotion = detector.detect_emotion(file)
    print(f"Detected emotion: {emotion}")

    return flask.jsonify({"emotion": emotion})

@app.route('/')
def index():
    return "Hello, World!"

if __name__ == '__main__':
    app.run(debug=True, port=3000)