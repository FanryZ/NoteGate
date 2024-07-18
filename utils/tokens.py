import jieba
import jieba.posseg as pseg
from .page import Page
from itertools import chain

filtered_flags = ["m", "q", "uj", "x", "r", "d", "p", "c", "u", "xc", "w"]

def tokenize(p: Page):
    tokens = pseg.cut(p.title)
    if p.excerpt:
        tokens = chain(
            tokens,
            pseg.cut(p.excerpt)
        )
    words = [word for word, flag in tokens \
             if flag not in filtered_flags]
    return " ".join(words)
