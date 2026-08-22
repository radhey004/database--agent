import {
  useState,
} from "react";

import {
  askAgent,
  approveRequest,
  rejectRequest,
} from "../api/client";

import {
  useDatabase,
} from "../context/DatabaseContext";

import ChatInput from "../components/ChatInput";
import ChatMessage from "../components/ChatMessage";


function ChatPage() {

  const {
    database,
  } = useDatabase();


  const [
    messages,
    setMessages,
  ] = useState([]);


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    approvalLoading,
    setApprovalLoading,
  ] = useState(false);


  const addMessage = (
    message
  ) => {

    setMessages(
      (previous) => [
        ...previous,
        message,
      ]
    );

  };


  /*
    Remove the approval panel after
    Approve or Reject succeeds.
  */

  const removeApprovalRequest = (
    requestId
  ) => {

    setMessages(
      (previous) =>
        previous.map(
          (message) => {

            if (
              message.requestId ===
              requestId
            ) {

              return {
                ...message,

                approvalRequired: false,
              };

            }

            return message;

          }
        )
    );

  };


  const handleAsk = async (
    question
  ) => {

    if (
      !database.connected ||
      !database.connectionId
    ) {

      addMessage({
        role: "agent",

        text:
          "Please connect a PostgreSQL database before asking a question.",
      });

      return;

    }


    addMessage({
      role: "user",
      text: question,
    });


    setLoading(true);


    try {

      const response =
        await askAgent(
          question,
          database.connectionId
        );


      /*
        Support both backend formats:

        {
          status: "pending_approval"
        }

        OR

        {
          approval_required: true
        }
      */

      const approvalRequired =
        response.status ===
          "pending_approval" ||
        response.approval_required ===
          true;


      addMessage({

        role: "agent",

        text:
          response.answer ||
          response.message ||
          (
            approvalRequired
              ? "This operation requires your approval."
              : ""
          ),

        sql:
          response.sql ||
          response.generated_sql ||
          "",

        result:
          response.result ||
          response.rows ||
          null,

        preview:
          response.preview ||
          null,

        approvalRequired:
          approvalRequired,

        requestId:
          response.request_id ||
          response.requestId ||
          null,

      });

    } catch (error) {

      addMessage({

        role: "agent",

        text:
          `Error: ${error.message}`,

      });

    } finally {

      setLoading(false);

    }

  };


  const handleApprove = async (
    requestId
  ) => {

    try {

      setApprovalLoading(true);


      const response =
        await approveRequest(
          requestId
        );


      /*
        Remove approval panel only
        after successful execution.
      */

      removeApprovalRequest(
        requestId
      );


      addMessage({

        role: "agent",

        text:
          response.message ||
          "Modification executed successfully.",

        result:
          response.result ||
          response.rows ||
          response,

      });

    } catch (error) {

      addMessage({

        role: "agent",

        text:
          `Approval failed: ${error.message}`,

      });

    } finally {

      setApprovalLoading(false);

    }

  };


  const handleReject = async (
    requestId
  ) => {

    try {

      setApprovalLoading(true);


      const response =
        await rejectRequest(
          requestId
        );


      /*
        Remove approval panel after
        successful rejection.
      */

      removeApprovalRequest(
        requestId
      );


      addMessage({

        role: "agent",

        text:
          response.message ||
          "Operation rejected.",

      });

    } catch (error) {

      addMessage({

        role: "agent",

        text:
          `Rejection failed: ${error.message}`,

      });

    } finally {

      setApprovalLoading(false);

    }

  };


  return (

    <div className="chat-page">

      <div className="chat-page-header">

        <div>

          <h2>
            Database Chat
          </h2>


          <p>

            {database.connected
              ? `Connected to ${
                  database.databaseName ||
                  "PostgreSQL"
                }. Ask anything about your database.`
              : "Connect a database to start querying."}

          </p>

        </div>

      </div>


      <div className="chat-messages">

        {messages.length === 0 && (

          <div className="empty-chat">

            <h2>
              Ask your database anything
            </h2>


            <p>

              {database.connected
                ? "Try asking:"
                : "Connect a database first to begin."}

            </p>


            {database.connected && (

              <div className="example-questions">

                <span>
                  Show all users
                </span>

                <span>
                  How many records are there?
                </span>

                <span>
                  Show the database schema
                </span>

              </div>

            )}

          </div>

        )}


        {messages.map(
          (message, index) => (

            <ChatMessage

              key={index}

              message={message}

              onApprove={
                handleApprove
              }

              onReject={
                handleReject
              }

              approvalLoading={
                approvalLoading
              }

            />

          )
        )}


        {loading && (

          <div className="thinking">

            <span />
            <span />
            <span />

            Agent is thinking...

          </div>

        )}

      </div>


      <ChatInput

        onSubmit={
          handleAsk
        }

        loading={
          loading
        }

      />

    </div>

  );

}


export default ChatPage;