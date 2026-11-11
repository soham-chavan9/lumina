"""Offline embeddings used when OpenAI is unavailable.

A hashed bag-of-words: each content word is cut to its first 5 letters (so
"notify"/"notification" and "timeline"/"timelines" match), hashed (CRC32, stable
across runs) into a fixed number of buckets, weighted by 1 + log(term
frequency), then L2-normalised. Retrieval is keyword-based rather than semantic, but it needs no
network, no model download and no GPU, so search keeps working offline.
"""

from __future__ import annotations

import math
import re
import zlib

import numpy as np
from langchain_core.embeddings import Embeddings

_TOKEN = re.compile(r"[a-z0-9]+")
_STOPWORDS = frozenset(
    """a about after all also an and any are as at be been before being but by can
    could did do does for from had has have how if in into is it its may might more
    must no not of on or other our out shall should so such than that the their them
    then there these they this those to under up upon was we were what when where
    which while who will with within would you your""".split()
)


class LocalHashEmbeddings(Embeddings):
    def __init__(self, dim: int = 2048):
        self.dim = dim

    def _embed(self, text: str) -> list[float]:
        counts: dict[int, int] = {}
        for token in _TOKEN.findall(text.lower()):
            if len(token) < 2 or token in _STOPWORDS:
                continue
            if token.isalpha():
                token = token[:5]
            bucket = zlib.crc32(token.encode()) % self.dim
            counts[bucket] = counts.get(bucket, 0) + 1
        vec = np.zeros(self.dim, dtype=np.float32)
        for bucket, tf in counts.items():
            vec[bucket] = 1.0 + math.log(tf)
        norm = float(np.linalg.norm(vec))
        if norm:
            vec /= norm
        return vec.tolist()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)
