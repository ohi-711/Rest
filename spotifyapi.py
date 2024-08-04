import spotipy
from dotenv import load_dotenv

class SpotifyAPI:
    def __init__(self, session):
        load_dotenv()
        self.cache_handler = spotipy.cache_handler.FlaskSessionCacheHandler(session)
        self.auth_manager = spotipy.oauth2.SpotifyOAuth(scope='user-read-currently-playing playlist-modify-private user-library-read user-modify-playback-state app-remote-control streaming user-read-playback-state',
                                                        cache_handler=self.cache_handler,
                                                        show_dialog=True)
        self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)

    def get_spotify(self):
        return self.spotify

    def get_auth_manager(self):
        return self.auth_manager

    def get_cache_handler(self):
        return self.cache_handler

    def get_song_emotion(self, track_id):

        # get audio features
        audio_features = self.spotify.audio_features(track_id)[0]

        # calculate values
        calc_happy = (audio_features['energy'] * 2 + audio_features['valence'] * 2 + min(audio_features['tempo'],180)/180 + (not audio_features['key'] % 2))/6
        calc_uplifting = (audio_features['energy'] * 3 + (not audio_features['key'] % 2) + (1 if audio_features['valence'] > 0.5 else 0))/5
        calc_calming = min((1-audio_features['energy'] + (200 - min(audio_features['tempo'], 200))/200 + audio_features['instrumentalness'] + abs(audio_features['loudness'])/60)/2,1)

        ret = None

        if calc_happy > calc_uplifting and calc_happy > calc_calming:
            ret = "happy"
        elif calc_uplifting > calc_happy and calc_uplifting > calc_calming:
            ret = "uplifting"
        else:
            ret = "calming"

        return ret

    def get_all_saved_tracks(self):
        results = self.spotify.current_user_saved_tracks()
        tracks = results['items']
        while results['next']:
            results = self.spotify.next(results)
            tracks.extend(results['items'])
        return tracks

    def get_current_user_playing_track(self):
        return self.spotify.current_user_playing_track()

    def start_playback(self, uris):
        self.spotify.start_playback(uris=uris)

    def the_add_to_queue(self, uri):
        print("CALLED", uri)
        self.spotify.add_to_queue(uri)

    def check_song_time(self):
        try:
            return self.spotify.current_playback()['progress_ms']
        except:
            return 0

    def get_song_length(self, track_id = None):
        if track_id is not None:
            return self.spotify.audio_features(track_id)[0]['duration_ms']
        try:
            return self.spotify.current_playback()['item']['duration_ms']
        except:
            return 0

    def get_cover(self):
        return self.spotify.current_playback()['item']['album']['images'][0]['url']

    def get_title(self):
        return self.spotify.current_playback()['item']['name']

    def get_artist(self):
        return self.spotify.current_playback()['item']['artists'][0]['name']