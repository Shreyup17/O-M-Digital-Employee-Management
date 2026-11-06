# Autonomous AI Knowledge Orchestrator for Enterprise O&M

### *Topic 6: Construction of Digital Employees for Operations and Maintenance*



**Enterprise Baseline:** China Telecom (Guangdong Company) Course Design Specification

---

## 📌 Project Overview

In enterprise IT and telecommunications frameworks, Operations and Maintenance (O&M) teams handle high volumes of repetitive inquiries, document lookups, and account provisioning workflows. Traditional manual approaches cause ticket bottlenecks, prolonged downtime, and fragmented knowledge retention.

This project implements an **Autonomous AI Knowledge Orchestrator and Digital Employee Management Platform**. Combining **Retrieval-Augmented Generation (RAG)**, **Robotic Process Automation (RPA)** principles, and a **Full-Stack Administrative Portal**, the platform provides:

1. **Automated Self-Service Technical Q&A:** Grounded retrieval over local, multi-source enterprise manuals, eliminating hallucinations and preserving data privacy.


2. **Personnel Account Management Console (CRUD):** A role-based administration portal to create, query, update, and freeze O&M personnel accounts.


3. **The Smart Feedback Loop (Self-Improving RAG):** An automated fallback mechanism that catches AI failure states, routes unresolved queries to a human engineering queue, and dynamically re-vectorizes human-provided solutions into the vector database via REST APIs.



---

## 🏗️ System Architecture

The platform follows a decoupled, multi-tier software engineering architecture designed to operate reliably within resource-constrained environments (4-Core CPU, 8GB RAM):

```
+---------------------------------------------------------------------------------------+
|                               PRESENTATION TIER (UI)                                  |
|   Unified Three-Panel Command Center Dashboard (HTML5, Tailwind CSS, Async Fetch API) |
+------------------------+----------------------------------+---------------------------+
                         |                                  |
                         v                                  v
+---------------------------------------------------------------------------------------+
|                                   LOGIC TIER (API)                                    |
|                      Python FastAPI Gateway (main.py, Uvicorn)                        |
|   * Personnel CRUD Endpoints              * Regex Cleansing & Exception Interceptor   |
|   * Issue Logging & Ticket Escalation     * Sync Orchestrator & Rate Circuit Breakers |
+------------------------+----------------------------------+---------------------------+
                         |                                  |
         +---------------+                                  +---------------+
         v                                                                  v
+----------------------------------+              +-------------------------------------+
|        RELATIONAL DATA TIER      |              |          AI & VECTOR RAG TIER       |
|    SQLAlchemy ORM + SQLite DB    |              | AnythingLLM Desktop + Local Storage |
|  * OMAccount (User profiles)     |              |  * Vector Index (LanceDB)           |
|  * IssueRecord (Escalations)     |              |  * Knowledge Chunking & Retrieval   |
+----------------------------------+              +------------------+------------------+
                                                                     |
                                                                     v
                                                  +-------------------------------------+
                                                  |        LOCAL / HYBRID LLM RUNNER    |
                                                  |   Ollama Engine (DeepSeek / Llama)  |
                                                  |   * Localhost or Google Colab T4    |
                                                  |     via Localtunnel/Ngrok Bridge    |
                                                  +-------------------------------------+

```

### Three-Panel Command Center Dashboard Layout

* **Left Panel — Personnel Directory & Management (CRUD):** View, register, filter, and freeze staff accounts.


* **Center Panel — Automated O&M Support Portal:** Conversational self-service assistant powered by RAG.


* **Right Panel — Human Escalation & Knowledge Sync Queue:** Lists unresolved questions flagged with `is_unanswered = True`. Technicians enter resolutions and trigger one-click re-indexing.



---

## 🔄 The Smart Feedback Loop

```
[ User Query ]
      │
      ▼
[ FastAPI Portal ] ──(REST API)──► [ AnythingLLM + Vector DB ]
      │                                       │
      │◄─────── Streamed AI Response ─────────┘
      │
[ Regex Cleansing & Anomaly Interception ]
      │
      ├─► Confident Match ──► [ Return Context-Grounded Answer to User ]
      │
      └─► Failure Detected ("I don't know", "Not mentioned", Timeout)
            │
            ├─► Set `is_unanswered = True` in SQLite (`IssueRecord`)
            ├─► Push Ticket to Right-Hand Escalation Panel
            │
            ▼
      [ Human O&M Technician Submits Solution ]
            │
            ├─► Set `is_unanswered = False` in SQLite
            └─► POST `/update-embeddings` API to AnythingLLM
                  │
                  ▼
            [ Knowledge Base Incrementally Re-indexed ]
            (Future queries are answered autonomously!)

```

---

## 🛠️ Technology Stack & Libraries

| Domain / Layer | Technology / Library | Role & Technical Justification |
| --- | --- | --- |
| **Backend Framework** | **FastAPI** | Asynchronous, high-throughput micro-framework capable of concurrent API calls between UI, database, and LLM services without blocking.

 |
