#!/usr/bin/env python3
"""
GLCS Interactive Test Script
Shows realistic use cases that work well
"""

from glcs import SimpleParser, SimpleMemory, ConsistencyChecker

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text}")
    print("=" * 60)

def test_statement(parser, checker, memory, text, description=""):
    print(f"\n{'→' if description else ''}  Testing: '{text}'")
    if description:
        print(f"   {description}")

    stmt = parser.parse(text)

    if not stmt:
        print("   ❌ Could not parse")
        return False

    print(f"   ✓ Parsed as: {stmt.type.value}")
    print(f"   ✓ Subject: '{stmt.subject}' | Predicate: '{stmt.predicate}'")

    is_consistent, conf, violations = checker.check_consistency(stmt)

    if is_consistent:
        print(f"   ✅ CONSISTENT (confidence: {conf:.0%})")
        memory.store(stmt)
        print("   💾 Stored in memory")
        return True
    else:
        print(f"   ❌ CONTRADICTION DETECTED!")
        for v in violations:
            print(f"      • {v}")
        return False

def main():
    parser = SimpleParser()
    memory = SimpleMemory(persist_path=None)
    checker = ConsistencyChecker(memory)

    print_header("GLCS Test Suite - What Works Well")

    # Test 1: Job Roles
    print_header("Test 1: Job Role Conflicts")
    test_statement(parser, checker, memory, "John is a manager", "Store John's role")
    test_statement(parser, checker, memory, "John is an engineer", "Try to change role - should fail!")
    test_statement(parser, checker, memory, "Mary is a developer", "Store Mary's role")

    # Test 2: Capabilities
    print_header("Test 2: Direct Negations")
    test_statement(parser, checker, memory, "Alice can code", "Alice has a skill")
    test_statement(parser, checker, memory, "Alice cannot code", "Opposite - should fail!")
    test_statement(parser, checker, memory, "Bob can swim", "Bob has a different skill")

    # Test 3: Universal Rules
    print_header("Test 3: Universal Rules")
    test_statement(parser, checker, memory, "All birds can fly", "Universal rule about birds")
    test_statement(parser, checker, memory, "Penguin cannot fly", "Exception - should fail!")

    # Show memory summary
    print_header("Memory Summary")
    stats = memory.get_stats()
    print(f"\n  Total statements stored: {stats['total']}")
    print(f"  Universal rules: {stats['universal']}")
    print(f"  Ground facts: {stats['ground']}")
    print(f"  Conditionals: {stats['conditional']}")

    print("\n" + "=" * 60)
    print(" Test complete! These are the types of contradictions")
    print(" GLCS can detect reliably.")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
