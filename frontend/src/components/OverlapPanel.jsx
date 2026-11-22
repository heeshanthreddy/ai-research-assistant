import { useState } from "react";
import { checkOverlap } from "../services/researchService";
import { errorMessage } from "../services/api";

function OverlapPanel({ projectId }) {
    const [text, setText] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);

    async function handleSubmit(event) {
        event.preventDefault();
        setBusy(true);
        setError("");
        setResult(null);
        try {
            setResult(await checkOverlap(projectId, text));
        } catch (err) {
            setError(errorMessage(err, "Overlap check failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div>
            {/* Input Card */}
            <form onSubmit={handleSubmit} className="card stack">
                <div className="card-header-row">
                    <div>
                        <h2>Semantic Overlap Detection</h2>
                        <p className="muted small">
                            Compares input text sentence-by-sentence against all chunks in this project to identify copied or paraphrased passages.
                        </p>
                    </div>
                    <span className="badge supported">Two-Stage Pipeline</span>
                </div>

                <div>
                    <textarea
                        rows={4}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        placeholder="Paste draft paragraphs, literature reviews, or manuscript excerpts here to check for overlap against your project's papers..."
                        required
                    />
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div className="muted small">
                        Identifies candidate chunks via cosine similarity, then computes exact sentence-level alignment.
                    </div>
                    <button type="submit" disabled={busy || !text.trim()}>
                        {busy ? "Scanning Corpus..." : "Run Overlap Check"}
                    </button>
                </div>

                {error && <div className="notice error">{error}</div>}
            </form>

            {/* Results Section */}
            {result && (
                <section className="card">
                    <div className="card-header-row">
                        <h2>Overlap Analysis Results</h2>
                        <span className={`badge ${result.flagged > 0 ? "invalid_citation" : "PROCESSED"}`}>
                            {result.flagged} / {result.total_sentences ?? 0} Flagged Sentences
                        </span>
                    </div>

                    <div className="notice ok" style={{ marginBottom: "16px" }}>
                        Scope note: {result.scope_note} (Threshold: &ge; {result.threshold} using {result.embedding?.backend}).
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                        {result.sentences.map((s, i) => (
                            <div
                                key={i}
                                className={`source ${s.flagged ? "flagged" : ""}`}
                                style={{ padding: "12px 14px", borderRadius: "8px" }}
                            >
                                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                                    <span className={`badge ${s.flagged ? "invalid_citation" : "supported"}`}>
                                        {s.flagged ? "⚠ Overlap Detected" : "✓ Original"}
                                    </span>
                                    <span style={{ fontSize: "0.92rem", fontWeight: 500 }}>{s.sentence}</span>
                                </div>

                                {s.match && (
                                    <div className="passage small" style={{ marginTop: "8px" }}>
                                        <strong>Matched Source ({s.match.similarity.toFixed(2)} similarity):</strong> &ldquo;{s.match.matched_sentence}&rdquo;
                                        <div className="muted" style={{ marginTop: "2px" }}>
                                            Paper: <em>{s.match.paper_title}</em> (Page {s.match.page_start}{s.match.page_end !== s.match.page_start ? `-${s.match.page_end}` : ""})
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}

export default OverlapPanel;
