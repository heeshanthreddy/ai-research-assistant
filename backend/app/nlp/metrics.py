"""Evaluation metrics (pure functions, no hidden data).

These are only meaningful when computed on a properly labelled evaluation set.
Running them on a handful of hand-made queries is a smoke test, not a benchmark.
"""
import math


def recall_at_k(ranked_ids, relevant_ids, k):
    relevant = set(relevant_ids)
    if not relevant:
        return None
    return len(set(ranked_ids[:k]) & relevant) / len(relevant)


def reciprocal_rank(ranked_ids, relevant_ids):
    relevant = set(relevant_ids)
    for i, rid in enumerate(ranked_ids, 1):
        if rid in relevant:
            return 1.0 / i
    return 0.0


def ndcg_at_k(ranked_ids, relevant_ids, k):
    relevant = set(relevant_ids)
    if not relevant:
        return None
    dcg = sum(1.0 / math.log2(i + 1) for i, rid in enumerate(ranked_ids[:k], 1) if rid in relevant)
    ideal = sum(1.0 / math.log2(i + 1) for i in range(1, min(len(relevant), k) + 1))
    return dcg / ideal if ideal else 0.0


def precision_recall_f1(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    return prec, rec, f1


def mean(values):
    vals = [v for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def evaluate_retrieval(queries, k):
    """queries: [{"ranked_ids": [...], "relevant_ids": [...]}] -> metrics dict."""
    return {
        "queries": len(queries), "k": k,
        f"recall@{k}": mean(recall_at_k(q["ranked_ids"], q["relevant_ids"], k) for q in queries),
        "mrr": mean(reciprocal_rank(q["ranked_ids"], q["relevant_ids"]) for q in queries
                    if q["relevant_ids"]),
        f"ndcg@{k}": mean(ndcg_at_k(q["ranked_ids"], q["relevant_ids"], k) for q in queries),
    }
