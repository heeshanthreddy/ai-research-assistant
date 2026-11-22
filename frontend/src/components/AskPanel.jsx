import { useState } from "react";
import { askQuestion, getChunk } from "../services/researchService";
import { errorMessage } from "../services/api";

const STATUS_LABEL = {
    supported: "Supported",
    weak_support: "Weak Support",
    invalid_citation: "Invalid Citation",
    uncited: "Uncited",
};

function AnswerText({ text, onMarker }) {
    return (
        <div className="answer">
            {text.split(/(\[\d+\])/g).map((part, i) => {
                const m = part.match(/^\[(\d+)\]$/);
                return m ? (
                    <button
                        key={i}
                        className="marker"
                        title="Click to inspect cited passage"
                        onClick={() => onMarker(Number(m[1]))}
                    >
                        {part}
                    </button>
                ) : (
                    <span key={i}>{part}</span>
                );
            })}
        </div>
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
        setBusy(true);
        setError("");
        setResult(null);
        setOpened({});
        try {
            setResult(await askQuestion(projectId, question));
        } catch (err) {
            setError(errorMessage(err, "Could not answer the question"));
        } finally {
            setBusy(false);
        }
    }

    async function openSource(number) {
        const src = result?.sources?.find((s) => s.number === number);
        if (!src) return;
        if (opened[number]) {
            setOpened((o) => {
                const n = { ...o };
                delete n[number];
                return n;
            });
            return;
        }
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
            {/* Question Submission Card */}
            <form onSubmit={handleAsk} className="card stack">
                <div className="card-header-row">
                    <div>
                        <h2>Ask a Research Question</h2>
                        <p className="muted small">
                            Answers are extracted word-for-word from your papers with automated citation verification.
                        </p>
                    </div>
                    <span className="badge supported">Extractive QA</span>
                </div>

                {processedCount === 0 && (
                    <div className="notice warn">
                        ⚠ No processed papers found. Ingest at least one PDF in the Papers tab before asking questions.
                    </div>
                )}

                <div>
                    <textarea
                        rows={3}
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        placeholder="e.g. What problem does the proposed method address, and what are the main findings?"
                        required
                    />
                </div>

                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div className="muted small">
                        Tip: Sentences with highest cosine similarity to your query are ranked using MMR.
                    </div>
                    <button type="submit" disabled={busy || !question.trim() || processedCount === 0}>
                        {busy ? "Retrieving & Verifying..." : "Query Corpus"}
                    </button>
                </div>

                {error && <div className="notice error">{error}</div>}
            </form>

            {/* Answer & Verification Results */}
            {result && (
                <section className="card">
                    <div className="card-header-row">
                        <h2>
                            Extractive Answer{" "}
                            <span className="tag">Word-for-Word Grounded</span>
                        </h2>
                        {result.insufficient_evidence ? (
                            <span className="badge FAILED">Insufficient Evidence</span>
                        ) : (
                            <span className="badge PROCESSED">Evidence Retrieved</span>
                        )}
                    </div>

                    <p className="muted small">{result.method_note}</p>

                    {result.insufficient_evidence ? (
                        <div style={{ marginTop: "12px" }}>
                            <div className="notice warn">{result.answer}</div>
                            {result.reason && <p className="muted small">{result.reason}</p>}
                        </div>
                    ) : (
                        <AnswerText text={result.answer} onMarker={openSource} />
                    )}

                    {/* Cited Source Passages */}
                    {result.sources && result.sources.length > 0 && (
                        <div style={{ marginTop: "20px" }}>
                            <h3>Cited Passages from Your Papers</h3>
                            <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                                {result.sources.map((s) => (
                                    <div key={s.number} className="source" style={{ paddingTop: "8px" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                                            <button className="marker" onClick={() => openSource(s.number)}>
                                                [{s.number}]
                                            </button>
                                            <strong>{s.paper_title}</strong>
                                            <span className="muted small">
                                                (Pages {s.page_start}{s.page_end !== s.page_start ? `-${s.page_end}` : ""}, Chunk #{s.chunk_index})
                                            </span>
                                            <button
                                                className="link small"
                                                onClick={() => openSource(s.number)}
                                                style={{ marginLeft: "auto" }}
                                            >
                                                {opened[s.number] ? "Hide Passage ▲" : "Inspect Passage ▼"}
                                            </button>
                                        </div>

                                        {opened[s.number] && (
                                            <div className="passage">
                                                <p style={{ margin: 0 }}>{opened[s.number].text}</p>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Citation Verification & Scoring Table */}
                    {v && (
                        <div style={{ marginTop: "24px", paddingTop: "16px", borderTop: "1px solid var(--rf-border)" }}>
                            <div className="card-header-row">
                                <h3>Automated Citation Verification</h3>
                                <div style={{ display: "flex", gap: "8px" }}>
                                    <span className="badge supported">
                                        Accuracy: {v.metrics.citation_accuracy === null ? "N/A" : `${(v.metrics.citation_accuracy * 100).toFixed(0)}%`}
                                    </span>
                                    <span className="badge PROCESSED">
                                        Coverage: {v.metrics.citation_coverage === null ? "N/A" : `${(v.metrics.citation_coverage * 100).toFixed(0)}%`}
                                    </span>
                                </div>
                            </div>

                            <div style={{ overflowX: "auto" }}>
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Answer Sentence</th>
                                            <th>Citation Marker</th>
                                            <th>Verification Status</th>
                                            <th>Support Score</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {v.sentences.map((s, i) => (
                                            <tr key={i}>
                                                <td style={{ maxWidth: "420px" }}>{s.sentence}</td>
                                                <td>
                                                    {s.markers.length > 0 ? (
                                                        s.markers.map((m) => (
                                                            <span key={m} className="tag" style={{ margin: "1px" }}>[{m}]</span>
                                                        ))
                                                    ) : (
                                                        <span className="muted small">None</span>
                                                    )}
                                                </td>
                                                <td>
                                                    <span className={`badge ${s.status}`}>
                                                        {STATUS_LABEL[s.status] || s.status}
                                                    </span>
                                                </td>
                                                <td>
                                                    {s.score !== null ? (
                                                        <strong style={{ color: s.score >= v.metrics.threshold ? "var(--rf-success)" : "var(--rf-warning)" }}>
                                                            {s.score.toFixed(3)}
                                                        </strong>
                                                    ) : (
                                                        <span className="muted">-</span>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>

                            <p className="muted small" style={{ marginTop: "10px" }}>
                                Threshold: {v.metrics.threshold} ({v.metrics.embedding_backend}). {v.metrics.caveat}
                            </p>
                        </div>
                    )}
                </section>
            )}
        </div>
    );
}

export default AskPanel;
