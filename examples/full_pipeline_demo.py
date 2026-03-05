from glcs.core.models import LogicalForm, Entity, Relation, LogicalType, Polarity
from glcs.core.semantic_encoder import SemanticEncoder
from glcs.core.memory_manager import MemoryManager
from glcs.core.consistency_checker import ConsistencyChecker

# Initialize components
encoder = SemanticEncoder()
memory = MemoryManager(collection_name="manual_test", in_memory=True)
checker = ConsistencyChecker(memory, encoder)

# Create some logical forms
form1 = LogicalForm(
    context_id="test_session",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans"),
    predicate=Relation(verb="are"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="All humans are mortal",
    confidence_score=0.95
)

form2 = LogicalForm(
    context_id="test_session",
    logical_type=LogicalType.GROUND_FACT,
    subject=Entity(name="socrates"),
    predicate=Relation(verb="is"),
    object=Entity(name="human"),
    polarity=Polarity.POSITIVE,
    source_text="Socrates is human",
    confidence_score=0.9
)

# Add embeddings
encoder.add_embedding_to_form(form1)
encoder.add_embedding_to_form(form2)

# Store in memory
memory.store_form(form1)
memory.store_form(form2)

# Check consistency (should be consistent)
report = checker.check_context_consistency("test_session")
print(f"Is consistent: {report.is_consistent}")
print(f"Violations: {len(report.violations)}")
print(f"Forms checked: {report.total_forms_checked}")

# Add a contradictory form
form3 = LogicalForm(
    context_id="test_session",
    logical_type=LogicalType.GROUND_FACT,
    subject=Entity(name="socrates"),
    predicate=Relation(verb="is"),
    object=Entity(name="mortal"),
    polarity=Polarity.NEGATIVE,  # CONTRADICTS the universal rule!
    source_text="Socrates is not mortal",
    confidence_score=0.85
)

encoder.add_embedding_to_form(form3)

# Check BEFORE storing (smart approach)
report = checker.check_form_against_context(form3, "test_session")
print(f"\nChecking new form against context:")
print(f"Is consistent: {report.is_consistent}")

if not report.is_consistent:
    print(f"\nFound {len(report.violations)} violation(s):")
    for v in report.violations:
        print(f"  - {v.severity}: {v.violation_type}")
        print(f"    {v.explanation}")


# Add a semantically similar form (redundant)
form4 = LogicalForm(
    context_id="test_session",
    logical_type=LogicalType.UNIVERSAL_RULE,
    subject=Entity(name="humans"),
    predicate=Relation(verb="are"),
    object=Entity(name="mortal"),
    polarity=Polarity.POSITIVE,
    source_text="Every person is mortal",  # Similar to form1
    confidence_score=0.9
)

encoder.add_embedding_to_form(form4)

# Check for redundancy
report = checker.check_form_against_context(form4, "test_session")
print(f"\nChecking for redundancy:")
print(f"Is consistent: {report.is_consistent}")

if not report.is_consistent:
    for v in report.violations:
        print(f"  - {v.severity}: {v.violation_type}")
        print(f"    {v.explanation}")

# Store the redundant form anyway
memory.store_form(form4)

# Get full context report
report = checker.check_context_consistency("test_session")
summary = checker.get_violation_summary(report.violations)

print(f"\n=== Violation Summary ===")
print(f"Total violations: {summary['total']}")
print(f"By type: {summary['by_type']}")
print(f"By severity: {summary['by_severity']}")
print(f"High severity: {summary['high_severity_count']}")

# Search by entity
socrates_forms = memory.search_by_entity("socrates")
print(f"\nForms mentioning Socrates: {len(socrates_forms)}")
for f in socrates_forms:
    print(f"  - {f.source_text}")

# Search by relation
mortal_forms = memory.search_by_relation("are")
print(f"\nForms using 'are': {len(mortal_forms)}")
for f in mortal_forms:
    print(f"  - {f.source_text}")

# Get context stats
stats = memory.get_context_stats("test_session")
print(f"\n=== Context Statistics ===")
print(f"Total forms: {stats['total_forms']}")
print(f"Logical types: {stats['logical_types']}")
print(f"Polarities: {stats['polarities']}")
print(f"Avg confidence: {stats['avg_confidence']:.2f}")

# Compare embeddings
similarity = encoder.cosine_similarity(form1.embedding, form4.embedding)
print(f"\nSimilarity between:")
print(f"  '{form1.source_text}'")
print(f"  '{form4.source_text}'")
print(f"  Similarity: {similarity:.4f}")

# Search for similar forms
similar = memory.search_similar_forms(form1.embedding, top_k=3)
print(f"\nTop {len(similar)} similar forms to '{form1.source_text}':")
for f in similar:
    print(f"  - {f.source_text}")