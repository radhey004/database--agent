const API_URL = "http://localhost:8001";


export async function askAgent(question) {

  const response = await fetch(
    `${API_URL}/ask`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify({
        question,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail || "Request failed"
    );
  }

  return data;
}


export async function approveRequest(
  requestId
) {

  const response = await fetch(
    `${API_URL}/approve/${requestId}`,
    {
      method: "POST",
    }
  );

  const data = await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail || "Approval failed"
    );
  }

  return data;
}


export async function rejectRequest(
  requestId
) {

  const response = await fetch(
    `${API_URL}/reject/${requestId}`,
    {
      method: "POST",
    }
  );

  const data = await response.json();

  if (!response.ok) {

    throw new Error(
      data.detail || "Rejection failed"
    );
  }

  return data;
}