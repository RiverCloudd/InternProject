const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");
const resetButton = document.querySelector("#resetButton");
const promptButton = document.querySelector("#promptButton");
const closePromptButton = document.querySelector("#closePromptButton");
const promptDialog = document.querySelector("#promptDialog");
const promptText = document.querySelector("#promptText");
const stateList = document.querySelector("#stateList");
const deliverablesEl = document.querySelector("#deliverables");
const collaborationList = document.querySelector("#collaborationList");
const ragSources = document.querySelector("#ragSources");
const agentSelect = document.querySelector("#agentSelect");
const agentTitle = document.querySelector("#agentTitle");
const agentDescription = document.querySelector("#agentDescription");

let agents = [];
let selectedAgentId = window.localStorage.getItem("selectedAgentId") || "gucci_group_chro";
let sessionIds = JSON.parse(window.localStorage.getItem("coworkerSessionIds") || "{}");

const descriptions = {
  gucci_group_ceo:
    "The CEO pressure-tests strategy, Group DNA, culture, and the balance between brand autonomy and Group needs.",
  gucci_group_chro:
    "The CHRO helps design competencies, 360 feedback, coaching, mobility, and people-process guardrails.",
  regional_comms_manager:
    "The Regional Manager translates the design into local rollout, communication, training, and adoption plans.",
};

function currentSessionId() {
  return sessionIds[selectedAgentId] || null;
}

function saveSessionId(sessionId) {
  sessionIds[selectedAgentId] = sessionId;
  window.localStorage.setItem("coworkerSessionIds", JSON.stringify(sessionIds));
}

function initialMessage() {
  const agent = agents.find((item) => item.agent_id === selectedAgentId);
  const role = agent ? agent.role : "AI co-worker";
  return `Hello, I am the ${role}. Tell me which part of the Gucci HRM simulation you are working on.`;
}

function addMessage(role, text) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = text;
  messagesEl.appendChild(message);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function updateState(state) {
  stateList.innerHTML = `
    <div><dt>Module</dt><dd>${state.current_module}</dd></div>
    <div><dt>Confidence</dt><dd>${state.user_confidence}</dd></div>
    <div><dt>Stuck turns</dt><dd>${state.stuck_counter}</dd></div>
  `;

  deliverablesEl.innerHTML = "";
  for (const item of state.missing_deliverables || []) {
    const li = document.createElement("li");
    li.textContent = item.replaceAll("_", " ");
    deliverablesEl.appendChild(li);
  }
}

function resetStatePanel() {
  updateState({
    current_module: "orientation",
    user_confidence: "unknown",
    stuck_counter: 0,
    missing_deliverables: [
      "group_dna",
      "competency_model",
      "360_feedback_plan",
      "coaching_program",
      "talent_mobility_plan",
      "regional_rollout_plan",
      "measurement_plan",
    ],
  });
  updateEngineTrace({ collaboration: { notes: [] }, rag_context: [] });
}

function updateEngineTrace(data) {
  collaborationList.innerHTML = "";
  const notes = data.collaboration?.notes || [];
  if (!notes.length) {
    const li = document.createElement("li");
    li.textContent = "No collaborator";
    collaborationList.appendChild(li);
  } else {
    for (const note of notes) {
      const li = document.createElement("li");
      li.textContent = note.role || note.agent_name || note.agent_id;
      collaborationList.appendChild(li);
    }
  }

  ragSources.innerHTML = "";
  const chunks = data.rag_context || data.context || [];
  for (const chunk of chunks.slice(0, 4)) {
    const li = document.createElement("li");
    li.textContent = chunk.source || "unknown source";
    ragSources.appendChild(li);
  }
  if (!chunks.length) {
    const li = document.createElement("li");
    li.textContent = "No retrieved context";
    ragSources.appendChild(li);
  }
}

function renderAgentHeader() {
  const agent = agents.find((item) => item.agent_id === selectedAgentId);
  agentTitle.textContent = agent ? agent.name : "AI Co-worker";
  agentDescription.textContent = descriptions[selectedAgentId] || "Select an AI co-worker for this simulation.";
}

function resetConversation() {
  messagesEl.innerHTML = "";
  addMessage("assistant", initialMessage());
  resetStatePanel();
}

async function sendMessage(message) {
  addMessage("user", message);
  inputEl.value = "";
  inputEl.disabled = true;

  try {
    const response = await fetch(`/chat/${selectedAgentId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: currentSessionId(), message }),
    });

    if (!response.ok) {
      throw new Error("Request failed");
    }

    const data = await response.json();
    saveSessionId(data.session_id);
    addMessage("assistant", data.assistant_message);
    updateState(data.state);
    updateEngineTrace(data);
  } catch (error) {
    addMessage("assistant", "The local app could not process that message. Please check the server and try again.");
  } finally {
    inputEl.disabled = false;
    inputEl.focus();
  }
}

async function loadAgents() {
  const response = await fetch("/api/agents");
  const data = await response.json();
  agents = data.agents || [];
  selectedAgentId = agents.some((agent) => agent.agent_id === selectedAgentId)
    ? selectedAgentId
    : data.default_agent_id;

  agentSelect.innerHTML = "";
  for (const agent of agents) {
    const option = document.createElement("option");
    option.value = agent.agent_id;
    option.textContent = agent.name;
    agentSelect.appendChild(option);
  }
  agentSelect.value = selectedAgentId;
  renderAgentHeader();
  resetConversation();
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  const message = inputEl.value.trim();
  if (message) {
    sendMessage(message);
  }
});

agentSelect.addEventListener("change", () => {
  selectedAgentId = agentSelect.value;
  window.localStorage.setItem("selectedAgentId", selectedAgentId);
  renderAgentHeader();
  resetConversation();
});

resetButton.addEventListener("click", () => {
  delete sessionIds[selectedAgentId];
  window.localStorage.setItem("coworkerSessionIds", JSON.stringify(sessionIds));
  resetConversation();
});

promptButton.addEventListener("click", async () => {
  promptText.textContent = "Loading...";
  promptDialog.showModal();
  try {
    const response = await fetch(`/api/system-prompt/${selectedAgentId}`);
    const data = await response.json();
    promptText.textContent = data.system_prompt;
  } catch (error) {
    promptText.textContent = "Could not load the system prompt preview.";
  }
});

closePromptButton.addEventListener("click", () => {
  promptDialog.close();
});

loadAgents().catch(() => {
  agents = [{ agent_id: selectedAgentId, name: "Gucci Group CHRO", role: "Gucci Group CHRO" }];
  renderAgentHeader();
  resetConversation();
});
