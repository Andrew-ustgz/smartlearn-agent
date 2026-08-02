const API = (
  import.meta.env.VITE_API_URL || "http://localhost:8000"
).replace(/\/$/, "");

const CHAT_ID = "day2-demo";

async function readJSON(response) {
  let data;

  try {
    data = await response.json();
  } catch {
    throw new Error(
      `The server returned an unreadable response (${response.status}).`,
    );
  }

  if (!response.ok) {
    let detail = data?.detail;

    if (Array.isArray(detail)) {
      detail = detail
        .map((item) => item?.msg)
        .filter(Boolean)
        .join("; ");
    }

    throw new Error(
      detail ||
        `The request failed with status ${response.status}.`,
    );
  }

  return data;
}

export async function uploadPDF(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(
    `${API}/upload?chat_id=${encodeURIComponent(CHAT_ID)}`,
    {
      method: "POST",
      body: formData,
    },
  );

  return readJSON(response);
}

export async function askQuestion(message) {
  const response = await fetch(`${API}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      chat_id: CHAT_ID,
      message,
    }),
  });

  return readJSON(response);
}