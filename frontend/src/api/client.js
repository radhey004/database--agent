const API_BASE_URL = import.meta.env.VITE_API_URL;

async function request(endpoint, options = {}) {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      credentials: "include",
    }
  );

  let data = null;

  try {
    data = await response.json();
  } catch {
    data = {};
  }

  if (!response.ok) {
    throw new Error(
      data.detail || "Something went wrong."
    );
  }

  return data;
}


// ============================================================
// AUTH
// ============================================================

export async function registerUser(
  email,
  password,
  acceptTerms
) {

  return request(
    "/auth/register",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({

        email,

        password,

        accept_terms:
          acceptTerms,

      }),

    }
  );

}


export async function loginUser(
  email,
  password
) {

  return request(
    "/auth/login",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({

        email,

        password,

      }),

    }
  );

}


export async function getCurrentUser() {

  return request(
    "/auth/me"
  );

}


export async function logoutUser() {

  return request(
    "/auth/logout",
    {
      method: "POST",
    }
  );

}


// ============================================================
// AGENT
// ============================================================

export async function askAgent(
  question,
  connectionId
) {

  return request(
    "/ask",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({

        question,

        connection_id:
          connectionId,

      }),

    }
  );

}


export async function approveRequest(
  requestId
) {

  return request(
    `/approve/${requestId}`,
    {
      method: "POST",
    }
  );

}


export async function rejectRequest(
  requestId
) {

  return request(
    `/reject/${requestId}`,
    {
      method: "POST",
    }
  );

}


// ============================================================
// DATABASE
// ============================================================

export async function testDatabaseConnection(
  databaseUrl
) {

  return request(
    "/database/test-connection",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({

        database_url:
          databaseUrl,

      }),

    }
  );

}


export async function connectDatabase(
  databaseUrl
) {

  return request(
    "/database/connect",
    {

      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body: JSON.stringify({

        database_url:
          databaseUrl,

      }),

    }
  );

}


export async function getCurrentDatabaseConnection(
  connectionId
) {

  return request(
    `/database/current/${encodeURIComponent(connectionId)}`
  );

}


export async function disconnectDatabase(
  connectionId
) {

  return request(
    `/database/disconnect/${connectionId}`,
    {
      method: "POST",
    }
  );

}