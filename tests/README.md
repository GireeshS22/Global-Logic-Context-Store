# GLCS Testing Guide

This directory contains all tests for the GLCS project.

## Test Organization

```
tests/
├── unit/              # Unit tests for individual components
├── integration/       # Integration tests for workflows
├── fixtures/          # Shared test data and fixtures
└── README.md         # This file
```

## Running Tests

### Run All Tests

```bash
# Run full test suite
poetry run pytest

# Run with verbose output
poetry run pytest -v

# Run with coverage report
poetry run pytest --cov=glcs --cov-report=html
```

### Run Specific Tests

```bash
# Run unit tests only
poetry run pytest tests/unit/

# Run integration tests only
poetry run pytest tests/integration/

# Run specific test file
poetry run pytest tests/unit/test_models.py

# Run specific test function
poetry run pytest tests/unit/test_models.py::test_logical_form_creation
```

### Run Tests in Parallel

```bash
# Install pytest-xdist first
poetry add --group dev pytest-xdist

# Run tests in parallel
poetry run pytest -n auto
```

## Test Coverage Requirements

- **Minimum Coverage**: 80% overall
- **Core Components**: 90%+ coverage
- **Utilities**: 85%+ coverage
- **API Layer**: 75%+ coverage

Check coverage:
```bash
poetry run pytest --cov=glcs --cov-report=term-missing
```

## Unit Tests (`unit/`)

Unit tests test individual components in isolation.

**Test Files**:
- `test_models.py` - Data model validation
- `test_config_manager.py` - Configuration loading and validation
- `test_logger.py` - Logging functionality
- `test_exceptions.py` - Custom exception hierarchy
- `test_semantic_encoder.py` - Vector encoding
- `test_memory_manager.py` - Memory operations
- `test_consistency_checker.py` - Consistency algorithms
- `test_logical_parser.py` - Statement parsing (with mocking)

**Unit Test Guidelines**:
1. Test one function/method per test
2. Use fixtures for common test data
3. Mock external dependencies (APIs, file system)
4. Test both success and failure cases
5. Test edge cases and boundary conditions

**Example Unit Test**:
```python
import pytest
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity

def test_logical_form_creation():
    """Test creating a valid LogicalForm."""
    form = LogicalForm(
        context_id="test-123",
        original_text="All employees work remotely",
        logical_type=LogicalType.UNIVERSAL_RULE,
        subject=Entity(text="employees", entity_id="e1"),
        predicate=Relation(text="work_remotely", relation_id="r1"),
        polarity=Polarity.POSITIVE
    )

    assert form.logical_type == LogicalType.UNIVERSAL_RULE
    assert form.subject.text == "employees"
    assert form.polarity == Polarity.POSITIVE
```

## Integration Tests (`integration/`)

Integration tests test complete workflows across multiple components.

**Test Files**:
- `test_glcs_manager.py` - End-to-end statement processing
- `test_api.py` - API endpoint testing (Phase 2)
- `test_consistency_workflows.py` - Multi-statement consistency scenarios

**Integration Test Guidelines**:
1. Test realistic workflows
2. Use minimal mocking (test actual component interaction)
3. Test error handling and recovery
4. Test data persistence across operations

**Example Integration Test**:
```python
def test_end_to_end_contradiction_detection():
    """Test full workflow: parse, encode, check, detect contradiction."""
    glcs = GLCSManager()

    # Add first statement
    result1 = glcs.process_statement(
        "All employees work remotely",
        context_id="test-123"
    )
    assert result1.is_consistent

    # Add contradicting statement
    result2 = glcs.process_statement(
        "All employees work from office",
        context_id="test-123"
    )
    assert not result2.is_consistent
    assert len(result2.violations) == 1
    assert result2.violations[0].type == "DirectContradiction"
```

## Test Fixtures (`fixtures/`)

Shared test data and helper functions.

**Files**:
- `sample_data.py` - Sample LogicalForm objects, test statements
- `conftest.py` - Pytest fixtures and configuration

**Using Fixtures**:
```python
# In fixtures/sample_data.py
from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity

SAMPLE_UNIVERSAL_RULE = LogicalForm(
    context_id="fixture",
    original_text="All birds can fly",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(text="birds", entity_id="e1"),
    predicate=Relation(text="can_fly", relation_id="r1"),
    polarity=Polarity.POSITIVE
)

# In test file
from tests.fixtures.sample_data import SAMPLE_UNIVERSAL_RULE

def test_using_fixture():
    assert SAMPLE_UNIVERSAL_RULE.logical_type == LogicalType.UNIVERSAL_RULE
```

## Mocking External Dependencies

For unit tests, mock external APIs and services:

```python
from unittest.mock import Mock, patch

@patch('glcs.core.logical_parser.OpenAI')
def test_parser_with_mock(mock_openai):
    """Test parser without calling actual OpenAI API."""
    # Configure mock
    mock_client = Mock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = Mock(
        choices=[Mock(message=Mock(content='{"subject": "test", ...}'))]
    )

    # Test parser
    parser = LogicalParser(api_key="fake-key")
    result = parser.parse("Test statement")

    # Verify mock was called
    assert mock_client.chat.completions.create.called
```

## Writing Good Tests

### DO:
✅ Test one thing per test function
✅ Use descriptive test names (`test_parser_handles_invalid_json`)
✅ Use fixtures for reusable test data
✅ Test edge cases and error conditions
✅ Keep tests independent (no shared state)
✅ Use assertions with clear messages
✅ Document complex test logic

### DON'T:
❌ Test implementation details (test behavior, not internals)
❌ Write tests that depend on execution order
❌ Use real API calls in unit tests (use mocks)
❌ Ignore test failures
❌ Skip writing tests for "simple" code
❌ Make tests too complex (tests should be simple to understand)

## Test Data

Test datasets are stored in `data/` directory:
- `data/contradiction_dataset/` - Contradiction detection benchmark
- `data/test_cases/` - Small test cases for unit tests

## Continuous Integration

Tests are run automatically on:
- Every commit (local pre-commit hook)
- Every pull request (CI pipeline)
- Before deployment

## Debugging Failed Tests

```bash
# Run with print statements visible
poetry run pytest -s

# Run with debugger on failure
poetry run pytest --pdb

# Run only failed tests from last run
poetry run pytest --lf

# Show detailed output
poetry run pytest -vv
```

## Performance Testing

For performance benchmarks:

```bash
# Run with timing information
poetry run pytest --durations=10

# Profile tests
poetry run pytest --profile
```

## Test Status by Stage

- ✅ **Stage 0.1**: Project structure smoke test
- ✅ **Stage 0.2**: Config, logger, exceptions tests
- ✅ **Stage 0.3**: Data models tests
- ⏳ **Stage 1.1**: Semantic encoder tests
- ⏳ **Stage 1.2**: Memory manager tests
- ⏳ **Stage 1.3**: Consistency checker tests
- ⏳ **Stage 1.4**: Logical parser tests

## Contributing Tests

When adding new features:
1. Write tests FIRST (TDD approach recommended)
2. Ensure all tests pass before committing
3. Maintain >80% coverage
4. Update this README if adding new test categories

---

**Last Updated**: Stage 0.1 (Project Structure Setup)
