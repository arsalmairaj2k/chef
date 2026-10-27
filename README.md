# AI Cooking Companion — Backend MVP

A Pakistan-first, voice-first AI Cooking Companion backend built with Python, FastAPI, SQLAlchemy 2.x, Alembic, and PostgreSQL.

The application guides users through cooking South Asian recipes (e.g., Chicken Karahi, Tarka Daal, Biryani) one step at a time, supporting natural code-switching in Urdu, Roman Urdu, and English.

---

## Architecture Principles

- **LLM proposes, backend validates & owns state**: The language model interprets user speech and proposes actions. The backend maintains the authoritative cooking state and executes verified state transitions.
- **Deterministic state machine**: No relying on conversational context memory for session progress.
- **Database integrity**: Relational schema enforced with foreign key constraints, unique indexes, and domain check constraints.
- **Untrusted input boundary**: Model proposals are treated as untrusted input. The model cannot execute arbitrary Python or SQL, mutate database records outside the domain service, or bypass step ordering.
- **Provider-independent action & LLM interface**: Actions, decision schemas, error taxonomy, and LLM adapters are decoupled from specific vendor SDKs.

---

## Project Structure

```text
CHEF/
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI application entrypoint & router registry
│   ├── ai/                      # AI Layer (Decoupled, Strict, Safe)
│   │   ├── __init__.py
│   │   ├── action_schemas.py    # Strict Pydantic argument schemas (extra="forbid")
│   │   ├── action_results.py    # Predictable ActionResult & ActionError models
│   │   ├── decision_schemas.py  # LLMDecision schemas (execute_action, answer_question, clarify)
│   │   ├── prompts.py           # Version-controlled system prompts & guidance
│   │   ├── tool_registry.py     # Explicit allowlisted registry & JSON schema exporter
│   │   ├── action_executor.py   # Safe execution engine & domain error mapping
│   │   └── providers/           # Provider-independent LLM abstraction
│   │       ├── __init__.py      # Provider factory with testing override support
│   │       ├── base.py          # Abstract BaseLLMProvider & normalized exceptions
│   │       ├── fake.py          # Deterministic, zero-cost fake provider for offline testing
│   │       └── openai_provider.py # Production OpenAI provider with structured output
│   ├── api/
│   │   ├── __init__.py
│   │   ├── health.py            # Health check routes (/health, /api/v1/health)
│   │   ├── recipes.py           # Recipe API endpoints (/api/v1/recipes)
│   │   ├── sessions.py          # Cooking session endpoints (/api/v1/sessions)
│   │   ├── actions.py           # Action execution endpoint (/api/v1/sessions/{id}/actions)
│   │   └── chat.py              # Conversational endpoint (/api/v1/sessions/{id}/message)
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py            # Pydantic Settings & environment config
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py              # SQLAlchemy DeclarativeBase
│   │   └── session.py           # Engine, session factory & get_db dependency
│   ├── models/
│   │   ├── __init__.py          # Model exports
│   │   ├── recipe.py            # Recipe ORM model
│   │   ├── ingredient.py        # Canonical Ingredient ORM model
│   │   ├── recipe_ingredient.py # RecipeIngredient junction model
│   │   ├── recipe_step.py       # Ordered RecipeStep ORM model
│   │   ├── cooking_session.py   # CookingSession ORM model
│   │   └── cooking_session_step.py # CookingSessionStep ORM model
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── recipe_repository.py # Recipe queries & eager loading
│   │   └── session_repository.py# Session queries & eager loading
│   ├── services/
│   │   ├── __init__.py
│   │   ├── recipe_service.py    # Recipe business logic & transactions
│   │   ├── session_service.py   # Deterministic cooking state machine
│   │   └── chat_service.py      # LLM orchestration & grounded responses
│   └── schemas/
│       ├── __init__.py          # Schema exports
│       ├── recipe.py            # Recipe Pydantic schemas
│       ├── cooking_session.py   # Cooking session Pydantic schemas
│       └── chat.py              # Conversational request, response & summary schemas
├── alembic/
│   ├── env.py                   # Alembic environment linked to project config & Base
│   ├── script.py.mako           # Migration template
│   └── versions/
│       ├── aa86fa0da21b_create_recipe_tables.py  # Initial migration
│       └── 6db08a17b290_add_cooking_sessions.py  # Cooking sessions migration
├── scripts/
│   └── seed_recipes.py          # Idempotent seed script for Pakistani recipes
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # In-memory SQLite fixtures & isolation
│   ├── unit/
│   │   ├── test_models.py       # Database models, constraints & relationships
│   │   ├── test_schemas.py      # Pydantic validation & constraint tests
│   │   ├── test_session_engine.py# State machine transitions & ordering tests
│   │   ├── test_actions.py      # Action validation, registry allowlist & executor tests
│   │   ├── test_decision_schemas.py # Structured decision schema tests
│   │   └── test_llm_provider.py # LLM provider abstraction, fake provider & error tests
│   └── integration/
│       ├── test_health.py       # Health check API tests
│       ├── test_recipes_api.py  # Recipe CRUD & query tests
│       ├── test_sessions_api.py # Session lifecycle & action tests
│       ├── test_actions_api.py  # Actions endpoint & tool discovery tests
│       ├── test_chat_api.py     # Conversational message endpoint tests
│       └── test_seed.py         # Seed idempotency & data integrity tests
├── .env.example                 # Template for environment variables
├── .env                         # Local environment variables
├── .gitignore                   # Git ignore rules
├── alembic.ini                  # Alembic CLI configuration
├── docker-compose.yml           # PostgreSQL 16 container definition
├── pyproject.toml               # Project dependencies and pytest configuration
├── project_instructions.md      # System requirements & project milestones
├── m2.md                        # Milestone 2 requirements
├── m3.md                        # Milestone 3 requirements
├── m4.md                        # Milestone 4 requirements
├── m5.md                        # Milestone 5 requirements
├── m6.md                        # Milestone 6 requirements
└── README.md
```

