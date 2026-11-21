"""Generate a small SYNTHETIC multi-page PDF for automated tests.

This is NOT a real research paper: the text was written for testing the pipeline
(abbreviations, decimals, hyphenation, running headers, page numbers and three
distinct topics so that chunking has something to split). Needs `reportlab`.
For a realistic check, run scripts/smoke_test.py with a real paper instead.
"""
import sys

PAGES = [
    [
        "Local Retrieval for Scientific Question Answering",
        "1 Introduction",
        "Researchers read many papers, and finding a specific fact takes a long time. "
        "Dense retrieval maps sentences to vectors so that similar meanings are close together. "
        "Smith et al. reported 0.85 accuracy on Fig. 3 of their study. "
        "Our system, e.g. a small research assistant, indexes uploaded papers on a laptop. "
        "A query is embedded with the same encoder, and the nearest passages are returned. "
        "This approach avoids exact keyword matching and tolerates paraphrases of the question.",
        "2 Document Processing",
        "Text is extracted page by page and cleaned before segmentation. "
        "Words split by hyphen-ation at the end of a line are joined back together. "
        "Running headers and page numbers are removed because they add noise to every chunk. "
        "Sentences are then segmented while protecting abbreviations such as et al. and decimals such as 3.14. "
        "Each sentence keeps the page number where it appeared so that citations can point to a page.",
    ],
    [
        "3 Evaluation Methodology",
        "We evaluate retrieval with Recall at k, mean reciprocal rank and nDCG. "
        "Recall at k asks whether a relevant passage appears among the top k results. "
        "Mean reciprocal rank averages the inverse rank of the first relevant passage. "
        "A labelled set of questions with known relevant passages is required for these metrics. "
        "Small hand-made sets only provide a smoke test and must not be reported as a benchmark. "
        "Metrics should always be reported together with the size of the evaluation set.",
        "4 Citation Grounding",
        "Every answer sentence should be traceable to a passage in the uploaded papers. "
        "The verifier compares an answer sentence with the sentences of the cited passage. "
        "A high similarity suggests support but does not prove logical entailment. "
        "Sentences without any citation marker are reported as uncited. "
        "Markers that point to a missing source are reported as invalid citations.",
    ],
    [
        "5 Limitations",
        "Embedding similarity is only a proxy for meaning, and negation can be missed. "
        "The lexical fallback encoder compares shared words and is not semantic. "
        "Scanned documents without a text layer cannot be processed without optical character recognition. "
        "Novelty estimates are relative to the uploaded papers and do not prove global novelty. "
        "Future work includes a labelled retrieval benchmark and entailment based verification.",
    ],
]


def build(path):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import simpleSplit

    c = canvas.Canvas(path, pagesize=A4)
    c.setTitle("Local Retrieval for Scientific Question Answering")
    c.setAuthor("Synthetic Test Author")
    width, height = A4
    for n, blocks in enumerate(PAGES, 1):
        c.setFont("Helvetica", 8)
        c.drawString(60, height - 35, "Synthetic Test Paper - Running Header")
        y = height - 80
        for i, block in enumerate(blocks):
            heading = len(block) < 60 and block[0].isdigit() or (n == 1 and i == 0)
            c.setFont("Helvetica-Bold", 16 if (n == 1 and i == 0) else 11) if heading else c.setFont("Helvetica", 10)
            for line in simpleSplit(block, "Helvetica", 10, width - 120):
                c.drawString(60, y, line)
                y -= 14
            y -= 8
        c.setFont("Helvetica", 8)
        c.drawString(width / 2, 30, str(n))
        c.showPage()
    c.save()
    return path


if __name__ == "__main__":
    print(build(sys.argv[1] if len(sys.argv) > 1 else "test_paper.pdf"))
