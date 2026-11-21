import { StrictMode } from 'react'; // it helps in finding bugs while developing
import { createRoot } from 'react-dom/client'; // it tells react to find html page and attach our react application to it.
import './index.css';   // it loads global css
import './styles/global.css'; // ResearchForge layout/components (loaded after index.css so it wins)
import App from './App.jsx'; // React starts by loading the App component( as everything resides in it )
import { AuthProvider } from "./context/AuthContext.jsx";

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <AuthProvider>
            <App />
        </AuthProvider>
    </StrictMode>
);