---

## Conversational Cooking Interaction Architecture (Milestone 6)

The conversational pipeline bridges unstructured natural language with the authoritative domain backend:

```text
User Text Message ("Pyaz brown ho gaye hain, agla step batao")
                     │
                     ▼
[Chat API Endpoint: POST /api/v1/sessions/{session_id}/message]
                     │
                     ▼
[ChatService Orchestrator]
  ├── 1. Validates message length and non-emptiness
  ├── 2. Loads authoritative CookingSession state from database
  ├── 3. Assembles minimal cooking context & allowlisted tool schemas
  └── 4. Dispatches to BaseLLMProvider (FakeLLMProvider or OpenAILLMProvider)
                     │
                     ▼
[Structured Decision Evaluation]
  ├── A. execute_action -> Verifies action in allowlist, validates parameters
  │       │
  │       ▼
  │   [ActionExecutor] -> Invokes SessionService / RecipeService
  │       │ (Atomic DB transaction: step marked COMPLETED, next marked IN_PROGRESS)
  │       ▼
  │   [Grounded Response] -> LLM constructs response grounded in real ActionResult
  │
  ├── B. answer_question -> Answers culinary inquiry WITHOUT mutating state
  │
  └── C. clarify -> Resolves ambiguous intent WITHOUT mutating state
                     │
                     ▼
[ChatMessageResponse Envelope]
  ├── reply: Grounded conversational answer for cook
  ├── session: Freshly reloaded CookingSession state
  ├── decision_type: 'execute_action' | 'answer_question' | 'clarify'
  └── action: { name, status: 'success' | 'error', error, data }
```

### Critical Safety Invariants
1. **Asking vs. Completing**: Asking a question about a step (e.g. *"How long to fry onions?"*) answers the question directly and **never** marks the step complete.
2. **Authoritative Execution**: The LLM cannot invent success. If the backend rejects an action (e.g., out-of-order step completion or cancelled session), `action.status` reports `"error"`, the failure reason is preserved, and the reply explains the failure.
3. **No Direct DB Mutations**: The model selects from allowlisted actions only. Dynamic code execution (`eval`), SQL strings, and arbitrary methods are prohibited.

---

## LLM Provider Abstraction & Configuration

### Primary Provider: Google Gemini (`gemini-2.5-flash`)
- **SDK**: `google-genai>=1.0.0` (Official Google GenAI SDK)
- **Model**: `gemini-2.5-flash` (or `gemini-1.5-flash` / `gemini-2.0-flash`)
- **Reason**: Native JSON structured outputs, speed, multilingual accuracy for Urdu and English code-switching, and generous API tier.

### Environment Variables
Configure provider settings in `.env`:

```ini
# LLM Provider Configuration ('gemini', 'fake', or 'openai')
LLM_PROVIDER=gemini         # Set to 'gemini' for real Gemini API, or 'fake' for offline testing
LLM_MODEL=gemini-2.5-flash  # Target Gemini model identifier
GEMINI_API_KEY=AIzaSy...    # Your Google Gemini API Key
OPENAI_API_KEY=             # Optional alternative provider
LLM_TIMEOUT_SECONDS=30.0    # Maximum timeout for provider requests
LLM_MAX_RETRIES=2           # Bounded retries for transient errors
LLM_MAX_MESSAGE_LENGTH=1000 # Inbound message character ceiling
```

