const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const conversation = document.querySelector("#conversation");
const status = document.querySelector("#status");
const button = document.querySelector("#ask-button");

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
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;
  addMessage("Question", value);
  question.value = "";
  button.disabled = true;
  status.textContent = "Searching approved documents...";
  try {
    const response = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: value, top_k: 5 }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The assistant could not answer right now.");
    addMessage("Assistant", payload.answer, payload.sources || []);
    status.textContent = "";
  } catch (error) {
    status.textContent = `${error.message} Try again.`;
  } finally {
    button.disabled = false;
  }
});