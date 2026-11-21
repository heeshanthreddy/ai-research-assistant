import api from "./api";

export async function loginUser(email, password) {
    const response = await api.post("/auth/login", { email: email, password: password });
    return response.data;
}

export async function registerUser(username, email, password) {
    const response = await api.post("/auth/register", { username, email, password });
    return response.data;
}

export async function getProfile() {
    const response = await api.get("/auth/profile");

    return response.data;
}