### Running Without an LLM Key
By default or when `LLM_PROVIDER=fake` is configured, the application runs **100% offline with zero cost and no external API credentials**, using a deterministic heuristic provider that understands completion, skipping, culinary questions, and code-switching cues.

---

## Conversational API Endpoint: Examples

### Endpoint
`POST /api/v1/sessions/{session_id}/message`

### 1. Step Completion
- **Request**:
```json
{
  "message": "Step 1 is done, onions are nicely browned."
}
```
- **Response (`200 OK`)**:
```json
{
  "reply": "Step marked completed! Next up: Step 2 - Add chicken, ginger-garlic paste, and spices.",
  "session": {
    "id": 1,
    "recipe_name": "Chicken Biryani",
    "status": "ACTIVE",
    "current_step_number": 2,
    "servings": 6,
    "steps": [
      {
        "step_number": 1,
        "instruction": "Slice onions and fry until golden brown.",
        "status": "COMPLETED"
      },
      {
        "step_number": 2,
        "instruction": "Add chicken, ginger-garlic paste, and spices.",
        "status": "IN_PROGRESS"
      }
    ]
  },
  "decision_type": "execute_action",
  "action": {
    "name": "complete_step",
    "status": "success",
    "error": null,
    "data": { ... }
  }
}
```

### 2. Asking About a Step (Zero Mutation)
- **Request**:
```json
{
  "message": "How long should I fry the onions for?"
}
```
- **Response (`200 OK`)**:
```json
{
  "reply": "Browning onions caramelizes natural sugars, creating a rich base flavor for the gravy.",
  "session": {
    "id": 1,
    "status": "ACTIVE",
    "current_step_number": 1
  },
  "decision_type": "answer_question",
  "action": null
}
```

### 3. Clarification on Ambiguity (Zero Mutation)
- **Request**:
```json
{
  "message": "Chicken daal diya"
}
```
- **Response (`200 OK`)**:
```json
{
  "reply": "Did you just add the ingredient to the pan, or has this cooking step finished completely?",
  "session": {
    "id": 1,
    "status": "ACTIVE",
    "current_step_number": 1
  },
  "decision_type": "clarify",
  "action": null
}
```

### 4. Failed Action Handling
- **Request** (attempting out-of-order completion):
```json
{
  "message": "I finished step 4!"
}
```
- **Response (`200 OK`)**:
```json
{
  "reply": "Action could not be completed: Step 4 is not the current active step (current active step is 1).",
  "session": {
    "id": 1,
    "status": "ACTIVE",
    "current_step_number": 1
  },
  "decision_type": "execute_action",
  "action": {
    "name": "complete_step",
    "status": "error",
    "error": "Step 4 is not the current active step (current active step is 1).",
    "data": null
  }
}
```

---

## Running Automated Tests

Run the full pytest suite:

```powershell
.venv\Scripts\pytest -v
```

*All 109 unit and integration tests run against an isolated in-memory SQLite database configured with strict foreign keys and transactional rollbacks.*

### Running Live Provider Smoke Test (Optional)
To run live integration tests against OpenAI:

```powershell
$env:OPENAI_API_KEY="sk-..."
.venv\Scripts\pytest -v -k test_live_openai_smoke_test
```

---

## Known Limitations

- **Text-Only**: Voice input/output (STT/TTS) and Android audio streams are deferred to later milestones.
- **Language Support Nuance**: While prompt guidelines instruct the model on Urdu and Roman Urdu code-switching, full support for regional dialects requires live evaluation datasets.
- **Provider Latency**: Responses through external LLMs are bounded by `LLM_TIMEOUT_SECONDS` (default: 30s) and internet connectivity.

---

## Development Roadmap & Milestones

1. [x] **Milestone 1**: Project initialization, backend structure, configuration, health endpoint, test verification.
2. [x] **Milestone 2**: Database layer and recipe domain models (SQLAlchemy 2.x, Alembic, Docker Compose, Pydantic schemas, seed script).
3. [x] **Milestone 3**: Recipe REST API implementation (List, Detail by ID, Detail by Slug, Steps, Create, Transactional Rollback).
4. [x] **Milestone 4**: Deterministic cooking session engine (Session lifecycle, step transitions, history preservation, cancellation, optimistic concurrency).
5. [x] **Milestone 5**: Cooking tools and action validation (Provider-independent action schemas, allowlisted registry, safe executor, structured ActionResult/ActionError envelope, development API endpoint).
6. [x] **Milestone 6**: LLM provider abstraction & structured action integration (Provider interface, fake provider, OpenAI adapter, decision schemas, prompts, chat orchestrator, `POST /sessions/{id}/message`, 109 passing tests).
7. [ ] **Milestone 7**: Advanced cooking assistant features (voice pipeline, ingredient scaling, substitution logic).
