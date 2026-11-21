import api from "./api";

// ---- projects -------------------------------------------------------------
export const listProjects = async () => (await api.get("/projects/")).data.projects;
export const createProject = async (data) => (await api.post("/projects/", data)).data.project;
export const getProject = async (id) => (await api.get(`/projects/${id}`)).data.project;
export const deleteProject = async (id) => (await api.delete(`/projects/${id}`)).data;

// ---- papers ---------------------------------------------------------------
export const listPapers = async (pid) => (await api.get(`/projects/${pid}/papers`)).data.papers;
export const deletePaper = async (pid, paperId) => (await api.delete(`/projects/${pid}/papers/${paperId}`)).data;
export const getPaperChunks = async (pid, paperId) => (await api.get(`/projects/${pid}/papers/${paperId}/chunks`)).data;
export const getChunk = async (pid, chunkId) => (await api.get(`/projects/${pid}/chunks/${chunkId}`)).data.chunk;
export const reindexProject = async (pid) => (await api.post(`/projects/${pid}/reindex`)).data;

export async function uploadPaper(pid, file) {
    const form = new FormData();
    form.append("file", file);
    return (await api.post(`/projects/${pid}/papers`, form)).data;
}

// ---- local NLP ------------------------------------------------------------
export const nlpStatus = async () => (await api.get("/nlp/status")).data;
export const askQuestion = async (pid, question) => (await api.post(`/projects/${pid}/ask`, { question })).data;
export const analyseIdea = async (pid, idea) => (await api.post(`/projects/${pid}/idea`, { idea })).data;
export const checkOverlap = async (pid, text) => (await api.post(`/projects/${pid}/overlap`, { text })).data;
export const pairSimilarity = async (text_a, text_b) => (await api.post("/nlp/pair-similarity", { text_a, text_b })).data;
