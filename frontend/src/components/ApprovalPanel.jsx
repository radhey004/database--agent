import {
  Check,
  X,
  AlertTriangle,
} from "lucide-react";

function ApprovalPanel({
  requestId,
  sql,
  preview,
  onApprove,
  onReject,
  loading,
}) {
  return (
    <div className="approval-panel">
      <div className="approval-header">
        <div className="warning-icon">
          <AlertTriangle size={20} />
        </div>

        <div>
          <h3>
            Approval Required
          </h3>

          <p>
            This operation will modify
            your database.
          </p>
        </div>
      </div>

      {sql && (
        <div className="sql-block">
          <div className="sql-label">
            GENERATED SQL
          </div>

          <pre>{sql}</pre>
        </div>
      )}

      {preview && (
        <div className="preview-box">
          <strong>
            Operation:
          </strong>{" "}
          {preview.operation}

          {preview.target && (
            <>
              <br />

              <strong>
                Target:
              </strong>{" "}
              {preview.target}
            </>
          )}

          {preview.affected_rows !==
            undefined &&
            preview.affected_rows !==
              null && (
              <>
                <br />

                <strong>
                  Affected rows:
                </strong>{" "}
                {preview.affected_rows}
              </>
            )}
        </div>
      )}

      <div className="approval-actions">
        <button
          className="approve-button"
          disabled={loading}
          onClick={() =>
            onApprove(requestId)
          }
        >
          <Check size={18} />

          Approve & Execute
        </button>

        <button
          className="reject-button"
          disabled={loading}
          onClick={() =>
            onReject(requestId)
          }
        >
          <X size={18} />

          Reject
        </button>
      </div>
    </div>
  );
}

export default ApprovalPanel;