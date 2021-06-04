from collections import Counter


class NGramClassifierRecord():
    def __init__(self):
        self.total_count = 0
        self.ngrams = Counter()

    def get_counts(self):
        return self.ngrams.most_common()

    def get_total(self):
        self.update_total(self)
        return self.total_count

    def add(self, ngrams):
        self.ngrams.update(ngrams)

    def update_total(self):
        self.total_count = sum(self.ngrams.values())
