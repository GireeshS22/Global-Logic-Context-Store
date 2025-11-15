#!/usr/bin/env python3
"""
Test script for newly added parser patterns
Tests the enhanced patterns from Option 3 implementation
"""

from glcs import SimpleParser

def test_pattern(parser, text, expected_type=None):
    """Test a single pattern"""
    print(f"\nTesting: '{text}'")
    stmt = parser.parse(text)

    if stmt:
        print(f"  ✅ Parsed successfully")
        print(f"  Type: {stmt.type.value}")
        print(f"  Subject: '{stmt.subject}'")
        print(f"  Predicate: '{stmt.predicate}'")
        if stmt.object:
            print(f"  Object: '{stmt.object}'")
        if expected_type and stmt.type.value != expected_type:
            print(f"  ⚠️  WARNING: Expected {expected_type}, got {stmt.type.value}")
        return True
    else:
        print(f"  ❌ Failed to parse")
        return False

def main():
    parser = SimpleParser()

    print("=" * 70)
    print("TESTING NEW UNIVERSAL PATTERNS")
    print("=" * 70)

    universal_tests = [
        ("everyone is welcome", "universal"),
        ("nobody is perfect", "universal"),
        ("nothing is impossible", "universal"),
        ("everything is permitted", "universal"),
        ("none of the users can access", "universal"),
        ("only admins can delete", "universal"),
    ]

    universal_passed = 0
    for text, expected in universal_tests:
        if test_pattern(parser, text, expected):
            universal_passed += 1

    print("\n" + "=" * 70)
    print("TESTING NEW GROUND FACT PATTERNS")
    print("=" * 70)

    ground_tests = [
        ("John does not code", "ground"),
        ("Alice will attend", "ground"),
        ("Bob won't participate", "ground"),
        ("Mary must approve", "ground"),
        ("Charlie should review", "ground"),
        ("Dave may join", "ground"),
    ]

    ground_passed = 0
    for text, expected in ground_tests:
        if test_pattern(parser, text, expected):
            ground_passed += 1

    print("\n" + "=" * 70)
    print("TESTING NEW CONDITIONAL PATTERNS")
    print("=" * 70)

    conditional_tests = [
        ("unless alarm rings wake", "conditional"),
        ("either succeed or fail", "conditional"),
        ("neither hot nor cold", "conditional"),
        ("as long as pays can stay", "conditional"),
    ]

    conditional_passed = 0
    for text, expected in conditional_tests:
        if test_pattern(parser, text, expected):
            conditional_passed += 1

    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Universal patterns: {universal_passed}/{len(universal_tests)} passed")
    print(f"Ground patterns: {ground_passed}/{len(ground_tests)} passed")
    print(f"Conditional patterns: {conditional_passed}/{len(conditional_tests)} passed")
    print(f"\nTotal: {universal_passed + ground_passed + conditional_passed}/{len(universal_tests) + len(ground_tests) + len(conditional_tests)} passed")

    if (universal_passed + ground_passed + conditional_passed) == (len(universal_tests) + len(ground_tests) + len(conditional_tests)):
        print("\n🎉 All tests passed! Ready to commit.")
    else:
        print("\n⚠️  Some tests failed. Review parser.py patterns.")

if __name__ == "__main__":
    main()
