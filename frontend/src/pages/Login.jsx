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
            setError(errorMessage(err, "Login failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="page narrow">
            <h1>ResearchForge</h1>
            <h2>Sign In</h2>

            {location.state?.registered && (
                <p className="notice ok">Account created. Please sign in.</p>
            )}

            <form onSubmit={handleLogin} className="stack">

                <input type="email" placeholder="Email" value={email} onChange={handleEmailChange} required />

                <input type="password" placeholder="Password" value={password} onChange={handlePasswordChange} required />

                {error && <p className="notice error">{error}</p>}

                <button type="submit" disabled={busy}> {busy ? "Signing in..." : "Login"} </button>

            </form>

            <p className="muted">No account? <Link to="/register">Create one</Link></p>
        </div>
    );
}

export default Login;
