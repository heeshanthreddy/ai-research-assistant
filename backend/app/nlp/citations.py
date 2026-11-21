"""Stage 8: citation verification.

Each answer sentence is compared with the sentences of the passage(s) it cites,
using embedding cosine similarity. THIS IS A PROXY FOR SEMANTIC SUPPORT, NOT A
GUARANTEE OF LOGICAL ENTAILMENT: a sentence can be similar to a source and still
say something different (e.g. negation, different numbers).

Statuses:  supported | weak_support | invalid_citation | uncited
"""
import re

from app.nlp.preprocessing import split_sentences

MARKER_RE = re.compile(r"\[(\d+(?:\s*,\s*\d+)*)\]")
_MARKER_PUNCT_RE = re.compile(r"([.!?])\s*((?:\[\d+(?:\s*,\s*\d+)*\]\s*)+)")


def normalise_markers(text):
    """'claim. [1]'  ->  'claim [1].'  so the marker stays with its sentence."""
    return _MARKER_PUNCT_RE.sub(lambda m: " " + m.group(2).strip() + m.group(1) + " ", text).strip()


def parse_markers(sentence):
    nums = []
    for m in MARKER_RE.finditer(sentence):
        nums.extend(int(x) for x in re.split(r"\s*,\s*", m.group(1)))
    return nums


def strip_markers(sentence):
    return re.sub(r"\s+", " ", MARKER_RE.sub("", sentence)).strip()


def compose_with_marker(sentence, number):
    """Append [n] before the final punctuation of an extracted sentence."""
    s = sentence.rstrip()
    if s and s[-1] in ".!?":
        return f"{s[:-1]} [{number}]{s[-1]}"
    return f"{s} [{number}]"


def verify_answer(answer_text, sources, embedder, threshold):
    """sources: {number(int): passage_text}. Returns per-sentence results + metrics."""
    sentences = split_sentences(normalise_markers(answer_text))
    cache = {}                                   # source number -> (sentences, matrix)

    def source_matrix(num):
        if num not in cache:
            sents = split_sentences(sources[num]) or [sources[num]]
            cache[num] = (sents, embedder.encode(sents))
        return cache[num]

    results = []
    for sent in sentences:
        markers = parse_markers(sent)
        body = strip_markers(sent)
        entry = {"sentence": sent, "markers": sorted(set(markers)), "status": None,
                 "score": None, "best_source": None, "best_source_sentence": None}
        if not markers:
            entry["status"] = "uncited"
        elif any(m not in sources for m in markers):
            entry["status"] = "invalid_citation"
        else:
            qv = embedder.encode([body])[0]
            best = (-1.0, None, None)
            for num in sorted(set(markers)):
                sents, mat = source_matrix(num)
                sims = mat @ qv
                j = int(sims.argmax())
                if float(sims[j]) > best[0]:
                    best = (float(sims[j]), num, sents[j])
            entry.update(score=round(best[0], 4), best_source=best[1], best_source_sentence=best[2],
                         status="supported" if best[0] >= threshold else "weak_support")
        results.append(entry)

    total = len(results)
    cited = [r for r in results if r["markers"]]
    supported = [r for r in results if r["status"] == "supported"]
    metrics = {
        "sentences": total,
        "cited_sentences": len(cited),
        "supported_sentences": len(supported),
        # accuracy: of the cited sentences, how many are supported by what they cite
        "citation_accuracy": (len(supported) / len(cited)) if cited else None,
        # coverage: share of answer sentences that carry any citation
        # (every sentence is counted: we do not try to detect which are 'factual')
        "citation_coverage": (len(cited) / total) if total else None,
        "threshold": threshold,
        "embedding_backend": embedder.name,
        "semantic": embedder.is_semantic,
        "caveat": ("Embedding similarity is a proxy for semantic support, "
                   "not a guarantee of logical entailment."),
    }
    return {"sentences": results, "metrics": metrics}
