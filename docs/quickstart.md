# Quickstart

Install GLCS, create the core objects, parse a statement, and check whether it is consistent with what is already stored.

## Install

```bash
pip install glcs
```

If you want the optional provider SDKs, install the matching extra:

```bash
pip install glcs[all-providers]
```

## Initialize

```python
from glcs import SimpleParser, SimpleMemory, SimpleConsistencyChecker

parser = SimpleParser()
memory = SimpleMemory()
checker = SimpleConsistencyChecker(memory)
```

## Parse

```python
statement = parser.parse("John is a manager")

if statement is None:
    raise ValueError("Could not parse the statement")

print(statement)
```

## Check consistency

```python
is_consistent, confidence, conflicts = checker.check_consistency(statement)

print(f"Consistent: {is_consistent}")
print(f"Confidence: {confidence:.2f}")
print(f"Conflicts: {conflicts}")

if is_consistent:
    memory.store(statement)
```

## Next steps

- Read the [API reference](api_reference.md) for the public Python modules.
- Review the [provider guide](PROVIDER_GUIDE.md) for API key and model setup.
- Use the [REST API guide](API_GUIDE.md) if you want to run GLCS as a service.