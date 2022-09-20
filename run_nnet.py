import argparse
import numpy
import pandas as pd
from keras import backend as K
from keras.models import Sequential
from keras.layers import Dense
from keras.models import model_from_json
from ngram_classifier import NGramClassifier
from sklearn.metrics import precision_recall_fscore_support

THRESHOLD = 0.80

CLASS_WEIGHTS = [
    ("num_days", 0.997821848),
    ("statuses_per_day", 1.065570851),
    ("followers_per_day", 1.021055002),
    ("following_per_day", 1.122703153),
    ("desc_len_terms", 1.171072307),
    ("num_list_items", 1.017727903),
    ("num_hashtags", 0.889418197),
    ("url_count", 1.018365516)
]


def get_input_vector(row, classifier):
    '''
    (classifier): p_good
    (classifier): p_bot
    num_days
    statuses_per_day
    followers_per_day
    following_per_day
    desc_len_terms
    num_list_items
    num_hashtags
    url_count
    '''
    class_probs = classifier.classify_text(
        str(row["user_profile_description"]))
    ret = [class_probs["good"], class_probs["bot"]]
    for label, weight in CLASS_WEIGHTS:
        try:
            ret.append(float(row[label]) * weight)
        except:
            ret.append(0.0)
    return ret


def get_training_output(row):
    class_label = str(row["class_value"])
    return 0.0 if class_label == "good" else 1.0


def recall_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)))
    recall = true_positives / (possible_positives + K.epsilon())
    return recall


def precision_m(y_true, y_pred):
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)))
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)))
    precision = true_positives / (predicted_positives + K.epsilon())
    return precision


def f1_m(y_true, y_pred):
    precision = precision_m(y_true, y_pred)
    recall = recall_m(y_true, y_pred)
    return 2*((precision*recall)/(precision+recall+K.epsilon()))


def is_bot_value(is_verified, value):
    if is_verified:
        return "good"
    return "bot" if value > THRESHOLD else "good"


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="test input csv file")
    parser.add_argument("-m", "--model", help="ngram model file")
    parser.add_argument("-n", "--nnetmodel", help="NNet model file")
    parser.add_argument("-o", "--output", help="output csv file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input file"
    if not args.model:
        raise "missing ngram model file"
    if not args.nnetmodel:
        raise "missing nnet model file"
    if not args.output:
        raise "missing output file"

    classifier = NGramClassifier(model_path=args.model)

    with open(args.nnetmodel, 'r') as json_file:
        loaded_model_json = json_file.read()
        nnet = model_from_json(loaded_model_json)
    nnet.load_weights(f'{args.nnetmodel}.h5')
    nnet.compile(loss='binary_crossentropy', optimizer='adam',
                 metrics=['acc', f1_m, precision_m, recall_m])

    df_test = pd.read_csv(args.input, keep_default_na=False)

    df_test = df_test.drop(df_test[df_test.verified == True].index)
    indexes = []
    targets_x = []
    predictions = []
    for index, row in df_test.iterrows():
        try:
            input_vector = get_input_vector(row, classifier)
        except:
            print(f'(error parsing row {index}... skipping...)')
            continue
        indexes.append(index)
        targets_x.append(input_vector)
    predictions = nnet.predict(numpy.array(targets_x))
    df_test["is_bot_belief"] = predictions
    df_test["is_bot"] = df_test.apply(lambda row: is_bot_value(
        row["verified"], row["is_bot_belief"]), axis=1)

    df_test.to_csv(args.output)
