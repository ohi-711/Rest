import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, redirect, request, session, render_template
import requests

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY")

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIFY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI"),
    scope="user-library-read playlist-modify-private"
)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/success")
def ahhhh():
    return render_template("ihatepython.html")

@app.route("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    session["token_info"] = sp_oauth.get_cached_token()
    return redirect(auth_url)

@app.route("/callback")
def callback():
    token_info = sp_oauth.get_access_token(request.args["code"])
    session["token_info"] = token_info
    return redirect("/generate")

@app.route("/generate")
def generate_playlist():
    token_info = session.get("token_info", None)
    if not token_info:
        return redirect("/login")

    sp = spotipy.Spotify(auth=token_info["access_token"])
    
    # Example API calls
    user = sp.current_user()
    playlists = sp.current_user_playlists()
    
    return render_template("index.html", user=user, playlists=playlists)

if __name__ == "__main__":
    app.run(debug=True)