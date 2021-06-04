import argparse
import pandas as pd
from ngram_classifier import NGramClassifier
from sklearn.metrics import precision_recall_fscore_support


def get_prediction(p):
    return "bot" if p["bot"] > p["good"] else "good"


def print_metrics(metrics):
    print(f'precision: (good) {metrics[0][0]}, (bot) {metrics[0][1]}')
    print(f'recall: (good) {metrics[1][0]}, (bot) {metrics[1][1]}')
    print(f'fscore: (good) {metrics[2][0]}, (bot) {metrics[2][1]}')
    print(f'counts: (good) {metrics[3][0]}, (bot) {metrics[3][1]}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input test csv file")
    parser.add_argument("-m", "--model", help="model file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input file"
    if not args.model:
        raise "missing model file"

    classifier = NGramClassifier(model_path=args.model)

    df = pd.read_csv(args.input, keep_default_na=False)
    x_values = []
    y_values = []
    for index, row in df.iterrows():
        this_text = str(row["user_profile_description"])
        this_class = str(row["class_value"])
        if this_text and len(this_text) > 0 and this_class and len(this_class) > 0:
            x_values.append(this_text)
            y_values.append(this_class)

    predicted = classifier.classify_text_list(x_values)

    targets = []
    predictions = []
    for i in range(0, len(x_values)):
        predictions.append(get_prediction(predicted[i]))
        targets.append(y_values[i])

    metrics = precision_recall_fscore_support(targets, predictions)
    print_metrics(metrics)
