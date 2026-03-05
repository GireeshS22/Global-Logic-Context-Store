# In Python interpreter:
from glcs import GLCSWrapper

# Create wrapper with smallest model
wrapper = GLCSWrapper(provider='ollama', model='qwen2:0.5b')

# Store some facts
wrapper.generate("John is a manager")
wrapper.generate("Alice is an engineer")
wrapper.generate("All managers must approve budgets")

# Get memory summary
summary = wrapper.get_memory_summary()
print(f"\nMemory Summary:")
print(f"Total statements: {summary['statistics']['total']}")
print(f"Ground facts: {summary['ground_facts']}")
print(f"Universal rules: {summary['universal_rules']}")

# Test contradiction
result = wrapper.generate("John is an engineer")
print(f"\nContradiction test:")
print(f"Consistent: {result['consistent']}")
print(f"Violations: {result['violations']}")

# Test it
result = wrapper.generate("What is 2 + 2?")
print(result['response'])