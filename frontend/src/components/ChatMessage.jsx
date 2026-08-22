import {
  Bot,
  User,
} from "lucide-react";

import QueryResult from "./QueryResult";
import ApprovalPanel from "./ApprovalPanel";

function ChatMessage({
  message,
  onApprove,
  onReject,
  approvalLoading,
}) {
  const isUser =
    message.role === "user";

  return (
    <div
      className={`message ${
        isUser
          ? "user-message"
          : "agent-message"
      }`}
    >
      <div className="message-avatar">
        {isUser ? (
          <User size={18} />
        ) : (
          <Bot size={18} />
        )}
      </div>

      <div className="message-content">
        {message.text && (
          <p className="message-text">
            {message.text}
          </p>
        )}

        {message.sql && (
          <div className="sql-block">
            <div className="sql-label">
              GENERATED SQL
            </div>

            <pre>
              {message.sql}
            </pre>
          </div>
        )}

        {message.result && (
          <QueryResult
            result={
              message.result
            }
          />
        )}

        {message.approvalRequired && (
          <ApprovalPanel
            requestId={
              message.requestId
            }
            sql={message.sql}
            preview={
              message.preview
            }
            onApprove={onApprove}
            onReject={onReject}
            loading={
              approvalLoading
            }
          />
        )}
      </div>
    </div>
  );
}

export default ChatMessage;