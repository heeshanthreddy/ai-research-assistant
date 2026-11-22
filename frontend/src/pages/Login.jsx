import { useState, useContext } from "react";
import { loginUser } from "../services/authService";
import { errorMessage } from "../services/api";
import AuthContext from "../context/AuthContext";
import { useNavigate, Link, useLocation } from "react-router-dom";

function Login() {
    const navigate = useNavigate();
    const location = useLocation();
    const { setIsAuthenticated } = useContext(AuthContext);
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [busy, setBusy] = useState(false);

    function handleEmailChange(event) {
        setEmail(event.target.value);
    }

    function handlePasswordChange(event) {
        setPassword(event.target.value);
    }

    async function handleLogin(event) {
        event.preventDefault();
        setError("");
        setBusy(true);

        try {
            const data = await loginUser(email, password);
            localStorage.setItem("access_token", data.access_token);
            setIsAuthenticated(true);
            navigate("/dashboard");
        } catch (err) {
            setError(errorMessage(err, "Login failed. Check your email and password."));
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
                    <h1 style={{ fontSize: "1.6rem", margin: "0 0 6px 0" }}>ResearchForge</h1>
                    <p className="muted small">Local NLP Academic Research Assistant</p>
                </div>

                {location.state?.registered && (
                    <div className="notice ok">
                        ✓ Account created successfully. Please sign in below.
                    </div>
                )}

                {error && <div className="notice error">{error}</div>}

                <form onSubmit={handleLogin} className="stack">
                    <div>
                        <label className="form-label">Email Address</label>
                        <input
                            type="email"
                            placeholder="name@university.edu"
                            value={email}
                            onChange={handleEmailChange}
                            required
                            autoFocus
                        />
                    </div>

                    <div>
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            placeholder="••••••••"
                            value={password}
                            onChange={handlePasswordChange}
                            required
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={busy}
                        style={{ marginTop: "8px", width: "100%", padding: "10px" }}
                    >
                        {busy ? "Authenticating Session..." : "Sign In to Workspace"}
                    </button>
                </form>

                <div style={{ textAlign: "center", marginTop: "20px", paddingTop: "16px", borderTop: "1px solid var(--rf-border)" }}>
                    <p className="muted small">
                        New to ResearchForge?{" "}
                        <Link to="/register" style={{ fontWeight: 600 }}>Create an account</Link>
                    </p>
                </div>
            </div>
        </div>
    );
}

export default Login;
