import { createContext, useState } from "react";
// use state --> "Run this when this component/provider starts." This fixes the refresh problem

const AuthContext = createContext();

export function AuthProvider({ children }) {

    const [isAuthenticated, setIsAuthenticated] = useState(() => !!localStorage.getItem("access_token"));
    function logout() {
        localStorage.removeItem("access_token");
        setIsAuthenticated(false);
    }

    return (
        <AuthContext.Provider value={{ isAuthenticated, setIsAuthenticated , logout }}>
            {children}
        </AuthContext.Provider>
    );
}

export default AuthContext;