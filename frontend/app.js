const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const conversation = document.querySelector("#conversation");
const status = document.querySelector("#status");
const button = document.querySelector("#ask-button");
const clearButton = document.querySelector("#clear-button");
const uploadForm = document.querySelector("#upload-form");
const documentFile = document.querySelector("#document-file");
const uploadButton = document.querySelector("#upload-button");
const uploadStatus = document.querySelector("#upload-status");
const documentList = document.querySelector("#document-list");
const refreshDocuments = document.querySelector("#refresh-documents");
const conversationHistory = [];
const apiBase = (window.APP_CONFIG?.apiBase || "http://localhost:8000").replace(/\/+$/, "");

async function loadDocuments() {
  try {
    const response = await fetch(`${apiBase}/documents`);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Could not load documents.");
    documentList.replaceChildren();
    if (!payload.documents.length) {
      documentList.append(Object.assign(document.createElement("li"), { textContent: "No indexed documents." }));
      return;
    }
    payload.documents.forEach((indexedDocument) => {
      const item = document.createElement("li");
      item.append(`${indexedDocument.name} (${indexedDocument.pages} pages, ${indexedDocument.chunks} chunks)`);
      const remove = document.createElement("button");
      remove.type = "button";
      remove.textContent = "Remove";
      remove.addEventListener("click", async () => {
        remove.disabled = true;
        try {
          const response = await fetch(`${apiBase}/documents/${encodeURIComponent(indexedDocument.name)}`, { method: "DELETE" });
          const payload = await response.json();
          if (!response.ok) throw new Error(payload.detail || "Could not remove document.");
          uploadStatus.textContent = `${indexedDocument.name} removed.`;
          await loadDocuments();
        } catch (error) {
          uploadStatus.textContent = error.message;
          remove.disabled = false;
        }
      });
      item.append(remove);
      documentList.append(item);
    });
  } catch (error) {
    documentList.replaceChildren(Object.assign(document.createElement("li"), { textContent: error.message }));
  }
}

function addMessage(label, text, sources = []) {
  conversation.querySelector(".empty")?.remove();
  const message = document.createElement("article");
  message.className = "message";
  const title = document.createElement("strong");
  title.textContent = label;
  const body = document.createElement("p");
  body.textContent = text;
  message.append(title, body);
  if (sources.length) {
    const list = document.createElement("ul");
    list.className = "sources";
    sources.forEach((source) => {
      const item = document.createElement("li");
      const page = source.page_number == null ? "page unavailable" : `page ${source.page_number}`;
      item.textContent = `${source.document_name}, ${page}`;
      list.append(item);
    });
    message.append(list);
  }
  conversation.append(message);
  conversationHistory.push({ role: label.toLowerCase(), text, sources });
}

clearButton.addEventListener("click", () => {
  conversationHistory.length = 0;
  conversation.replaceChildren(Object.assign(document.createElement("p"), {
    className: "empty",
    textContent: "Ask a question about the indexed hospital guidelines.",
  }));
  status.textContent = "Conversation cleared.";
});

refreshDocuments.addEventListener("click", loadDocuments);

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = documentFile.files[0];
  if (!file) return;
  const formData = new FormData();
  formData.append("file", file);
  uploadButton.disabled = true;
  uploadStatus.textContent = "Uploading PDF and creating local embeddings...";
  try {
    const response = await fetch(`${apiBase}/documents/upload`, { method: "POST", body: formData });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "Document indexing failed.");
    uploadStatus.textContent = `${payload.document} indexed: ${payload.pages} pages, ${payload.chunks} chunks.`;
    uploadForm.reset();
    await loadDocuments();
  } catch (error) {
    uploadStatus.textContent = error.message;
  } finally {
    uploadButton.disabled = false;
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;
  addMessage("Question", value);
  question.value = "";
  button.disabled = true;
  status.textContent = "Searching approved documents...";
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 90000);
  try {
    const response = await fetch(`${apiBase}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: value, top_k: 7 }),
      signal: controller.signal,
    });

    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The assistant could not answer right now.");
    addMessage("Assistant", payload.answer, payload.sources || []);
    status.textContent = "";
  } catch (error) {
    status.textContent = error.name === "AbortError"
      ? "The request took too long. Restart the API and try again."
      : `${error.message} Try again.`;
  } finally {
    clearTimeout(timeout);
    button.disabled = false;
  }
});