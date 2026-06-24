from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import textwrap


PAGE_W = 612
PAGE_H = 792
MARGIN_X = 54
TOP_Y = 738
BOTTOM_Y = 54
CONTENT_W = PAGE_W - (MARGIN_X * 2)


def esc(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


@dataclass
class TextLine:
    text: str
    x: float
    y: float
    font: str
    size: int
    color: tuple[float, float, float]


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float
    fill: tuple[float, float, float]


class SimplePdf:
    def __init__(self, title: str) -> None:
        self.title = title
        self.pages: list[list[TextLine | Rect]] = [[]]
        self.y = TOP_Y
        self.page_no = 1

    def _current(self) -> list[TextLine | Rect]:
        return self.pages[-1]

    def new_page(self) -> None:
        self.pages.append([])
        self.page_no += 1
        self.y = TOP_Y

    def ensure(self, height: float) -> None:
        if self.y - height < BOTTOM_Y:
            self.footer()
            self.new_page()

    def line(
        self,
        text: str,
        *,
        x: float = MARGIN_X,
        font: str = "F1",
        size: int = 10,
        color: tuple[float, float, float] = (0.09, 0.10, 0.12),
        leading: float | None = None,
    ) -> None:
        leading = leading if leading is not None else size * 1.35
        self.ensure(leading)
        self._current().append(TextLine(text, x, self.y, font, size, color))
        self.y -= leading

    def para(
        self,
        text: str,
        *,
        x: float = MARGIN_X,
        width_chars: int = 94,
        font: str = "F1",
        size: int = 10,
        color: tuple[float, float, float] = (0.09, 0.10, 0.12),
        after: float = 7,
    ) -> None:
        for wrapped in textwrap.wrap(text, width=width_chars, break_long_words=False):
            self.line(wrapped, x=x, font=font, size=size, color=color, leading=size * 1.32)
        self.y -= after

    def bullet(self, text: str, *, level: int = 0) -> None:
        indent = MARGIN_X + 14 + (level * 18)
        bullet_x = MARGIN_X + (level * 18)
        lines = textwrap.wrap(text, width=88 - (level * 4), break_long_words=False)
        if not lines:
            return
        self.line("-", x=bullet_x, size=10, leading=0)
        self.line(lines[0], x=indent, size=10, leading=13)
        for line in lines[1:]:
            self.line(line, x=indent, size=10, leading=13)
        self.y -= 2

    def h1(self, text: str) -> None:
        self.ensure(42)
        self.y -= 5
        self._current().append(Rect(MARGIN_X, self.y - 5, 4, 22, (0.18, 0.45, 0.70)))
        self.line(text, x=MARGIN_X + 12, font="F2", size=15, color=(0.12, 0.29, 0.45), leading=24)
        self.y -= 2

    def h2(self, text: str) -> None:
        self.ensure(30)
        self.line(text, font="F2", size=12, color=(0.12, 0.29, 0.45), leading=18)

    def callout(self, label: str, text: str) -> None:
        lines = textwrap.wrap(f"{label}: {text}", width=92, break_long_words=False)
        height = 18 + (len(lines) * 12)
        self.ensure(height + 8)
        self._current().append(Rect(MARGIN_X, self.y - height + 8, CONTENT_W, height, (0.95, 0.97, 0.99)))
        self.y -= 8
        first = True
        for line in lines:
            self.line(line, x=MARGIN_X + 12, font="F2" if first else "F1", size=9, color=(0.12, 0.20, 0.28), leading=12)
            first = False
        self.y -= 8

    def code(self, text: str) -> None:
        lines = []
        for raw in text.splitlines():
            lines.extend(textwrap.wrap(raw, width=86, break_long_words=False) or [""])
        height = 16 + (len(lines) * 11)
        self.ensure(height + 10)
        self._current().append(Rect(MARGIN_X, self.y - height + 8, CONTENT_W, height, (0.96, 0.96, 0.96)))
        self.y -= 8
        for line in lines:
            self.line(line, x=MARGIN_X + 12, font="F3", size=8, color=(0.12, 0.12, 0.12), leading=11)
        self.y -= 9

    def footer(self) -> None:
        self._current().append(TextLine("Multi-Agent AI Co-worker Engine - Source Code Report", MARGIN_X, 32, "F1", 8, (0.35, 0.38, 0.42)))
        self._current().append(TextLine(str(self.page_no), PAGE_W - MARGIN_X - 10, 32, "F1", 8, (0.35, 0.38, 0.42)))

    def save(self, path: Path) -> None:
        self.footer()
        objects: list[bytes] = []

        def add(obj: bytes) -> int:
            objects.append(obj)
            return len(objects)

        font1 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
        font2 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
        font3 = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

        page_ids = []
        content_ids = []
        for page in self.pages:
            stream_lines = []
            for item in page:
                if isinstance(item, Rect):
                    r, g, b = item.fill
                    stream_lines.append(f"{r} {g} {b} rg {item.x} {item.y} {item.w} {item.h} re f")
                else:
                    r, g, b = item.color
                    stream_lines.append(
                        f"BT {r} {g} {b} rg /{item.font} {item.size} Tf {item.x} {item.y} Td ({esc(item.text)}) Tj ET"
                    )
            stream = "\n".join(stream_lines).encode("latin-1", errors="replace")
            content_ids.append(add(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"))
            page_ids.append(None)

        pages_id_placeholder = len(objects) + len(self.pages) + 1
        for i, content_id in enumerate(content_ids):
            page_ids[i] = add(
                f"<< /Type /Page /Parent {pages_id_placeholder} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
                f"/Resources << /Font << /F1 {font1} 0 R /F2 {font2} 0 R /F3 {font3} 0 R >> >> "
                f"/Contents {content_id} 0 R >>".encode()
            )

        pages_id = add(
            f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] /Count {len(page_ids)} >>".encode()
        )
        catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode())
        info_id = add(f"<< /Title ({esc(self.title)}) /Producer (Codex SimplePdf) >>".encode())

        output = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for idx, obj in enumerate(objects, start=1):
            offsets.append(len(output))
            output.extend(f"{idx} 0 obj\n".encode())
            output.extend(obj)
            output.extend(b"\nendobj\n")
        xref_pos = len(output)
        output.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        output.extend(b"0000000000 65535 f \n")
        for off in offsets[1:]:
            output.extend(f"{off:010d} 00000 n \n".encode())
        output.extend(
            f"trailer << /Size {len(objects) + 1} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF\n".encode()
        )
        path.write_bytes(output)


def build_report() -> SimplePdf:
    pdf = SimplePdf("Multi-Agent AI Co-worker Engine - Source Code Report")

    pdf.line("Multi-Agent AI Co-worker Engine", font="F2", size=22, color=(0.08, 0.18, 0.29), leading=28)
    pdf.line("Source Code Architecture Report", font="F2", size=16, color=(0.18, 0.45, 0.70), leading=22)
    pdf.para(
        "This report explains the mission, simulation context, source-code design, prototype architecture, "
        "API surface, retrieval layer, memory model, interaction modes, safety controls, evaluation approach, "
        "and limitations of the submitted local FastAPI prototype.",
        size=10,
        after=12,
    )
    pdf.callout(
        "Executive summary",
        "The prototype demonstrates a configurable multi-agent AI co-worker engine with a browser UI, FastAPI API layer, "
        "agent personas, RAG-style retrieval, blackboard memory, safety checks, and deterministic mock LLM output for review without paid keys.",
    )

    sections = [
        (
            "1. Problem & mission",
            [
                "The problem is to help a learner complete a Gucci HRM leadership-development simulation without replacing the learner's own reasoning. The system must behave like an AI co-worker: useful, structured, domain-aware, and bounded.",
                "The mission of the source code is to provide a local multi-agent prototype that can route questions, consult specialist personas, retrieve relevant simulation context, maintain state, and return explainable metadata for review.",
            ],
            [
                "Support the learner with scaffolding instead of final-answer outsourcing.",
                "Expose a local API-first prototype suitable for inspection and testing.",
                "Keep the system runnable without a paid LLM key through MockLLMClient.",
            ],
        ),
        (
            "2. Gucci simulation context",
            [
                "The case context is a Group-level HRM and leadership-development assignment for Gucci. The prototype models workstreams around Group DNA, leadership competencies, 360 feedback, coaching, talent mobility, and regional rollout.",
                "Knowledge files in data/ and shared/ provide the assignment context, deliverables, guardrails, tool catalog, and shared prompt template. Agent-specific folders add persona-level behavior, tasks, skills, memory schema, examples, and handoff rules.",
            ],
            [
                "Core themes: Vision, Entrepreneurship, Passion, and Trust.",
                "Key tension: Group-wide consistency versus brand or regional adaptation.",
                "Expected learner outputs: competency model, feedback plan, coaching program, rollout plan, and measurement plan.",
            ],
        ),
        (
            "3. Multi-agent AI co-worker design",
            [
                "The design uses multiple specialized co-workers rather than a single assistant. Each agent has a bounded role and can be selected directly from the UI. The boss agent can coordinate the team when the user needs synthesis across domains.",
                "The code separates persona configuration from runtime orchestration. This makes the prototype easier to extend with new agents or new workflows without rewriting the API layer.",
            ],
            [
                "Config-driven agents live under agents/<agent_id>/.",
                "Runtime behavior is handled by BaseAgent, MultiAgentOrchestrator, IntentRouter, PromptBuilder, and LLM clients.",
                "The UI deliberately hides system prompts while allowing agent switching.",
            ],
        ),
        (
            "4. Agent personas: CEO, CHRO, Regional Manager",
            [
                "The CEO persona focuses on enterprise strategy, Group DNA, governance, and tradeoffs between Group non-negotiables and local autonomy. The CHRO persona focuses on competencies, 360 feedback, coaching, mobility, succession, and development integrity.",
                "The Regional Manager persona focuses on rollout, localization, communication channels, trainer readiness, employee voice, and adoption metrics. Together, these personas cover strategy, people-system design, and implementation.",
            ],
            [
                "CEO: pressure-tests strategic clarity and executive tradeoffs.",
                "CHRO: makes HR design observable, fair, developmental, and measurable.",
                "Regional Manager: turns plans into localized adoption and communication workflows.",
            ],
        ),
        (
            "5. Multi-agent architecture",
            [
                "The central runtime object is MultiAgentOrchestrator. It constructs loader, retriever, prompt builder, LLM client, intent router, message bus, blackboard, memory manager, supervisor, synthesizer, safety checker, and tool router.",
                "The architecture supports direct response, consultation, panel responses, debate synthesis, and handoff behavior. Supporting agents communicate through the MessageBus, while final user-facing responses are produced by the active primary agent or the synthesizer.",
            ],
            [
                "AgentLoader loads YAML and Markdown persona modules.",
                "IntentRouter decides primary and supporting agents.",
                "Synthesizer merges panel or debate outputs.",
                "MessageBus records private inter-agent consultation messages.",
            ],
        ),
        (
            "6. API layer",
            [
                "The FastAPI layer is intentionally small. app.py creates the FastAPI app, mounts the static UI, creates the default orchestrator, and includes routes from src/api/routes.py.",
                "The API supports /health, /agents, /api/agents, /chat, /chat/{agent_id}, and /api/chat compatibility routes. Pydantic schemas in src/api/schemas.py define request and response shapes.",
            ],
            [
                "GET /health returns service status.",
                "GET /api/agents returns the default agent and available agents.",
                "POST /chat supports advanced mode selection.",
                "POST /chat/{agent_id} supports the browser UI's selected-agent workflow.",
            ],
        ),
        (
            "7. RAG + Vector DB design",
            [
                "The retrieval layer builds chunks from data/, shared/, and agents/ files. MockEmbeddingClient creates deterministic local embeddings, while MockVectorDB provides an in-memory vector-store interface with cosine similarity.",
                "The design intentionally mimics production RAG shape without requiring FAISS or hosted embeddings. It also filters retrieved context by agent scope where possible and falls back to broader retrieval when needed.",
            ],
            [
                "RAGIndexBuilder chunks Markdown and YAML knowledge files.",
                "Retriever.retrieve returns scored raw chunks for internal prompt construction.",
                "Public API responses expose metadata only, not full retrieved prompt text.",
                "system_prompt.md files are excluded from the public retrieval index.",
            ],
        ),
        (
            "8. Memory + shared blackboard",
            [
                "The prototype uses two memory concepts. MemoryStore keeps per-session conversational state for the agent runtime, while Blackboard stores shared project state such as current module, active deliverable, missing outputs, decisions, risks, and retrieval history.",
                "The blackboard lets future turns inherit context from previous turns without exposing hidden prompt logic. It also helps the orchestrator track deliverable progress and debugging metadata.",
            ],
            [
                "Blackboard.load initializes session state.",
                "Blackboard.update_from_turn records module, intent, last response summary, and retrieval history.",
                "MemoryStore tracks session-level confidence, completed deliverables, and conversation history.",
            ],
        ),
        (
            "9. Interaction modes: direct, consult, debate, panel, handoff",
            [
                "Interaction modes are selected explicitly or inferred in auto mode. Direct mode uses one active agent. Consult mode asks supporting agents for private input before the primary agent responds. Panel mode collects multiple panelist responses and synthesizes them.",
                "Debate mode creates a proposal, asks supporting agents to challenge it, and synthesizes a response. Handoff mode changes the primary agent to a supporting specialist when the request belongs elsewhere.",
            ],
            [
                "direct: one agent answers.",
                "consult: active agent consults selected specialists.",
                "panel: multiple agents provide perspectives.",
                "debate: proposal plus critique workflow.",
                "handoff: transfer to the more relevant agent.",
            ],
        ),
        (
            "10. Supervisor / Director agent",
            [
                "The current code uses Supervisor plus IntentRouter as the director-like control layer. Supervisor detects module, vagueness, safety status, stuck signals, and completed deliverables. IntentRouter detects intent and selects primary/supporting agents.",
                "The boss agent is also available as a user-selectable coordinator persona. It consults CEO, CHRO, and Regional Manager when broad synthesis is needed.",
            ],
            [
                "Supervisor.analyze returns status, module, redirect flags, and recommended action.",
                "IntentRouter maps intent to primary and supporting agents.",
                "Boss agent provides a human-facing coordination persona.",
            ],
        ),
        (
            "11. Safety guardrails",
            [
                "SafetyChecker identifies prompt extraction, instruction override attempts, confidential data requests, final-answer outsourcing, off-track prompts, and harmful HR requests. The orchestrator blocks prompt-extraction attempts before prompt construction proceeds.",
                "The UI no longer exposes a system-prompt preview. Public chat responses return retrieved-context metadata only, reducing the chance of leaking internal configuration or prompt content.",
            ],
            [
                "Prompt extraction returns a blocked response.",
                "Agent rules prohibit revealing hidden instructions.",
                "The reportable API metadata avoids raw prompt or raw retrieved text exposure.",
            ],
        ),
        (
            "12. Prototype implementation",
            [
                "The implementation is intentionally lightweight and local. It uses FastAPI for the API layer, static HTML/CSS/JavaScript for the UI, YAML/Markdown for agent configuration, and Python classes for routing, memory, safety, retrieval, and orchestration.",
                "MockLLMClient provides deterministic English responses for reliable grading. GeminiLLMClient is optional and loaded only when .env requests Gemini and a real key is present.",
            ],
            [
                "Entry point: app.py.",
                "UI: static/index.html, static/app.js, static/styles.css.",
                "Tests: tests/test_agent.py.",
                "Run guide: RUNNING.md.",
            ],
        ),
        (
            "13. Demo / sample API response",
            [
                "A typical browser request posts to /chat/{agent_id}. For example, posting an education communication request to regional_comms_manager returns a structured campaign-planning response and metadata about state, route, safety flags, and collaborators.",
            ],
            [],
        ),
        (
            "14. Evaluation metrics",
            [
                "Evaluation should cover both engineering quality and assistant behavior. The prototype includes tests for agent list behavior, boss consultation, consult mode, debate mode, prompt-extraction blocking, hidden prompt endpoint removal, metadata-only retrieved context, mock fallback, and retriever metadata.",
                "Product-level evaluation should measure whether the assistant is helpful, scoped, context-aware, safe, and faithful to the simulation.",
            ],
            [
                "Functional: endpoint success, routing accuracy, mode selection, session continuity.",
                "Retrieval: relevant context, agent-scope filtering, no hidden prompt leakage.",
                "Safety: prompt-extraction refusal, assignment-scaffolding behavior, no confidential data fabrication.",
                "UX: agent switching clarity, response depth, English consistency, browser reliability.",
                "Learning value: asks useful questions, scaffolds deliverables, avoids writing the final assignment end-to-end.",
            ],
        ),
        (
            "15. Limitations & next steps",
            [
                "The prototype is intentionally local and simplified. Mock embeddings and MockVectorDB approximate the production architecture but do not provide semantic retrieval quality equivalent to hosted embeddings or FAISS. MockLLMClient is deterministic and useful for grading, but it is not a substitute for a high-quality model in real use.",
                "Next steps should focus on replacing mock components, expanding tests, adding richer observability, and improving evaluation with realistic user transcripts.",
            ],
            [
                "Replace mock embeddings with a production embedding model.",
                "Add persistent vector DB storage and indexing scripts.",
                "Add authentication and request logging for hosted use.",
                "Add structured evaluation datasets and rubric-based scoring.",
                "Improve frontend state handling and add loading/error states.",
                "Add model-cost controls, retry behavior, and streaming responses.",
            ],
        ),
    ]

    for title, paras, bullets in sections:
        pdf.h1(title)
        for para in paras:
            pdf.para(para)
        for bullet in bullets:
            pdf.bullet(bullet)
        if title.startswith("13."):
            pdf.code(
                "POST /chat/regional_comms_manager\n"
                "{\n"
                '  "session_id": "demo-session",\n'
                '  "message": "I need to build an education communication project."\n'
                "}\n\n"
                "Sample response excerpt:\n"
                "{\n"
                '  "agent_id": "regional_comms_manager",\n'
                '  "assistant_message": "For an education communication project, build the campaign around an audience journey...",\n'
                '  "collaboration": {"collaborators": ["gucci_group_chro"]},\n'
                '  "safety_flags": {},\n'
                '  "context": [{"document_id": "module_3_rollout_adoption", "score": 0.74}]\n'
                "}"
            )

    pdf.h1("Closing assessment")
    pdf.para(
        "The source code presents a coherent local prototype for a multi-agent AI co-worker engine. Its strongest qualities are the separation between configuration and runtime, the API-first structure, the multi-mode orchestration design, the explicit safety layer, and the ability to run without paid credentials. The main engineering limitations are mock retrieval quality, non-persistent vector storage, deterministic mock responses, and the absence of production deployment concerns such as authentication, monitoring, and hosted storage."
    )
    return pdf


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    out_dir = root / "reports"
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "AI_Coworker_Source_Code_Report.pdf"
    build_report().save(out_path)
    print(out_path)


if __name__ == "__main__":
    main()
