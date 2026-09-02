import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import {
  getCurrentUser,
} from "../api/client";


const AuthContext =
  createContext(null);


export function AuthProvider({
  children,
}) {

  const [
    user,
    setUser,
  ] = useState(null);


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    authenticated,
    setAuthenticated,
  ] = useState(false);


  const loadUser = async () => {

    try {

      const response =
        await getCurrentUser();

      setUser(
        response.user
      );

      setAuthenticated(
        true
      );

    } catch {

      setUser(null);

      setAuthenticated(
        false
      );

    } finally {

      setLoading(false);

    }
  };


  useEffect(() => {

    loadUser();

  }, []);


  const login = (
    loggedInUser
  ) => {

    setUser(
      loggedInUser
    );

    setAuthenticated(
      true
    );

  };


  const logout = () => {

    setUser(null);

    setAuthenticated(
      false
    );

  };


  return (
    <AuthContext.Provider
      value={{
        user,
        authenticated,
        loading,
        login,
        logout,
        refreshUser:
          loadUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}


export function useAuth() {

  const context =
    useContext(
      AuthContext
    );


  if (!context) {

    throw new Error(
      "useAuth must be used inside AuthProvider."
    );

  }


  return context;
}