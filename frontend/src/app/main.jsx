import { createRoot } from "react-dom/client";
import Router from "./router";
import Providers from "./Providers";
import "@shared/styles/globals.css";

createRoot(document.getElementById("root")).render(
  <Providers><Router /></Providers>
);
