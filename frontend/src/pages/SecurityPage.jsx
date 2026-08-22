import {
  ShieldCheck,
  Lock,
  Database,
  EyeOff,
} from "lucide-react";

function SecurityPage() {
  const items = [
    {
      icon: Lock,
      title: "Connection Protection",
      text:
        "Database connections are validated before use.",
    },
    {
      icon: EyeOff,
      title: "Write Approval",
      text:
        "INSERT, UPDATE, DELETE and DDL operations require explicit approval.",
    },
    {
      icon: Database,
      title: "Schema-Aware Queries",
      text:
        "The agent validates generated SQL against the discovered database schema.",
    },
    {
      icon: ShieldCheck,
      title: "SQL Safety Validation",
      text:
        "Queries pass through validation before execution.",
    },
  ];

  return (
    <div className="page-container">
      <div className="page-heading">
        <div className="page-icon">
          <ShieldCheck size={26} />
        </div>

        <div>
          <h2>
            Security & Privacy
          </h2>

          <p>
            How the Database AI Agent
            handles your database
            operations.
          </p>
        </div>
      </div>

      <div className="security-grid">
        {items.map(
          (item) => {
            const Icon =
              item.icon;

            return (
              <div
                key={item.title}
                className="security-card"
              >
                <Icon size={22} />

                <h3>
                  {item.title}
                </h3>

                <p>
                  {item.text}
                </p>
              </div>
            );
          }
        )}
      </div>
    </div>
  );
}

export default SecurityPage;