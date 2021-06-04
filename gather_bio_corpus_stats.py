import argparse
from collections import Counter
from nltk.corpus import stopwords
from utils import clean_text, tokenize, get_urls, get_hashtags
from sklearn.feature_extraction.text import CountVectorizer
import pandas as pd

stop_words = stopwords.words('english')


class StatsCorpus():
    def __init__(self):
        self._corpus = []
        self._total_terms = 0
        self._unique_terms = Counter()


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False


def get_tokens_for_counting(tokens):
    ret = []
    for this_token in tokens:
        if len(this_token) < 3:
            continue
        if is_number(this_token):
            continue
        ret.append(this_token)
    return ret


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", help="input csv file")
    args = parser.parse_args()

    df = pd.read_csv(args.input, keep_default_na=False)
    term_counter = Counter()
    hashtag_counter = Counter()
    url_counter = Counter()
    for index, row in df.iterrows():
        input_text = str(row["user_profile_description"])
        if not input_text:
            continue

        urls = get_urls(input_text)
        hashtags = get_hashtags(input_text)
        cleaned = clean_text(input_text, remove_urls=True)
        tokens = tokenize(cleaned)
        if len(tokens) == 0:
            continue
        tokens = [x for x in tokens if x not in stop_words]
        tokens_for_count = get_tokens_for_counting(tokens)
        for token in tokens_for_count:
            term_counter[token] += 1

        for url in urls:
            url_counter[url.lower()] += 1
        for hashtag in hashtags:
            hashtag_counter[hashtag.lower()] += 1

    print('top 100 terms:')
    print(term_counter.most_common(100))
    print(f'{len(term_counter)} unique, {sum(term_counter.values())} total')

    print('top 100 urls:')
    print(url_counter.most_common(100))

    print("top 100 hashtags:")
    print(hashtag_counter.most_common(100))
    print(f'{len(hashtag_counter)} unique, {sum(hashtag_counter.values())} total')
