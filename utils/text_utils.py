import html
import re
import string
import sys
import unicodedata
from itertools import islice, tee, groupby
from nltk.tokenize import WordPunctTokenizer

regex_clean_newlines = re.compile(r"[\r|\n|\r\n]")
regex_strip_urls = re.compile(r"\[http[s]?://.*?\s(.*?)\]")
regex_strip_punct = re.compile(r'[%s]' % re.escape(string.punctuation))

punct_unicode_tbl = dict.fromkeys(i for i in range(sys.maxunicode)
                                  if unicodedata.category(chr(i)).startswith('P'))


def get_ngrams(str_, n_grams=2):
    '''
    gets all the ngrams for a string
    '''
    tuples = zip(*(islice(seq, index, None)
                   for index, seq in enumerate(tee("".join(str_.split()), n_grams))))
    return list("".join(tup) for tup in tuples)


def count_ngrams(str_, n_grams=2):
    '''
    returns a list of the counts of each ngram in the input
    sorted by greatest to least count
    '''
    ngrams = get_ngrams(str_, n_grams)
    ret_list = [(key, len(list(group)))
                for key, group in groupby(sorted(ngrams))]
    ret_list = sorted(ret_list, key=lambda x: x[1])
    ret_list.reverse()
    return ret_list


def count_repeating_ngrams(str_, ngrams=(2, 4), n_repeats_min=2):
    '''
    Sums the count of number of ngrams that repeat equal to or
    more than 'n_repeats_min' times
    Example:
        count_repeating_ngrams('aaaa', ngrams(2,2)) -> [3]
        count_repeating_ngrams('aaaa', ngrams(2,3)) -> [3,2]
        count_repeating_ngrams('abab', ngrams(2,2)) -> [2]
    '''
    output = list()
    for ngram in range(ngrams[0], ngrams[1] + 1):
        ngrams = count_ngrams(str_, ngram)
        this_count = sum(this_ngram[1] if this_ngram[1] >=
                         n_repeats_min else 0 for this_ngram in ngrams)
        output.append(this_count)
    return output


def remove_punctuation(input_string):
    working = regex_strip_punct.sub(" ", input_string)
    return working.translate(punct_unicode_tbl)


def clean_newlines(input_text):
    return regex_clean_newlines.sub(" ", input_text)


def clean_text(str_, remove_urls=False):
    if not str_:
        return ""

    cleaned = clean_newlines(str(str_))
    cleaned = html.unescape(cleaned)
    if remove_urls:
        cleaned = regex_strip_urls.sub(" ", cleaned)
    cleaned = remove_punctuation(cleaned)
    cleaned = re.sub(r"=", " ", cleaned)
    cleaned = re.sub(r"\s\s+", " ", cleaned)

    return cleaned.strip().lower()


def tokenize(str_):
    return WordPunctTokenizer().tokenize(str_)


def get_list_item_count(raw_text):
    splitted = re.split(r'[\.;\:]', raw_text)
    return len(splitted)


def get_list_item_count(raw_text):
    splitted = re.split(r'[\.;\:]', raw_text)
    return len(splitted)


def get_hashtags(input_text):
    return re.findall(r'#(\w+)', input_text)


def get_hashtag_count(tokens):
    counter = 0
    prev_was_hash = False
    for this_token in tokens:
        if this_token == "#":
            prev_was_hash = True
            continue
        if this_token.isalpha() and prev_was_hash:
            counter += 1
        prev_was_hash = False
    return counter


def get_urls(raw_text):
    return re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', raw_text)


def get_url_count(raw_text):
    return len(get_urls(raw_text))
