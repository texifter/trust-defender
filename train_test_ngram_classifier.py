import csv
import pandas as pd
from ngram_classifier import NGramClassifier
from sklearn.metrics import precision_recall_fscore_support
from timeit import default_timer as timer

CLASSES = ["bot", "good"]
TEXT_COLUMN = "user_profile_description"
CLASS_COLUMN = "class_value"

training_data = "./resources/training.csv"
testing_data = "./resources/test.csv"
metric_output = "./resources/test_ngram_metrics.csv"


def get_xy_for_data(df):
    x_values = []
    y_values = []
    for index, row in df_train.iterrows():
        this_text = str(row[TEXT_COLUMN])
        this_class = str(row[CLASS_COLUMN])
        if this_text and len(this_text) > 0 and this_class and len(this_class) > 0:
            x_values.append(this_text)
            y_values.append(this_class)
    return x_values, y_values


df_train = pd.read_csv(training_data, keep_default_na=False)
train_x, train_y = get_xy_for_data(df_train)

df_test = pd.read_csv(testing_data, keep_default_na=False)
test_x, test_y = get_xy_for_data(df_test)


def print_metrics(metrics):
    print(
        f'precision: ({CLASSES[0]}) {metrics[0][0]}, ({CLASSES[1]}) {metrics[0][1]}')
    print(
        f'recall: ({CLASSES[0]}) {metrics[1][0]}, ({CLASSES[1]}) {metrics[1][1]}')
    print(
        f'fscore: ({CLASSES[0]}) {metrics[2][0]}, ({CLASSES[1]}) {metrics[2][1]}')
    print(
        f'counts: ({CLASSES[0]}) {metrics[3][0]}, ({CLASSES[1]}) {metrics[3][1]}')


def get_prediction(p):
    return CLASSES[0] if p[CLASSES[0]] > p[CLASSES[1]] else CLASSES[1]


def run_class_and_test(ngram_min, ngram_max):
    classifier = NGramClassifier(
        classes=CLASSES, min_len=ngram_min, max_len=ngram_max)
    classifier.train_text(train_x, train_y)
    classifier.update_counts()

    predicted = classifier.classify_text_list(test_x)

    predictions = []
    for i in range(0, len(test_x)):
        predictions.append(get_prediction(predicted[i]))

    return precision_recall_fscore_support(test_y, predictions)


out_cols = ["range", f"p({CLASSES[0]})", f"p({CLASSES[1]})", f"r({CLASSES[0]})",
            f"r({CLASSES[1]})", f"f({CLASSES[0]})", f"f({CLASSES[1]})", "time"]

with open(metric_output, 'w') as metric_out:
    csv_writer = csv.writer(metric_out, delimiter=',',
                            quotechar='"', quoting=csv.QUOTE_MINIMAL)
    csv_writer.writerow(out_cols)
    for ngram_min in range(5, 10):
        for ngram_max in range(ngram_min, 10):
            print('----------------')
            print(f'testing ngrams({ngram_min},{ngram_max})')

            start = timer()
            metrics = run_class_and_test(ngram_min, ngram_max)
            end = timer()
            run_time = (end - start)
            print_metrics(metrics)

            metrics_row = [f'ngrams({ngram_min},{ngram_max})',
                           metrics[0][0], metrics[0][1],
                           metrics[1][0], metrics[1][1],
                           metrics[2][0], metrics[2][1],
                           run_time
                           ]
            csv_writer.writerow(metrics_row)

print('---- DONE ----')
