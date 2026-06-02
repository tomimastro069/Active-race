# SDD Init Context — activia-trace (active-trace-main)

**Project**: activia-trace  
**Repository**: /home/cristian/repos_utn/Active-race/active-trace-main  
**Date**: 2026-06-02  
**Phase**: Initialization Complete

---

## Project Summary

**activia-trace** is an academic management and traceability platform for multi-tenant institutions. It operates as an orchestration layer over Moodle: consolidates grades, detects delays, manages outbound communication with approval, manages teaching teams, meetings, colloquies, honorarium liquidations, and complete audit trails. Each institution is an isolated tenant; the product name is *trace* — everything is audited.

**Status**: Foundation phase complete (C-01 through knowledge base + roadmap established). Ready for implementation sprints.

---

## Stack Detection

### Backend Stack
| Component | Technology | Details |
|-----------|------------|---------|
| **Language** | Python 3.13.5 | snake_case conventions |
| **Framework** | FastAPI ≥0.108.0 | REST API, async |
| **ORM** | SQLAlchemy 2.0+ async | Async queries, repositories pattern |
| **Migrations** | Alembic ≥1.13.1 | Schema versioning |
| **Database** | PostgreSQL + asyncpg | JSONB for flexible schemas |
| **Validation** | Pydantic v2 | DTOs, `extra='forbid'` |
| **Auth** | JWT + Argon2id | Access tokens + refresh rotation |
| **Encryption** | AES-256 | PII/secrets at rest |
| **Background Jobs** | Async worker | Communication queue |
| **Integrations** | Moodle WS + N8N | External orchestration |
| **Observability** | OpenTelemetry | Structured JSON logs |
| **Testing** | pytest + pytest-asyncio + httpx | Unit/integration/E2E (E2E pending) |

**Detected from**: `backend/pyproject.toml`, `backend/app/`, `backend/tests/conftest.py`

### Frontend Stack
| Component | Status |
|-----------|--------|
| Framework | Planned: React 18 + TypeScript (C-21) |
| State | Planned: TanStack Query |
| Forms | Planned: React Hook Form + Zod |
| Styling | Planned: Tailwind CSS |
| Bundler | Planned: Vite |
| **Current Status** | ❌ Not yet in repository |

### Infrastructure
| Component | Technology |
|-----------|-----------|
| Containers | Docker + docker-compose |
| Deploy | Easypanel |
| CI/CD | (Not yet detected — likely GitHub Actions) |

---

## Project Structure (Detected)

```
active-trace-main/
├── .atl/                           # [NEW] Artifact registry
│   ├── skill-registry.md           # [NEW] Active skills inventory
│   └── testing-capabilities.md     # [NEW] Test framework config
├── .agents/skills/                 # Project agent skills
├── .claude/skills/                 # Project Claude skills
├── .engram/                        # Persistent memory (Engram)
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI entry
│   │   ├── api/                    # Route handlers
│   │   ├── core/                   # Config, security
│   │   ├── models/                 # SQLAlchemy ORM
│   │   ├── repositories/           # Data access layer
│   │   ├── schemas/                # Pydantic DTOs
│   │   ├── services/               # Business logic
│   │   ├── integrations/           # Moodle, N8N
│   │   └── workers/                # Background jobs
│   ├── tests/
│   │   ├── conftest.py             # Fixtures (env, DB, session)
│   │   ├── test_*.py               # 11 test files
│   │   └── ...                     # Unit + integration tests
│   └── pyproject.toml              # Python deps, pytest config
├── docs/
│   ├── ARQUITECTURA.md             # Technical architecture
│   ├── PRD.md                      # Product requirements
│   └── ...
├── knowledge-base/                 # [CORE] Domain knowledge
│   ├── 01_vision_y_objetivos.md
│   ├── 02_descripcion_general.md
│   ├── ...
│   └── 11_historias_de_usuario.md  # User stories
├── openspec/
│   ├── specs/                      # Capability specs
│   ├── changes/                    # Change artifacts
│   └── [NO config.yaml yet]
├── AGENTS.md                       # Agent instructions
├── CLAUDE.md                       # Claude instructions (copy)
├── CHANGES.md                      # Implementation roadmap (24 changes)
├── skills-lock.json                # Locked skill versions
├── .env.example                    # Environment template
└── docker-compose.yml              # Local dev environment
```

