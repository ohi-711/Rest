import os
from flask import Flask, session, request, redirect
from flask_session import Session
import spotipy
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
Session(app)

userdb = {}
songdb = {
        "happy": [],
        "uplifting": [],
        "calming": []
    }

@app.route('/')
def index():

    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private user-library-read user-modify-playback-state app-remote-control streaming user-read-playback-state',
                                               cache_handler=cache_handler,
                                               show_dialog=True)
    sp = spotipy.Spotify(auth_manager=auth_manager)

    if request.args.get("code"):
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'

    # if user is not in the database, add them, and initialize their liked songs
    if auth_manager.get_access_token(session.get("token_info"))['access_token'] not in userdb:
        init_user(auth_manager.get_access_token(session.get("token_info"))['access_token'], auth_manager, sp)



    print(userdb[auth_manager.get_access_token(session.get("token_info"))['access_token']])

    print(songdb)

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return f'<h2>Hi {spotify.me()["display_name"]}, ' \
           f'<small><a href="/sign_out">[sign out]<a/></small></h2>' \
           f'<a href="/playlists">my playlists</a> | ' \
           f'<a href="/currently_playing">currently playing</a> | ' \
           f'<a href="/saved_tracks">my saved tracks</a> | ' \
           f'<a href="/play_liked_song">play liked song</a> | ' \
        f'<a href="/current_user">me</a>' \


@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()

@app.route('/saved_tracks')
def saved_tracks():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')

    spotify = spotipy.Spotify(auth_manager=auth_manager)

    # get info on all of the user's saved tracks
    saved_tracks = get_all_saved_tracks(spotify)


    return saved_tracks

    #return spotify.current_user_saved_tracks()

@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."

@app.route('/play_liked_song')
def play_liked_song():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    sp = spotipy.Spotify(auth_manager=auth_manager)

    track = sp.current_user_playing_track()
    print(track)
    if track is None or track['is_playing'] == False:
        sp.start_playback(uris=["spotify:track:1GK6aJgUOlFq2nWk8J9Od9"])
    else:
        sp.add_to_queue("spotify:track:1GK6aJgUOlFq2nWk8J9Od9")
    return "Playing liked song"



@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()

def get_all_saved_tracks(spotify):
    results = spotify.current_user_saved_tracks()
    tracks = results['items']
    while results['next']:
        results = spotify.next(results)
        tracks.extend(results['items'])
    return tracks

def init_user(user_id, auth_manager, sp):
    userdb[user_id] = {
        "liked_songs": []
    }

    saved_tracks = get_all_saved_tracks(spotipy.Spotify(auth_manager=auth_manager))

    for track in saved_tracks:
        userdb[user_id]["liked_songs"].append(track['track']['id'])
        init_track(track['track']['id'], sp)

def init_track(track_id, sp):
    if track_id in songdb:
        return



    # get audio features
    audio_features = sp.audio_features(track_id)[0]
    print(audio_features)

    # calculate values
    calc_happy = (audio_features['energy'] * 2 + audio_features['valence'] * 2 + min(audio_features['tempo'],180)/180 + (not audio_features['key'] % 2))/6
    calc_uplifting = (audio_features['energy'] * 3 + (not audio_features['key'] % 2) + (1 if audio_features['valence'] > 0.5 else 0))/5
    calc_calming = min((1-audio_features['energy'] + (200 - min(audio_features['tempo'], 200))/200 + audio_features['instrumentalness'] + abs(audio_features['loudness'])/60)/2,1)

    # whichever is highest, set song to that

    if calc_happy > calc_uplifting and calc_happy > calc_calming:
        songdb['happy'].append(track_id)
    elif calc_uplifting > calc_happy and calc_uplifting > calc_calming:
        songdb['uplifting'].append(track_id)
    else:
        songdb['calming'].append(track_id)








'''
Following lines allow application to be run more conveniently with
`python app.py` (Make sure you're using python3)
(Also includes directive to leverage pythons threading capacity.)
'''
if __name__ == '__main__':
    app.run(threaded=True, port=int(os.environ.get("PORT",
                                                   os.environ.get("SPOTIPY_REDIRECT_URI", 5000).split(":")[-1])))