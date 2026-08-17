export async function askAgent(question) {
  const response = await fetch(
    "http://localhost:8001/ask",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
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