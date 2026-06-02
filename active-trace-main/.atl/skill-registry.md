# Skill Registry — activia-trace (active-trace-main)

**Generated**: 2026-06-02 | **Project**: activia-trace | **Stack**: Python 3.13 + FastAPI + PostgreSQL + React 18 (planned)

## Active Skills Registry

This registry catalogs all available skills for the active-trace-main project, indexed by availability tier and project role.

### Tier 1: Core Development (Mandatory)

These skills are essential for the project's primary workflow.

| Skill | Location | Role | Trigger Pattern |
|-------|----------|------|-----------------|
| **test-driven-development** | `.config/opencode/skills` | Backend (TDD) | Strict TDD mode, test-first workflow |
| **python-testing-patterns** | `.config/opencode/skills` | Backend (QA) | pytest, unit/integration/E2E test design |
| **fastapi-templates** | `.config/opencode/skills` | Backend (Core) | FastAPI routes, schemas, dependency injection |
| **postgresql-table-design** | `.config/opencode/skills` | Backend (DB) | SQLAlchemy models, migrations, Alembic |
| **api-security-best-practices** | `.config/opencode/skills` | Backend (Security) | JWT, RBAC, multi-tenancy, auth |
| **code-review-excellence** | `.config/opencode/skills` | Transversal (QA) | PR review, quality gates |

### Tier 2: OPSX Workflow (Foundation)

These skills orchestrate the SDD/OpenSpec change lifecycle.

| Skill | Location | Role | Trigger Pattern |
|-------|----------|------|-----------------|
| **openspec-init** | `.config/opencode/skills` | Orchestrator | Initialize openspec/ in project |
| **openspec-explore** | `.claude/skills` | Orchestrator | `/opsx:explore`, exploratory thinking |
| **openspec-propose** | `.claude/skills` | Orchestrator | `/opsx:propose`, create change artifacts |
| **openspec-apply-change** | `.claude/skills` | Executor | `/opsx:apply`, implement tasks |
| **openspec-verify** | `.config/opencode/skills` | Executor | Verify implementation vs specs |
| **openspec-archive-change** | `.claude/skills` | Executor | Archive completed change |

### Tier 3: Foundation & Knowledge Base

Bootstrap skills for project setup.

| Skill | Location | Role | Trigger Pattern |
|-------|----------|------|-----------------|
| **kb-creator** | `.config/opencode/skills` | Orchestrator | Build knowledge-base/ from docs |
| **roadmap-generator** | `.config/opencode/skills` | Orchestrator | Generate CHANGES.md roadmap |
| **agents-md-generator** | `.config/opencode/skills` | Orchestrator | Generate AGENTS.md from KB |
| **jr-orchestrator** | `.config/opencode/skills` | Orchestrator | Foundation flow: init → kb → roadmap → rules |

### Tier 4: Specialized Domains

Domain-specific improvements and reviews.

| Skill | Location | Role | Trigger Pattern |
|-------|----------|------|-----------------|
| **branch-pr** | `.config/opencode/skills` | Executor | Create issue-first PRs |
| **chained-pr** | `.config/opencode/skills` | Executor | Split large PRs, stacked reviews |
| **work-unit-commits** | `.config/opencode/skills` | Executor | Plan commits as review units |
| **systematic-debugging** | `.config/opencode/skills` | Transversal | Debug patterns, logs, traces |
| **postgresql-optimization** | `.config/opencode/skills` | Backend (Perf) | Query optimization, indexes |
| **comment-writer** | `.config/opencode/skills` | Transversal | Warm collaboration comments |
| **judgment-day** | `.config/opencode/skills` | Transversal | Blind dual review, fix issues |
| **cognitive-doc-design** | `.config/opencode/skills` | Transversal | Design docs, READMEs, RFCs |

### Tier 5: Future/Planned (Not yet active)

These skills are available but not yet integrated into the project workflow.

