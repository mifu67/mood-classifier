import numpy as np
import math
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
BUCKETS_PER_FEATURE = {0: 10, 1: 10, 2: 10, 3: 12, 4: 2, 5: 10}
NUM_MOODS = 2

CID = '******'
SECRET = '******'
REDIRECT_URI = '******'


def initialize_array(num_buckets):
    array = []
    for i in range(num_buckets):
        array.append([0, 0])
    return array


def train(data, mle):
    num_features = len(data[1]) - 1
    y_index = num_features
    feature_counts = {}
    for i in range(num_features):
        feature_counts[i] = initialize_array(BUCKETS_PER_FEATURE[i])
    y_counts = [0, 0]
    feature_p_hats = feature_counts
    y_p_hats = y_counts

    for row in data:
        if row[y_index] == 0:
            y_counts[0] += 1
            for i in range(num_features):
                value = row[i]
                feature_counts[i][value][0] += 1
        else:
            y_counts[1] += 1
            for i in range(num_features):
                value = row[i]
                feature_counts[i][value][1] += 1

    # calculate estimated parameters
    if mle:
        # for each feature
        for feature in feature_counts:
            # for each value that the feature could take on
            for i in range(len(feature_counts[feature])):
                feature_p_hats[feature][i][0] = feature_counts[feature][i][0] / y_counts[0]
                feature_p_hats[feature][i][1] = feature_counts[feature][i][1] / y_counts[1]
        for i in range(NUM_MOODS):
            y_p_hats[i] = y_counts[i] / len(data)
    else:
        # for each feature
        for feature in feature_counts:
            # for each value that the feature could take on
            for i in range(len(feature_counts[feature])):
                feature_p_hats[feature][i][0] = (feature_counts[feature][i][0] + 1)/ (y_counts[0] + 2)
                feature_p_hats[feature][i][1] = (feature_counts[feature][i][1] + 1) / (y_counts[1] + 2)
        for i in range(NUM_MOODS):
            y_p_hats[i] = (y_counts[i] + 1) / (len(data) + 2)

    return feature_p_hats, y_p_hats


def test(data, feature_p_hats, y_p_hats):
    num_features = len(data[1]) - 1
    y_index = num_features

    class_0_tested = 0
    class_0_correct = 0
    class_1_tested = 0
    class_1_correct = 0

    for row in data:
        predictions = []
        for y_val in range(NUM_MOODS):
            prediction = y_p_hats[y_val]
            for feature in feature_p_hats:
                x_val = row[feature]
                prediction *= feature_p_hats[feature][x_val][y_val]
            predictions.append(prediction)
        predicted_y = np.argmax(predictions)

        # check prediction accuracy
        if row[y_index] == 0:
            class_0_tested += 1
            if predicted_y == 0:
                class_0_correct += 1
        else:
            class_1_tested += 1
            if predicted_y == 1:
                class_1_correct += 1

    total_tested = class_0_tested + class_1_tested
    total_correct = class_0_correct + class_1_correct
    accuracy = total_correct / total_tested

    print("Class 0: tested", class_0_tested, ", correctly classified", class_0_correct)
    print("Class 1: tested", class_1_tested, ", correctly classified", class_1_correct)
    print("Overall: tested", total_tested, ", correctly classified", total_correct)
    print("Accuracy =", accuracy)


def analyze_song(song_data, feature_p_hats, y_p_hats):
    predictions = []
    for y_val in range(NUM_MOODS):
        prediction = y_p_hats[y_val]
        for feature in feature_p_hats:
            x_val = song_data[feature]
            prediction *= feature_p_hats[feature][x_val][y_val]
        predictions.append(prediction)
    predicted_y = np.argmax(predictions)
    return predicted_y


def decimal_to_discrete(decimal):
    return math.floor(decimal * 10)


def get_track_features(sp, track_url):
    meta = sp.track(track_url)
    features = sp.audio_features(track_url)

    print("Okay, running algorithm on", meta['name'])
    acousticness = decimal_to_discrete(features[0]['acousticness'])
    danceability = decimal_to_discrete(features[0]['danceability'])
    energy = decimal_to_discrete(features[0]['energy'])
    key = features[0]['key']
    mode = features[0]['mode']
    valence = decimal_to_discrete(features[0]['valence'])

    track = [acousticness, danceability, energy, key, mode, valence]
    return track


def main():
    mode = input("Welcome to the song mood guesser ^_^ Press 1 to see accuracy reports, ot press 2 to analyze a song: ")
    training = np.genfromtxt(
        "mood_training.csv",  # filename
        delimiter=',',  # csv cells are demarcated with commas
        skip_header=1,
        dtype=np.int8 # This informs how all data should be interpreted
    )
    feature_p_hats_mle, y_p_hats_mle = train(training, True)

    if mode == "1":
        testing = np.genfromtxt(
            "mood_testing.csv",  # filename
            delimiter=',',  # csv cells are demarcated with commas
            skip_header=1,
            dtype=np.int8 # This informs how all data should be interpreted
        )
        print("Classification results with MLE:")
        test(testing, feature_p_hats_mle, y_p_hats_mle)
        print("---------------------------------------")
        feature_p_hats_map, y_p_hats_map = train(training, False)
        print("Classification results with MAP:")
        test(testing, feature_p_hats_map, y_p_hats_map)
    elif mode == "2":
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=CID, client_secret=SECRET,
                                                       redirect_uri=REDIRECT_URI))
        song = input("Enter a Spotify song URL, or type 'quit' to quit: ")
        while song != "quit":
            # okay I didn't wrap this in an except so I'm just trusting that the URL is correct... oops
            song_data = get_track_features(sp, song)
            print("Analyzing ...")
            # for dramatic effect :)
            time.sleep(1)
            print("Wait for it...")
            # also for dramatic effect B)
            time.sleep(1)
            prediction = analyze_song(song_data, feature_p_hats_mle, y_p_hats_mle)
            if prediction == 0:
                print("I think that this song is sad :'(")
            else:
                print("I think that this song is happy :D")
            song = input("Enter a Spotify song URL, or type 'quit' to quit: ")

        print("bye!")
    else:
        print("bye!")


if __name__ == "__main__":
    main()
