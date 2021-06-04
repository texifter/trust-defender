import argparse
import pandas as pd
from ngram_classifier import NGramClassifier

CLASSES = ["bot", "good"]
TEXT_COLUMN = "user_profile_description"
CLASS_COLUMN = "class_value"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input csv file")
    parser.add_argument("-o", "--output", help="output file")
    args = parser.parse_args()

    if not args.input:
        raise "missing input file"
    if not args.output:
        raise "missing output file"

    classifier = NGramClassifier(classes=CLASSES, min_len=5, max_len=9)

    df = pd.read_csv(args.input, keep_default_na=False)
    x_values = []
    y_values = []
    total_rows = len(df.index)
    for index, row in df.iterrows():
        this_text = str(row[TEXT_COLUMN])
        this_class = str(row[CLASS_COLUMN])
        if this_text and len(this_text) > 0 and this_class and len(this_class) > 0:
            x_values.append(this_text)
            y_values.append(this_class)

        if index % 1000 == 0:
            print(f'trained {index} of {total_rows}')

    classifier.train_text(x_values, y_values)
    classifier.serialize(args.output, max_to_save=100000)
