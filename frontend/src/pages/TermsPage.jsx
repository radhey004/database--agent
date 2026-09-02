import {
  ShieldCheck,
} from "lucide-react";

import {
  Link,
} from "react-router-dom";


function TermsPage() {

  return (

    <div className="page-container">

      <div className="page-heading">

        <div className="page-icon">

          <ShieldCheck
            size={26}
          />

        </div>

        <div>

          <h2>
            Terms & Conditions
          </h2>

          <p>
            Version 1.0
          </p>

        </div>

      </div>


      <div className="terms-card">

        <section>

          <h3>
            1. Database Operations
          </h3>

          <p>
            The Database AI Agent generates and
            executes database queries based on
            user requests. Database modifications
            are executed only after the required
            user approval.
          </p>

        </section>


        <section>

          <h3>
            2. User Responsibility
          </h3>

          <p>
            Users are responsible for reviewing
            generated SQL and the associated
            preview before approving a database
            modification.
          </p>

        </section>


        <section>

          <h3>
            3. Data Modification
          </h3>

          <p>
            Approved operations may modify,
            create, alter, or delete data and
            database objects. Users should maintain
            appropriate backups of important data.
          </p>

        </section>


        <section>

          <h3>
            4. Credentials
          </h3>

          <p>
            Database credentials should be treated
            as confidential. The application should
            never receive credentials through chat
            messages.
          </p>

        </section>


        <section>

          <h3>
            5. Approval Records
          </h3>

          <p>
            The application may maintain security
            and audit information necessary to
            demonstrate that an operation required
            and received user approval.
          </p>

        </section>


        <section>

          <h3>
            6. Service Limitations
          </h3>

          <p>
            Users should not rely on the agent as
            a replacement for database backups,
            administrative controls, or professional
            database administration.
          </p>

        </section>


        <div className="terms-footer">

          <Link
            to="/register"
          >
            Back to registration
          </Link>

        </div>

      </div>

    </div>

  );

}


export default TermsPage;