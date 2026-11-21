import { useState } from "react";
import { pairSimilarity } from "../services/researchService";
import { errorMessage } from "../services/api";

function PairPanel() {
    const [a, setA] = useState("");
    const [b, setB] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState("");
    const [result, setResult] = useState(null);

    async function handleSubmit(event) {
        event.preventDefault();
        setBusy(true); setError(""); setResult(null);
        try {
            setResult(await pairSimilarity(a, b));
        } catch (err) {
            setError(errorMessage(err, "Comparison failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div>
            <form onSubmit={handleSubmit} className="card stack">
                <h2>Passage-pair similarity</h2>
                <textarea rows={3} value={a} onChange={(e) => setA(e.target.value)} placeholder="Passage A" required />
                <textarea rows={3} value={b} onChange={(e) => setB(e.target.value)} placeholder="Passage B" required />
                <button type="submit" disabled={busy}>{busy ? "Comparing..." : "Compare"}</button>
                {error && <p className="notice error">{error}</p>}
            </form>

            {result && (
                <section className="card">
                    <table>
                        <thead><tr><th>Feature</th><th>Value</th></tr></thead>
                        <tbody>
                            {Object.entries(result.features).map(([k, v]) => (
                                <tr key={k}><td>{k}</td><td>{v.toFixed(3)}</td></tr>
                            ))}
                        </tbody>
                    </table>
                    {result.prediction
                        ? <p>Classifier: {result.prediction.similar ? "similar" : "not similar"} (p = {result.prediction.probability})</p>
                        : <p className="notice warn">{result.model.note}</p>}
                </section>
            )}
        </div>
    );
}

export default PairPanel;
