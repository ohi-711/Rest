"""Python Flask WebApp Auth0 integration example
"""

import json
import os
from os import environ as env
from urllib.parse import quote_plus, urlencode
import requests
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for, request
from flask_session import Session
import spotipy


# Load environment variables from .env file
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Create Flask app instance
app = Flask(__name__)

# Set secret key for session management
app.config['SECRET_KEY'] = os.urandom(64)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'

Session(app)

# Initialize OAuth client
oauth = OAuth(app)

# Register Auth0 as OAuth client
oauth.register(
    "auth0",
    client_id=env.get("AUTH0_CLIENT_ID"),
    client_secret=env.get("AUTH0_CLIENT_SECRET"),
    client_kwargs={
        "scope": "openid profile email",
    },
    server_metadata_url=f'https://{env.get("AUTH0_DOMAIN")}/.well-known/openid-configuration',
)


# Define routes

# Route for login page
@app.route("/login")
def login():
    # Redirect to Auth0 login page
    return oauth.auth0.authorize_redirect(
        redirect_uri=url_for("callback", _external=True)
    )

# Route for callback after login
@app.route("/callback", methods=["GET", "POST"])
def callback():
    # Get access token from Auth0
    token = oauth.auth0.authorize_access_token()
    # Store token in session
    session["user"] = token
    # Redirect to home page
    return redirect("/dashboard")

# Route for home page
@app.route("/")
def home():
    # Render home.html template with user information
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
    )

@app.route("/dashboard")
def dashboard():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private',
                                               cache_handler=cache_handler,
                                               show_dialog=True)

    if request.args.get("code"):
        # Step 2. Being redirected from Spotify auth page
        auth_manager.get_access_token(request.args.get("code"))
        return redirect('/dashboard')

    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        # Step 1. Display sign in link when no token
        auth_url = auth_manager.get_authorize_url()
        return f'<h2><a href="{auth_url}">Sign in</a></h2>'
    # Render home.html template with user information

    # Assuming auth_manager is already set up for Spotipy
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    
    # Retrieve Spotify user details
    spotify_user_info = spotify.me()
    
    # Prepare data to pass to the template
    user_data = {
        "display_name": spotify_user_info["display_name"],
        # Add other user details you wish to display
    }

    token_info = auth_manager.get_access_token(session.get("token_info"))
    
    return render_template(
        "dashboard.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
        display_name=spotify_user_info["display_name"],
        sign_out_link="/sign_out",
        playlists_link="/playlists",
        currently_playing_link="/currently_playing",
        current_user_link="/current_user",
        user=user_data,
        token_info = token_info
    )

# Route for logout
@app.route("/logout")
def logout():
    # Clear session
    session.clear()
    # Redirect to Auth0 logout page
    return redirect(
        "https://"
        + env.get("AUTH0_DOMAIN")
        + "/v2/logout?"
        + urlencode(
            {
                "returnTo": url_for("home", _external=True),
                "client_id": env.get("AUTH0_CLIENT_ID"),
            },
            quote_via=quote_plus,
        )
    )

@app.route('/sign_out')
def sign_out():
    session.pop("token_info", None)
    return redirect('/dashboard')


@app.route('/playlists')
def playlists():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/dashboard')

    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user_playlists()


@app.route('/currently_playing')
def currently_playing():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/dashboard')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    track = spotify.current_user_playing_track()
    if not track is None:
        return track
    return "No track currently playing."


@app.route('/current_user')
def current_user():
    cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
    auth_manager = spotipy.oauth2.SpotifyOAuth(cache_handler=cache_handler)
    if not auth_manager.validate_token(cache_handler.get_cached_token()):
        return redirect('/dashboard')
    spotify = spotipy.Spotify(auth_manager=auth_manager)
    return spotify.current_user()

""" headers = {
    'Authorization': f'Bearer {API_TOKEN}',
    'Content-Type': 'application/json',
}

spotify_tokens = {
    'access_token': 'ACCESS_TOKEN_FROM_SPOTIFY',
    'refresh_token': 'REFRESH_TOKEN_FROM_SPOTIFY',
}

response = requests.patch(
    f'https://' + env.get("AUTH0_DOMAIN") + '/api/v2/users/' + session.get("user")["userinfo"]['sub'],
    json={'app_metadata': spotify_tokens},
    headers=headers,
)

if response.status_code == 200:
    print("Spotify tokens successfully stored.")
else:
    print(f"Failed to store tokens. Status code: {response.status_code}")
 """
# Run Flask app
if __name__ == "__main__":
    #port = int(env.get("PORT", env.get("SPOTIPY_REDIRECT_URI", "3000").split(":")[-1]))
    app.run(host="127.0.0.1", port=3000, threaded=True)
