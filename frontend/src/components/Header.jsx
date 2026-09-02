import {
  Database,
  ShieldCheck,
  LogOut,
  User,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  disconnectDatabase as disconnectDatabaseApi,
  logoutUser,
} from "../api/client";

import {
  useDatabase,
} from "../context/DatabaseContext";

import {
  useAuth,
} from "../context/AuthContext";


function Header() {

  const navigate =
    useNavigate();


  const {
    database,
    disconnectDatabase,
  } = useDatabase();


  const {
    user,
    logout,
  } = useAuth();


  const handleDisconnect =
    async () => {

      try {

        if (
          database.connectionId
        ) {

          await disconnectDatabaseApi(
            database.connectionId
          );

        }

      } catch (error) {

        console.error(
          "Disconnect error:",
          error
        );

      } finally {

        disconnectDatabase();

        navigate("/");

      }

    };


  const handleLogout =
    async () => {

      try {

        if (
          database.connectionId
        ) {

          try {

            await disconnectDatabaseApi(
              database.connectionId
            );

          } catch (error) {

            console.error(
              "Database disconnect error:",
              error
            );

          }

        }


        await logoutUser();

      } catch (error) {

        console.error(
          "Logout error:",
          error
        );

      } finally {

        disconnectDatabase();

        logout();

        navigate(
          "/login",
          {
            replace: true,
          }
        );

      }

    };


  return (

    <header className="header">

      <Link
        to="/"
        className="brand"
      >

        <div className="brand-icon">

          <Database
            size={20}
          />

        </div>


        <div>

          <h1>
            Database AI Agent
          </h1>

          <span>
            Natural language database assistant
          </span>

        </div>

      </Link>


      <div className="header-actions">

        <Link
          to="/security"
          className="icon-button"
          title="Security & Privacy"
        >

          <ShieldCheck
            size={19}
          />

        </Link>


        <Link
          to="/connect"
          className={`connection-status ${
            database.connected
              ? "connected"
              : ""
          }`}
        >

          <span
            className="status-dot"
          />

          {database.connected
            ? database.databaseName ||
              "Database Connected"
            : "No Database"}

        </Link>


        {database.connected && (

          <button
            className="disconnect-button"
            onClick={
              handleDisconnect
            }
          >

            <LogOut
              size={16}
            />

            Disconnect

          </button>

        )}


        {user && (

          <div className="user-menu">

            <div className="user-info">

              <User
                size={16}
              />

              <span>
                {user.email}
              </span>

            </div>


            <button
              className="logout-button"
              onClick={
                handleLogout
              }
              title="Logout"
            >

              <LogOut
                size={16}
              />

            </button>

          </div>

        )}

      </div>

    </header>

  );

}


export default Header;