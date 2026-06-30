const API_BASE_URL = "http://127.0.0.1:8000";

const apiStatus = document.querySelector("#apiStatus");
const chatModel = document.querySelector("#chatModel");
const embedModel = document.querySelector("#embedModel");
const fileInput = document.querySelector("#fileInput");
const uploadButton = document.querySelector("#uploadButton");
const clearButton = document.querySelector("#clearButton");
const refreshDocuments = document.querySelector("#refreshDocuments");
const documentsList = document.querySelector("#documentsList");
const documentCount = document.querySelector("#documentCount");
const chatForm = document.querySelector("#chatForm");
const messageInput = document.querySelector("#messageInput");
const messages = document.querySelector("#messages");
const topK = document.querySelector("#topK");
const topKValue = document.querySelector("#topKValue");
const dropZone = document.querySelector(".drop-zone");

function setStatus(kind, text) {
  apiStatus.className = `status status-${kind}`;
  apiStatus.textContent = text;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || `Request failed with ${response.status}`);
  }
  return payload;
}

async function loadHealth() {
  try {
    const health = await request("/health");
    setStatus(health.ollama?.ok ? "ok" : "error", health.ollama?.ok ? "Backend online" : "Ollama offline");
    chatModel.textContent = health.chat_model || "chat model";
    embedModel.textContent = health.embedding_model || "embedding model";
  } catch (error) {
    setStatus("error", "Backend offline");
  }
}

async function loadDocuments() {
  try {
    const payload = await request("/documents");
    renderDocuments(payload.documents || []);
  } catch (error) {
    documentsList.innerHTML = `<div class="empty-state">${escapeHtml(error.message)}</div>`;
    documentCount.textContent = "0";
  }
}

function renderDocuments(documents) {
  documentCount.textContent = String(documents.length);
  if (!documents.length) {
    documentsList.innerHTML = `<div class="empty-state">No documents indexed</div>`;
    return;
  }
  documentsList.innerHTML = documents
    .map(
      (document) => `
        <article class="document-item">
          <div class="document-name">${escapeHtml(document.filename)}</div>
          <div class="document-meta">${document.chunk_count} chunks · ${formatDate(document.created_at)}</div>
        </article>
      `,
    )
    .join("");
}

async function uploadFiles() {
  const files = Array.from(fileInput.files || []);
  if (!files.length) {
    addMessage("assistant", "Select at least one file first.");
    return;
  }

  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  setBusy(uploadButton, true, "Uploading");
  try {
    const payload = await request("/ingest", {
      method: "POST",
      body: formData,
    });
    const names = payload.ingested.map((item) => `${item.filename} (${item.chunks} chunks)`).join(", ");
    addMessage("assistant", `Indexed ${names}.`);
    fileInput.value = "";
    await loadDocuments();
  } catch (error) {
    addMessage("assistant", error.message);
  } finally {
    setBusy(uploadButton, false, "Upload");
  }
}

async function clearDocuments() {
  const confirmed = window.confirm("Clear all indexed documents?");
  if (!confirmed) return;

  setBusy(clearButton, true, "Clearing");
  try {
    await request("/documents", { method: "DELETE" });
    addMessage("assistant", "Knowledge base cleared.");
    await loadDocuments();
  } catch (error) {
    addMessage("assistant", error.message);
  } finally {
    setBusy(clearButton, false, "Clear");
  }
}

async function sendMessage(event) {
  event.preventDefault();
  const message = messageInput.value.trim();
  if (!message) return;

  addMessage("user", message);
  messageInput.value = "";
  resizeTextarea();

  const pending = addMessage("assistant", "Thinking...");
  chatForm.classList.add("is-loading");
  try {
    const payload = await request("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, top_k: Number(topK.value) }),
    });
    pending.remove();
    addMessage("assistant", payload.answer, payload.sources || []);
  } catch (error) {
    pending.remove();
    addMessage("assistant", error.message);
  } finally {
    chatForm.classList.remove("is-loading");
  }
}

function addMessage(role, text, sources = []) {
  const article = document.createElement("article");
  article.className = `message ${role}-message`;
  article.innerHTML = `
    <div class="avatar">${role === "user" ? "You" : "AI"}</div>
    <div class="bubble">
      <p>${escapeHtml(text)}</p>
      ${renderSources(sources)}
    </div>
  `;
  messages.appendChild(article);
  messages.scrollTop = messages.scrollHeight;
  return article;
}

function renderSources(sources) {
  if (!sources.length) return "";
  return `
    <div class="sources">
      ${sources
        .map(
          (source) => `
            <details class="source">
              <summary>${escapeHtml(source.filename)} · chunk ${source.chunk_id} · ${Number(source.score).toFixed(3)}</summary>
              <p>${escapeHtml(source.text)}</p>
            </details>
          `,
        )
        .join("")}
    </div>
  `;
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  button.textContent = label;
}

function resizeTextarea() {
  messageInput.style.height = "auto";
  messageInput.style.height = `${Math.min(messageInput.scrollHeight, 160)}px`;
}

function formatDate(value) {
  if (!value) return "";
  return new Date(value.replace(" ", "T")).toLocaleString([], {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

uploadButton.addEventListener("click", uploadFiles);
clearButton.addEventListener("click", clearDocuments);
refreshDocuments.addEventListener("click", loadDocuments);
chatForm.addEventListener("submit", sendMessage);
messageInput.addEventListener("input", resizeTextarea);
topK.addEventListener("input", () => {
  topKValue.textContent = topK.value;
});

dropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropZone.classList.add("dragover");
});

dropZone.addEventListener("dragleave", () => {
  dropZone.classList.remove("dragover");
});

dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropZone.classList.remove("dragover");
  fileInput.files = event.dataTransfer.files;
});

loadHealth();
loadDocuments();

