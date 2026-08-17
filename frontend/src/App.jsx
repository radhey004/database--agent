import { useState } from "react";
import { askAgent } from "./api";

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  async function handleAsk() {
    if (!question.trim()) return;

    setLoading(true);
    setAnswer(null);

    try {
      const data = await askAgent(question);
      setAnswer(data);
    } catch (error) {
      setAnswer({ error: error.message });
    } finally {
      setLoading(false);
    }
  }

  return (
    <main style={styles.page}>
      <div style={styles.container}>

        {/* Header */}
        <div style={styles.header}>
          <div style={styles.logo}>DB</div>

          <div>
            <h1 style={styles.title}>Database AI Agent</h1>
            <p style={styles.subtitle}>
              Ask questions about your PostgreSQL database in plain English.
            </p>
          </div>
        </div>

        {/* Input Card */}
        <div style={styles.card}>
          <label style={styles.label}>Ask your database</label>

          <div style={styles.inputRow}>
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleAsk()}
              placeholder="e.g. How many users are there?"
              style={styles.input}
            />

            <button
              onClick={handleAsk}
              disabled={loading}
              style={{
                ...styles.button,
                opacity: loading ? 0.7 : 1,
              }}
            >
              {loading ? "Thinking..." : "Ask"}
            </button>
          </div>

          <div style={styles.examples}>
            <span>Try:</span>

            <button
              style={styles.example}
              onClick={() => setQuestion("How many users are there?")}
            >
              User count
            </button>

            <button
              style={styles.example}
              onClick={() =>
                setQuestion("Which products have less than 10 items in stock?")
              }
            >
              Low stock
            </button>

            <button
              style={styles.example}
              onClick={() =>
                setQuestion("Which product has been ordered the most?")
              }
            >
              Best-selling product
            </button>
          </div>
        </div>

        {/* Error */}
        {answer?.error && (
          <div style={styles.error}>
            <strong>Error</strong>
            <p>{answer.error}</p>
          </div>
        )}

        {/* Result */}
        {answer?.sql && (
          <div style={styles.results}>

            {/* SQL */}
            <section style={styles.resultCard}>
              <div style={styles.resultHeader}>
                <h2 style={styles.resultTitle}>Generated SQL</h2>
                <span style={styles.badge}>READ ONLY</span>
              </div>

              <pre style={styles.code}>
                {answer.sql}
              </pre>
            </section>

            {/* Database Result */}
            <section style={styles.resultCard}>
              <div style={styles.resultHeader}>
                <h2 style={styles.resultTitle}>Database Result</h2>
                <span style={styles.successBadge}>SUCCESS</span>
              </div>

              <pre style={styles.code}>
                {JSON.stringify(answer.result, null, 2)}
              </pre>
            </section>

          </div>
        )}

        {/* Footer */}
        <footer style={styles.footer}>
          LangGraph · MCP · Neon PostgreSQL · Groq / Ollama
        </footer>

      </div>
    </main>
  );
}


const styles = {
  page: {
    minHeight: "100vh",
    background: "#f6f7fb",
    padding: "60px 20px",
    fontFamily:
      "-apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif",
    color: "#1f2937",
  },

  container: {
    maxWidth: "900px",
    margin: "0 auto",
  },

  header: {
    display: "flex",
    alignItems: "center",
    gap: "16px",
    marginBottom: "30px",
  },

  logo: {
    width: "52px",
    height: "52px",
    borderRadius: "14px",
    background: "#111827",
    color: "white",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    fontWeight: "700",
    fontSize: "18px",
  },

  title: {
    margin: 0,
    fontSize: "30px",
    fontWeight: "700",
    color: "#111827",
  },

  subtitle: {
    margin: "6px 0 0",
    color: "#6b7280",
    fontSize: "15px",
  },

  card: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: "16px",
    padding: "24px",
    boxShadow: "0 4px 20px rgba(0,0,0,0.04)",
  },

  label: {
    display: "block",
    fontSize: "14px",
    fontWeight: "600",
    marginBottom: "10px",
    color: "#374151",
  },

  inputRow: {
    display: "flex",
    gap: "10px",
  },

  input: {
    flex: 1,
    padding: "13px 15px",
    border: "1px solid #d1d5db",
    borderRadius: "10px",
    fontSize: "15px",
    outline: "none",
    background: "#fafafa",
  },

  button: {
    padding: "13px 22px",
    border: "none",
    borderRadius: "10px",
    background: "#111827",
    color: "white",
    fontSize: "14px",
    fontWeight: "600",
    cursor: "pointer",
  },

  examples: {
    display: "flex",
    alignItems: "center",
    flexWrap: "wrap",
    gap: "8px",
    marginTop: "16px",
    fontSize: "13px",
    color: "#6b7280",
  },

  example: {
    border: "1px solid #e5e7eb",
    background: "#f9fafb",
    borderRadius: "20px",
    padding: "6px 11px",
    color: "#4b5563",
    cursor: "pointer",
    fontSize: "12px",
  },

  results: {
    marginTop: "24px",
    display: "grid",
    gap: "18px",
  },

  resultCard: {
    background: "white",
    border: "1px solid #e5e7eb",
    borderRadius: "16px",
    overflow: "hidden",
    boxShadow: "0 4px 20px rgba(0,0,0,0.03)",
  },

  resultHeader: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "16px 20px",
    borderBottom: "1px solid #e5e7eb",
  },

  resultTitle: {
    margin: 0,
    fontSize: "15px",
    fontWeight: "600",
    color: "#111827",
  },

  badge: {
    fontSize: "10px",
    fontWeight: "700",
    padding: "5px 8px",
    borderRadius: "6px",
    background: "#fef3c7",
    color: "#92400e",
  },

  successBadge: {
    fontSize: "10px",
    fontWeight: "700",
    padding: "5px 8px",
    borderRadius: "6px",
    background: "#dcfce7",
    color: "#166534",
  },

  code: {
    margin: 0,
    padding: "20px",
    background: "#111827",
    color: "#e5e7eb",
    fontSize: "14px",
    lineHeight: "1.6",
    overflowX: "auto",
    minHeight: "40px",
  },

  error: {
    marginTop: "20px",
    padding: "16px",
    borderRadius: "12px",
    background: "#fef2f2",
    border: "1px solid #fecaca",
    color: "#991b1b",
  },

  footer: {
    textAlign: "center",
    marginTop: "35px",
    fontSize: "12px",
    color: "#9ca3af",
  },
};