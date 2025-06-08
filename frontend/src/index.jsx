// frontend/src/index.jsx

import "./shared/styles/main.css"; // ✅ Correct path now
import "whatwg-fetch";

import { createRoot } from "react-dom/client";
import App from "./app/main";

const root = document.getElementById("root");
createRoot(root).render(<App />);
