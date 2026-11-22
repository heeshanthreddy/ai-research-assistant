import { useContext } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import AuthContext from "../context/AuthContext";

function Sidebar({ profile, projectCount = 0 }) {
    const location = useLocation();
    const navigate = useNavigate();
    const { logout } = useContext(AuthContext);

    function handleLogout() {
        logout();
        navigate("/login");
    }

    const isDashboard = location.pathname === "/dashboard" || location.pathname === "/";

    return (
        <aside className="app-sidebar">
            <div className="sidebar-top">
                <div className="sidebar-section-title">Workspace Navigation</div>
                <div className="sidebar-menu">
                    <Link
                        to="/dashboard"
                        className={`sidebar-item ${isDashboard ? "active" : ""}`}
                    >
                        <span className="sidebar-icon">📁</span>
                        <span>Projects Dashboard</span>
                    </Link>
                </div>

                <div className="sidebar-section-title">Local NLP Engine</div>
                <div className="sidebar-engine-card">
                    <div className="sidebar-engine-title">
                        <span>Local Pipeline</span>
                        <span className="sidebar-engine-status" title="Active & Ready"></span>
                    </div>
                    <div className="sidebar-engine-desc">
                        PyMuPDF text extraction, semantic chunking, and exact cosine retrieval running locally on CPU.
                    </div>
                    <div style={{ marginTop: "10px", display: "flex", gap: "6px", flexWrap: "wrap" }}>
                        <span className="badge PROCESSED" style={{ fontSize: "0.72rem" }}>Zero Cloud AI</span>
                        <span className="badge supported" style={{ fontSize: "0.72rem" }}>Extractive Grounding</span>
                    </div>
                </div>

                <div className="sidebar-section-title">System Metrics</div>
                <div className="sidebar-menu">
                    <div className="sidebar-item" style={{ cursor: "default" }}>
                        <span className="sidebar-icon">📊</span>
                        <span>Active Projects:</span>
                        <strong style={{ marginLeft: "auto", color: "var(--rf-primary)" }}>{projectCount}</strong>
                    </div>
                    <div className="sidebar-item" style={{ cursor: "default" }}>
                        <span className="sidebar-icon">🔒</span>
                        <span>Privacy:</span>
                        <span className="badge PROCESSED" style={{ marginLeft: "auto", fontSize: "0.7rem" }}>Offline</span>
                    </div>
                </div>

                <div className="sidebar-section-title">Research Highlights</div>
                <div style={{ padding: "0 10px", fontSize: "0.8rem", color: "var(--rf-text-muted)", lineHeight: "1.5" }}>
                    • Extractive Question Answering<br />
                    • Automatic Citation Verification<br />
                    • Corpus-relative Novelty Analysis
                </div>
            </div>

            <div className="sidebar-footer">
                <div className="sidebar-user-card">
                    <div className="sidebar-user-avatar">
                        {profile?.user_id ? `U${profile.user_id}` : "RF"}
                    </div>
                    <div className="sidebar-user-details">
                        <div className="sidebar-user-name">
                            {profile?.user_id ? `Researcher #${profile.user_id}` : "Researcher"}
                        </div>
                        <div className="sidebar-user-role">Authenticated Session</div>
                    </div>
                </div>
                <button
                    onClick={handleLogout}
                    className="btn-nav-logout"
                    style={{ width: "100%", textAlign: "center", marginTop: "6px" }}
                >
                    Sign Out
                </button>
            </div>
        </aside>
    );
}

export default Sidebar;
