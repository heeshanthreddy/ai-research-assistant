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
        if (!file) { setError("Choose a PDF first."); return; }
        setBusy(true); setError(""); setInfo("");
        try {
            const data = await uploadPaper(projectId, file);
            setInfo(data.message);
            fileRef.current.value = "";
            await onChanged();
        } catch (err) {
            setError(errorMessage(err, "Upload failed"));
        } finally {
            setBusy(false);
        }
    }

    async function handleDelete(paper) {
        if (!window.confirm(`Delete "${paper.title || paper.original_filename}"?`)) return;
        try {
            await deletePaper(projectId, paper.id);
            if (viewing?.paper.id === paper.id) setViewing(null);
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
            <form onSubmit={handleUpload} className="card stack">
                <h2>Upload a research paper (PDF)</h2>
                <input type="file" accept="application/pdf,.pdf" ref={fileRef} />
                <button type="submit" disabled={busy}>
                    {busy ? "Extracting, chunking and embedding... (first run may take a while)" : "Upload and process"}
                </button>
                {info && <p className="notice ok">{info}</p>}
                {error && <p className="notice error">{error}</p>}
            </form>

            <section className="card">
                <h2>Papers</h2>
                {papers === null && <p className="muted">Loading...</p>}
                {papers && papers.length === 0 && <p className="muted">No papers yet.</p>}
                {papers && papers.length > 0 && (
                    <table>
                        <thead><tr><th>Title</th><th>Pages</th><th>Chunks</th><th>Status</th><th></th></tr></thead>
                        <tbody>
                            {papers.map((p) => (
                                <tr key={p.id}>
                                    <td>
                                        {p.title || p.original_filename}
                                        <div className="muted small">{p.original_filename} {p.extraction_method ? `- ${p.extraction_method}` : ""}</div>
                                        {p.processing_error && <div className="error-text small">{p.processing_error}</div>}
                                        {p.processing_warnings && <div className="warn-text small">{p.processing_warnings}</div>}
                                    </td>
                                    <td>{p.num_pages ?? "-"}</td>
                                    <td>{p.chunk_count}</td>
                                    <td><span className={`badge ${p.status}`}>{p.status}</span></td>
                                    <td className="actions">
                                        {p.status === "PROCESSED" && <button onClick={() => handleView(p)}>View chunks</button>}
                                        <button className="danger" onClick={() => handleDelete(p)}>Delete</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </section>

            {viewing && (
                <section className="card">
                    <h2>Chunks of "{viewing.paper.title || viewing.paper.original_filename}" ({viewing.chunks.length})</h2>
                    {viewing.chunks.map((c) => (
                        <div className="chunk" key={c.id}>
                            <div className="muted small">
                                chunk #{c.chunk_index} (id {c.id}) - pages {c.page_start}
                                {c.page_end !== c.page_start ? `-${c.page_end}` : ""} - {c.word_count} words
                            </div>
                            <p>{c.text}</p>
                        </div>
                    ))}
                </section>
            )}
        </div>
    );
}

export default PapersPanel;
