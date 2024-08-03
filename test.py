data = {
  "acousticness": 0.0364,
  "analysis_url": "https://api.spotify.com/v1/audio-analysis/2Z9ao6iBMuO7iwkbHuZ7nU",
  "danceability": 0.0821,
  "duration_ms": 129167,
  "energy": 0.291,
  "id": "2Z9ao6iBMuO7iwkbHuZ7nU",
  "instrumentalness": 0.847,
  "key": 10,
  "liveness": 0.114,
  "loudness": -16.895,
  "mode": 0,
  "speechiness": 0.0355,
  "tempo": 170.319,
  "time_signature": 4,
  "track_href": "https://api.spotify.com/v1/tracks/2Z9ao6iBMuO7iwkbHuZ7nU",
  "type": "audio_features",
  "uri": "spotify:track:2Z9ao6iBMuO7iwkbHuZ7nU",
  "valence": 0.0689
}

calc_happy = (data['energy'] * 2 + data['valence'] * 2 + min(data['tempo'],180)/180 + (not data['key'] % 2))/6
calc_uplifting = (data['energy'] * 3 + (not data['key'] % 2) + (1 if data['valence'] > 0.5 else 0))/5
calc_calming = min((1-data['energy'] + (200 - min(data['tempo'], 200))/200 + data['instrumentalness'] + abs(data['loudness'])/60)/2,1)




print(calc_happy, calc_uplifting, calc_calming)