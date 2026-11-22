import { useState } from "react";
import { analyseIdea } from "../services/researchService";
import { errorMessage } from "../services/api";

function IdeaPanel({ projectId }) {
    const [idea, setIdea] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);

    async function handleSubmit(event) {
        event.preventDefault();
        setBusy(true);
        setError("");
        setResult(null);
        try {
            setResult(await analyseIdea(projectId, idea));
        } catch (err) {
            setError(errorMessage(err, "Idea analysis failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div>
            {/* Idea Input Card */}
            <form onSubmit={handleSubmit} className="card stack">
                <div className="card-header-row">
                    <div>
                        <h2>Research Idea Novelty Analysis</h2>
                        <p className="muted small">
                            Compares your proposed research hypothesis against all papers in this project to identify corpus-relative gaps.
                        </p>
                    </div>
                    <span className="badge supported">Corpus-Relative Analysis</span>
                </div>

                <div>
                    <textarea
                        rows={4}
                        value={idea}
                        onChange={(e) => setIdea(e.target.value)}
                        placeholder="Describe your research proposal, methodology, or hypothesis (e.g. Using lexical hashing as a low-latency fallback for scientific question answering when GPU resources are constrained)..."
                        required
                    />
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div className="muted small">
                        Calculates mean cosine similarity of top matching papers and extracts absent content bigrams.
                    </div>
                    <button type="submit" disabled={busy || !idea.trim()}>
                        {busy ? "Analyzing Idea..." : "Analyze Hypothesis"}
                    </button>
                </div>

                {error && <div className="notice error">{error}</div>}
            </form>

            {/* Ingestion Warning */}
            {result && !result.available && (
                <div className="notice warn">
                    ⚠ {result.reason}
                </div>
            )}

            {/* Analysis Results Card */}
            {result && result.available && (
                <section className="card">
                    <div className="notice ok" style={{ marginBottom: "18px" }}>
                        <strong>Corpus Scope Note:</strong> {result.scope_note}
                    </div>

                    {/* Metrics Row */}
                    <div className="stats-grid" style={{ marginBottom: "20px" }}>
                        <div className="stat-card">
                            <div>
                                <div className="stat-info-label">Average Similarity</div>
                                <div className="stat-info-value" style={{ color: "var(--rf-primary)" }}>
                                    {result.average_similarity_closest.toFixed(3)}
                                </div>
                                <div className="stat-info-sub">Across closest papers</div>
                            </div>
                            <div className="stat-icon-wrapper">≈</div>
                        </div>

                        <div className="stat-card">
                            <div>
                                <div className="stat-info-label">Corpus-Relative Novelty</div>
                                <div className="stat-info-value" style={{ color: "var(--rf-success)" }}>
                                    {result.novelty_estimate.toFixed(3)}
                                </div>
                                <div className="stat-info-sub">1 - Average Similarity</div>
                            </div>
                            <div className="stat-icon-wrapper" style={{ background: "var(--rf-success-bg)", color: "var(--rf-success)" }}>★</div>
                        </div>
                    </div>

                    <p className="muted small" style={{ marginBottom: "16px" }}>{result.novelty_note}</p>

                    {/* Closest Papers */}
                    <h3>Closest Papers in Corpus</h3>
                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {result.closest_papers.map((p) => (
                            <div key={p.paper_id} className="source" style={{ paddingTop: "8px" }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <strong style={{ fontSize: "0.95rem" }}>{p.paper_title}</strong>
                                    <span className="badge supported">
                                        Similarity: {p.similarity.toFixed(3)}
                                    </span>
                                </div>

                                <div className="passage" style={{ marginTop: "8px" }}>
                                    <div className="muted small" style={{ marginBottom: "4px" }}>
                                        Best matching passage (Pages {p.best_passage.page_start}-{p.best_passage.page_end}, Cosine: {p.best_passage.similarity.toFixed(3)}):
                                    </div>
                                    <p style={{ margin: 0, fontStyle: "italic" }}>
                                        &ldquo;{p.best_passage.text}&rdquo;
                                    </p>
                                </div>
                            </div>
                        ))}
                    </div>

                    {/* Content Bigram Gaps */}
                    <h3 style={{ marginTop: "24px" }}>Possible Research Gaps in Corpus</h3>
                    {result.possible_gaps.length === 0 ? (
                        <p className="muted small">
                            Every content-word bigram in your proposed idea was found somewhere in the ingested corpus.
                        </p>
                    ) : (
                        <div>
                            <p className="muted small">
                                These key bigrams from your idea do not appear anywhere in the uploaded papers:
                            </p>
                            <div style={{ display: "flex", flexWrap: "wrap", gap: "6px", marginTop: "8px" }}>
                                {result.possible_gaps.map((g) => (
                                    <span className="tag" key={g} style={{ fontSize: "0.85rem", padding: "4px 10px" }}>
                                        + {g}
                                    </span>
                                ))}
                            </div>
                        </div>
                    )}
                    <p className="muted small" style={{ marginTop: "12px" }}>{result.gaps_note}</p>
                </section>
            )}
        </div>
    );
}

export default IdeaPanel;
