#import theano
#theano.config.device = 'gpu'
#theano.config.floatX = 'float32'

import argparse
import csv
import numpy
from keras import backend as K
from keras.models import Sequential
from keras.layers import Dense
import pandas as pd
from ngram_classifier import NGramClassifier
from sklearn.metrics import precision_recall_fscore_support
from timeit import default_timer as timer
import tensorflow as tf

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
        ret.append(float(row[label]) * weight)
    return ret


def get_training_output(row):
    class_label = str(row["class_value"])
    return 0.0 if class_label == "good" else 1.0


def print_metrics(which_round, metrics):
    print(
        f'round: {which_round} : p() {metrics[0][0]:.4f}, {metrics[0][1]:.4f} : r() {metrics[1][0]:.4f}, {metrics[1][1]:.4f} : f() {metrics[2][0]:.4f}, {metrics[2][1]:.4f}')


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input csv file")
    parser.add_argument("-m", "--model", help="ngram model file")
    parser.add_argument("-o", "--output", help="output file")
    parser.add_argument("-n", "--numrounds", help="number rounds to train")
    parser.add_argument("-t", "--testfile", help="testing_file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input file"
    if not args.model:
        raise "missing model file"
    if not args.output:
        raise "missing output file"
    if not args.numrounds:
        raise "missing number of training rounds"
    if not args.testfile:
        raise "missing test file"

    classifier = NGramClassifier(model_path=args.model)

    num_training_rounds = int(args.numrounds)

    df = pd.read_csv(args.input, keep_default_na=False)
    df_test = pd.read_csv(args.testfile, keep_default_na=False)
    n_rows = len(df.index)

    nnet = Sequential()
    nnet.add(Dense(22, input_dim=10, activation='relu'))
    nnet.add(Dense(1, activation='sigmoid'))
    nnet.compile(loss='binary_crossentropy', optimizer='adam',
                 metrics=['acc', f1_m, precision_m, recall_m])

    print('----------------')

    # for i in range(0,num_training_rounds):
    start = timer()
    df_train = df.sample(frac=1.0).reset_index(drop=True)
    x_values = []
    y_values = []
    for index, row in df_train.iterrows():
        input_vector = get_input_vector(row, classifier)
        output_val = get_training_output(row)
        x_values.append(input_vector)
        y_values.append(output_val)
    nnet.fit(numpy.array(x_values), numpy.array(y_values),
             epochs=num_training_rounds, batch_size=25)

    targets_x = []
    targets_y = []
    predictions = []
    for index, row in df_test.iterrows():
        input_vector = get_input_vector(row, classifier)
        targets_x.append(input_vector)
        targets_y.append(get_training_output(row))
    loss, accuracy, f1_score, precision, recall = nnet.evaluate(
        numpy.array(targets_x), numpy.array(targets_y), verbose=0)

    end = timer()
    run_time = (end - start)

    print("model trained.")
    model_json = nnet.to_json()
    with open(args.output, "w") as json_file:
        json_file.write(model_json)
    # serialize weights to HDF5
    nnet.save_weights(f'{args.output}.h5')