| **ASGI Server** | **Uvicorn** | High-performance production ASGI web server to serve FastAPI asynchronously.

 |
| **Database & ORM** | **SQLAlchemy** | Decouples application logic from raw SQL, providing type safety, data integrity, and session handling.

 |
| **Relational Storage** | **SQLite (`om_management.db`)** | Serverless, zero-configuration embedded database matching strict sandbox isolation guidelines.

 |
| **API Client** | **Requests** | Executes synchronous HTTP communications with AnythingLLM developer endpoints.

 |
| **RAG Orchestrator** | **AnythingLLM** | Manages vector parsing, chunking, LanceDB embeddings, and model provider routing.

 |
| **Local LLM Engine** | **Ollama** | Local runtime hosting quantized inference models (`deepseek-r1`, `llama3.2`) with low RAM footprints.

 |
| **Cloud-GPU Bridge** | **Localtunnel / Ngrok** | Encrypted reverse proxy tunnel mapping remote GPU instances (e.g., Google Colab) to local orchestrators.

 |
| **Frontend UI** | **HTML5, Tailwind CSS, JS (Fetch)** | Lightweight, unified command-center interface without external frontend build pipelines.

 |

---

## 📂 Repository File Structure

```
├── static/
│   └── index.html             # Three-panel dashboard (Admin CRUD, Chat, Escalation)
├── trainData/                 # Domain documents (Network logs, manuals, FAQs)
├── database.py                # SQLAlchemy engine initialization and session maker
├── models.py                  # Database schemas (OMAccount, IssueRecord)
├── main.py                    # FastAPI application, CRUD routes, RPA sync pipeline
├── requirements.txt           # Project package dependencies
├── .gitignore                 # Excludes .venv, *.db, cache, and sensitive tokens
├── O&M FAQs.docx / .pdf       # Enterprise baseline operational guidelines
└── om_management.db           # SQLite database instance (generated on startup)

```

---

## 🚀 Getting Started

### 1. Prerequisites

* Python 3.10+
* [Ollama](https://ollama.com/) (or Google Colab with GPU runtime)
* [AnythingLLM Desktop](https://anythingllm.com/)

### 2. Environment Setup

Clone the repository and install dependencies:

```bash
git clone https://github.com/Shreyup17/O-M-Digital-Employee-Management.git
cd O-M-Digital-Employee-Management

# Create and activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install required dependencies
pip install -r requirements.txt

```

### 3. Start LLM & RAG Services

1. **Start Ollama Engine:**
```bash
ollama run llama3.2
# or: ollama run deepseek-r1:8b

```


2. **Launch AnythingLLM:**
* Create workspace: `om-digital-employee` (ensure workspace slug is URL-safe).
* Set **LLM Provider** to `Ollama` (`http://localhost:11434` or your reverse-tunnel URL).
* Upload and embed documents from `trainData/`.
* Obtain your **Developer Master API Key** under Settings $\rightarrow$ Tools $\rightarrow$ Developer API.



### 4. Run the Application Backend

Start the FastAPI server:

```bash
uvicorn main:app --reload --port 8000

```

Open your browser and navigate to:

* **Web Dashboard:** `http://localhost:8000/static/index.html`
* **Swagger API Docs:** `http://localhost:8000/docs`

---

## 📡 Core API Endpoints

### Personnel Account Management (CRUD)

* `POST /accounts/` — Register a new O&M employee with hashed credentials.


* `GET /accounts/` — Query personnel accounts with multi-field filters (`id`, `name`, `department`).


* `PUT /accounts/{id}` — Update staff profile information.


* `DELETE /accounts/{id}` — Execute a soft delete/freeze (`is_active = False`) to preserve historical audit trails.



### Knowledge Retrieval & Smart Feedback Loop

* `POST /query-portal/` — Forwards user query to RAG pipeline; runs regex anomaly check and logs unanswered issues.


* `GET /issues/` — Retrieves all unresolved tickets (`is_unanswered = True`) for human review.


* `PUT /resolve-issue/{id}` — Commits human solution to SQLite and dispatches `/update-embeddings` API payload to AnythingLLM.



---

## 💡 Engineering Skills & Competencies Demonstrated

* **Architectural Separation of Concerns (SoC):** Cleanly decoupling presentation, asynchronous application logic, relational persistence, and vector RAG components.


* **Defensive Engineering & Exception Interception:** Utilizing deterministic regex pattern matching to prevent silent model failures and catch knowledge gaps.


* **Concurrency & Race Condition Handling:** Employing rate-limiting buffers and asynchronous polling to prevent SQLite file collisions and vector database write locks during embedding updates.


* **Hardware & Compute Budgeting:** Quantization profiling (GGUF), edge-compute optimization, and designing hybrid cloud reverse-tunnel topologies to satisfy rigid enterprise baseline specifications.
