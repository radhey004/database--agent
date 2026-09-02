import {
  useState,
} from "react";

import {
  Database,
  LogIn,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  loginUser,
} from "../api/client";

import {
  useAuth,
} from "../context/AuthContext";


function LoginPage() {

  const navigate =
    useNavigate();


  const {
    login,
  } = useAuth();


  const [
    email,
    setEmail,
  ] = useState("");


  const [
    password,
    setPassword,
  ] = useState("");


  const [
    error,
    setError,
  ] = useState("");


  const [
    loading,
    setLoading,
  ] = useState(false);


  const handleSubmit =
    async (event) => {

      event.preventDefault();

      setError("");

      setLoading(true);


      try {

        const response =
          await loginUser(
            email.trim(),
            password
          );


        login(
          response.user
        );


        navigate("/");

      } catch (error) {

        setError(
          error.message
        );

      } finally {

        setLoading(false);

      }

    };


  return (

    <div className="auth-page">

      <div className="auth-card">

        <div className="auth-brand">

          <div className="brand-icon">

            <Database
              size={22}
            />

          </div>

          <h1>
            Database AI Agent
          </h1>

        </div>


        <div className="auth-heading">

          <h2>
            Welcome back
          </h2>

          <p>
            Sign in to continue to your database agent.
          </p>

        </div>


        {error && (

          <div className="auth-error">
            {error}
          </div>

        )}


        <form
          onSubmit={
            handleSubmit
          }
          className="auth-form"
        >

          <label>
            Email
          </label>

          <input
            type="email"
            value={email}
            onChange={(event) =>
              setEmail(
                event.target.value
              )
            }
            placeholder="you@example.com"
            autoComplete="email"
            required
          />


          <label>
            Password
          </label>

          <input
            type="password"
            value={password}
            onChange={(event) =>
              setPassword(
                event.target.value
              )
            }
            placeholder="Your password"
            autoComplete="current-password"
            required
          />


          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >

            <LogIn size={18} />

            {loading
              ? "Signing in..."
              : "Sign In"}

          </button>

        </form>


        <p className="auth-switch">

          Don't have an account?

          {" "}

          <Link
            to="/register"
          >
            Create one
          </Link>

        </p>

      </div>

    </div>

  );

}


export default LoginPage;