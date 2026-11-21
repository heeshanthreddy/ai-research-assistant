"""Stage 3: semantic chunking (TextTiling-style, on sentence embeddings).

1. Embed every sentence.
2. For each gap between sentences compare the mean embedding of the `window`
   sentences before it with the `window` sentences after it (cosine).
3. A low score = likely topic change. Cut where score < mean - k * std.
4. Enforce the size limits: split chunks above max_tokens at their weakest gap,
   merge chunks below min_tokens into the more similar neighbour.

Sentences are never broken. Words are used as a cheap token count. The numeric
defaults live in config.py and are not tuned on any benchmark.
"""
import numpy as np


def _words(sentences):
    return sum(len(s.split()) for s in sentences)


def _gap_scores(E, window):
    """gap[i] = similarity between the windows before and after boundary i (1..n-1)."""
    n = len(E)
    gaps = np.zeros(n)              # index 0 unused
    for i in range(1, n):
        left = E[max(0, i - window):i].mean(axis=0)
        right = E[i:i + window].mean(axis=0)
        denom = np.linalg.norm(left) * np.linalg.norm(right)
        gaps[i] = float(left @ right / denom) if denom > 0 else 0.0
    return gaps


def _split_oversize(seg, texts, gaps, max_tokens):
    """seg = (start, end) sentence index range; split at the weakest interior gap."""
    s, e = seg
    if e - s <= 1 or _words(texts[s:e]) <= max_tokens:
        return [seg]
    cut = min(range(s + 1, e), key=lambda i: gaps[i])
    return (_split_oversize((s, cut), texts, gaps, max_tokens)
            + _split_oversize((cut, e), texts, gaps, max_tokens))


def semantic_chunk(sentences, embed_fn, min_tokens=40, max_tokens=220, break_std=0.5, window=3):
    """sentences: [Sentence(text, page)]. Returns a list of chunk dicts."""
    if not sentences:
        return []
    texts = [s.text for s in sentences]
    n = len(texts)
    if n == 1:
        segments = [(0, 1)]
        gaps = np.zeros(1)
    else:
        E = embed_fn(texts)
        gaps = _gap_scores(E, window)
        g = gaps[1:]
        threshold = g.mean() - break_std * g.std()
        cuts = [i for i in range(1, n) if gaps[i] < threshold]
        bounds = [0] + cuts + [n]
        segments = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]

    # enforce maximum size
    split = []
    for seg in segments:
        split.extend(_split_oversize(seg, texts, gaps, max_tokens))
    segments = split

    # enforce minimum size by merging into the more similar neighbour
    blocked = set()
    while len(segments) > 1:
        small = [(i, _words(texts[a:b])) for i, (a, b) in enumerate(segments)
                 if _words(texts[a:b]) < min_tokens and segments[i] not in blocked]
        if not small:
            break
        i = min(small, key=lambda x: x[1])[0]
        a, b = segments[i]
        options = []
        if i > 0:
            options.append((gaps[a], i - 1))          # merge with previous
        if i < len(segments) - 1:
            options.append((gaps[b], i + 1))          # merge with next
        options.sort(reverse=True)
        merged = False
        for _, j in options:
            lo, hi = (min(i, j), max(i, j))
            new = (segments[lo][0], segments[hi][1])
            if _words(texts[new[0]:new[1]]) <= max_tokens:
                segments[lo:hi + 1] = [new]
                merged = True
                break
        if not merged:
            blocked.add(segments[i])

    chunks = []
    for idx, (a, b) in enumerate(segments):
        group = sentences[a:b]
        chunks.append({
            "chunk_index": idx,
            "text": " ".join(s.text for s in group),
            "page_start": min(s.page for s in group),
            "page_end": max(s.page for s in group),
            "word_count": _words([s.text for s in group]),
            "sentence_count": len(group),
        })
    return chunks
