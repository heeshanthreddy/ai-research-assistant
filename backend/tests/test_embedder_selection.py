"""Embedder selection / fallback logic.

The real MiniLM model cannot be downloaded in every environment, so the MiniLM
wrapper is exercised through a stand-in `sentence_transformers` module. These
tests verify OUR wrapper code (CPU device, normalisation flag, dtype, fallback
rules). They do not measure MiniLM's semantic quality.
"""
import sys
import types
import unittest

import numpy as np

from app.nlp import embeddings


class _FakeST:
    calls = []

    def __init__(self, name, device=None):
        _FakeST.calls.append(("init", name, device))

    def get_sentence_embedding_dimension(self):
        return 384

    def encode(self, texts, **kw):
        _FakeST.calls.append(("encode", kw))
        return np.ones((len(texts), 384), dtype=np.float64) / np.sqrt(384)


def _install_fake(present):
    sys.modules.pop("sentence_transformers", None)
    if present:
        mod = types.ModuleType("sentence_transformers")
        mod.SentenceTransformer = _FakeST
        sys.modules["sentence_transformers"] = mod
    else:
        sys.modules["sentence_transformers"] = None      # makes `import` raise ImportError


class Selection(unittest.TestCase):
    def setUp(self):
        embeddings.reset_embedder()
        self._old = sys.modules.get("sentence_transformers")
        _FakeST.calls.clear()

    def tearDown(self):
        embeddings.reset_embedder()
        if self._old is None:
            sys.modules.pop("sentence_transformers", None)
        else:
            sys.modules["sentence_transformers"] = self._old

    def test_auto_uses_minilm_on_cpu_when_available(self):
        _install_fake(True)
        e = embeddings.get_embedder({"EMBEDDING_BACKEND": "auto"})
        self.assertTrue(e.is_semantic)
        self.assertEqual(e.name, "minilm:sentence-transformers/all-MiniLM-L6-v2")
        self.assertEqual(_FakeST.calls[0], ("init", "sentence-transformers/all-MiniLM-L6-v2", "cpu"))
        v = e.encode(["a", "b"])
        self.assertEqual(v.dtype, np.float32)
        self.assertEqual(v.shape, (2, 384))
        self.assertTrue(_FakeST.calls[-1][1]["normalize_embeddings"])

    def test_auto_falls_back_to_hashing_and_says_why(self):
        _install_fake(False)
        e = embeddings.get_embedder({"EMBEDDING_BACKEND": "auto"})
        self.assertFalse(e.is_semantic)
        st = embeddings.embedder_status({"EMBEDDING_BACKEND": "auto"})
        self.assertIn("LEXICAL", st["note"])
        self.assertIn("MiniLM unavailable", st["fallback_reason"])

    def test_explicit_minilm_does_not_silently_fall_back(self):
        _install_fake(False)
        with self.assertRaises(RuntimeError):
            embeddings.get_embedder({"EMBEDDING_BACKEND": "minilm"})

    def test_explicit_hashing_never_loads_minilm(self):
        _install_fake(True)
        e = embeddings.get_embedder({"EMBEDDING_BACKEND": "hashing"})
        self.assertFalse(e.is_semantic)
        self.assertEqual(_FakeST.calls, [])

    def test_unknown_backend_rejected(self):
        with self.assertRaises(RuntimeError):
            embeddings.get_embedder({"EMBEDDING_BACKEND": "gemini"})


if __name__ == "__main__":
    unittest.main()
