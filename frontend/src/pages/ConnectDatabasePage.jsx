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
  Plug,
} from "lucide-react";

import {
  connectDatabase as connectDatabaseApi,
  testDatabaseConnection,
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
    testing,
    setTesting,
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
    database,
    connectDatabase,
  } = useDatabase();


  // ==========================================================
  // TEST
  // ==========================================================

  const handleTest =
    async () => {

      if (!databaseUrl.trim()) {

        setResult({
          success: false,
          message:
            "Enter a PostgreSQL connection URL.",
        });

        return;
      }


      try {

        setTesting(true);

        setResult(null);


        const response =
          await testDatabaseConnection(
            databaseUrl.trim()
          );


        setResult({

          success: true,

          message:
            response.message,

          databaseName:
            response.database_name,

          host:
            response.host,

          version:
            response.version,

        });

      } catch (error) {

        setResult({

          success: false,

          message:
            error.message,

        });

      } finally {

        setTesting(false);

      }

    };


  // ==========================================================
  // CONNECT
  // ==========================================================

  const handleSubmit =
    async (event) => {

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
          await connectDatabaseApi(
            databaseUrl.trim()
          );


        connectDatabase({

          connectionId:
            response.connection_id,

          databaseName:
            response.database_name,

          host:
            response.host,

          version:
            response.version,

        });


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
            Connect your PostgreSQL database
            securely.
          </p>

        </div>

      </div>


      {/* =====================================================
          CURRENT CONNECTION
      ====================================================== */}

      {database.connected && (

        <div className="connection-card">

          <div className="connection-result success">

            <CheckCircle2 size={21} />

            <div>

              <strong>
                Database Connected
              </strong>

              <p>
                PostgreSQL
              </p>

              <small>

                Database:
                {" "}
                {database.databaseName}

                <br />

                Host:
                {" "}
                {database.host}

              </small>

            </div>

          </div>

        </div>

      )}


      {/* =====================================================
          CONNECT
      ====================================================== */}

      <div className="connection-card">

        <div className="section-heading">

          <div>

            <h3>
              Connect Database
            </h3>

            <p>
              Enter your PostgreSQL connection
              URL to establish a runtime connection.
            </p>

          </div>

        </div>


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

              required
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

            Your database credentials are used
            only to establish the runtime connection.
            They are not stored by this application.

          </p>


          <div className="connection-form-actions">

            <button
              type="button"
              className="secondary-button"
              disabled={
                testing ||
                loading
              }
              onClick={handleTest}
            >

              <Plug size={16} />

              {testing
                ? "Testing..."
                : "Test Connection"}

            </button>


            <button
              type="submit"
              className="connect-button"
              disabled={
                loading ||
                testing
              }
            >

              {loading
                ? "Connecting..."
                : "Connect"}

            </button>

          </div>

        </form>


        {/* =================================================
            SECURITY
        ================================================== */}

        <div className="security-notice">

          <ShieldCheck size={20} />

          <div>

            <strong>
              Credential Security
            </strong>

            <ul>

              <li>
                Database credentials are not
                stored in browser localStorage.
              </li>

              <li>
                Database credentials are not
                stored in the application database.
              </li>

              <li>
                The AI agent never receives
                the database password.
              </li>

              <li>
                Connections are user-scoped
                runtime sessions.
              </li>

            </ul>

          </div>

        </div>


        {/* =================================================
            RESULT
        ================================================== */}

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
                  ? "Success"
                  : "Operation Failed"}

              </strong>


              <p>
                {result.message}
              </p>


              {result.databaseName && (

                <small>

                  Database:
                  {" "}
                  {result.databaseName}

                  <br />

                  Host:
                  {" "}
                  {result.host}

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