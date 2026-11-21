"""Stage 4: local sentence embeddings.

Two backends, always reported honestly:

* MiniLMEmbedder  - sentence-transformers/all-MiniLM-L6-v2 on CPU. SEMANTIC.
* HashingEmbedder - signed feature hashing of content-word uni/bi-grams. LEXICAL ONLY:
  it measures shared words, not meaning. It exists so the application still runs
  (and can be tested) when the MiniLM model cannot be loaded.

All vectors are float32 and L2-normalised, so cosine similarity = dot product.
"""
import math
import re
import zlib
import logging

import numpy as np

log = logging.getLogger(__name__)
from app.nlp.stopwords import STOPWORDS

_TOKEN_RE = re.compile(r"[a-z0-9]+")


class BaseEmbedder:
    name = "base"          # stored with every vector
    model = ""
    is_semantic = False
    dim = 0

    def encode(self, texts):
        raise NotImplementedError

    def info(self):
        return {"backend": self.name, "model": self.model,
                "semantic": self.is_semantic, "dim": self.dim}


class HashingEmbedder(BaseEmbedder):
    is_semantic = False
    model = "signed feature hashing of content-word unigrams+bigrams"

    def __init__(self, dim=1024):
        self.dim = dim
        self.name = f"hashing:{dim}"

    def _vector(self, text):
        # stop-words are dropped: otherwise "the/of/with" overlap makes unrelated
        # sentences look similar to each other
        tokens = [t for t in _TOKEN_RE.findall(text.lower()) if t not in STOPWORDS]
        feats = tokens + [a + "_" + b for a, b in zip(tokens, tokens[1:])]
        vec = np.zeros(self.dim, dtype=np.float32)
        counts = {}
        for f in feats:
            counts[f] = counts.get(f, 0) + 1
        for f, c in counts.items():
            h = zlib.crc32(f.encode("utf-8"))
            sign = 1.0 if (h >> 31) & 1 else -1.0
            vec[h % self.dim] += sign * (1.0 + math.log(c))
        norm = np.linalg.norm(vec)
        return vec / norm if norm > 0 else vec

    def encode(self, texts):
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack([self._vector(t) for t in texts]).astype(np.float32)


class MiniLMEmbedder(BaseEmbedder):
    is_semantic = True

    def __init__(self, model_name):
        from sentence_transformers import SentenceTransformer   # may raise ImportError
        self.model = model_name
        self._m = SentenceTransformer(model_name, device="cpu")  # may raise (download/load)
        self.dim = int(self._m.get_sentence_embedding_dimension())
        self.name = f"minilm:{model_name}"

    def encode(self, texts):
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        out = self._m.encode(list(texts), batch_size=32, normalize_embeddings=True,
                             show_progress_bar=False, convert_to_numpy=True)
        return np.asarray(out, dtype=np.float32)


_cache = {"embedder": None, "fallback_reason": None, "key": None}


def get_embedder(config=None):
    """Return the process-wide embedder chosen by EMBEDDING_BACKEND."""
    if config is None:
        from flask import current_app
        config = current_app.config
    mode = str(config.get("EMBEDDING_BACKEND", "auto")).lower()
    model = config.get("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    dim = int(config.get("HASHING_DIM", 1024))
    key = (mode, model, dim)
    if _cache["embedder"] is not None and _cache["key"] == key:
        return _cache["embedder"]

    embedder, reason = None, None
    if mode in ("auto", "minilm"):
        try:
            embedder = MiniLMEmbedder(model)
            log.info("Using semantic embedder %s", embedder.name)
        except Exception as exc:                      # not installed / cannot download
            reason = f"MiniLM unavailable ({type(exc).__name__}: {exc})"
            if mode == "minilm":
                raise RuntimeError(reason)
            log.warning("%s - falling back to the lexical hashing embedder", reason)
    elif mode != "hashing":
        raise RuntimeError(f"Unknown EMBEDDING_BACKEND '{mode}' (use auto|minilm|hashing)")
    if embedder is None:
        embedder = HashingEmbedder(dim)
    _cache.update(embedder=embedder, fallback_reason=reason, key=key)
    return embedder


def embedder_status(config=None):
    emb = get_embedder(config)
    info = emb.info()
    info["fallback_reason"] = _cache["fallback_reason"]
    info["note"] = ("Semantic embeddings (MiniLM)." if emb.is_semantic else
                    "LEXICAL fallback: similarity reflects shared words, not meaning.")
    return info


def set_embedder(embedder):
    """Test hook / manual override."""
    _cache.update(embedder=embedder, fallback_reason=None, key=None)


def reset_embedder():
    _cache.update(embedder=None, fallback_reason=None, key=None)


def cosine_matrix(a, b):
    """Rows of a x rows of b cosine similarity (inputs already L2-normalised)."""
    return np.asarray(a, dtype=np.float32) @ np.asarray(b, dtype=np.float32).T
