# from . import db
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB


class TokenClassfier():

    def __init__(self) -> None:
        self.tokenizer = None
        self.classifier = None

    def tokenize_fit(self, tokens, pros):
        X = self.tokenizer.fit_transform(tokens)
        self.classifier.fit(X, pros)

    def reset(self):
        self.tokenizer = TfidfVectorizer()
        self.classifier = MultinomialNB()

    def infer(self, tokens):
        Xs = self.tokenizer.transform(tokens)
        predictions = self.classifier.predict_proba(Xs)[:, 1]
        return predictions
    