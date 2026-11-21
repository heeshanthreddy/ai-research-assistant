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
            setError(errorMessage(err, "Registration failed"));
        } finally {
            setBusy(false);
        }
    }

    return (
        <div className="page narrow">
            <h1>ResearchForge</h1>
            <h2>Create Account</h2>

            <form onSubmit={handleRegister} className="stack">
                <input placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} required />
                <input type="email" placeholder="Email" value={email} onChange={(e) => setEmail(e.target.value)} required />
                <input type="password" placeholder="Password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                {error && <p className="notice error">{error}</p>}
                <button type="submit" disabled={busy}>{busy ? "Creating..." : "Register"}</button>
            </form>

            <p className="muted">Already registered? <Link to="/login">Sign in</Link></p>
        </div>
    );
}

export default Register;
