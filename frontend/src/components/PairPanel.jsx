import { useState } from "react";
import { pairSimilarity } from "../services/researchService";
import { errorMessage } from "../services/api";

function PairPanel() {
    const [a, setA] = useState("");
    const [b, setB] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);

    async function handleSubmit(event) {
        event.preventDefault();
        setBusy(true);
        setError("");
        setResult(null);
        try {
            setResult(await pairSimilarity(a, b));
        } catch (err) {
            setError(errorMessage(err, "Comparison failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div>
            {/* Input Form */}
            <form onSubmit={handleSubmit} className="card stack">
                <div className="card-header-row">
                    <div>
                        <h2>Passage-Pair Semantic Feature Comparison</h2>
                        <p className="muted small">
                            Computes 4 distinct similarity metrics: dense embedding cosine, lexical TF-IDF cosine, Jaccard word-overlap, and length ratio.
                        </p>
                    </div>
                    <span className="badge supported">Feature Extractor</span>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "16px" }}>
                    <div>
                        <label className="form-label">Passage A</label>
                        <textarea
                            rows={4}
                            value={a}
                            onChange={(e) => setA(e.target.value)}
                            placeholder="Enter the first research text or passage..."
                            required
                        />
                    </div>
                    <div>
                        <label className="form-label">Passage B</label>
                        <textarea
                            rows={4}
                            value={b}
                            onChange={(e) => setB(e.target.value)}
                            placeholder="Enter the second research text or passage to compare..."
                            required
                        />
                    </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "6px" }}>
                    <button type="submit" disabled={busy || !a.trim() || !b.trim()}>
                        {busy ? "Extracting Features..." : "Compute Similarity Features"}
                    </button>
                </div>

                {error && <div className="notice error">{error}</div>}
            </form>

            {/* Results Table & Classifier State */}
            {result && (
                <section className="card">
                    <div className="card-header-row">
                        <h2>Extracted Feature Vector</h2>
                        <span className="badge PROCESSED">Feature Extraction Complete</span>
                    </div>

                    <div style={{ overflowX: "auto" }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Similarity Feature Metric</th>
                                    <th>Computed Value (0.000 - 1.000)</th>
                                    <th>Methodology Description</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(result.features).map(([k, v]) => {
                                    const descriptions = {
                                        embedding_cosine: "Cosine similarity between L2-normalized sentence embedding vectors.",
                                        tfidf_cosine: "Sparse TF-IDF unigram and bigram cosine similarity.",
                                        jaccard: "Intersection over union of content-word token sets.",
                                        length_ratio: "Ratio of shorter passage token length to longer passage length.",
                                    };
                                    return (
                                        <tr key={k}>
                                            <td style={{ fontWeight: 600 }}>{k}</td>
                                            <td>
                                                <strong style={{ color: "var(--rf-primary)", fontSize: "1.05rem" }}>
                                                    {v.toFixed(3)}
                                                </strong>
                                            </td>
                                            <td className="muted small">
                                                {descriptions[k] || "Metric feature"}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>

                    <div style={{ marginTop: "16px" }}>
                        {result.prediction ? (
                            <div className="notice ok">
                                <strong>Classifier Verdict:</strong>{" "}
                                {result.prediction.similar ? "Semantically Equivalent / Similar" : "Dissimilar"}{" "}
                                (Probability: {(result.prediction.probability * 100).toFixed(1)}%)
                            </div>
                        ) : (
                            <div className="notice warn">
                                ℹ {result.model.note}
                            </div>
                        )}
                    </div>
                </section>
            )}
        </div>
    );
}

export default PairPanel;
