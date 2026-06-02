# SDD Initialization Index — active-trace-main

**Status**: ✅ Complete | **Date**: 2026-06-02

---

## Quick Navigation

### 🎯 Start Here (New Agent or Session)

1. **Read AGENTS.md** (first 100 lines)
   - Project vision, stack, skills assignment, roadmap summary

2. **Read .atl/sdd-init-context.md** (this session's SDD context)
   - Stack detected, conventions, governance, blockers

3. **Read knowledge-base/10_preguntas_abiertas.md** (if planning implementation)
   - 4 critical blockers (PA-01, PA-07, PA-22, PA-25)

4. **Load appropriate skill** before writing code
   - Backend endpoint? → `skill("fastapi-templates")` + `skill("api-security-best-practices")`
   - DB model? → `skill("postgresql-table-design")` + `skill("test-driven-development")`
   - Test? → `skill("python-testing-patterns")`

---

## Artifact Registry (.atl/)

### 1. skill-registry.md (147 lines, 7.7 KB)

**Purpose**: Catalog all 35+ available skills, indexed by tier and role.

**Contains**:
- Tier 1: Core Development (mandatory skills)
- Tier 2: OPSX Workflow (change lifecycle skills)
- Tier 3: Foundation & KB (bootstrap skills)
- Tier 4: Specialized Domains (reviews, debugging, optimization)
- Tier 5: Future/Planned (not yet active)
- Activation matrix by task type
- Project conventions (naming, structure, quality)

**When to use**: 
- "What skill should I load?" → consult activation matrix
- "What are the project naming conventions?" → read Conventions section
- "What's blocking my implementation?" → see Blockers section

---

### 2. testing-capabilities.md (310 lines, 8.8 KB)

**Purpose**: Complete testing framework documentation with Strict TDD mode enabled.

**Contains**:
- Test runner: pytest ≥7.4.0 + pytest-asyncio
- Test layers: Unit ✅, Integration ✅, E2E ❌ (pending frontend)
- Coverage gates: ≥80% lines, ≥90% business rules
- TDD cycle (RED/GREEN/TRIANGULATE/REFACTOR) — mandatory
- Breaking TDD rules (fail code review)
- Current test suite: 11 test files
- Quick-start guide for running tests

**When to use**:
- "How do I run tests?" → see Quick Start section
- "What's the TDD cycle?" → read TDD Cycle section
- "What test infrastructure is available?" → read Test Layers section
- "How do I add a new test?" → follow TDD cycle pattern

---

### 3. sdd-init-context.md (279 lines, 11 KB)

**Purpose**: Project context, stack detection, conventions, and governance.

**Contains**:
- Stack summary (Python 3.13, FastAPI, SQLAlchemy async, PostgreSQL, pytest)
- Project structure map (directories, key files)
- Testing capabilities (runners, layers, coverage)
- Persistence & registry status (Hybrid: OPSX + Engram)
- Governance levels (CRÍTICO, ALTO, MEDIO, BAJO)
- 4 critical blockers (PA-01, PA-07, PA-22, PA-25)
- Hard rules (12 non-negotiable rules)
- Next steps for implementation

**When to use**:
- "What's the project stack?" → read Stack Detection
- "What are the hard rules?" → read Conventions & Rules
- "What's blocking implementation?" → read Blockers section
- "What's the governance level for this domain?" → read Governance Levels

---

## Memory Persistence (Engram)

All three artifacts are also saved to persistent memory for cross-session recovery:

| Observation | Title | Topic Key | Type |
|-------------|-------|-----------|------|
| 1 | SDD Init: active-trace-main | sdd-init/active-trace-main | architecture |
| 2 | Testing Capabilities | sdd/active-trace-main/testing-capabilities | config |
| 3 | Skill Registry | skill-registry/active-trace-main | config |

**Recovery**: In any session, run:
```bash
mem_search "sdd-init/active-trace-main"
```

---

## Project Structure Reference

```
active-trace-main/
│
├── .atl/                                 # ← SDD Init artifacts (NEW)
│   ├── skill-registry.md
│   ├── testing-capabilities.md
│   └── sdd-init-context.md
│
├── AGENTS.md                             # ← START HERE (project instructions)
├── CLAUDE.md                             # (copy of AGENTS.md)
├── CHANGES.md                            # 24-change roadmap
│
├── knowledge-base/                       # Domain knowledge (agnóstic of tech)
│   ├── 01_vision_y_objetivos.md         # Scope & objectives
│   ├── 02_descripcion_general.md        # System overview
│   ├── 03_actores_y_roles.md            # Auth, RBAC, perms (READ EARLY)
│   ├── 04_modelo_de_datos.md            # Entities, ERD
│   ├── 05_reglas_de_negocio.md          # Business rules (RN-XX)
│   ├── 06_funcionalidades.md            # Features by epic
│   ├── 07_flujos_principales.md         # End-to-end flows
│   ├── 08_arquitectura_propuesta.md     # Patterns & structure
│   ├── 09_decisiones_y_supuestos.md     # Closed decisions
│   ├── 10_preguntas_abiertas.md         # ⚠️ BLOCKERS (PA-01, PA-07, PA-22, PA-25)
│   └── 11_historias_de_usuario.md       # User stories
│
├── openspec/                             # OPSX workflow artifacts
│   ├── specs/                            # Capability specifications
│   ├── changes/                          # Per-change artifacts
│   └── [config.yaml missing — can be created if needed]
│
├── backend/
│   ├── pyproject.toml                    # Python deps, pytest config
│   ├── tests/
│   │   ├── conftest.py                   # Fixtures (env, DB, session)
│   │   ├── test_app_startup.py
│   │   ├── test_config.py
│   │   ├── test_database.py
│   │   ├── test_encryption.py
│   │   ├── test_health.py
│   │   ├── test_migrations.py
│   │   ├── test_observability.py
│   │   ├── test_placeholders.py
│   │   ├── test_repository.py
│   │   └── test_tenant_models.py
│   └── app/
│       ├── main.py
│       ├── api/                         # Route handlers
│       ├── core/                        # Config, security
│       ├── models/                      # SQLAlchemy ORM
│       ├── repositories/                # Data access layer
│       ├── schemas/                     # Pydantic DTOs
│       ├── services/                    # Business logic
│       ├── integrations/                # Moodle, N8N
│       └── workers/                     # Background jobs
│
├── docs/                                 # Technical documentation
│   ├── ARQUITECTURA.md                   # Clean Architecture, security
│   └── PRD.md                            # Product requirements
│
└── .claude/, .agents/, .engram/          # Skill/memory directories
```

---

## Workflow: Using SDD Artifacts

### For Backend Development

1. **Before writing any code**:
   ```bash
   skill("python-testing-patterns")  # Load test patterns
   skill("fastapi-templates")         # Load FastAPI patterns
   ```

2. **Write a failing test FIRST** (RED phase):
   ```python
   @pytest.mark.asyncio
   async def test_new_feature(db_session):
       result = await repository.new_method()
       assert result is not None
   ```

3. **Write minimum code to pass** (GREEN phase):
   ```python
   async def new_method(self):
       return "implement me"
   ```

4. **Triangulate** (add 2+ test cases), then **refactor**.

5. **Reference** `.atl/testing-capabilities.md` for:
   - Coverage commands
   - Running specific tests
   - Understanding test layers

### For Change Planning

1. **Check blockers**: Read `knowledge-base/10_preguntas_abiertas.md`
2. **Identify change**: Find `C-XX-name` in `CHANGES.md`
3. **Propose change**: `/opsx:propose C-XX-name` (orchestrator delegates)
4. **Implement tasks**: `/opsx:apply C-XX-name` (with loaded skills)
5. **Archive**: `/opsx:archive C-XX-name` (after verification)

### For Code Review

1. Load: `skill("code-review-excellence")`
2. Check: TDD cycle evidence (from `.atl/testing-capabilities.md`)
3. Verify: All hard rules satisfied (from `.atl/sdd-init-context.md`)
4. Enforce: No CRÍTICO-level code without human approval

---

## Governance Quick Reference

**Before implementing**, identify the **governance level** of your domain:

| Level | Example Domains | Rule |
|-------|-----------------|------|
| 🔴 **CRÍTICO** | Auth, multi-tenancy, RBAC, audit, core models | Analysis only; NO code without approval |
| 🟡 **ALTO** | Config, file injection, backup/restore | Propose → review → write |
| 🟠 **MEDIO** | Business logic, integrations, pipelines | Implement with checkpoints |
| 🟢 **BAJO** | Simple CRUDs, pages, catalogs, types | Full autonomy if tests pass |

For CRÍTICO domains, describe your plan first and wait for approval before writing code.

---

## Four Critical Blockers

**STOP before implementing these changes**:

1. **PA-01**: Materia vs InstanciaDictado
   - Blocks: C-06, C-02
   - Impact: Core data model definition

2. **PA-07**: Cohortes ↔ Carrera (relationship)
   - Blocks: C-06
   - Impact: Student grouping semantics

3. **PA-22/PA-23**: Plus Keys & Liquidation Accumulation
   - Blocks: C-18
   - Impact: Financial calculations

4. **PA-25**: NEXO Role Semantics
   - Blocks: C-04, C-03
   - Impact: Authorization model

**Action**: Resolve these in `knowledge-base/10_preguntas_abiertas.md` before touching affected changes.

---

## Checklists

### Starting a New Task
- [ ] Read relevant KB files (from `knowledge-base/`)
- [ ] Check `.atl/sdd-init-context.md` for governance level
- [ ] Load appropriate skills
- [ ] Write failing test FIRST (TDD RED phase)
- [ ] Verify test runs and fails as expected
- [ ] Write minimum code to pass (GREEN phase)
- [ ] Add 2+ test cases (TRIANGULATE)
- [ ] Refactor with tests green
- [ ] Reference blockers if relevant

### Adding a New Skill
- [ ] Document in `.atl/skill-registry.md` (Tier, activation rules)
- [ ] Update topic_key in Engram: `skill-registry/active-trace-main`
- [ ] Notify team of new activation rules

### End of Session
- [ ] Save progress to Engram with appropriate topic_key
- [ ] Include TDD cycle evidence (if applicable)
- [ ] Note any blockers or discoveries
- [ ] Update `.atl/` if conventions/governance changed

---

## Support & Recovery

### Lost Context?
```bash
mem_search "sdd-init/active-trace-main"
mem_search "testing-capabilities"
mem_search "skill-registry"
```

### Need Full Context?
```bash
mem_context project:active-trace-main
```

### Need to Update Registry?
Load the skill-registry skill:
```bash
skill("skill-registry")
```

---

## Status Summary

✅ **SDD Initialization Complete**
- Stack detected: Python 3.13 + FastAPI + PostgreSQL + pytest
- Strict TDD Mode: ENABLED
- Skills: 35+ catalogued and indexed
- Testing: Unit ✅, Integration ✅, E2E ❌ (pending frontend)
- Governance: Levels assigned to all domains
- Blockers: 4 critical blockers identified
- Artifacts: 3 files (736 lines) + 3 Engram observations

**Ready for**: Implementation sprints, new task allocation, OPSX workflow

---

**Generated**: 2026-06-02 | **Version**: 1.0 | **Status**: ✅ ACTIVE