---

## Testing Capabilities (Detected)

### Test Framework
- ✅ **Runner**: pytest ≥7.4.0
- ✅ **Async Support**: pytest-asyncio ≥0.23.0 (auto mode)
- ✅ **Integration Layer**: Real PostgreSQL (async), no DB mocks
- ✅ **HTTP Client**: httpx (async, for API tests)

### Test Layers
| Layer | Status | Tool | Files |
|-------|--------|------|-------|
| **Unit** | ✅ Available | pytest fixtures | `test_config.py`, `test_encryption.py` |
| **Integration** | ✅ Available | async DB fixtures | `test_repository.py`, `test_tenant_models.py` |
| **E2E** | ❌ Pending | Playwright (planned) | Will add after C-21 |

### Coverage
- **Target**: ≥80% lines, ≥90% business rules
- **Tool**: pytest-cov
- **Command**: `python3 -m pytest backend/tests/ --cov=app --cov-report=html`

### Quality Tools
| Tool | Status | Command |
|------|--------|---------|
| Linter (ruff) | ✅ Available | `ruff check app/` |
| Type checker | ✅ Available | Pydantic v2 (runtime) |
| Formatter (ruff) | ✅ Available | `ruff format app/` |

### Strict TDD Mode
- **Status**: ✅ **ENABLED**
- **Rule**: All new production code must follow test-first cycle (RED → GREEN → TRIANGULATE → REFACTOR)
- **Enforcement**: Violations fail code review

---

## Persistence & Registry Status

### Artifacts Created (SDD Init Phase)

✅ **Skill Registry** → `.atl/skill-registry.md`
  - 35+ skills catalogued
  - Indexed by tier (Core, OPSX, Foundation, Specialized, Future)
  - Includes activation rules and conventions

✅ **Testing Capabilities** → `.atl/testing-capabilities.md`
  - Complete test runner configuration
  - Test layer inventory (unit, integration, E2E pending)
  - Coverage gates and TDD enforcement rules
  - Quick-start guide

✅ **SDD Context** → `.atl/sdd-init-context.md` (this file)
  - Stack detection summary
  - Project structure
  - Governance levels
  - Blockers & open questions

### Persistence Mode

**Active**: Hybrid mode (OPSX + Engram)
- OpenSpec directory exists: ✅ `/home/cristian/repos_utn/Active-race/active-trace-main/openspec/`
- Engram available: ✅ (persistent memory enabled)
- Registry persisted: ✅ (Engram + `.atl/skill-registry.md`)

---

## Governance Levels (Agent Autonomy)

**Decision Gate**: Before any significant work, identify the governance level.

| Level | Domains | Behavior |
|-------|---------|----------|
| **CRÍTICO** | Auth, multi-tenancy, RBAC, audit log, liquidations, core models | Analysis only. NO code written without explicit human approval. |
| **ALTO** | Config files, file injection, backup/restore | Propose → wait for review → write |
| **MEDIO** | Business logic, domain adapters, pipelines | Implement with checkpoints; surface non-obvious decisions |
| **BAJO** | Simple CRUDs, pages, catalogs, type definitions, read-only utils | Full autonomy if tests pass |

**Applied to active-trace**:
- 🔴 **CRÍTICO**: Tenant filtering, auth endpoints (C-03, C-04), audit log (C-05)
- 🟡 **ALTO**: Import pipeline (C-02), structure definitions (C-06)
- 🟠 **MEDIO**: Dashboard (C-07), messaging (C-09), reporting (C-11)
- 🟢 **BAJO**: Utility endpoints, read-only catalogs

