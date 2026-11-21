import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getProject, listPapers } from "../services/researchService";
import { errorMessage } from "../services/api";
import StatusBanner from "../components/StatusBanner";
import PapersPanel from "../components/PapersPanel";
import AskPanel from "../components/AskPanel";
import IdeaPanel from "../components/IdeaPanel";
import OverlapPanel from "../components/OverlapPanel";
import PairPanel from "../components/PairPanel";

const TABS = [
    ["papers", "Papers"], ["ask", "Ask"], ["idea", "Idea analysis"],
    ["overlap", "Overlap"], ["pair", "Pair similarity"],
];

function ProjectWorkspace() {
    const { projectId } = useParams();
    const [project, setProject] = useState(null);
    const [papers, setPapers] = useState(null);
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
                setProject(await getProject(projectId));
            } catch (err) {
                setError(errorMessage(err, "Project not found"));
            }
            await refreshPapers();
        }
        load();
    }, [projectId, refreshPapers]);

    const processed = (papers || []).filter((p) => p.status === "PROCESSED").length;

    return (
        <div className="page">
            <p><Link to="/dashboard">&larr; Projects</Link></p>
            <h1>{project ? project.title : "Project"}</h1>
            {error && <p className="notice error">{error}</p>}

            <StatusBanner projectId={projectId} onReindexed={refreshPapers} />

            <div className="tabs">
                {TABS.map(([key, label]) => (
                    <button key={key} className={tab === key ? "tab active" : "tab"} onClick={() => setTab(key)}>{label}</button>
                ))}
            </div>

            {tab === "papers" && <PapersPanel projectId={projectId} papers={papers} onChanged={refreshPapers} />}
            {tab === "ask" && <AskPanel projectId={projectId} processedCount={processed} />}
            {tab === "idea" && <IdeaPanel projectId={projectId} />}
            {tab === "overlap" && <OverlapPanel projectId={projectId} />}
            {tab === "pair" && <PairPanel />}
        </div>
    );
}

export default ProjectWorkspace;
