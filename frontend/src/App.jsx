import { useState } from "react";

import {
  askAgent,
  approveRequest,
  rejectRequest,
} from "./api";

import "./App.css";


export default function App() {

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [approvalLoading, setApprovalLoading] =
    useState(false);


  async function handleAsk() {

    if (!question.trim()) return;

    setLoading(true);
    setAnswer(null);

    try {

      const data = await askAgent(
        question
      );

      setAnswer(data);

    } catch (error) {

      setAnswer({
        status: "error",
        error: error.message,
      });

    } finally {

      setLoading(false);
    }
  }


  async function handleApprove() {

    if (!answer?.request_id) return;

    setApprovalLoading(true);

    try {

      const data = await approveRequest(
        answer.request_id
      );

      setAnswer(data);

    } catch (error) {

      setAnswer({
        status: "error",
        error: error.message,
      });

    } finally {

      setApprovalLoading(false);
    }
  }


  async function handleReject() {

    if (!answer?.request_id) return;

    setApprovalLoading(true);

    try {

      const data = await rejectRequest(
        answer.request_id
      );

      setAnswer(data);

    } catch (error) {

      setAnswer({
        status: "error",
        error: error.message,
      });

    } finally {

      setApprovalLoading(false);
    }
  }


  return (
    <main className="page">

      <div className="container">

        {/* HEADER */}

        <div className="header">

          <div className="logo">
            DB
          </div>

          <div>

            <h1 className="title">
              Database AI Agent
            </h1>

            <p className="subtitle">
              Query and safely modify your PostgreSQL
              database using natural language.
            </p>

          </div>

        </div>


        {/* ASK CARD */}

        <div className="card">

          <label className="label">
            Ask your database
          </label>

          <div className="inputRow">

            <input
              value={question}
              onChange={(e) =>
                setQuestion(e.target.value)
              }
              onKeyDown={(e) =>
                e.key === "Enter" &&
                handleAsk()
              }
              placeholder="e.g. How many users are there?"
              className="input"
            />

            <button
              onClick={handleAsk}
              disabled={loading}
              className="button"
              style={{
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading
                ? "Thinking..."
                : "Ask"}
            </button>

          </div>


          {/* EXAMPLES */}

          <div className="examples">

            <span>Try:</span>

            <button
              className="example"
              onClick={() =>
                setQuestion(
                  "How many users are there?"
                )
              }
            >
              User count
            </button>


            <button
              className="example"
              onClick={() =>
                setQuestion(
                  "Which products have less than 10 items in stock?"
                )
              }
            >
              Low stock
            </button>


            <button
              className="example"
              onClick={() =>
                setQuestion(
                  "Update the city of user 1 to Pune"
                )
              }
            >
              Update user
            </button>


            <button
              className="example"
              onClick={() =>
                setQuestion(
                  "Create a table called employees with id, name and email"
                )
              }
            >
              Create table
            </button>

          </div>

        </div>


        {/* ERROR */}

        {answer?.error && (

          <div className="error">

            <strong>Error</strong>

            <p>
              {answer.error}
            </p>

          </div>

        )}


        {/* ================================================= */}
        {/* HUMAN APPROVAL PREVIEW */}
        {/* ================================================= */}

        {answer?.status === "pending_approval" && (

          <div className="approvalCard">

            {/* HEADER */}

            <div className="approvalHeader">

              <div>

                <h2 className="resultTitle">
                  Human Approval Required
                </h2>

                <p className="approvalText">
                  Review what this operation will
                  affect before executing it.
                </p>

              </div>

              <span className="warningBadge">
                PENDING
              </span>

            </div>


            {/* OPERATION INFORMATION */}

            <div className="previewGrid">

              <div className="previewItem">

                <span className="previewLabel">
                  Operation
                </span>

                <strong>
                  {answer.preview?.operation}
                </strong>

              </div>


              <div className="previewItem">

                <span className="previewLabel">
                  Target
                </span>

                <strong>
                  {answer.preview?.target}
                </strong>

              </div>


              {answer.preview?.affected_rows !== null &&
                answer.preview?.affected_rows !== undefined && (

                <div className="previewItem">

                  <span className="previewLabel">
                    Affected Rows
                  </span>

                  <strong>
                    {answer.preview.affected_rows}
                  </strong>

                </div>

              )}

            </div>


            {/* AFFECTED ROWS */}

            {answer.preview?.rows?.length > 0 && (

              <div>

                <div className="sectionLabel">
                  Rows That Will Be Affected
                </div>

                <pre className="code">
                  {JSON.stringify(
                    answer.preview.rows,
                    null,
                    2
                  )}
                </pre>

              </div>

            )}


            {/* DDL MESSAGE */}

            {answer.preview?.message && (

              <div className="previewMessage">
                {answer.preview.message}
              </div>

            )}


            {/* SQL */}

            <div className="sectionLabel">
              Generated SQL
            </div>

            <pre className="code">
              {answer.sql}
            </pre>


            {/* ACTIONS */}

            <div className="approvalActions">

              <button
                onClick={handleReject}
                disabled={approvalLoading}
                className="rejectButton"
              >
                Reject
              </button>


              <button
                onClick={handleApprove}
                disabled={approvalLoading}
                className="approveButton"
              >
                {approvalLoading
                  ? "Executing..."
                  : "Approve & Execute"}
              </button>

            </div>

          </div>

        )}


        {/* ================================================= */}
        {/* READ RESULT */}
        {/* ================================================= */}

        {answer?.status === "completed" && (

          <div className="results">

            <section className="resultCard">

              <div className="resultHeader">

                <h2 className="resultTitle">
                  Generated SQL
                </h2>

                <span className="badge">
                  READ
                </span>

              </div>

              <pre className="code">
                {answer.sql}
              </pre>

            </section>


            <section className="resultCard">

              <div className="resultHeader">

                <h2 className="resultTitle">
                  Database Result
                </h2>

                <span className="successBadge">
                  SUCCESS
                </span>

              </div>

              <pre className="code">
                {JSON.stringify(
                  answer.result,
                  null,
                  2
                )}
              </pre>

            </section>

          </div>

        )}


        {/* ================================================= */}
        {/* APPROVED RESULT */}
        {/* ================================================= */}

        {answer?.status ===
          "approved_and_executed" && (

          <div className="results">

            <section className="approvalSuccessCard">

              <div className="approvalHeader successHeader">

                <div>

                  <h2 className="resultTitle">
                    Modification Executed
                  </h2>

                  <p className="successText">
                    The approved operation was
                    successfully applied to the database.
                  </p>

                </div>

                <span className="successBadge">
                  SUCCESS
                </span>

              </div>


              {/* WHAT WAS AFFECTED */}

              <div className="previewGrid">

                <div className="previewItem">

                  <span className="previewLabel">
                    Operation
                  </span>

                  <strong>
                    {answer.preview?.operation}
                  </strong>

                </div>


                <div className="previewItem">

                  <span className="previewLabel">
                    Target
                  </span>

                  <strong>
                    {answer.preview?.target}
                  </strong>

                </div>


                <div className="previewItem">

                  <span className="previewLabel">
                    Rows Affected
                  </span>

                  <strong>
                    {answer.result?.row_count ?? "-"}
                  </strong>

                </div>

              </div>


              {/* EXECUTED SQL */}

              <div className="sectionLabel">
                Executed SQL
              </div>

              <pre className="code">
                {answer.sql}
              </pre>


              {/* RESULT */}

              <div className="sectionLabel">
                Database Result
              </div>

              <pre className="code">
                {JSON.stringify(
                  answer.result,
                  null,
                  2
                )}
              </pre>

            </section>

          </div>

        )}


        {/* ================================================= */}
        {/* REJECTED */}
        {/* ================================================= */}

        {answer?.status === "rejected" && (

          <div className="rejected">

            <strong>
              Modification rejected
            </strong>

            <p>
              No database changes were made.
            </p>

          </div>

        )}


        {/* FOOTER */}

        <footer className="footer">
          LangGraph · MCP · PostgreSQL ·
          Groq / Ollama · Human-in-the-Loop
        </footer>

      </div>

    </main>
  );
}