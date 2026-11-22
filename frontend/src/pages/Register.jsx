import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { registerUser } from "../services/authService";
import { errorMessage } from "../services/api";

function Register() {
    const navigate = useNavigate();
    const [username, setUsername] = useState("");
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    async function handleRegister(event) {
        event.preventDefault();
        setError("");
        setBusy(true);
        try {
            await registerUser(username, email, password);
            navigate("/login", { state: { registered: true } });
        } catch (err) {
            setError(errorMessage(err, "Registration failed. Try a different username/email."));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "calc(100vh - 120px)", padding: "24px 16px" }}>
            <div className="card" style={{ width: "100%", maxWidth: "440px", padding: "36px 32px", borderRadius: "16px", boxShadow: "var(--rf-shadow-md)" }}>
                <div style={{ textAlign: "center", marginBottom: "24px" }}>
                    <div className="nav-logo-icon" style={{ margin: "0 auto 12px", width: "42px", height: "42px", fontSize: "18px" }}>
                        RF
                    </div>
                    <h1 style={{ fontSize: "1.6rem", margin: "0 0 6px 0" }}>Create Researcher Account</h1>
                    <p className="muted small">Set up your local research assistant workspace</p>
                </div>

                {error && <div className="notice error">{error}</div>}

                <form onSubmit={handleRegister} className="stack">
                    <div>
                        <label className="form-label">Researcher / Username *</label>
                        <input
                            placeholder="e.g. jdoe_nlp"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            autoFocus
                        />
                    </div>

                    <div>
                        <label className="form-label">Academic Email Address *</label>
                        <input
                            type="email"
                            placeholder="name@university.edu"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            required
                        />
                    </div>

                    <div>
                        <label className="form-label">Password *</label>
                        <input
                            type="password"
                            placeholder="Minimum 6 characters"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={busy}
                        style={{ marginTop: "8px", width: "100%", padding: "10px" }}
                    >
                        {busy ? "Creating Account..." : "Register & Continue"}
                    </button>
                </form>

                <div style={{ textAlign: "center", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--rf-border)" }}>
                    <p className="muted small">
                        Already have an account?{" "}
                        <Link to="/login" style={{ fontWeight: 600 }}>Sign in</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default Register;
