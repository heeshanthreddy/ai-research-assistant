"""Functional unit tests for the NLP building blocks (no database, no network)."""
import math
import unittest

import numpy as np

from app.nlp.preprocessing import split_sentences, clean_page_text, segment_document
from app.nlp.chunking import semantic_chunk
from app.nlp.preprocessing import Sentence
from app.nlp.embeddings import HashingEmbedder
from app.nlp.retrieval import mmr
from app.nlp import metrics
from app.nlp import citations as cit
from app.nlp.idea_analysis import content_bigrams


class SentenceSplitting(unittest.TestCase):
    def test_abbreviations_and_decimals_do_not_split(self):
        text = ("Smith et al. reported 0.85 accuracy on Fig. 3. The model is fast. "
                "K. Reddy used e.g. BERT, i.e. a transformer (see Sec. 4.2). It reached 92.5% on No. 5!")
        s = split_sentences(text)
        self.assertEqual(len(s), 4)
        self.assertTrue(s[0].endswith("Fig. 3."))
        self.assertTrue(s[2].startswith("K. Reddy"))

    def test_hyphenation_and_page_numbers(self):
        out = clean_page_text("We study seman-\ntic search over the\nlarge corpus.\n7")
        self.assertIn("semantic search over the large corpus.", out)
        self.assertNotIn("7", out)

    def test_repeated_headers_removed_and_pages_tracked(self):
        pages = [(i, f"Running Header\nSentence number {i} is here. Another one follows.") for i in (1, 2, 3)]
        sents = segment_document(pages)
        self.assertTrue(all("Running Header" not in s.text for s in sents))
        self.assertEqual({s.page for s in sents}, {1, 2, 3})

    def test_sentence_continued_across_pages_is_joined(self):
        sents = segment_document([(1, "This sentence continues on the"), (2, "next page without stopping. New one.")])
        self.assertEqual(sents[0].page, 1)
        self.assertIn("continues on the next page", sents[0].text)


class Embedder(unittest.TestCase):
    def test_hashing_is_normalised_and_lexical(self):
        e = HashingEmbedder(512)
        v = e.encode(["dense retrieval of papers", "dense retrieval of papers", "completely different words here"])
        self.assertAlmostEqual(float(np.linalg.norm(v[0])), 1.0, places=5)
        self.assertAlmostEqual(float(v[0] @ v[1]), 1.0, places=5)
        self.assertLess(float(v[0] @ v[2]), 0.3)
        self.assertFalse(e.is_semantic)


class Chunking(unittest.TestCase):
    def _sents(self, topics, per_topic=8):
        sents = []
        for t in topics:
            for i in range(per_topic):
                sents.append(Sentence(f"{t} word number {i} " + " ".join([t] * 6) + " filler text here.", 1))
        return sents

    def test_chunks_follow_topic_changes_and_keep_sentences(self):
        sents = self._sents(["alpha", "beta", "gamma"])
        chunks = semantic_chunk(sents, HashingEmbedder(512).encode, min_tokens=10, max_tokens=500,
                                break_std=0.5, window=3)
        self.assertGreater(len(chunks), 1)
        joined = " ".join(c["text"] for c in chunks)
        for s in sents:                                    # no sentence lost or cut
            self.assertIn(s.text, joined)
        # a topic boundary should not leave a chunk mixing alpha and gamma
        for c in chunks:
            self.assertFalse("alpha" in c["text"] and "gamma" in c["text"])

    def test_max_size_enforced(self):
        sents = self._sents(["alpha"], per_topic=40)
        chunks = semantic_chunk(sents, HashingEmbedder(512).encode, min_tokens=5, max_tokens=60)
        self.assertTrue(all(c["word_count"] <= 60 or c["sentence_count"] == 1 for c in chunks))
        self.assertGreater(len(chunks), 3)

    def test_min_size_merges_small_chunks(self):
        sents = self._sents(["alpha", "beta"], per_topic=3)
        chunks = semantic_chunk(sents, HashingEmbedder(512).encode, min_tokens=40, max_tokens=500)
        self.assertTrue(all(c["word_count"] >= 40 for c in chunks) or len(chunks) == 1)

    def test_empty_and_single(self):
        self.assertEqual(semantic_chunk([], HashingEmbedder().encode), [])
        self.assertEqual(len(semantic_chunk([Sentence("Only one sentence here.", 3)], HashingEmbedder().encode)), 1)


