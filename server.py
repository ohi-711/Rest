"""Python Flask WebApp Auth0 integration example
"""

import json
from os import environ as env
from urllib.parse import quote_plus, urlencode
import requests
from authlib.integrations.flask_client import OAuth
from dotenv import find_dotenv, load_dotenv
from flask import Flask, redirect, render_template, session, url_for

# Load environment variables from .env file
ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

# Create Flask app instance
app = Flask(__name__)

# Set secret key for session management
app.secret_key = env.get("APP_SECRET_KEY")

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
    return redirect("/")

# Route for home page
@app.route("/")
def home():
    # Render home.html template with user information
    return render_template(
        "home.html",
        session=session.get("user"),
        pretty=json.dumps(session.get("user"), indent=4),
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

headers = {
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

# Run Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=env.get("PORT", 3000))