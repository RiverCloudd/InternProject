const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");
const resetButton = document.querySelector("#resetButton");
const agentSelect = document.querySelector("#agentSelect");
const agentTitle = document.querySelector("#agentTitle");
const agentDescription = document.querySelector("#agentDescription");

let agents = [];
let selectedAgentId = window.localStorage.getItem("selectedAgentId") || "gucci_group_chro";
let sessionIds = loadSessionIds();
window.localStorage.removeItem("bossMode");

const descriptions = {
  gucci_group_boss:
    "The team lead coordinates CEO, CHRO, and Regional Comms perspectives into one integrated next move.",
  gucci_group_ceo:
    "The CEO pressure-tests strategy, Group DNA, culture, and the balance between brand autonomy and Group needs.",
  gucci_group_chro:
    "The CHRO helps design competencies, 360 feedback, coaching, mobility, and people-process guardrails.",
  regional_comms_manager:
    "The Regional Manager translates the design into local rollout, communication, training, and adoption plans.",
};

function defaultAgentId() {
  return agents.some((agent) => agent.agent_id === "gucci_group_chro")
    ? "gucci_group_chro"
    : agents[0]?.agent_id || "gucci_group_chro";
}

function normalizeSelectedAgentId(preferredId) {
  return agents.some((agent) => agent.agent_id === preferredId)
    ? preferredId
    : defaultAgentId();
}

function loadSessionIds() {
  try {
    const parsed = JSON.parse(window.localStorage.getItem("coworkerSessionIds") || "{}");
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch (error) {
    window.localStorage.removeItem("coworkerSessionIds");
    return {};
  }
}

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
  window.localStorage.setItem("coworkerLastState", JSON.stringify(state));
}

function resetStatePanel() {
  window.localStorage.removeItem("coworkerLastState");
  window.localStorage.removeItem("coworkerLastTrace");
}

function updateEngineTrace(data) {
  window.localStorage.setItem("coworkerLastTrace", JSON.stringify(data));
}

function renderAgentHeader() {
  selectedAgentId = normalizeSelectedAgentId(selectedAgentId);
  const agent = agents.find((item) => item.agent_id === selectedAgentId);
  agentTitle.textContent = agent ? agent.name : "Gucci Group CHRO";
  agentDescription.textContent = descriptions[selectedAgentId] || "Select an AI co-worker for this simulation.";
  agentSelect.value = selectedAgentId;
}

function populateAgentSelect(agentList) {
  agentSelect.innerHTML = "";
  for (const agent of agentList) {
    const option = document.createElement("option");
    option.value = agent.agent_id;
    option.textContent = agent.name;
    agentSelect.appendChild(option);
  }
  selectedAgentId = normalizeSelectedAgentId(selectedAgentId);
  agentSelect.value = selectedAgentId;
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
  selectedAgentId = normalizeSelectedAgentId(selectedAgentId || data.default_agent_id);
  window.localStorage.setItem("selectedAgentId", selectedAgentId);

  populateAgentSelect(agents);
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

loadAgents().catch(() => {
  agents = [
    { agent_id: "gucci_group_boss", name: "Group Boss", role: "Multi-agent Team Lead" },
    { agent_id: "gucci_group_ceo", name: "Group CEO", role: "Gucci Group CEO" },
    { agent_id: "gucci_group_chro", name: "Group CHRO", role: "Gucci Group CHRO" },
    {
      agent_id: "regional_comms_manager",
      name: "Regional Comms Manager",
      role: "Employer Branding & Internal Communications Regional Manager",
    },
  ];
  selectedAgentId = agents.some((agent) => agent.agent_id === selectedAgentId)
    ? selectedAgentId
    : "gucci_group_chro";
  populateAgentSelect(agents);
  renderAgentHeader();
  resetConversation();
});
