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
        setBusy(true); setError(""); setResult(null);
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
            <form onSubmit={handleSubmit} className="card stack">
                <h2>Research idea analysis</h2>
                <p className="muted small">Compares your idea with the papers uploaded to this project. The result is
                    relative to this corpus only.</p>
                <textarea rows={3} value={idea} onChange={(e) => setIdea(e.target.value)}
                          placeholder="Describe a proposed research idea..." required />
                <button type="submit" disabled={busy}>{busy ? "Analysing..." : "Analyse idea"}</button>
                {error && <p className="notice error">{error}</p>}
            </form>

            {result && !result.available && <p className="notice warn">{result.reason}</p>}

            {result && result.available && (
                <section className="card">
                    <p className="notice">{result.scope_note}</p>
                    <p>
                        Average similarity to the {result.closest_papers.length} closest paper(s):{" "}
                        <strong>{result.average_similarity_closest.toFixed(3)}</strong> - corpus-relative novelty
                        estimate (1 - similarity): <strong>{result.novelty_estimate.toFixed(3)}</strong>
                    </p>
                    <p className="muted small">{result.novelty_note}</p>

                    <h3>Closest papers</h3>
                    {result.closest_papers.map((p) => (
                        <div className="source" key={p.paper_id}>
                            <strong>{p.paper_title}</strong> - similarity {p.similarity.toFixed(3)}
                            <p className="passage">
                                Best passage (pages {p.best_passage.page_start}-{p.best_passage.page_end},
                                similarity {p.best_passage.similarity.toFixed(3)}): {p.best_passage.text}
                            </p>
                        </div>
                    ))}

                    <h3>Possible gaps in this corpus</h3>
                    {result.possible_gaps.length === 0
                        ? <p className="muted">Every content-word bigram of the idea appears somewhere in the uploaded papers.</p>
                        : <p>{result.possible_gaps.map((g) => <span className="tag" key={g}>{g}</span>)}</p>}
                    <p className="muted small">{result.gaps_note}</p>
                </section>
            )}
        </div>
    );
}

export default IdeaPanel;
