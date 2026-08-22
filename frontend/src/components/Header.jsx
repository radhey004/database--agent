import {
  Database,
  ShieldCheck,
  LogOut,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  disconnectDatabase as disconnectDatabaseApi,
} from "../api/client";

import {
  useDatabase,
} from "../context/DatabaseContext";


function Header() {
  const navigate =
    useNavigate();

  const {
    database,
    disconnectDatabase,
  } = useDatabase();


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

        /*
          Always clear frontend session,
          even if backend session has
          already expired.
        */

        disconnectDatabase();

        navigate("/");
      }
    };


  return (
    <header className="header">

      <Link
        to="/"
        className="brand"
      >

        <div className="brand-icon">
          <Database size={20} />
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
          <ShieldCheck size={19} />
        </Link>


        <Link
          to="/connect"
          className={`connection-status ${
            database.connected
              ? "connected"
              : ""
          }`}
        >

          <span className="status-dot" />

          {database.connected
            ? database.databaseName ||
              "Database Connected"
            : "No Database"}

        </Link>


        {database.connected && (

          <button
            className="disconnect-button"
            onClick={handleDisconnect}
          >

            <LogOut size={16} />

            Disconnect

          </button>

        )}

      </div>

    </header>
  );
}


export default Header;