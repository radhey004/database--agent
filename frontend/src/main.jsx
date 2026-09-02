import React from "react";

import ReactDOM from "react-dom/client";

import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import "./index.css";

import App from "./App";

import ChatPage from "./pages/ChatPage";

import ConnectDatabasePage
  from "./pages/ConnectDatabasePage";

import SecurityPage
  from "./pages/SecurityPage";

import LoginPage
  from "./pages/LoginPage";

import RegisterPage
  from "./pages/RegisterPage";

import TermsPage
  from "./pages/TermsPage";

import {
  DatabaseProvider,
} from "./context/DatabaseContext";

import {
  AuthProvider,
} from "./context/AuthContext";

import {
  ChatProvider,
} from "./context/ChatContext";


ReactDOM.createRoot(
  document.getElementById(
    "root"
  )
).render(

  <React.StrictMode>

    <AuthProvider>

      <DatabaseProvider>

        <ChatProvider>

          <BrowserRouter>

            <Routes>

              {/* =========================================
                  PUBLIC ROUTES
              ========================================== */}

              <Route
                path="/login"
                element={
                  <LoginPage />
                }
              />


              <Route
                path="/register"
                element={
                  <RegisterPage />
                }
              />


              <Route
                path="/terms"
                element={
                  <TermsPage />
                }
              />


              {/* =========================================
                  PROTECTED APPLICATION
              ========================================== */}

              <Route
                path="/"
                element={
                  <App />
                }
              >

                <Route
                  index
                  element={
                    <ChatPage />
                  }
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


              <Route
                path="*"
                element={
                  <Navigate
                    to="/"
                    replace
                  />
                }
              />

            </Routes>

          </BrowserRouter>

        </ChatProvider>

      </DatabaseProvider>

    </AuthProvider>

  </React.StrictMode>

);