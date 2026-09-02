import {
  useState,
} from "react";

import {
  Database,
  UserPlus,
} from "lucide-react";

import {
  Link,
  useNavigate,
} from "react-router-dom";

import {
  registerUser,
} from "../api/client";

import {
  useAuth,
} from "../context/AuthContext";


function RegisterPage() {

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
    confirmPassword,
    setConfirmPassword,
  ] = useState("");


  const [
    acceptTerms,
    setAcceptTerms,
  ] = useState(false);


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


      if (
        password !==
        confirmPassword
      ) {

        setError(
          "Passwords do not match."
        );

        return;

      }


      if (!acceptTerms) {

        setError(
          "You must accept the Terms & Conditions."
        );

        return;

      }


      setLoading(true);


      try {

        const response =
          await registerUser(

            email.trim(),

            password,

            acceptTerms

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

      <div className="auth-card register-card">

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
            Create your account
          </h2>

          <p>
            Securely access your database agent.
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
            placeholder="At least 8 characters"
            autoComplete="new-password"
            required
          />


          <label>
            Confirm Password
          </label>

          <input
            type="password"
            value={confirmPassword}
            onChange={(event) =>
              setConfirmPassword(
                event.target.value
              )
            }
            placeholder="Repeat your password"
            autoComplete="new-password"
            required
          />


          <label className="terms-checkbox">

            <input
              type="checkbox"
              checked={acceptTerms}
              onChange={(event) =>
                setAcceptTerms(
                  event.target.checked
                )
              }
            />

            <span>

              I agree to the{" "}

              <Link
                to="/terms"
        
              >
                Terms & Conditions
              </Link>

              {" "}and understand that
              approved database operations
              may modify or permanently
              delete data.

            </span>

          </label>


          <button
            type="submit"
            className="auth-submit"
            disabled={loading}
          >

            <UserPlus size={18} />

            {loading
              ? "Creating account..."
              : "Create Account"}

          </button>

        </form>


        <p className="auth-switch">

          Already have an account?

          {" "}

          <Link
            to="/login"
          >
            Sign in
          </Link>

        </p>

      </div>

    </div>

  );

}


export default RegisterPage;