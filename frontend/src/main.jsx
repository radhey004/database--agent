import React from "react";
import ReactDOM from "react-dom/client";

import {
  BrowserRouter,
  Routes,
  Route,
} from "react-router-dom";

import "./index.css";

import App from "./App";

import ChatPage from "./pages/ChatPage";

import ConnectDatabasePage from "./pages/ConnectDatabasePage";

import SecurityPage from "./pages/SecurityPage";

import {
  DatabaseProvider,
} from "./context/DatabaseContext";

ReactDOM.createRoot(
  document.getElementById("root")
).render(
  <React.StrictMode>
    <DatabaseProvider>
      <BrowserRouter>
        <Routes>
          <Route
            path="/"
            element={<App />}
          >
            <Route
              index
              element={<ChatPage />}
            />

            <Route
              path="connect"
              element={
                <ConnectDatabasePage />
              }
            />

            <Route
              path="security"
              element={
                <SecurityPage />
              }
            />
          </Route>
        </Routes>
      </BrowserRouter>
    </DatabaseProvider>
  </React.StrictMode>
);