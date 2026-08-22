const API_URL = "http://localhost:8001";

async function request(endpoint, options = {}) {
  const response = await fetch(
    `${API_URL}${endpoint}`,
    options
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(
      data.detail ||
      "Something went wrong."
    );
  }

  return data;
}


export async function askAgent(
  question,
  connectionId
) {
  return request("/ask", {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify({
      question,
      connection_id: connectionId,
    }),
  });
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


export async function connectDatabase(
  databaseUrl
) {
  return request(
    "/database/connect",
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        database_url: databaseUrl,
      }),
    }
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