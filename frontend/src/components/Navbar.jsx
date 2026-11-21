import { useContext } from "react";
import { Link, useNavigate } from "react-router-dom";
import AuthContext from "../context/AuthContext";

function Navbar() {

    const { isAuthenticated, logout } = useContext(AuthContext);
    const navigate = useNavigate();

    function handleLogout() {
        logout();
        navigate("/login");
    }

    return (
        <nav>

            <Link to="/">
                ResearchForge 🚀
            </Link>

            {isAuthenticated && (
                <>
                    <Link to="/dashboard">
                        Dashboard
                    </Link>

                    <button onClick={handleLogout}>
                        Logout
                    </button>
                </>
            )}

        </nav>
    );
}

export default Navbar;