| Skill | Location | Role | Status |
|-------|----------|------|--------|
| **typescript-advanced-types** | `.config/opencode/skills` | Frontend (Types) | Planned for C-21 (frontend shell) |
| **tailwind-design-system** | `.config/opencode/skills` | Frontend (Design) | Planned for C-21 |
| **playwright-best-practices** | `.config/opencode/skills` | Frontend (E2E) | Planned for frontend E2E tests |
| **multi-stage-dockerfile** | `.config/opencode/skills` | DevOps | Available, not yet deployed |
| **go-testing** | `.config/opencode/skills` | Auxiliary | Go lang testing (not in scope) |

---

## Skill Activation Rules

### When to Load Each Skill

| Context | Skill(s) | Load Pattern |
|---------|----------|--------------|
| Starting any backend task | `python-testing-patterns` + `fastapi-templates` or `postgresql-table-design` | Load before reading code |
| Implementing a new endpoint | `fastapi-templates` + `api-security-best-practices` | Check patterns first |
| Writing model/migration | `postgresql-table-design` + `test-driven-development` | Design DB contract before code |
| Writing integration test | `python-testing-patterns` + `test-driven-development` | Use TDD + real DB, no mocks |
| Security-critical code (auth, RBAC) | `api-security-best-practices` + `code-review-excellence` | Review before writing |
| Proposing a new change | `openspec-propose` via orchestrator | Delegate to sub-agent |
| Implementing change tasks | `openspec-apply-change` via orchestrator | Delegate to executor |
| Reviewing code | `code-review-excellence` | Load before starting PR review |
| Creating commits | `work-unit-commits` + optionally `branch-pr` | Use for commit planning |

---

## Project Conventions (Derived from AGENTS.md)

### Language & Naming
- **Backend**: Python 3.13, `snake_case` for functions/vars/modules/columns
- **Frontend**: TypeScript + React 18 (planned C-21+), `PascalCase` for components
- **SQL**: PostgreSQL, JSONB for flexible schemas, soft delete always

### Code Structure
- **Backend**: Clean Architecture → Routers → Services → Repositories → Models
- **Backend file limit**: ≤500 LOC per file
- **Frontend**: Feature-based modules (features/{name}/{components,hooks,services,types,pages})
- **React components**: <200 LOC, no `any`, no class components, no CSS modules

### Quality Standards
- **Coverage**: ≥80% lines, ≥90% business logic rules
- **TDD**: Strict mode enabled (test-first for all new logic)
- **Commits**: Conventional Commits, types: feat/fix/refactor/docs/test/chore
- **No mocks of DB**: Always use real DB or ephemeral test container

### Security & Multi-Tenancy
- **Identity**: Always from JWT session, never from request params/body
- **Tenancy**: `tenant_id` in every table, repositories filter by default
- **RBAC**: Fine-grained `modulo:accion` (fail-closed, no superuser)
- **PII/Secrets**: AES-256 encryption always, passwords use Argon2id
- **Soft delete**: All deletes are logical (append-only audit trail)

### CI/CD & Testing
- **Test command**: `python3 -m pytest backend/tests/ -v` (async, real DB)
- **Linter**: ruff (Python)
- **Type checker**: mypy or built-in Pydantic v2
- **DB migrations**: Alembic, one per schema change
- **OpenTelemetry**: Instrumented for observability

---

## Blockers & Open Questions

> ⚠️ **CRITICAL**: Do NOT implement these modules without resolving their blockers:
> - **C-06** (Estructura Académica): Blocked on PA-01 (Materia vs InstanciaDictado), PA-07 (cohortes ↔ carrera)
> - **C-18** (Liquidaciones): Blocked on PA-22/PA-23 (claves de Plus, acumulación)
>
> See `knowledge-base/10_preguntas_abiertas.md` for full open questions list.

---

## Next Steps

1. **Verify test runner**: `python3 -m pytest backend/tests/ --collect-only -q` should list test files
2. **Load skills as needed**: Before any backend work, run `skill("python-testing-patterns")` or `skill("fastapi-templates")`
3. **Follow OPSX workflow**: Use `/opsx:explore`, `/opsx:propose`, `/opsx:apply`, `/opsx:archive` for changes
4. **Maintain registry**: If skills are added/removed, update this file via `skill("skill-registry")`

---

**Registry Status**: ✅ Active | **Last Updated**: 2026-06-02 | **Version**: 1.0
