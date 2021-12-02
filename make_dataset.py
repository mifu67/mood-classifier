import pandas as pd
import spotipy
import math
from spotipy.oauth2 import SpotifyOAuth

CID = '******'
SECRET = '******'
REDIRECT_URI = '******'
USERNAME = 'mechllfu-us'
# hardcoded playlist IDs below: I didn't want to deal with the API
# any more than I had to oops
SAD_TRAINING = '5cBZXRDvsVgyEHl9pZKxNj'
HAPPY_TRAINING = '1dOBsih7CGV6ItEX3OjQCU'
SAD_TESTING = '5TxyaITBxPuvzlWgTlbROK'
HAPPY_TESTING = '5VOUZuCBEYjV4q1LvTwzGH'


def get_track_ids(sp, playlist_id):
    ids = []
    playlist = sp.user_playlist_tracks(USERNAME, playlist_id)
    for item in playlist['items']:
        track = item['track']
        ids.append(track['id'])
    while playlist['next']:
        playlist = sp.next(playlist)
        for item in playlist['items']:
            track = item['track']
            ids.append(track['id'])
    return ids


def decimal_to_discrete(decimal):
    return math.floor(decimal * 10)


def get_track_features(sp, track_id, mood):
    features = sp.audio_features(track_id)

    acousticness = decimal_to_discrete(features[0]['acousticness'])
    danceability = decimal_to_discrete(features[0]['danceability'])
    energy = decimal_to_discrete(features[0]['energy'])
    key = features[0]['key']
    mode = features[0]['mode']
    valence = decimal_to_discrete(features[0]['valence'])

    track = [acousticness, danceability, energy, key, mode, valence, mood]
    return track


def make_dataset(sp, name, sad_playlist, happy_playlist):
    tracks = []
    sad_ids = get_track_ids(sp, sad_playlist)
    for track_id in sad_ids:
        tracks.append(get_track_features(sp, track_id, 0))
    happy_ids = get_track_ids(sp, happy_playlist)
    for track_id in happy_ids:
        tracks.append(get_track_features(sp, track_id, 1))

    df = pd.DataFrame(tracks, columns=['acousticness', 'danceability', 'energy', 'key',
                                       'mode', 'valence', 'mood'])
    print(df.head())
    df.to_csv(name, index=False)


def main():
    scope = "user-library-read"
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CID, client_secret=SECRET,
                                                   redirect_uri=REDIRECT_URI, scope=scope))
    if sp:
        print("success")

    make_dataset(sp, "mood_training.csv", SAD_TRAINING, HAPPY_TRAINING)
    make_dataset(sp, "mood_testing.csv", SAD_TESTING, HAPPY_TESTING)


if __name__ == "__main__":
    main()