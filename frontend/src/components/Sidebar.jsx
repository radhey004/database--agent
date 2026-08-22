import {
  MessageSquare,
  Database,
  ShieldCheck,
} from "lucide-react";

import {
  NavLink,
} from "react-router-dom";

function Sidebar() {
  const items = [
    {
      name: "Database Chat",
      path: "/",
      icon: MessageSquare,
    },
    {
      name: "Connect Database",
      path: "/connect",
      icon: Database,
    },
    {
      name: "Security & Privacy",
      path: "/security",
      icon: ShieldCheck,
    },
  ];

  return (
    <aside className="sidebar">
      <nav>
        {items.map((item) => {
          const Icon = item.icon;

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `nav-item ${
                  isActive
                    ? "active"
                    : ""
                }`
              }
            >
              <Icon size={19} />

              <span>
                {item.name}
              </span>
            </NavLink>
          );
        })}
      </nav>

      <div className="sidebar-footer">
        <p>
          Database AI Agent V2
        </p>

        <span>
          LangGraph • PostgreSQL
        </span>
      </div>
    </aside>
  );
}

export default Sidebar;