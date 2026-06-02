# Testing Capabilities — activia-trace (active-trace-main)

**Project**: activia-trace-main  
**Stack**: Python 3.13 + FastAPI + PostgreSQL + async/SQLAlchemy 2.0  
**Detected**: 2026-06-02  
**Strict TDD Mode**: ✅ **ENABLED**

---

## Executive Summary

The project has a **mature testing foundation**:
- ✅ Test runner: `pytest` with async support (`pytest-asyncio`)
- ✅ Integration layer: Real PostgreSQL (async), no DB mocks
- ✅ Unit test framework: Standard pytest fixtures
- ✅ Coverage tracking: `pytest-cov` available
- ✅ Strict TDD Mode: **ENABLED** (Strict mode rules apply to all new logic)

---

## Test Runner

| Attribute | Value |
|-----------|-------|
| **Framework** | pytest ≥7.4.0 |
| **Async Support** | pytest-asyncio ≥0.23.0 (auto mode) |
| **Command** | `cd backend && python3 -m pytest tests/` |
| **Test Discovery** | `tests/`, pattern `test_*.py` |
| **Config File** | `backend/pyproject.toml` (pytest.ini_options) |

### Test Configuration (pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
```

### Running Tests

```bash
# Run all tests
cd backend && python3 -m pytest tests/ -v

# Run with coverage
cd backend && python3 -m pytest tests/ --cov=app --cov-report=html

# Run specific test file
cd backend && python3 -m pytest tests/test_health.py -v

# Run async tests only
cd backend && python3 -m pytest tests/ -k "async" -v
```

---

## Test Layers & Coverage

### Layer 1: Unit Tests
| Status | Details |
|--------|---------|
| ✅ Available | Pure function testing, models, schemas, validators |
| Tool | pytest (fixtures) |
| Example Files | `test_config.py`, `test_encryption.py`, `test_database.py` |
| **Coverage Target** | ≥80% lines, ≥90% business rules |

**Unit Test Pattern** (from `conftest.py`):
- Fixtures for environment setup (`env_setup`)
- Settings fixture (`settings`) — loads config
- Synchronous fixtures for unit tests, async for integration

### Layer 2: Integration Tests
| Status | ✅ Available |
|--------|-----------|
| **Database** | Real PostgreSQL (async) |
| **Connection** | Async SQLAlchemy engine + sessions |
| **Isolation** | Per-test cleanup (tables created/dropped) |
| **Fixtures** | `test_engine`, `db_session` |
| Example Files | `test_repository.py`, `test_tenant_models.py` |

**Integration Test Pattern** (from `conftest.py`):
```python
@pytest.fixture
async def db_session(test_engine):
    """Provide an async database session for tests"""
    async_session_factory = async_sessionmaker(...)
    async with async_session_factory() as session:
        yield session
        await session.rollback()  # Cleanup
```

**Key Rule**: NO DB MOCKS. Tests use real PostgreSQL (ephemeral in CI).

### Layer 3: E2E Tests
| Status | ❌ Not yet available |
|--------|-----------|
| **Tool** | Planned: Playwright (once frontend is built) |
| **Trigger** | After C-21 (frontend shell) |
| Notes | Frontend not yet in repository |

---

## Coverage & Quality

### Coverage Tracking

```bash
# Generate coverage report
cd backend && python3 -m pytest tests/ \
  --cov=app \
  --cov-report=html \
  --cov-report=term-missing

# View HTML report
open htmlcov/index.html
```

**Coverage Gates**:
- **Line coverage minimum**: 80%
- **Business rule coverage minimum**: 90%
- **Branches tested**: All critical paths (auth, multi-tenancy, RBAC)

### Linting & Type Checking

| Tool | Command | Status |
|------|---------|--------|
| Linter (ruff) | `ruff check app/` | ✅ Available |
| Type checker (Pydantic) | `python3 -m pydantic_core` or mypy | ✅ Available (via Pydantic v2) |
| Formatter | `ruff format app/` | ✅ Available |

```bash
# Check linting
cd backend && python3 -m ruff check app/

# Format code
cd backend && python3 -m ruff format app/

