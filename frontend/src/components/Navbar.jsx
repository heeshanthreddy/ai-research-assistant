import { useContext } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import AuthContext from "../context/AuthContext";

function Navbar() {
    const { isAuthenticated, logout } = useContext(AuthContext);
    const navigate = useNavigate();
    const location = useLocation();

    function handleLogout() {
        logout();
        navigate("/login");
    }

    const isDashboard = location.pathname === "/dashboard";

    return (
        <nav>
            <Link to={isAuthenticated ? "/dashboard" : "/login"} className="nav-brand">
                <div className="nav-logo-icon">RF</div>
                <div className="nav-brand-title">
                    <span>ResearchForge</span>
                    <span className="nav-brand-tag">v2.0 • Local NLP</span>
                </div>
            </Link>

            {isAuthenticated && (
                <div className="nav-menu">
                    <Link
                        to="/dashboard"
                        className={`nav-link ${isDashboard ? "active" : ""}`}
                    >
                        Projects
                    </Link>

                    <div className="nav-user-badge" title="Local Extractive & Citation Engine">
                        <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--rf-success)" }}></span>
                        <span>100% Offline & Private</span>
                    </div>

                    <button onClick={handleLogout} className="btn-nav-logout">
                        Logout
                    </button>
                </div>
            )}
        </nav>
    );
}

export default Navbar;
