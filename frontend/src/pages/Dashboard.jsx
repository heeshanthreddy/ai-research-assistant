import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import { getProfile } from "../services/authService";
import { errorMessage } from "../services/api";
import { listProjects, createProject, deleteProject } from "../services/researchService";
import Sidebar from "../components/sidebar";

function Dashboard() {
    const [profile, setProfile] = useState(null);
    const [projects, setProjects] = useState(null);       // null = loading
    const [error, setError] = useState("");
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [field, setField] = useState("");
    const [searchQuery, setSearchQuery] = useState("");
    const [isCreating, setIsCreating] = useState(false);
    const [busy, setBusy] = useState(false);

    useEffect(() => {
        async function load() {
            try {
                const [profData, projData] = await Promise.all([
                    getProfile(),
                    listProjects()
                ]);
                setProfile(profData);
                setProjects(projData);
            } catch (err) {
                setError(errorMessage(err, "Could not load your projects"));
                setProjects([]);
            }
        }
        load();
    }, []);

    async function handleCreate(event) {
        event.preventDefault();
        setError("");
        setBusy(true);
        try {
            const project = await createProject({ title, description, research_field: field });
            setProjects((prev) => [...(prev || []), project]);
            setTitle("");
            setDescription("");
            setField("");
            setIsCreating(false);
        } catch (err) {
            setError(errorMessage(err, "Could not create the project"));
        } finally {
            setBusy(false);
        }
    }

    async function handleDelete(project) {
        if (!window.confirm(`Delete "${project.title}" and all its papers?`)) return;
        try {
            await deleteProject(project.id);
            setProjects((prev) => prev.filter((p) => p.id !== project.id));
        } catch (err) {
            setError(errorMessage(err, "Could not delete the project"));
        }
    }

    // Filter projects based on real-time search query
    const filteredProjects = useMemo(() => {
        if (!projects) return [];
        if (!searchQuery.trim()) return projects;
        const q = searchQuery.toLowerCase();
        return projects.filter(
            (p) =>
                p.title.toLowerCase().includes(q) ||
                (p.research_field && p.research_field.toLowerCase().includes(q)) ||
                (p.description && p.description.toLowerCase().includes(q))
        );
    }, [projects, searchQuery]);

    // Unique research fields count
    const uniqueFieldsCount = useMemo(() => {
        if (!projects || projects.length === 0) return 0;
        const fields = new Set(projects.map((p) => p.research_field).filter(Boolean));
        return fields.size || 1;
    }, [projects]);

    return (
        <div className="app-container">
            <Sidebar profile={profile} projectCount={projects ? projects.length : 0} />

            <main className="app-main">
                {/* Welcome Hero Section */}
                <section className="welcome-banner">
                    <div className="welcome-content">
                        <div className="welcome-title">
                            <span>Welcome to ResearchForge</span>
                            <span style={{ fontSize: "1.1rem" }}>🎓</span>
                        </div>
                        <p className="welcome-subtitle">
                            An academic AI research assistant for citation-grounded extractive question answering,
                            semantic chunking, and corpus overlap detection. Everything executes locally with zero external API dependencies.
                        </p>
                        <div className="welcome-highlights">
                            <div className="welcome-chip">
                                <span className="welcome-chip-icon">🛡️</span>
                                <span>Zero Cloud LLM Dependency</span>
                            </div>
                            <div className="welcome-chip">
                                <span className="welcome-chip-icon">📑</span>
                                <span>Extractive Evidence Grounding</span>
                            </div>
                            <div className="welcome-chip">
                                <span className="welcome-chip-icon">🎯</span>
                                <span>Automated Citation Verification</span>
                            </div>
                            <div className="welcome-chip">
                                <span className="welcome-chip-icon">⚡</span>
                                <span>Native PyMuPDF Parsing</span>
                            </div>
                        </div>
                    </div>
                </section>

                {error && <div className="notice error">{error}</div>}

                {/* Metrics Overview Grid */}
                <div className="stats-grid">
                    <div className="stat-card">
                        <div>
                            <div className="stat-info-label">Total Projects</div>
                            <div className="stat-info-value">{projects ? projects.length : 0}</div>
                            <div className="stat-info-sub">Active research spaces</div>
                        </div>
                        <div className="stat-icon-wrapper">📁</div>
                    </div>

                    <div className="stat-card">
                        <div>
                            <div className="stat-info-label">Research Fields</div>
                            <div className="stat-info-value">{uniqueFieldsCount}</div>
                            <div className="stat-info-sub">Domains represented</div>
                        </div>
                        <div className="stat-icon-wrapper" style={{ background: "#ecfdf5", color: "#059669" }}>🔬</div>
                    </div>

                    <div className="stat-card">
                        <div>
                            <div className="stat-info-label">NLP Processing</div>
                            <div className="stat-info-value" style={{ fontSize: "1.25rem", marginTop: "4px" }}>Local CPU</div>
                            <div className="stat-info-sub">Embedding cosine scan</div>
                        </div>
                        <div className="stat-icon-wrapper" style={{ background: "#fef3c7", color: "#d97706" }}>⚙️</div>
                    </div>

                    <div className="stat-card">
                        <div>
                            <div className="stat-info-label">Verification Mode</div>
                            <div className="stat-info-value" style={{ fontSize: "1.25rem", marginTop: "4px" }}>Sentence N-Gram</div>
                            <div className="stat-info-sub">Attribution checking</div>
                        </div>
                        <div className="stat-icon-wrapper" style={{ background: "#f5f3ff", color: "#7c3aed" }}>✓</div>
                    </div>
                </div>

                {/* Toolbar: Search, Filters & Action Buttons */}
                <div className="dashboard-toolbar">
                    <div className="toolbar-search">
                        <svg
                            className="search-icon-svg"
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <circle cx="11" cy="11" r="8"></circle>
                            <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                        </svg>
                        <input
                            type="text"
                            className="search-input"
                            placeholder="Filter projects by title, field, or keywords..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                        />
                    </div>

                    <div className="toolbar-actions">
                        <button
                            onClick={() => setIsCreating(!isCreating)}
                            style={{ display: "inline-flex", alignItems: "center", gap: "6px" }}
                        >
                            <span>{isCreating ? "✕ Close Form" : "+ New Research Project"}</span>
                        </button>
                    </div>
                </div>

                {/* Create Project Form (Collapsible/Dedicated) */}
                {isCreating && (
                    <section className="card" style={{ border: "1px solid var(--rf-primary-border)", background: "#ffffff" }}>
                        <div className="card-header-row">
                            <h2>Create New Research Project</h2>
                            <span className="badge supported">New Workspace</span>
                        </div>
                        <form onSubmit={handleCreate} className="stack">
                            <div>
                                <label className="form-label">Project Title *</label>
                                <input
                                    placeholder="e.g. Transformer Architectures for Dense Information Retrieval"
                                    value={title}
                                    onChange={(e) => setTitle(e.target.value)}
                                    required
                                />
                            </div>

                            <div>
                                <label className="form-label">Research Domain / Field (Optional)</label>
                                <input
                                    placeholder="e.g. Natural Language Processing, Machine Learning, Information Retrieval"
                                    value={field}
                                    onChange={(e) => setField(e.target.value)}
                                />
                            </div>

                            <div>
                                <label className="form-label">Description / Research Goals (Optional)</label>
                                <textarea
                                    placeholder="Brief overview of research questions, corpus focus, and expected analysis..."
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={3}
                                />
                            </div>

                            <div style={{ display: "flex", gap: "10px", marginTop: "6px" }}>
                                <button type="submit" disabled={busy}>
                                    {busy ? "Creating Project..." : "Initialize Project"}
                                </button>
                                <button
                                    type="button"
                                    className="secondary"
                                    onClick={() => {
                                        setIsCreating(false);
                                        setTitle("");
                                        setDescription("");
                                        setField("");
                                    }}
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </section>
                )}

                {/* Projects Section */}
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "16px" }}>
                    <h2>
                        Your Research Projects{" "}
                        {projects && <span className="muted small">({filteredProjects.length})</span>}
                    </h2>
                </div>

                {/* Loading State */}
                {projects === null && (
                    <div className="empty-state-card">
                        <div className="empty-state-icon">⌛</div>
                        <div className="empty-state-title">Loading Research Projects</div>
                        <div className="empty-state-desc">Fetching your projects from the local database...</div>
                    </div>
                )}

                {/* Zero Projects Empty State */}
                {projects && projects.length === 0 && !isCreating && (
                    <div className="empty-state-card">
                        <div className="empty-state-icon">📚</div>
                        <div className="empty-state-title">No Research Projects Yet</div>
                        <div className="empty-state-desc">
                            Create your first project to upload research papers (PDF), run extractive question answering,
                            and verify citations with local sentence-level attribution.
                        </div>
                        <button onClick={() => setIsCreating(true)}>
                            + Create Your First Project
                        </button>
                    </div>
                )}

                {/* Search Zero Results Empty State */}
                {projects && projects.length > 0 && filteredProjects.length === 0 && (
                    <div className="empty-state-card">
                        <div className="empty-state-icon">🔍</div>
                        <div className="empty-state-title">No Projects Found</div>
                        <div className="empty-state-desc">
                            No projects match &ldquo;<strong>{searchQuery}</strong>&rdquo;. Try searching for a different title or research field.
                        </div>
                        <button className="secondary" onClick={() => setSearchQuery("")}>
                            Clear Search Filter
                        </button>
                    </div>
                )}

                {/* Projects Grid */}
                {projects && filteredProjects.length > 0 && (
                    <div className="projects-grid">
                        {filteredProjects.map((p) => {
                            const createdDate = p.created_at
                                ? new Date(p.created_at).toLocaleDateString(undefined, {
                                      year: "numeric",
                                      month: "short",
                                      day: "numeric",
                                  })
                                : "Recent";

                            return (
                                <div className="project-card" key={p.id}>
                                    <div>
                                        <div className="project-card-header">
                                            <span className="project-field-badge">
                                                {p.research_field || "General Research"}
                                            </span>
                                            <span className="project-status-dot">
                                                {p.status || "ACTIVE"}
                                            </span>
                                        </div>

                                        <Link to={`/projects/${p.id}`} className="project-card-title">
                                            {p.title}
                                        </Link>

                                        <div className="project-card-desc">
                                            {p.description || "No project description provided. Click to open the workspace and ingest research papers."}
                                        </div>
                                    </div>

                                    <div className="project-card-footer">
                                        <div className="project-card-meta">
                                            <span>Created: {createdDate}</span>
                                        </div>

                                        <div className="project-card-actions">
                                            <Link to={`/projects/${p.id}`} className="btn-open-project">
                                                <span>Open Workspace</span>
                                                <span>&rarr;</span>
                                            </Link>
                                            <button
                                                className="btn-delete-project"
                                                title={`Delete ${p.title}`}
                                                onClick={() => handleDelete(p)}
                                            >
                                                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                                    <polyline points="3 6 5 6 21 6"></polyline>
                                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                                </svg>
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </main>
        </div>
    );
}

export default Dashboard;
