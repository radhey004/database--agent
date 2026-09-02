import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  disconnectDatabase as disconnectDatabaseApi,
  getCurrentDatabaseConnection,
} from "../api/client";

const DatabaseContext = createContext(null);

const EMPTY_DATABASE = {
  connected: false,
  connectionId: null,
  databaseName: null,
  host: null,
  version: null,
};

const CONNECTION_ID_KEY = "dbagent_connection_id";

function readStoredConnectionId() {
  try {
    return localStorage.getItem(CONNECTION_ID_KEY);
  } catch {
    return null;
  }
}

function saveConnectionId(connectionId) {
  if (!connectionId) return;

  try {
    localStorage.setItem(
      CONNECTION_ID_KEY,
      connectionId
    );
  } catch (error) {
    console.error(
      "Unable to persist database connection ID:",
      error
    );
  }
}

function removeConnectionId() {
  try {
    localStorage.removeItem(
      CONNECTION_ID_KEY
    );
  } catch (error) {
    console.error(
      "Unable to remove database connection ID:",
      error
    );
  }
}

export function DatabaseProvider({ children }) {

  /*
   * Restore the connection ID immediately.
   *
   * IMPORTANT:
   * Only the opaque connection ID is stored.
   *
   * Never store:
   * - database URL
   * - username
   * - password
   * - SSL credentials
   */

  const [database, setDatabase] = useState(() => {

    const connectionId =
      readStoredConnectionId();

    if (!connectionId) {
      return EMPTY_DATABASE;
    }

    return {
      connected: true,
      connectionId,
      databaseName: null,
      host: null,
      version: null,
    };
  });

  const [loading, setLoading] = useState(false);


  // ============================================================
  // RESTORE CONNECTION AFTER PAGE LOAD
  // ============================================================

  useEffect(() => {

    let cancelled = false;

    const restoreConnection = async () => {

      const connectionId =
        readStoredConnectionId();

      /*
       * Nothing was previously connected.
       */

      if (!connectionId) {

        if (!cancelled) {
          setDatabase(
            EMPTY_DATABASE
          );

          setLoading(false);
        }

        return;
      }

      /*
       * IMPORTANT:
       *
       * Do NOT set loading=true here.
       *
       * The UI already knows the connection ID,
       * so it can immediately show the connected state.
       */

      try {

        const response =
          await getCurrentDatabaseConnection(
            connectionId
          );

        if (cancelled) {
          return;
        }

        if (
          !response ||
          response.success === false
        ) {
          /*
           * Do NOT remove the connection ID
           * because of a temporary backend/MCP error.
           */

          return;
        }

        setDatabase({
          connected: true,

          connectionId:
            response.connection_id ||
            connectionId,

          databaseName:
            response.database_name ||
            null,

          host:
            response.host ||
            null,

          version:
            response.version ||
            null,
        });

      } catch (error) {

        /*
         * IMPORTANT:
         *
         * DO NOT remove localStorage here.
         *
         * A temporary network/MCP failure must
         * not destroy the user's connection state.
         *
         * The connection ID remains available for
         * the next request / refresh.
         */

        console.warn(
          "Database connection verification failed:",
          error
        );

      } finally {

        if (!cancelled) {
          setLoading(false);
        }

      }
    };

    restoreConnection();

    return () => {
      cancelled = true;
    };

  }, []);


  // ============================================================
  // CONNECT DATABASE
  // ============================================================

  const connectDatabase = ({
    connectionId,
    databaseName,
    host,
    version,
  }) => {

    if (!connectionId) {
      throw new Error(
        "Database connection ID is required."
      );
    }

    /*
     * Persist ONLY the opaque ID.
     *
     * The actual database credentials remain
     * inside the backend/MCP process.
     */

    saveConnectionId(
      connectionId
    );

    setDatabase({
      connected: true,

      connectionId,

      databaseName:
        databaseName || null,

      host:
        host || null,

      version:
        version || null,
    });
  };


  // ============================================================
  // DISCONNECT DATABASE
  // ============================================================

  const disconnectDatabase = async () => {

    const connectionId =
      database.connectionId;

    /*
     * Remove from UI only after explicitly
     * requesting disconnect.
     */

    try {

      if (connectionId) {

        await disconnectDatabaseApi(
          connectionId
        );
      }

    } catch (error) {

      console.error(
        "Failed to disconnect database:",
        error
      );

    } finally {

      /*
       * Explicit disconnect means the user
       * really wants the connection removed.
       */

      removeConnectionId();

      setDatabase(
        EMPTY_DATABASE
      );
    }
  };


  return (
    <DatabaseContext.Provider
      value={{
        database,

        loading,

        connectDatabase,

        disconnectDatabase,
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
}


// ============================================================
// HOOK
// ============================================================

export function useDatabase() {

  const context =
    useContext(DatabaseContext);

  if (!context) {

    throw new Error(
      "useDatabase must be used inside DatabaseProvider."
    );
  }

  return context;
}