---

## Known Blockers & Open Questions

> ⚠️ **DO NOT CODE** these until blockers are resolved:

### Critical Blockers (High Priority)

**PA-01**: Catálogo de Materias — *Materia vs InstanciaDictado*
- **Blocks**: C-06 (Structure), C-02 (Import)
- **Impact**: CRITICAL — defines core data model
- **Status**: ❌ OPEN

**PA-07**: Cohortes ↔ Carrera (many-to-many relationship)
- **Blocks**: C-06 (Structure)
- **Impact**: CRITICAL — affects student grouping
- **Status**: ❌ OPEN

**PA-22/PA-23**: Plus Keys & Liquidation Accumulation
- **Blocks**: C-18 (Liquidations)
- **Impact**: HIGH — affects financials
- **Status**: ❌ OPEN

**PA-25**: NEXO Role Semantics
- **Blocks**: C-04 (RBAC), C-03 (Auth)
- **Impact**: HIGH — authorization model depends on it
- **Status**: ❌ OPEN

### See Also
- Full list: `knowledge-base/10_preguntas_abiertas.md`
- Constraints: `knowledge-base/09_decisiones_y_supuestos.md`

---

## Conventions & Rules (Hard Rules)

### Must Enforce
1. ✅ **No builds** without explicit user request
2. ✅ **No commits** without explicit user request
3. ✅ **Conventional Commits**: `type(scope): message` (no Co-Authored-By)
4. ✅ **Pydantic `extra='forbid'`**: All schemas reject unknown fields
5. ✅ **snake_case** in Python; **PascalCase** in React
6. ✅ **Identity from JWT**, never from request params
7. ✅ **Multi-tenancy row-level**: `tenant_id` in every table
8. ✅ **RBAC fine-grained**: `modulo:accion`, fail-closed
9. ✅ **Secrets AES-256**, passwords Argon2id
10. ✅ **Soft delete always**: No hard deletes
11. ✅ **≤500 LOC/file** (backend), <200 LOC (React)
12. ✅ **Strict TDD**: Test first, minimum code, triangulate

---

## Next Steps

1. ✅ **SDD Init Complete**
   - Stack detected and documented
   - Testing capabilities catalogued
   - Skill registry built
   - Strict TDD mode enabled

2. 📋 **Ready for First Change Implementation**
   - Next: `/opsx:apply C-01-foundation-setup` (or identify blocking questions first)
   - Load `python-testing-patterns` + `fastapi-templates` before starting
   - Follow Strict TDD cycle for all new code

3. 🔧 **Immediate Blockers to Resolve**
   - Review `knowledge-base/10_preguntas_abiertas.md` (especially PA-01, PA-07, PA-22, PA-25)
   - Propose meetings to close ambiguities before C-06, C-18 implementation
   - Document decisions back to knowledge base

4. 📚 **Orientation for New Agents**
   - Read: `AGENTS.md` (this project's instructions)
   - Read: Relevant KB files from `knowledge-base/`
   - Load: Appropriate skills before writing code
   - Verify: No commits/builds without user request

---

## Checklist: SDD Init Complete ✅

- ✅ Stack detected (Python 3.13, FastAPI, SQLAlchemy async, pytest)
- ✅ Testing framework catalogued (unit, integration, TDD enabled)
- ✅ Skill registry built (`.atl/skill-registry.md`)
- ✅ Testing capabilities documented (`.atl/testing-capabilities.md`)
- ✅ Governance levels identified
- ✅ Conventions & hard rules extracted
- ✅ Blockers documented
- ✅ Project structure mapped
- ✅ Persistence ready (Engram + OpenSpec hybrid mode)

---

**Status**: ✅ SDD Initialization Complete | **Date**: 2026-06-02 | **Ready for Implementation**: YES
