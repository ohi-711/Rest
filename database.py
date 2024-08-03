import json

class UserDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.users = {}
        self.load_db()

    def load_db(self):
        try:
            with open(self.db_path, 'r') as f:
                self.users = json.load(f)
        except FileNotFoundError:
            self.save_db()

    def save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.users, f)

    def add_user(self, user_token, user_data):
        self.users[user_token] = user_data
        self.save_db()

    def get_user(self, user_token):
        return self.users.get(user_token, None)

    def user_exists(self, user_token):
        return self.get_user(user_token) is not None

    def get_user_spotify(self, user_token):
        user = self.get_user(user_token)
        if user is None:
            return None
        return user.get("spotify", None)

    def user_linked_spotify(self, user_token):
        return self.get_user_spotify(user_token) is not None

    def modify_user(self, user_token, user_data):
        self.users[user_token] = user_data
        self.save_db()

class SongDatabase:
    def __init__(self, db_path):
        self.db_path = db_path
        self.songs = {
            "happy": [],
            "uplifting": [],
            "calming": []
        }
        self.load_db()

    def load_db(self):
        try:
            with open(self.db_path, 'r') as f:
                self.songs = json.load(f)
        except FileNotFoundError:
            self.save_db()

    def save_db(self):
        with open(self.db_path, 'w') as f:
            json.dump(self.songs, f)

    def add_song(self, song_type, song_data):
        self.songs[song_type].append(song_data)
        self.save_db()

    def get_songs(self, song_type):
        return self.songs.get(song_type, [])

