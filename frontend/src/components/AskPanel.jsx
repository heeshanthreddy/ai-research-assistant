import { useState } from "react";
import { askQuestion, getChunk } from "../services/researchService";
import { errorMessage } from "../services/api";

const STATUS_LABEL = {
    supported: "supported", weak_support: "weak support",
    invalid_citation: "invalid citation", uncited: "uncited",
};

function AnswerText({ text, onMarker }) {
    return (
        <p className="answer">
            {text.split(/(\[\d+\])/g).map((part, i) => {
                const m = part.match(/^\[(\d+)\]$/);
                return m
                    ? <button key={i} className="marker" onClick={() => onMarker(Number(m[1]))}>{part}</button>
                    : <span key={i}>{part}</span>;
            })}
        </p>
    );
}

function AskPanel({ projectId, processedCount }) {
    const [question, setQuestion] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);
    const [opened, setOpened] = useState({});       // number -> chunk from /chunks/<id>

    async function handleAsk(event) {
        event.preventDefault();
        setBusy(true); setError(""); setResult(null); setOpened({});
        try {
            setResult(await askQuestion(projectId, question));
        } catch (err) {
            setError(errorMessage(err, "Could not answer the question"));
        } finally {
            setBusy(false);
        }
    }

    async function openSource(number) {
        const src = result.sources.find((s) => s.number === number);
        if (!src) return;
        if (opened[number]) { setOpened((o) => { const n = { ...o }; delete n[number]; return n; }); return; }
        try {
            const chunk = await getChunk(projectId, src.chunk_id);
            setOpened((o) => ({ ...o, [number]: chunk }));
        } catch (err) {
            setError(errorMessage(err, "Could not open the passage"));
        }
    }

    const v = result?.verification;
    return (
        <div>
            <form onSubmit={handleAsk} className="card stack">
                <h2>Ask a question about your papers</h2>
                {processedCount === 0 && <p className="notice warn">Upload and process a paper first.</p>}
                <textarea rows={2} value={question} onChange={(e) => setQuestion(e.target.value)}
                          placeholder="e.g. How is the model evaluated?" required />
                <button type="submit" disabled={busy || !question.trim()}>{busy ? "Searching..." : "Ask"}</button>
                {error && <p className="notice error">{error}</p>}
            </form>

            {result && (
                <section className="card">
                    <h2>Answer <span className="tag">extractive</span></h2>
                    <p className="muted small">{result.method_note}</p>

                    {result.insufficient_evidence ? (
                        <>
                            <p className="notice warn">{result.answer}</p>
                            {result.reason && <p className="muted small">{result.reason}</p>}
                        </>
                    ) : (
                        <AnswerText text={result.answer} onMarker={openSource} />
                    )}

                    {result.sources.length > 0 && (
                        <>
                            <h3>Sources</h3>
                            {result.sources.map((s) => (
                                <div key={s.number} className="source">
                                    <button className="marker" onClick={() => openSource(s.number)}>[{s.number}]</button>{" "}
                                    <strong>{s.paper_title}</strong>, page {s.page_start}
                                    {s.page_end !== s.page_start ? `-${s.page_end}` : ""} - chunk #{s.chunk_index} (id {s.chunk_id})
                                    {opened[s.number] && <p className="passage">{opened[s.number].text}</p>}
                                </div>
                            ))}
                        </>
                    )}

                    {v && (
                        <>
                            <h3>Citation verification</h3>
                            <table>
                                <thead><tr><th>Answer sentence</th><th>Cites</th><th>Status</th><th>Similarity</th></tr></thead>
                                <tbody>
                                    {v.sentences.map((s, i) => (
                                        <tr key={i}>
                                            <td>{s.sentence}</td>
                                            <td>{s.markers.map((m) => `[${m}]`).join(" ")}</td>
                                            <td><span className={`badge ${s.status}`}>{STATUS_LABEL[s.status]}</span></td>
                                            <td>{s.score !== null ? s.score.toFixed(2) : "-"}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                            <p className="small">
                                Citation accuracy: <strong>{v.metrics.citation_accuracy === null ? "n/a" : v.metrics.citation_accuracy.toFixed(2)}</strong>{" "}
                                (supported / cited sentences) - coverage: <strong>{v.metrics.citation_coverage === null ? "n/a" : v.metrics.citation_coverage.toFixed(2)}</strong>{" "}
                                (cited / all answer sentences) - threshold {v.metrics.threshold} on {v.metrics.embedding_backend}
                            </p>
                            <p className="muted small">{v.metrics.caveat} For extractive answers the sentences are copied
                                from the sources, so high scores mainly confirm that each citation points to the right passage.</p>
                        </>
                    )}
                </section>
            )}
        </div>
    );
}

export default AskPanel;
