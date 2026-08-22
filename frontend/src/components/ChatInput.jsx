import {
  Send,
} from "lucide-react";

import {
  useState,
} from "react";

function ChatInput({
  onSubmit,
  loading,
}) {
  const [question, setQuestion] =
    useState("");

  const handleSubmit = (event) => {
    event.preventDefault();

    const value = question.trim();

    if (!value || loading) {
      return;
    }

    onSubmit(value);

    setQuestion("");
  };

  return (
    <form
      className="chat-input-container"
      onSubmit={handleSubmit}
    >
      <textarea
        value={question}
        onChange={(event) =>
          setQuestion(
            event.target.value
          )
        }
        placeholder="Ask anything about your database..."
        rows="1"
        disabled={loading}
      />

      <button
        type="submit"
        disabled={
          loading ||
          !question.trim()
        }
      >
        <Send size={19} />
      </button>
    </form>
  );
}

export default ChatInput;