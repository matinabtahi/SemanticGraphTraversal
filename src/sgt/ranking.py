"""Pluggable relevance scoring; scores are not probabilities or truth values."""
import math
import re
from collections import Counter


def tokens(text):
    return re.findall(r"[a-z0-9]+", re.sub(r"([a-z])([A-Z])", r"\1 \2", text).lower())


class LexicalScorer:
    """Offline token cosine baseline, explicitly not embedding similarity."""
    name = "lexical-cosine"

    def score(self, query, texts):
        q = Counter(tokens(query))
        normq = math.sqrt(sum(v*v for v in q.values()))
        values = []
        for text in texts:
            d = Counter(tokens(text))
            denominator = normq * math.sqrt(sum(v*v for v in d.values()))
            values.append(sum(v*d[k] for k, v in q.items()) / denominator if denominator else 0.0)
        return values


class SentenceTransformerScorer:
    """Optional local embeddings. Model download is explicit on construction."""
    def __init__(self, model="sentence-transformers/all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)
        self.name = f"sentence-transformers:{model}"

    def score(self, query, texts):
        if not texts:
            return []
        q = self.model.encode([query], normalize_embeddings=True)[0]
        vectors = self.model.encode(texts, normalize_embeddings=True)
        return [float(v @ q) for v in vectors]
