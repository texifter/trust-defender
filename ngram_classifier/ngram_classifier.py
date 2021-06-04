import pickle
import math
from .ngram_classifier_record import NGramClassifierRecord
from collections import Counter, Sequence
import utils as text_utils


class NGramClassifier():

    def __init__(self, classes=None,
                 model_path=None,
                 min_len=2, max_len=5
                 ):

        self._classes = {}
        self._trained = False
        self._min = min_len
        self._max = max_len
        if model_path:
            self.load(model_path)
            return

        if not classes:
            raise "missing parameter classes"
        if not isinstance(classes, list):
            raise "invalid value for parameter classes"

        for this_class in classes:
            these_classes = {}
            for nval in range(self._min, self._max):
                these_classes[nval] = NGramClassifierRecord()
            self._classes[this_class] = these_classes

    def _get_ngrams(self, text, ngram_count):
        ngram_list = list(text_utils.get_ngrams(text, ngram_count))
        return list("".join(n) for n in ngram_list)

    def _train_class(self, input_text, class_label):
        '''
        trains a class with the input text
        1) clean the input text
        2) for each ngram value in _min to _max:
            2a) get the ngrams for the cleaned text
            2b) update the ngram list for that class / ngram count
        '''
        if class_label not in self._classes:
            raise f'Unknown class label found: {class_label}'

        cleaned = text_utils.clean_text(input_text)
        for nval in range(self._min, self._max):
            if len(cleaned) < nval:
                continue
            ngram_list = self._get_ngrams(cleaned, nval)
            self._classes[class_label][nval].add(ngram_list)

    def _get_default_classify_return(self):
        ret = {}
        per_class = 1/len(self._classes.keys())
        for this_class in self._classes.keys():
            ret[this_class] = per_class
        return ret

    def _get_scale_factor(self, text_length):
        if text_length <= 10:
            return 1.0
        return 1.0 / math.pow(math.log(text_length), 2)

    def _calculate_classify_ratios(self, input_text):
        text_length = len(input_text)
        scale_factor = self._get_scale_factor(text_length)
        class_ratios = []
        for nval in range(self._min, self._max):
            if len(input_text) < nval:
                continue

            class_counts = {}
            overall_count = 0
            for this_class in self._classes.keys():
                this_count = self._classes[this_class][nval].total_count
                overall_count += this_count
                class_counts[this_class] = this_count

            p = {}
            for this_class in self._classes.keys():
                p[this_class] = math.log((class_counts[this_class] + 1) * (
                    1 - class_counts[this_class] / overall_count) / (class_counts[this_class] + overall_count))

            ngram_list = self._get_ngrams(input_text, nval)

            for this_ngram in ngram_list:
                count_class = {}
                for this_class in self._classes.keys():
                    p_count = 0 if this_ngram not in self._classes[this_class][
                        nval].ngrams else self._classes[this_class][nval].ngrams[this_ngram]
                    p_gram = (p_count + 1) / \
                        (class_counts[this_class] + overall_count)
                    p[this_class] += math.log(p_gram)

            d = 0.0
            for this_class in self._classes.keys():
                p[this_class] *= scale_factor
                d += math.exp(p[this_class])

            if d != 0.0:
                vals = {}
                for this_class in self._classes.keys():
                    vals[this_class] = math.exp(p[this_class]) / d
                class_ratios.append(vals)

        return class_ratios

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    # ----------------------------------------------------------------

    def classify_text(self, input_text, is_cleaned=False):
        """Classify input text

        Returns a dictionary of {
            "class_1": p(c1),
            "class_2": p(c2),
            ... etc ...
        }
        """

        assert(self._trained), "model must be trained before classifying"

        if is_cleaned:
            cleaned_text = input_text
        else:
            cleaned_text = text_utils.clean_text(input_text)

        if len(cleaned_text) < 2:
            return self._get_default_classify_return()

        class_ratios = self._calculate_classify_ratios(cleaned_text)
        if len(class_ratios) == 0:
            return self._get_default_classify_return()

        avgs = {}
        total_avg = 0.0
        for this_ratio_set in class_ratios:
            for this_class in self._classes.keys():
                if not this_class in avgs:
                    avgs[this_class] = this_ratio_set[this_class]
                else:
                    avgs[this_class] += this_ratio_set[this_class]
                total_avg += this_ratio_set[this_class]

        if total_avg == 0.0:
            return self._get_default_classify_return()

        ret = {}
        for this_class in self._classes.keys():
            ret[this_class] = avgs[this_class] / total_avg
        return ret

    def classify_text_list(self, text_list):
        return ([self.classify_text(t) for t in text_list])

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    # ----------------------------------------------------------------

    def train_text(self, text_items, class_designations):
        assert(len(text_items) == len(class_designations)
               ), "Input arrays must be equal length"

        for index in range(0, len(text_items)):
            this_text = text_items[index]
            this_class = class_designations[index]
            self._train_class(this_text, this_class)
        self._trained = True
        self.update_counts()

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    # ----------------------------------------------------------------

    def update_counts(self):
        """ Manual call to update the total counts for each class """
        for this_class in self._classes.keys():
            for nval in range(self._min, self._max):
                self._classes[this_class][nval].update_total()

    # ----------------------------------------------------------------
    # ----------------------------------------------------------------
    # ----------------------------------------------------------------

    def serialize(self, output_path, max_to_save):
        """Saves the classifier data to a file
        writes out the min/max ngrams, the class list, and the class data/counts for each
        """
        with open(output_path, 'wb') as output_file:
            pickle.dump(self._min, output_file)
            pickle.dump(self._max, output_file)
            key_list = list(self._classes.keys())
            pickle.dump(key_list, output_file)
            for this_key in key_list:
                for nval in range(self._min, self._max):
                    pickle.dump(
                        dict(self._classes[this_key][nval].ngrams.most_common(max_to_save)), output_file)

    def load(self, input_path):
        """Loads classifier data from a file
        includes the min/max ngrams, the class list, and the class data/counts
        """
        self._classes = {}
        self._trained = False
        with open(input_path, 'rb') as input_file:
            self._min = pickle.load(input_file)
            self._max = pickle.load(input_file)
            key_list = pickle.load(input_file)
            for this_class in key_list:
                these_classes = {}
                for nval in range(self._min, self._max):
                    ngram_data = pickle.load(input_file)
                    these_classes[nval] = NGramClassifierRecord()
                    these_classes[nval].ngrams = Counter(ngram_data)
                    these_classes[nval].update_total()
                self._classes[this_class] = these_classes
        self._trained = True
