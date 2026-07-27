const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api";

async function request(endpoint, options = {}) {
  const config = {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  };

  if (config.body && typeof config.body !== "string") {
    config.body = JSON.stringify(config.body);
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
  const text = await response.text();
  const data = text ? tryParseJson(text) : null;

  if (!response.ok) {
    const message =
      data?.message ||
      data?.error ||
      data?.detail ||
      text ||
      `Request failed: ${response.status}`;
    throw new Error(message);
  }

  return data;
}

function tryParseJson(text) {
  try {
    return JSON.parse(text);
  } catch {
    return { message: text };
  }
}

export function scanEmails() {
  return request("/scan-emails", {
    method: "POST",
    body: {},
  });
}

export function runEmailAction(action, email) {
  return request("/scan-emails", {
    method: "POST",
    body: { action, email },
  });
}

export function summarizeMeeting(transcript) {
  return request("/summarize", {
    method: "POST",
    body: { transcript },
  });
}

export function generateResearch(topic) {
  return request("/research", {
    method: "POST",
    body: { topic },
  });
}

export function analyzeJournal(entry) {
  return request("/journal", {
    method: "POST",
    body: { entry },
  });
}

export function startTranscription() {
  return request("/transcribe", {
    method: "POST",
    body: {},
  });
}

export function searchKnowledgeHub(query) {
  return request("/knowledge-hub", {
    method: "POST",
    body: { query },
  });
}

export function runMeetingPipeline(transcript, useSample) {
  return request("/pipeline/run", {
    method: "POST",
    body: { transcript, use_sample: useSample },
  });
}

export { API_BASE_URL };
