import {
  createContext,
  useContext,
  useState,
} from "react";


const DatabaseContext =
  createContext(null);


export function DatabaseProvider({
  children,
}) {
  const [database, setDatabase] =
    useState({
      connected: false,

      connectionId: null,

      databaseName: null,

      host: null,

      version: null,
    });


  const connectDatabase = ({
    connectionId,
    databaseName,
    host,
    version,
  }) => {
    setDatabase({
      connected: true,

      connectionId,

      databaseName,

      host,

      version,
    });
  };


  const disconnectDatabase = () => {
    setDatabase({
      connected: false,

      connectionId: null,

      databaseName: null,

      host: null,

      version: null,
    });
  };


  return (
    <DatabaseContext.Provider
      value={{
        database,
        connectDatabase,
        disconnectDatabase,
      }}
    >
      {children}
    </DatabaseContext.Provider>
  );
}


export function useDatabase() {
  const context = useContext(
    DatabaseContext
  );

  if (!context) {
    throw new Error(
      "useDatabase must be used inside DatabaseProvider."
    );
  }

  return context;
}