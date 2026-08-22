import {
  useState,
} from "react";

import {
  Database,
  CheckCircle2,
  AlertCircle,
  Eye,
  EyeOff,
  ShieldCheck,
} from "lucide-react";

import {
  connectDatabase,
} from "../api/client";

import {
  useDatabase,
} from "../context/DatabaseContext";


function ConnectDatabasePage() {
  const [
    databaseUrl,
    setDatabaseUrl,
  ] = useState("");

  const [
    loading,
    setLoading,
  ] = useState(false);

  const [
    result,
    setResult,
  ] = useState(null);

  const [
    showPassword,
    setShowPassword,
  ] = useState(false);


  const {
    connectDatabase: saveDatabaseConnection,
  } = useDatabase();


  const handleSubmit = async (
    event
  ) => {
    event.preventDefault();

    if (!databaseUrl.trim()) {
      setResult({
        success: false,
        message:
          "Enter a PostgreSQL connection URL.",
      });

      return;
    }

    try {
      setLoading(true);
      setResult(null);

      const response =
        await connectDatabase(
          databaseUrl.trim()
        );

      /*
        Only safe metadata is stored
        in React state.

        The database URL is NOT stored.
      */

      saveDatabaseConnection({
        connectionId:
          response.connection_id,

        databaseName:
          response.database_name,

        host:
          response.host,

        version:
          response.version,
      });


      /*
        Clear credential immediately
        from component state.
      */

      setDatabaseUrl("");


      setResult({
        success: true,

        message:
          response.message,

        databaseName:
          response.database_name,

        host:
          response.host,
      });

    } catch (error) {

      setResult({
        success: false,

        message:
          error.message,
      });

    } finally {

      setLoading(false);
    }
  };


  return (
    <div className="page-container">

      <div className="page-heading">

        <div className="page-icon">
          <Database size={26} />
        </div>

        <div>
          <h2>
            Connect Database
          </h2>

          <p>
            Connect your PostgreSQL
            database securely to the agent.
          </p>
        </div>

      </div>


      <div className="connection-card">

        <form
          onSubmit={handleSubmit}
        >

          <label>
            PostgreSQL Connection URL
          </label>


          <div className="password-input">

            <input
              type={
                showPassword
                  ? "text"
                  : "password"
              }

              value={databaseUrl}

              onChange={(event) =>
                setDatabaseUrl(
                  event.target.value
                )
              }

              placeholder="postgresql://username:password@host:5432/database"

              autoComplete="off"

              spellCheck="false"
            />


            <button
              type="button"

              onClick={() =>
                setShowPassword(
                  !showPassword
                )
              }
            >
              {showPassword ? (
                <EyeOff size={18} />
              ) : (
                <Eye size={18} />
              )}
            </button>

          </div>


          <p className="field-help">
            Your credentials are used only
            to establish the database session.
          </p>


          <button
            className="connect-button"

            disabled={loading}
          >
            {loading
              ? "Connecting..."
              : "Connect Database"}
          </button>

        </form>


        <div className="security-notice">

          <ShieldCheck size={20} />

          <div>

            <strong>
              Your credentials stay private
            </strong>

            <ul>
              <li>
                Database credentials are sent
                only when establishing the
                connection.
              </li>

              <li>
                Your browser stores only a
                temporary connection ID.
              </li>

              <li>
                Database passwords are never
                returned by the API.
              </li>

              <li>
                The AI agent does not receive
                your database password.
              </li>

              <li>
                Connections to PostgreSQL use
                the database provider's TLS/SSL
                configuration.
              </li>

              <li>
                Disconnecting destroys the
                server-side database session.
              </li>
            </ul>

          </div>

        </div>


        {result && (

          <div
            className={`connection-result ${
              result.success
                ? "success"
                : "error"
            }`}
          >

            {result.success ? (
              <CheckCircle2 size={21} />
            ) : (
              <AlertCircle size={21} />
            )}


            <div>

              <strong>
                {result.success
                  ? "Database Connected"
                  : "Connection Failed"}
              </strong>


              <p>
                {result.message}
              </p>


              {result.success && (
                <small>

                  Database: {
                    result.databaseName
                  }

                  <br />

                  Host: {
                    result.host
                  }

                </small>
              )}

            </div>

          </div>

        )}

      </div>

    </div>
  );
}


export default ConnectDatabasePage;