import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getProfile } from "../services/authService";
import { errorMessage } from "../services/api";
import { listProjects, createProject, deleteProject } from "../services/researchService";

function Dashboard() {

    const [profile, setProfile] = useState(null);
    const [projects, setProjects] = useState(null);       // null = loading
    const [error, setError] = useState("");
    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [field, setField] = useState("");

    useEffect(() => {

        async function load() {
            try {
                setProfile(await getProfile());
                setProjects(await listProjects());
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
        try {
            const project = await createProject({ title, description, research_field: field });
            setProjects((prev) => [...(prev || []), project]);
            setTitle(""); setDescription(""); setField("");
        } catch (err) {
            setError(errorMessage(err, "Could not create the project"));
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

    return (
        <div className="page">
            <h1>ResearchForge Dashboard</h1>
            {profile && <p className="muted">Signed in (user id {profile.user_id})</p>}

            {error && <p className="notice error">{error}</p>}

            <section className="card">
                <h2>New project</h2>
                <form onSubmit={handleCreate} className="stack">
                    <input placeholder="Project title" value={title} onChange={(e) => setTitle(e.target.value)} required />
                    <input placeholder="Research field (optional)" value={field} onChange={(e) => setField(e.target.value)} />
                    <textarea placeholder="Description (optional)" value={description} onChange={(e) => setDescription(e.target.value)} rows={2} />
                    <button type="submit">Create project</button>
                </form>
            </section>

            <section className="card">
                <h2>Your projects</h2>
                {projects === null && <p className="muted">Loading...</p>}
                {projects && projects.length === 0 && <p className="muted">No projects yet. Create one above.</p>}
                {projects && projects.map((p) => (
                    <div className="row" key={p.id}>
                        <div>
                            <Link to={`/projects/${p.id}`}><strong>{p.title}</strong></Link>
                            <div className="muted small">{p.research_field || "no field"} {p.description ? `- ${p.description}` : ""}</div>
                        </div>
                        <button className="danger" onClick={() => handleDelete(p)}>Delete</button>
                    </div>
                ))}
            </section>
        </div>
    );
}

export default Dashboard;
