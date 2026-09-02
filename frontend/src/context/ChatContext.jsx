import {
  createContext,
  useContext,
  useEffect,
  useState,
} from "react";

import { useAuth } from "./AuthContext";

const ChatContext = createContext(null);

const STORAGE_PREFIX = "database_agent_chat_";

function getStorageKey(userId) {
  if (!userId) {
    return null;
  }

  return `${STORAGE_PREFIX}${userId}`;
}

function loadMessages(userId) {
  const storageKey = getStorageKey(userId);

  if (!storageKey) {
    return [];
  }

  try {
    const saved = localStorage.getItem(storageKey);

    if (!saved) {
      return [];
    }

    const parsed = JSON.parse(saved);

    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.error(
      "Failed to load chat history:",
      error
    );

    return [];
  }
}

export function ChatProvider({ children }) {
  const { user, loading: authLoading } = useAuth();

  const userId =
    user?.id ||
    user?.user_id ||
    user?._id ||
    null;

  const [messages, setMessages] = useState([]);

  const [loadedUserId, setLoadedUserId] =
    useState(null);

  // ============================================
  // LOAD CHAT FOR CURRENT USER
  // ============================================

  useEffect(() => {
    if (authLoading) {
      return;
    }

    if (!userId) {
      setMessages([]);
      setLoadedUserId(null);
      return;
    }

    const userMessages =
      loadMessages(userId);

    setMessages(userMessages);
    setLoadedUserId(userId);
  }, [userId, authLoading]);

  // ============================================
  // SAVE CHAT FOR CURRENT USER
  // ============================================

  useEffect(() => {
    if (
      authLoading ||
      !userId ||
      loadedUserId !== userId
    ) {
      return;
    }

    const storageKey =
      getStorageKey(userId);

    try {
      localStorage.setItem(
        storageKey,
        JSON.stringify(messages)
      );
    } catch (error) {
      console.error(
        "Failed to save chat history:",
        error
      );
    }
  }, [
    messages,
    userId,
    loadedUserId,
    authLoading,
  ]);

  // ============================================
  // ADD MESSAGE
  // ============================================

  const addMessage = (message) => {
    if (!userId) {
      return;
    }

    setMessages((previous) => [
      ...previous,
      {
        ...message,
        id:
          message.id ||
          crypto.randomUUID(),
      },
    ]);
  };

  // ============================================
  // REMOVE APPROVAL REQUEST
  // ============================================

  const removeApprovalRequest = (
    requestId
  ) => {
    setMessages((previous) =>
      previous.map((message) => {
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
      })
    );
  };

  // ============================================
  // CLEAR CURRENT USER CHAT
  // ============================================

  const clearMessages = () => {
    if (!userId) {
      return;
    }

    const storageKey =
      getStorageKey(userId);

    setMessages([]);

    try {
      localStorage.removeItem(
        storageKey
      );
    } catch (error) {
      console.error(
        "Failed to clear chat history:",
        error
      );
    }
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        addMessage,
        removeApprovalRequest,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

// ============================================
// HOOK
// ============================================

export function useChat() {
  const context =
    useContext(ChatContext);

  if (!context) {
    throw new Error(
      "useChat must be used inside ChatProvider."
    );
  }

  return context;
}