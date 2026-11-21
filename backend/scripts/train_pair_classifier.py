"""Train the passage-pair classifier from YOUR labelled CSV (text_a,text_b,label).

    python scripts/train_pair_classifier.py path/to/labelled_pairs.csv

No dataset is bundled. Without one the classifier stays untrained/unvalidated.
Reported precision/recall/F1 are from a held-out 30% split of your CSV only.
"""
import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import create_app                      # noqa: E402
from app.nlp.embeddings import get_embedder     # noqa: E402
from app.nlp.classifier import train_from_csv   # noqa: E402

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    app = create_app()
    with app.app_context():
        print(json.dumps(train_from_csv(sys.argv[1], get_embedder()), indent=2))
