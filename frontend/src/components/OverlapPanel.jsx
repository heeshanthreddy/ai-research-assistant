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
        setBusy(true); setError(""); setResult(null);
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
            <form onSubmit={handleSubmit} className="card stack">
                <h2>Semantic overlap check</h2>
                <p className="muted small">Checks your text against the papers in this project. It is an overlap
                    checker for your own corpus, not a web-scale plagiarism detector.</p>
                <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)}
                          placeholder="Paste a paragraph to check..." required />
                <button type="submit" disabled={busy}>{busy ? "Checking..." : "Check overlap"}</button>
                {error && <p className="notice error">{error}</p>}
            </form>

            {result && (
                <section className="card">
                    <p className="small">
                        {result.flagged} of {result.total_sentences ?? 0} sentence(s) flagged at similarity &gt;= {result.threshold} ({result.embedding.backend}).
                    </p>
                    {result.sentences.map((s, i) => (
                        <div key={i} className={`source ${s.flagged ? "flagged" : ""}`}>
                            <span className={`badge ${s.flagged ? "invalid_citation" : "supported"}`}>{s.flagged ? "overlap" : "no overlap"}</span>{" "}
                            {s.sentence}
                            {s.match && (
                                <p className="passage small">
                                    Closest sentence ({s.match.similarity.toFixed(2)}): "{s.match.matched_sentence}" -{" "}
                                    {s.match.paper_title}, page {s.match.page_start}
                                    {s.match.page_end !== s.match.page_start ? `-${s.match.page_end}` : ""}
                                </p>
                            )}
                        </div>
                    ))}
                    <p className="muted small">{result.scope_note}</p>
                </section>
            )}
        </div>
    );
}

export default OverlapPanel;
