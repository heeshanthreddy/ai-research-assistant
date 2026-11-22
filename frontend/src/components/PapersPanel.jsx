import { useRef, useState } from "react";
import { uploadPaper, deletePaper, getPaperChunks } from "../services/researchService";
import { errorMessage } from "../services/api";

function PapersPanel({ projectId, papers, onChanged }) {
    const fileRef = useRef(null);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [info, setInfo] = useState("");
    const [viewing, setViewing] = useState(null);     // { paper, chunks }

    async function handleUpload(event) {
        event.preventDefault();
        const file = fileRef.current?.files?.[0];
        if (!file) {
            setError("Please select a PDF document first.");
            return;
        }
        setBusy(true);
        setError("");
        setInfo("");
        try {
            const data = await uploadPaper(projectId, file);
            setInfo(data.message || "Paper uploaded and processed successfully.");
            if (fileRef.current) fileRef.current.value = "";
            await onChanged();
        } catch (err) {
            setError(errorMessage(err, "Upload and processing failed"));
        } finally {
            setBusy(false);
        }
    }

    async function handleDelete(paper) {
        if (!window.confirm(`Delete "${paper.title || paper.original_filename}" and all its chunks?`)) return;
        try {
            await deletePaper(projectId, paper.id);
            if (viewing?.paper?.id === paper.id) setViewing(null);
            await onChanged();
        } catch (err) {
            setError(errorMessage(err, "Delete failed"));
        }
    }

    async function handleView(paper) {
        setError("");
        try {
            setViewing(await getPaperChunks(projectId, paper.id));
        } catch (err) {
            setError(errorMessage(err, "Could not load chunks"));
        }
    }

    return (
        <div>
            {/* Upload Paper Card */}
            <form onSubmit={handleUpload} className="card" style={{ marginBottom: "20px" }}>
                <div className="card-header-row">
                    <div>
                        <h2>Upload & Ingest Research Paper (PDF)</h2>
                        <p className="muted small" style={{ margin: "2px 0 0 0" }}>
                            PyMuPDF extracts per-page text, cleans ligatures & running headers, and splits text into semantic chunks.
                        </p>
                    </div>
                    <span className="badge supported">PDF Text Layer Required</span>
                </div>

                <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap", marginTop: "10px" }}>
                    <input
                        type="file"
                        accept="application/pdf,.pdf"
                        ref={fileRef}
                        style={{ flex: 1, minWidth: "260px" }}
                    />
                    <button type="submit" disabled={busy} style={{ whiteSpace: "nowrap" }}>
                        {busy ? "Processing & Embedding..." : "Upload & Process Paper"}
                    </button>
                </div>

                {info && <div className="notice ok" style={{ marginTop: "12px" }}>✓ {info}</div>}
                {error && <div className="notice error" style={{ marginTop: "12px" }}>⚠ {error}</div>}
            </form>

            {/* Papers List */}
            <section className="card">
                <div className="card-header-row">
                    <h2>
                        Uploaded Research Papers{" "}
                        {papers && <span className="muted small">({papers.length})</span>}
                    </h2>
                </div>

                {papers === null && (
                    <div style={{ padding: "20px", textAlign: "center" }} className="muted">
                        Loading documents from repository...
                    </div>
                )}

                {papers && papers.length === 0 && (
                    <div className="empty-state-card" style={{ padding: "32px 16px" }}>
                        <div className="empty-state-icon">📄</div>
                        <div className="empty-state-title">No Papers Ingested</div>
                        <div className="empty-state-desc">
                            Select a research paper PDF above to extract text, generate semantic chunks, and enable extractive QA.
                        </div>
                    </div>
                )}

                {papers && papers.length > 0 && (
                    <div style={{ overflowX: "auto" }}>
                        <table>
                            <thead>
                                <tr>
                                    <th>Document Title / File</th>
                                    <th>Pages</th>
                                    <th>Chunks</th>
                                    <th>Pipeline Status</th>
                                    <th style={{ textAlign: "right" }}>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {papers.map((p) => (
                                    <tr key={p.id}>
                                        <td>
                                            <div style={{ fontWeight: 600, color: "var(--rf-text-primary)" }}>
                                                {p.title || p.original_filename}
                                            </div>
                                            <div className="muted small">
                                                {p.original_filename} {p.extraction_method ? `• Engine: ${p.extraction_method}` : ""}
                                            </div>
                                            {p.processing_error && <div className="error-text small">Error: {p.processing_error}</div>}
                                            {p.processing_warnings && <div className="warn-text small">Advisory: {p.processing_warnings}</div>}
                                        </td>
                                        <td>{p.num_pages ?? "-"}</td>
                                        <td>
                                            <span className="tag">{p.chunk_count}</span>
                                        </td>
                                        <td>
                                            <span className={`badge ${p.status}`}>{p.status}</span>
                                        </td>
                                        <td className="actions" style={{ justifyContent: "flex-end" }}>
                                            {p.status === "PROCESSED" && (
                                                <button
                                                    type="button"
                                                    className="secondary"
                                                    style={{ padding: "5px 10px", fontSize: "0.82rem" }}
                                                    onClick={() => handleView(p)}
                                                >
                                                    View Chunks
                                                </button>
                                            )}
                                            <button
                                                type="button"
                                                className="danger"
                                                style={{ padding: "5px 10px", fontSize: "0.82rem" }}
                                                onClick={() => handleDelete(p)}
                                            >
                                                Delete
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </section>

            {/* Semantic Chunks Viewer Drawer/Section */}
            {viewing && (
                <section className="card" style={{ marginTop: "20px", border: "1px solid var(--rf-primary-border)" }}>
                    <div className="card-header-row">
                        <div>
                            <h2>
                                Semantic Chunks: &ldquo;{viewing.paper?.title || viewing.paper?.original_filename}&rdquo;
                            </h2>
                            <p className="muted small">
                                Showing {viewing.chunks?.length || 0} chunks partitioned by sentence embedding topic shifts.
                            </p>
                        </div>
                        <button
                            type="button"
                            className="secondary"
                            onClick={() => setViewing(null)}
                            style={{ fontSize: "0.82rem" }}
                        >
                            ✕ Close Chunks Viewer
                        </button>
                    </div>

                    <div style={{ display: "flex", flexDirection: "column", gap: "12px", maxHeight: "500px", overflowY: "auto", paddingRight: "6px" }}>
                        {viewing.chunks?.map((c) => (
                            <div
                                key={c.id}
                                style={{
                                    background: "var(--rf-surface-subtle)",
                                    border: "1px solid var(--rf-border)",
                                    borderRadius: "8px",
                                    padding: "14px 16px",
                                }}
                            >
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                                    <span style={{ fontWeight: 600, fontSize: "0.82rem", color: "var(--rf-primary)" }}>
                                        Chunk #{c.chunk_index} (ID: {c.id})
                                    </span>
                                    <div style={{ display: "flex", gap: "6px" }}>
                                        <span className="badge uncited" style={{ fontSize: "0.72rem" }}>
                                            Pages {c.page_start}{c.page_end !== c.page_start ? `-${c.page_end}` : ""}
                                        </span>
                                        <span className="badge supported" style={{ fontSize: "0.72rem" }}>
                                            {c.word_count} words
                                        </span>
                                    </div>
                                </div>
                                <p style={{ margin: 0, fontSize: "0.9rem", lineHeight: "1.55", color: "var(--rf-text-primary)" }}>
                                    {c.text}
                                </p>
                            </div>
                        ))}
                    </div>
                </section>
            )}
        </div>
    );
}

export default PapersPanel;
