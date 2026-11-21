import axios from "axios";
// axios is used as a messenger b/w react and flask. it is a tool that allows JavaScript to make HTTP requests

const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:5000/api"
});

api.interceptors.request.use(
    (config) => {

        const token = localStorage.getItem("access_token");

        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }

        return config;
    }
);

// An expired/invalid token on a protected call sends the user back to the login page.
api.interceptors.response.use(
    (response) => response,
    (error) => {
        const url = error.config?.url || "";
        const isAuthForm = url.startsWith("/auth/login") || url.startsWith("/auth/register");
        const hadToken = !!localStorage.getItem("access_token");
        if ((error.response?.status === 401 || error.response?.status === 422) && hadToken && !isAuthForm) {
            localStorage.removeItem("access_token");
            window.location.href = "/login";
        }
        return Promise.reject(error);
    }
);

// Readable message from a failed request.
export function errorMessage(error, fallback = "Something went wrong") {
    if (error.response) {
        const d = error.response.data;
        return d?.error || d?.message || `${fallback} (HTTP ${error.response.status})`;
    }
    if (error.request) {
        return "Cannot reach the backend. Is it running on http://127.0.0.1:5000 ?";
    }
    return error.message || fallback;
}

export default api;