# Type checking (Pydantic v2 validates at parse time)
cd backend && python3 -c "from pydantic import ValidationError; print('Type checking active')"
```

---

## Test Suite Inventory

### Current Test Files (11 files)

Located in `backend/tests/`:

| File | Purpose | Type | Status |
|------|---------|------|--------|
| `conftest.py` | Fixtures (env, DB, session, settings) | Setup | ✅ Active |
| `test_app_startup.py` | FastAPI app initialization | Unit | ✅ Active |
| `test_config.py` | Settings & configuration | Unit | ✅ Active |
| `test_database.py` | DB connection & session | Integration | ✅ Active |
| `test_encryption.py` | AES-256 encryption/decryption | Unit | ✅ Active |
| `test_health.py` | Health check endpoint | Integration | ✅ Active |
| `test_migrations.py` | Alembic migrations | Integration | ✅ Active |
| `test_observability.py` | OpenTelemetry instrumentation | Unit | ✅ Active |
| `test_placeholders.py` | Placeholder/scaffolding tests | Unit | ✅ Active |
| `test_repository.py` | Repository pattern (CRUD, filtering) | Integration | ✅ Active |
| `test_tenant_models.py` | Tenant-scoped models | Integration | ✅ Active |

### Async Testing Pattern

All integration tests use **async fixtures**:
```python
@pytest.mark.asyncio
async def test_something(db_session, settings):
    """Test async repository"""
    result = await repository.get_by_id(db_session, id_value)
    assert result is not None
```

---

## Strict TDD Mode — Enforcement Rules

### When Enabled

**Status**: ✅ **ENABLED** — All new production code must follow the TDD cycle.

### The TDD Cycle (MANDATORY for all tasks)

For EVERY task, follow this cycle strictly:

```
1. SAFETY NET (if modifying existing files)
   └─ Run existing tests → confirm baseline passing

2. RED (Write failing test FIRST)
   └─ Test describes expected behavior from spec
   └─ Test references code that does NOT yet exist
   └─ DO NOT proceed until test fails as expected

3. GREEN (Write MINIMUM code to pass)
   └─ Implement ONLY what the test needs
   └─ "Fake It" is valid (hardcoded returns OK at this stage)
   └─ Run tests → MUST PASS

4. TRIANGULATE (Add 2nd+ test case)
   └─ Different inputs/expected outputs
   └─ If "Fake It" breaks → generalize logic
   └─ Cover all spec scenarios

5. REFACTOR (Improve, no behavior change)
   └─ Extract functions, improve names
   └─ Run tests after EACH change
   └─ Tests MUST still pass

6. Mark task complete [x]
```

### Breaking TDD Rules

These violations **FAIL code review**:
- ❌ Writing production code before the test
- ❌ Skipping GREEN execution (running tests & confirming they pass)
- ❌ Skipping TRIANGULATE for multi-scenario specs
- ❌ Writing trivial assertions (type-only checks, ghost loops)
- ❌ Mocking the database (use real DB or ephemeral container)

---

## Environment & Dependencies

### Python Version
```
Required: Python ≥3.13, <4.0
Detected: 3.13.5
```

### Core Test Dependencies (from pyproject.toml)

```
pytest>=7.4.0              # Test framework
pytest-asyncio>=0.23.0     # Async test support
httpx>=0.25.0              # Async HTTP client (for API testing)
```

### Database Setup for Tests

```bash
# PostgreSQL must be running (local or Docker)
docker run -d \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=active_trace_test \
  -p 5432:5432 \
  postgres:16-alpine
```

### Environment Variables (from conftest.py)

```python
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/active_trace_test"
SECRET_KEY = "test-secret-key-must-be-32-chars!"
ENCRYPTION_KEY = "12345678901234567890123456789012"  # 32 bytes
ACCESS_TOKEN_EXPIRE_MINUTES = "15"
```

---

## Limitations & Future Improvements

### Current Limitations
- 🟡 **E2E tests not available** (frontend not yet in repo; planned for C-21)
- 🟡 **Performance/load tests not yet configured** (not in first phase)
- 🟡 **Mutation testing not set up** (ruff covers linting only)

### Recommendations for Next Phase
1. Add E2E layer once frontend is built (Playwright)
2. Configure CI/CD to run coverage gates on every PR
3. Add mutation testing to verify test quality
4. Document test data factories for consistent seeding

---

## Quick Start — Running Tests

```bash
# 1. Ensure PostgreSQL is running
docker run -d -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16-alpine

# 2. Navigate to backend
cd backend

# 3. Run all tests
python3 -m pytest tests/ -v

# 4. Run with coverage
python3 -m pytest tests/ --cov=app --cov-report=term-missing --cov-report=html

# 5. Run specific layer
python3 -m pytest tests/test_repository.py -v  # Integration tests
```

---

## Checkpoint: TDD Enabled ✅

**When implementing new tasks**:
1. Load the `test-driven-development` skill: `skill("test-driven-development")`
2. Follow the TDD cycle: RED → GREEN → TRIANGULATE → REFACTOR
3. Include TDD cycle evidence in your implementation summary (table format)
4. Report any blockers or violations upfront

---

**Status**: ✅ Ready for TDD workflow | **Last Verified**: 2026-06-02 | **Version**: 1.0
