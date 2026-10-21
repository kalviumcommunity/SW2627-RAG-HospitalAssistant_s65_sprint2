const form = document.querySelector("#ask-form");
const question = document.querySelector("#question");
const conversation = document.querySelector("#conversation");
const status = document.querySelector("#status");
const button = document.querySelector("#ask-button");

function addMessage(label, text) {
  conversation.querySelector(".empty")?.remove();
  const message = document.createElement("article");
  message.className = "message";
  const title = document.createElement("strong");
  title.textContent = label;
  const body = document.createElement("p");
  body.textContent = text;
  message.append(title, body);
  conversation.append(message);
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const value = question.value.trim();
  if (!value) return;
  addMessage("Question", value);
  question.value = "";
  status.textContent = "Ready for backend integration.";
});