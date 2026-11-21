import { useEffect, useState } from "react";
import { nlpStatus, reindexProject } from "../services/researchService";
import { errorMessage } from "../services/api";

// Shows which embedder is active and warns clearly when it is the lexical fallback.
function StatusBanner({ projectId, onReindexed }) {
    const [status, setStatus] = useState(null);
    const [error, setError] = useState("");
    const [msg, setMsg] = useState("");

    useEffect(() => {
        let cancelled = false;
        nlpStatus()
            .then((s) => { if (!cancelled) setStatus(s); })
            .catch((err) => { if (!cancelled) setError(errorMessage(err, "NLP status unavailable")); });
        return () => { cancelled = true; };
    }, []);

    async function handleReindex() {
        setMsg("");
        try {
            const r = await reindexProject(projectId);
            setMsg(r.message);
            if (onReindexed) onReindexed();
        } catch (err) {
            setMsg(errorMessage(err, "Re-index failed"));
        }
    }

    if (error) return <p className="notice error">{error}</p>;
    if (!status) return <p className="notice">Loading NLP status...</p>;
    const e = status.embedding;
    return (
        <div className={`notice ${e.semantic ? "ok" : "warn"}`}>
            <strong>Embeddings:</strong> {e.backend} ({e.semantic ? "semantic" : "LEXICAL fallback"}).{" "}
            {e.semantic ? "Runs locally on CPU." :
                "Similarity reflects shared words, not meaning. Install sentence-transformers (see README) for semantic mode."}
            {e.fallback_reason && <div className="small">Reason: {e.fallback_reason}</div>}
            <div className="small">
                Question answering: extractive (sentences copied from your papers, no external API).{" "}
                <button className="link" onClick={handleReindex}>Re-index project with current embedder</button> {msg}
            </div>
        </div>
    );
}

export default StatusBanner;
