const state = {
  sessionId: null,
  mediaRecorder: null,
  recordedBlob: null,
  recordedMimeType: "audio/webm",
};

const healthStatus = document.getElementById("health-status");
const sessionIdEl = document.getElementById("session-id");
const responseSourceEl = document.getElementById("response-source");
const textResponseEl = document.getElementById("text-response");
const rawJsonEl = document.getElementById("raw-json");
const visualsGridEl = document.getElementById("visuals-grid");
const errorBoxEl = document.getElementById("error-box");
const audioPlayerEl = document.getElementById("audio-player");
const recordingStatusEl = document.getElementById("recording-status");

document.getElementById("new-session-btn").addEventListener("click", resetSession);
document.getElementById("send-chat-btn").addEventListener("click", sendChat);
document.getElementById("send-image-btn").addEventListener("click", sendImage);
document.getElementById("send-audio-btn").addEventListener("click", sendAudio);
document.getElementById("record-btn").addEventListener("click", toggleRecording);
document.getElementById("interrupt-btn").addEventListener("click", sendInterruption);

checkHealth();
renderSession();

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    healthStatus.textContent = data.configured ? "Ready" : "Missing API key / project";
    healthStatus.style.color = data.ok ? "var(--success)" : "var(--danger)";
  } catch {
    healthStatus.textContent = "Service unavailable";
    healthStatus.style.color = "var(--danger)";
  }
}

function resetSession() {
  state.sessionId = null;
  state.recordedBlob = null;
  renderSession();
  renderResponse({ text: "Started a fresh local demo session.", audio: "", visuals: [], interrupted: false }, "system");
}

function renderSession() {
  sessionIdEl.textContent = state.sessionId || "new session";
}

async function sendChat() {
  const text = document.getElementById("chat-text").value.trim();
  const includeAudio = document.getElementById("chat-audio").checked;
  if (!text) {
    showError("Enter a message before sending chat.");
    return;
  }
  clearError();
  await postJson("/agentx/live-agent/chat", { text, include_audio: includeAudio, session_id: state.sessionId }, "text chat");
}

async function sendImage() {
  const file = document.getElementById("image-file").files[0];
  const prompt = document.getElementById("image-prompt").value.trim();
  if (!file) {
    showError("Choose an image before sending it to Gemini.");
    return;
  }
  clearError();
  const form = new FormData();
  form.append("file", file);
  if (prompt) form.append("prompt", prompt);
  if (state.sessionId) form.append("session_id", state.sessionId);
  await postForm("/agentx/live-agent/image", form, "image reasoning");
}

async function sendAudio({ interruption = false } = {}) {
  const uploadFile = document.getElementById("audio-file").files[0];
  const prompt = document.getElementById("audio-prompt").value.trim();
  const file = state.recordedBlob || uploadFile;
  if (!file) {
    showError("Upload or record audio before sending it.");
    return;
  }
  clearError();
  const form = new FormData();
  form.append("file", file, file.name || `recording.${extensionForMime(state.recordedMimeType)}`);
  if (prompt) form.append("prompt", prompt);
  if (state.sessionId) form.append("session_id", state.sessionId);
  if (interruption) form.append("interruption_signal", "true");
  await postForm("/agentx/live-agent/audio", form, interruption ? "interruption" : "voice input");
}

async function sendInterruption() {
  await sendAudio({ interruption: true });
}

async function postJson(url, body, sourceLabel) {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    await handleResponse(response, sourceLabel);
  } catch (error) {
    showError(error.message || "Request failed.");
  }
}

async function postForm(url, formData, sourceLabel) {
  try {
    const response = await fetch(url, { method: "POST", body: formData });
    await handleResponse(response, sourceLabel);
  } catch (error) {
    showError(error.message || "Request failed.");
  }
}

async function handleResponse(response, sourceLabel) {
  const text = await response.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { detail: text };
  }
  if (!response.ok) {
    showError(data.detail || data.message || `Request failed with status ${response.status}`);
    rawJsonEl.textContent = JSON.stringify(data, null, 2);
    return;
  }
  clearError();
  state.sessionId = data.session_id || state.sessionId;
  renderSession();
  renderResponse(data, sourceLabel);
}

function renderResponse(data, sourceLabel) {
  responseSourceEl.textContent = sourceLabel;
  textResponseEl.textContent = data.text || "No text returned.";
  rawJsonEl.textContent = JSON.stringify(data, null, 2);
  renderVisuals(data.visuals || []);
  renderAudio(data.audio || "");
}

function renderVisuals(visuals) {
  if (!visuals.length) {
    visualsGridEl.className = "visuals-grid empty";
    visualsGridEl.textContent = "Visual summaries will appear here.";
    return;
  }
  visualsGridEl.className = "visuals-grid";
  visualsGridEl.innerHTML = visuals
    .map((item) => {
      const title = escapeHtml(item.title || item.type || "Visual");
      const content = escapeHtml(stringifyValue(item.content));
      return `<div class="visual-card"><strong>${title}</strong><div>${content}</div></div>`;
    })
    .join("");
}

function renderAudio(audioBase64) {
  if (!audioBase64) {
    audioPlayerEl.classList.add("hidden");
    audioPlayerEl.removeAttribute("src");
    return;
  }
  audioPlayerEl.src = `data:audio/mp3;base64,${audioBase64}`;
  audioPlayerEl.classList.remove("hidden");
}

function showError(message) {
  errorBoxEl.textContent = message;
  errorBoxEl.classList.remove("hidden");
}

function clearError() {
  errorBoxEl.textContent = "";
  errorBoxEl.classList.add("hidden");
}

async function toggleRecording() {
  if (state.mediaRecorder && state.mediaRecorder.state === "recording") {
    state.mediaRecorder.stop();
    return;
  }
  if (!navigator.mediaDevices?.getUserMedia) {
    showError("This browser does not support microphone recording.");
    return;
  }
  clearError();
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const mimeType = MediaRecorder.isTypeSupported("audio/webm") ? "audio/webm" : "audio/mp4";
  state.recordedMimeType = mimeType;
  const chunks = [];
  state.mediaRecorder = new MediaRecorder(stream, { mimeType });
  state.mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) chunks.push(event.data);
  };
  state.mediaRecorder.onstop = () => {
    state.recordedBlob = new Blob(chunks, { type: mimeType });
    recordingStatusEl.textContent = "Recording captured. You can now send it to Gemini.";
    document.getElementById("record-btn").textContent = "Start Recording";
    stream.getTracks().forEach((track) => track.stop());
  };
  state.mediaRecorder.start();
  recordingStatusEl.textContent = "Recording... click again to stop.";
  document.getElementById("record-btn").textContent = "Stop Recording";
}

function stringifyValue(value) {
  return typeof value === "string" ? value : JSON.stringify(value);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function extensionForMime(mimeType) {
  if (mimeType.includes("webm")) return "webm";
  if (mimeType.includes("mp4")) return "mp4";
  if (mimeType.includes("wav")) return "wav";
  return "bin";
}