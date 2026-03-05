from glcs.core import LLMLogicalParser
parser = LLMLogicalParser(provider='ollama', model='qwen2.5:0.5b')
form = parser.parse('I started from office at 9:00 AM today and it was raining outside', 'test')
print(f'✓ Parsed: {form.source_text}')
print(f'  Subject: {form.subject.name}')
print(f'  Type: {form.logical_type.value}')
