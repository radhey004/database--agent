import {
  Navigate,
  Outlet,
  useLocation,
} from "react-router-dom";

import Header from "./components/Header";
import Sidebar from "./components/Sidebar";

import {
  useAuth,
} from "./context/AuthContext";


function ProtectedRoute() {

  const {
    authenticated,
    loading,
  } = useAuth();


  const location =
    useLocation();


  if (loading) {

    return (

      <div className="auth-loading">

        <div className="auth-loading-spinner" />

        Checking session...

      </div>

    );

  }


  if (!authenticated) {

    return (

      <Navigate
        to="/login"
        replace
        state={{
          from:
            location.pathname,
        }}
      />

    );

  }


  return (

    <div className="app-shell">

      <Header />

      <div className="app-body">

        <Sidebar />

        <main className="main-content">

          <Outlet />

        </main>

      </div>

    </div>

  );

}


function App() {

  return (
    <ProtectedRoute />
  );

}


export default App;