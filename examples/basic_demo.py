"""
Basic demo of GLCS functionality

This script demonstrates the core GLCS features:
- Parsing logical statements
- Storing facts in memory
- Detecting contradictions
- Querying stored knowledge
"""

from glcs import SimpleParser, SimpleMemory, ConsistencyChecker
from glcs.core import LogicalType


def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)


def main():
    """Run the basic GLCS demo"""

    print_section("GLCS Basic Demo")
    print("\nInitializing GLCS components...")

    # Initialize components
    parser = SimpleParser()
    memory = SimpleMemory(persist_path="demo_memory.json")
    checker = ConsistencyChecker(memory)

    print("✓ Parser initialized")
    print("✓ Memory initialized")
    print("✓ Consistency checker initialized")

    # Demo 1: Parse and store simple facts
    print_section("Demo 1: Storing Basic Facts")

    facts = [
        "All birds can fly",
        "All employees have benefits",
        "John is an employee",
        "Mary is a manager",
    ]

    for fact in facts:
        print(f"\nProcessing: '{fact}'")
        stmt = parser.parse(fact)

        if stmt:
            print(f"  ✓ Parsed as {stmt.type.value}")
            print(f"  Subject: {stmt.subject}")
            print(f"  Predicate: {stmt.predicate}")

            # Check consistency
            is_consistent, confidence, violations = checker.check_consistency(stmt)

            if is_consistent:
                print(f"  ✓ Consistent (confidence: {confidence:.2f})")
                memory.store(stmt)
                print("  ✓ Stored in memory")
            else:
                print(f"  ✗ Inconsistent!")
                for violation in violations:
                    print(f"    - {violation}")
        else:
            print("  ✗ Could not parse")

    # Demo 2: Detect contradictions
    print_section("Demo 2: Detecting Contradictions")

    contradictions = [
        "Penguins cannot fly",  # Contradicts "All birds can fly"
        "Bob is an employee",   # Consistent
        "Bob has no benefits",  # Would contradict if we had better reasoning
    ]

    for statement in contradictions:
        print(f"\nChecking: '{statement}'")
        stmt = parser.parse(statement)

        if stmt:
            is_consistent, confidence, violations = checker.check_consistency(stmt)

            if is_consistent:
                print(f"  ✓ Consistent (confidence: {confidence:.2f})")
                memory.store(stmt)
            else:
                print(f"  ✗ Contradiction detected!")
                for violation in violations:
                    print(f"    - {violation}")

                # Get suggestion
                suggestion = checker.suggest_alternative(stmt, violations)
                if suggestion:
                    print(f"\n  💡 Suggestion: {suggestion}")

    # Demo 3: Query stored knowledge
    print_section("Demo 3: Querying Stored Knowledge")

    print("\nMemory statistics:")
    stats = memory.get_stats()
    print(f"  Universal rules: {stats['universal']}")
    print(f"  Conditional rules: {stats['conditional']}")
    print(f"  Ground facts: {stats['ground']}")
    print(f"  Total statements: {stats['total']}")

    print("\nUniversal rules in memory:")
    universals = memory.query(type=LogicalType.UNIVERSAL)
    for stmt in universals:
        print(f"  - {stmt.raw_text}")

    print("\nGround facts in memory:")
    grounds = memory.query(type=LogicalType.GROUND)
    for stmt in grounds[:5]:  # Show first 5
        print(f"  - {stmt.raw_text}")

    print("\nFacts about 'john':")
    john_facts = memory.query(subject="john")
    for stmt in john_facts:
        print(f"  - {stmt.raw_text}")

    # Demo 4: Knowledge base verification
    print_section("Demo 4: Knowledge Base Verification")

    is_consistent, inconsistencies = checker.verify_knowledge_base()

    if is_consistent:
        print("✓ Knowledge base is internally consistent!")
    else:
        print("✗ Knowledge base has inconsistencies:")
        for inconsistency in inconsistencies:
            print(f"  - {inconsistency}")

    # Demo 5: Supporting facts
    print_section("Demo 5: Finding Supporting Facts")

    test_stmt = parser.parse("John is experienced")
    if test_stmt:
        supporting = checker.get_supporting_facts(test_stmt)
        print(f"\nSupporting facts for '{test_stmt.raw_text}':")
        if supporting:
            for fact in supporting:
                print(f"  - {fact.raw_text}")
        else:
            print("  (no supporting facts found)")

    print_section("Demo Complete")
    print("\nMemory has been saved to 'demo_memory.json'")
    print("You can run this demo again to see persistence in action!")


if __name__ == "__main__":
    main()
