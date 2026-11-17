# Scheme Navigator — Complete Product Architecture & Systems Blueprint

**Document Version:** 2.0.0 (Master Enterprise Baseline)  
**Date:** November 12, 2026  
**Target Territory:** Maharashtra, India  

---

## 1. System Overview & Architectural Tenets

**Maharashtra Scheme Navigator** is a high-assurance, evidence-backed digital public infrastructure platform. It transforms fragmented government welfare discovery and application preparation into a seamless, dignified citizen experience.

```
+----------------------------------------------------------------------------------------------------+
|                                      CITIZEN TOUCHPOINTS                                           |
|   [Find Schemes for Me]         [Explore Schemes Library]        [Prepare My Application]          |
|   (Guided AI Interview)         (Independent Discovery)          (Document Prep & Roadmap)         |
+----------------------------------------------------------------------------------------------------+
                                                 |
                                                 v HTTPS / TLS 1.3
+----------------------------------------------------------------------------------------------------+
|                                    SECURITY & GATEWAY LAYER                                        |
|   - WAF & Rate Limiter (Sliding Window / Redis Token Bucket)                                       |
|   - Stateless HMAC-SHA256 Session Ownership Authentication                                        |
|   - Security Headers (HSTS, CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff)           |
+----------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+----------------------------------------------------------------------------------------------------+
|                                 FASTAPI APPLICATION SERVICES                                       |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+    |
|  |   Rule Engine      |  | LangGraph Dialogue |  | Document Pre-Audit |  |  Prerequisite DAG  |    |
|  | (Deterministic 3VL)|  | (Stateful Chatbot) |  | (Vision / OCR)     |  | (Topological RTS)  |    |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+    |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+    |
|  | Source Registry    |  |  Channel Registry  |  | Lifecycle Monitor  |  | Reviewer Workspaces|    |
|  | (35+ MH Depts)     |  | (Safe Hand-Off)    |  | (Hash & Suspension)|  | (Human-in-the-Loop)|    |
|  +--------------------+  +--------------------+  +--------------------+  +--------------------+    |
+----------------------------------------------------------------------------------------------------+
                                                 |
                                                 v
+----------------------------------------------------------------------------------------------------+
|                                   DATA & PERSISTENCE TIERS                                         |
|  [Relational DB: PostgreSQL / SQLite WAL]   [Distributed Cache / Lock: Redis]                      |
|  [Encrypted Object Storage: MinIO / S3]     [Air-Gapped Source Repository: SHA-256 Lineage]        |
+----------------------------------------------------------------------------------------------------+
```

---

## 2. Core Subsystem Architecture

### 2.1 Deterministic Three-Valued Rule Engine (`src/scheme_navigator/services/rule_engine.py`)
- Evaluates citizen profiles against formalized scheme conditions using Kleene three-valued logic (`TRUE`, `FALSE`, `UNKNOWN`).
- Generates four deterministic eligibility outcomes:
  - `ELIGIBLE`: All statutory conditions evaluate strictly to `True`.
  - `INELIGIBLE`: At least one condition evaluates to `False`.
  - `NEEDS_INFORMATION`: Missing information (`UNKNOWN`); missing fields are tracked explicitly without assuming rejection.
  - `NEEDS_REVIEW`: High-discretion conditions requiring human administrative assessment.
- Pure deterministic execution: LLMs are strictly forbidden from modifying condition outcomes.

### 2.2 LangGraph Conversational Interview Engine (`src/scheme_navigator/agents/interviewer.py`)
- Guides citizens through minimal, progressive questioning.
- Tracks citizen state via `InterviewSessionStore` backed by persistent SQLite / PostgreSQL.
- Dynamically derives next questions based on information gaps, pruning redundant inquiries.

### 2.3 Prerequisite Dependency Planner (`src/scheme_navigator/planner/dag.py`)
- Constructs a directed acyclic graph (DAG) of application dependencies using NetworkX.
- Resolves certificate prerequisites (e.g. Domicile $\rightarrow$ Income $\rightarrow$ Non-Creamy Layer).
- Computes critical path timelines using statutory limits under the Maharashtra Right to Services (RTS) Act 2015.

### 2.4 Document Pre-Audit Engine (`src/scheme_navigator/documents/audit.py`)
- Validates file security (magic bytes, MIME type, size limits $\le 10$MB).
- Extracts structured attributes (name, annual income, certificate date, issuing authority) using configured vision extractors.
- Confidence scoring: Extractions with `overall_confidence < 0.75` automatically route to `DocumentReviewStore` for human reviewer verification.
- Enforces an explicit machine extraction disclaimer: pre-audits do not constitute official government document verification.

### 2.5 Source Registry & Lifecycle Monitor (`src/scheme_navigator/source_registry/`)
- Tracks 35+ departments, corporations, central schemes, and local bodies.
- Maintains SHA-256 digests over source documents to detect amendments and supersessions.
- Triggers publication suspension if unverified changes compromise citizen guidance safety.

---

## 3. Data Tier & Persistence Architecture

| Environment | Relational Persistence | Session & Rate Limiting | Document Staging |
|---|---|---|---|
| **Local Demonstration** | SQLite 3.40+ in WAL mode (`interviews.sqlite3`, `document_reviews.sqlite3`, `ingestion.sqlite3`) with 10s busy timeouts. | In-memory sliding window rate limiter; in-memory thread ownership maps. | Local ephemeral staging with automated 24-hour retention purge. |
| **Enterprise Production** | PostgreSQL 16+ with row-level security (RLS), connection pooling (PgBouncer), and automated point-in-time recovery (PITR). | Redis 7+ cluster for distributed token-bucket rate limiting and session lease locking. | Encrypted S3-compatible object store (AES-256 / SSE-KMS) with strict pre-signed URLs. |

---

## 4. Security & Compliance Architecture

- **Stateless HMAC-SHA256 Session Ownership:** Prevents cross-citizen session hijacking in shared computing environments (e.g. Gram Panchayat cyber kiosks or CSCs).
- **Zero-PII Storage Invariant:** Browser storage (`localStorage`) is restricted to a 7-key snapshot allowlist containing zero names, Aadhaar numbers, or document contents.
- **Air-Gapped Source Repository:** Documented source lineage with cryptographic digests guarantees reproducible, untampered legal rules.
- **SSRF Connection Pinning:** Internal microservices are shielded against SSRF attacks through domain whitelisting and loopback isolation.