class MMR(unittest.TestCase):
    def test_diversity_beats_near_duplicate(self):
        q = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        a = np.array([0.99, 0.14, 0.0]); a /= np.linalg.norm(a)           # most relevant
        b = np.array([0.98, 0.15, 0.0]); b /= np.linalg.norm(b)           # near-duplicate of a
        c = np.array([0.80, 0.0, 0.6]); c /= np.linalg.norm(c)            # relevant but different
        vecs = np.vstack([a, b, c]).astype(np.float32)
        self.assertEqual(mmr(q, vecs, 2, lam=0.5), [0, 2])                # picks diverse c over b
        self.assertEqual(mmr(q, vecs, 2, lam=1.0), [0, 1])                # lambda=1: pure relevance
        self.assertEqual(mmr(q, vecs, 5, lam=0.7)[0], 0)
        self.assertEqual(mmr(q, np.zeros((0, 3)), 3, 0.7), [])


class Metrics(unittest.TestCase):
    def test_hand_computed_values(self):
        ranked, rel = [5, 3, 9, 1], [3, 1]
        self.assertAlmostEqual(metrics.recall_at_k(ranked, rel, 2), 0.5)
        self.assertAlmostEqual(metrics.recall_at_k(ranked, rel, 4), 1.0)
        self.assertAlmostEqual(metrics.reciprocal_rank(ranked, rel), 0.5)
        dcg = 1 / math.log2(3) + 1 / math.log2(5)
        ideal = 1 / math.log2(2) + 1 / math.log2(3)
        self.assertAlmostEqual(metrics.ndcg_at_k(ranked, rel, 4), dcg / ideal)
        self.assertEqual(metrics.reciprocal_rank([7, 8], [1]), 0.0)
        p, r, f = metrics.precision_recall_f1([1, 1, 0, 0], [1, 0, 1, 0])
        self.assertEqual((p, r), (0.5, 0.5))
        self.assertAlmostEqual(f, 0.5)


class Citations(unittest.TestCase):
    def setUp(self):
        self.emb = HashingEmbedder(1024)
        self.sources = {
            1: "Dense retrieval maps sentences to vectors. Similar meanings are close together.",
            2: "Scanned documents cannot be processed without optical character recognition.",
        }

    def test_marker_helpers(self):
        self.assertEqual(cit.parse_markers("A claim [1][3] and [2, 4]."), [1, 3, 2, 4])
        self.assertEqual(cit.normalise_markers("A claim. [1]"), "A claim [1].")
        self.assertEqual(cit.strip_markers("A claim [1]."), "A claim .")
        self.assertEqual(cit.compose_with_marker("It works.", 2), "It works [2].")

    def test_all_statuses(self):
        answer = ("Dense retrieval maps sentences to vectors [1]. "
                  "The moon is made of green cheese [2]. "
                  "This has no citation at all. "
                  "Something about a missing source [9].")
        res = cit.verify_answer(answer, self.sources, self.emb, threshold=0.5)
        status = [s["status"] for s in res["sentences"]]
        self.assertEqual(status, ["supported", "weak_support", "uncited", "invalid_citation"])
        m = res["metrics"]
        self.assertEqual((m["sentences"], m["cited_sentences"], m["supported_sentences"]), (4, 3, 1))
        self.assertAlmostEqual(m["citation_accuracy"], 1 / 3)
        self.assertAlmostEqual(m["citation_coverage"], 3 / 4)
        self.assertIn("proxy", m["caveat"])

    def test_marker_after_period_stays_with_its_sentence(self):
        res = cit.verify_answer("Dense retrieval maps sentences to vectors. [1]", self.sources, self.emb, 0.5)
        self.assertEqual(res["sentences"][0]["status"], "supported")

    def test_empty_answer_gives_none_metrics(self):
        res = cit.verify_answer("", self.sources, self.emb, 0.5)
        self.assertIsNone(res["metrics"]["citation_accuracy"])


class IdeaHelpers(unittest.TestCase):
    def test_content_bigrams_drop_stopwords(self):
        self.assertEqual(content_bigrams("The use of graph neural networks for protein folding"),
                         ["graph neural", "neural networks", "networks protein", "protein folding"])


if __name__ == "__main__":
    unittest.main()
