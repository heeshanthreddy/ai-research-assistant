import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProject, listPapers } from "../services/researchService";
import { getProfile } from "../services/authService";
import { errorMessage } from "../services/api";
import StatusBanner from "../components/StatusBanner";
import PapersPanel from "../components/PapersPanel";
import AskPanel from "../components/AskPanel";
import IdeaPanel from "../components/IdeaPanel";
import OverlapPanel from "../components/OverlapPanel";
import PairPanel from "../components/PairPanel";
import Sidebar from "../components/sidebar";

const TABS = [
    ["papers", "📄 Papers & Ingestion"],
    ["ask", "💬 Extractive QA"],
    ["idea", "💡 Research Idea Analysis"],
    ["overlap", "🔍 Semantic Overlap"],
    ["pair", "⚖️ Pair Classifier"],
];

function ProjectWorkspace() {
    const { projectId } = useParams();
    const [project, setProject] = useState(null);
    const [papers, setPapers] = useState(null);
    const [profile, setProfile] = useState(null);
    const [tab, setTab] = useState("papers");
    const [error, setError] = useState("");

    const refreshPapers = useCallback(async () => {
        try {
            setPapers(await listPapers(projectId));
        } catch (err) {
            setError(errorMessage(err, "Could not load papers"));
            setPapers([]);
        }
    }, [projectId]);

    useEffect(() => {
        async function load() {
            try {
                const [profData, projData] = await Promise.all([
                    getProfile().catch(() => null),
                    getProject(projectId)
                ]);
                setProfile(profData);
                setProject(projData);
            } catch (err) {
                setError(errorMessage(err, "Project not found"));
            }
            await refreshPapers();
        }
        load();
    }, [projectId, refreshPapers]);

    const processed = (papers || []).filter((p) => p.status === "PROCESSED").length;

    return (
        <div className="app-container">
            <Sidebar profile={profile} projectCount={1} />

            <main className="app-main">
                {/* Academic Breadcrumb Navigation */}
                <div className="breadcrumb-nav">
                    <Link to="/dashboard">Dashboard</Link>
                    <span className="breadcrumb-separator">/</span>
                    <Link to="/dashboard">Projects</Link>
                    <span className="breadcrumb-separator">/</span>
                    <span style={{ color: "var(--rf-text-primary)", fontWeight: 600 }}>
                        {project ? project.title : "Workspace"}
                    </span>
                </div>

                {/* Project Header Card */}
                <div className="card" style={{ marginTop: "4px", marginBottom: "20px" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "12px" }}>
                        <div>
                            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "6px" }}>
                                <span className="project-field-badge">
                                    {project?.research_field || "General Research"}
                                </span>
                                <span className="badge supported" style={{ fontSize: "0.72rem" }}>
                                    {processed} / {papers ? papers.length : 0} Papers Processed
                                </span>
                            </div>
                            <h1 style={{ margin: "4px 0 8px 0" }}>{project ? project.title : "Project Workspace"}</h1>
                            {project?.description && (
                                <p className="muted" style={{ fontSize: "0.92rem", maxWidth: "800px" }}>
                                    {project.description}
                                </p>
                            )}
                        </div>

                        <Link to="/dashboard" className="btn-open-project" style={{ border: "1px solid var(--rf-border)" }}>
                            &larr; Back to Dashboard
                        </Link>
                    </div>
                </div>

                {error && <div className="notice error">{error}</div>}

                {/* NLP Status & Embedding Mode Banner */}
                <StatusBanner projectId={projectId} onReindexed={refreshPapers} />

                {/* Workspace Navigation Tabs */}
                <div className="tabs">
                    {TABS.map(([key, label]) => (
                        <button
                            key={key}
                            className={tab === key ? "tab active" : "tab"}
                            onClick={() => setTab(key)}
                        >
                            {label}
                        </button>
                    ))}
                </div>

                {/* Active Tool Panel */}
                <div className="workspace-tab-content">
                    {tab === "papers" && (
                        <PapersPanel projectId={projectId} papers={papers} onChanged={refreshPapers} />
                    )}
                    {tab === "ask" && (
                        <AskPanel projectId={projectId} processedCount={processed} />
                    )}
                    {tab === "idea" && (
                        <IdeaPanel projectId={projectId} />
                    )}
                    {tab === "overlap" && (
                        <OverlapPanel projectId={projectId} />
                    )}
                    {tab === "pair" && (
                        <PairPanel />
                    )}
                </div>
            </main>
        </div>
    );
}

export default ProjectWorkspace;
