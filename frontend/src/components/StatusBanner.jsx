import { useEffect, useState } from "react";
import { nlpStatus, reindexProject } from "../services/researchService";
import { errorMessage } from "../services/api";

// Displays active NLP embedder and enables project re-indexing
function StatusBanner({ projectId, onReindexed }) {
    const [status, setStatus] = useState(null);
    const [error, setError] = useState("");
    const [msg, setMsg] = useState("");
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        let cancelled = false;
        nlpStatus()
            .then((s) => { if (!cancelled) setStatus(s); })
            .catch((err) => { if (!cancelled) setError(errorMessage(err, "NLP status unavailable")); });
        return () => { cancelled = true; };
    }, []);

    async function handleReindex() {
        setMsg("");
        setBusy(true);
        try {
            const r = await reindexProject(projectId);
            setMsg(r.message || "Project re-indexed successfully.");
            if (onReindexed) onReindexed();
        } catch (err) {
            setMsg(errorMessage(err, "Re-index failed"));
        } finally {
            setBusy(false);
        }
    }

    if (error) return <div className="notice error">{error}</div>;
    if (!status) return <div className="notice">Initializing NLP status monitor...</div>;

    const e = status.embedding;
    return (
        <div
            className={`notice ${e.semantic ? "ok" : "warn"}`}
            style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "20px" }}
        >
            <div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
                    <strong>Active Embedder:</strong>
                    <span className={`badge ${e.semantic ? "PROCESSED" : "weak_support"}`} style={{ fontSize: "0.75rem" }}>
                        {e.backend} ({e.semantic ? "Semantic Mode" : "Lexical Hashing Fallback"})
                    </span>
                    <span className="badge supported" style={{ fontSize: "0.75rem" }}>
                        100% Local CPU
                    </span>
                </div>
                <div className="small">
                    {e.semantic
                        ? "MiniLM dense vectors compute semantic similarity directly on your machine."
                        : "Lexical hashing maps n-grams to signed unit vectors without external network calls."}
                    {e.fallback_reason && <span className="muted"> ({e.fallback_reason})</span>}
                </div>
            </div>

            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <button
                    type="button"
                    className="secondary"
                    onClick={handleReindex}
                    disabled={busy}
                    style={{ fontSize: "0.82rem", padding: "6px 12px" }}
                >
                    {busy ? "Re-indexing Vectors..." : "⚡ Re-index Project"}
                </button>
                {msg && <span className="small" style={{ fontWeight: 600 }}>{msg}</span>}
            </div>
        </div>
    );
}

export default StatusBanner;
