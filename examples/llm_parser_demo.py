"""
LLM Parser Demo - Stage 1.5

This example demonstrates the LLM-based logical parser, showing how it
handles complex sentences that regex parsers cannot process.

Run with: python examples/llm_parser_demo.py
"""

from glcs.core import LLMLogicalParser


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_form(form):
    """Print LogicalForm details."""
    print(f"\n📋 Parsed Statement: '{form.source_text}'")
    print(f"   Subject: {form.subject.name} ({form.subject.entity_type or 'untyped'})")
    print(f"   Predicate: {form.predicate.verb} ({form.predicate.relation_type or 'untyped'})")
    if form.object:
        print(f"   Object: {form.object.name} ({form.object.entity_type or 'untyped'})")
    else:
        print(f"   Object: None")
    print(f"   Type: {form.logical_type.value}")
    print(f"   Polarity: {form.polarity.value}")
    print(f"   Confidence: {form.confidence_score:.2f}")


def demo_simple_statements():
    """Demo 1: Parse simple statements."""
    print_section("Demo 1: Simple Statements")

    parser = LLMLogicalParser(provider='ollama')
    print("✓ Initialized LLM Parser (provider: ollama)")

    statements = [
        "John is a manager",
        "Alice works in engineering",
        "The server is online",
        "Bob is not an engineer"
    ]

    for stmt in statements:
        try:
            form = parser.parse(stmt, context_id="demo-1")
            print_form(form)
        except Exception as e:
            print(f"❌ Failed to parse '{stmt}': {e}")


def demo_complex_sentences():
    """Demo 2: Parse complex sentences (regex parser would fail)."""
    print_section("Demo 2: Complex Sentences (Regex Would Fail)")

    parser = LLMLogicalParser(provider='ollama')

    complex_statements = [
        "John, who recently joined from Google, is our new technical lead",
        "The system automatically restarts when it detects a crash",
        "Employees working remotely must complete their timesheets by Friday",
        "All managers, except those in sales, report to the VP"
    ]

    print("\n🎯 These complex sentences require LLM understanding:")
    for stmt in complex_statements:
        try:
            form = parser.parse(stmt, context_id="demo-2")
            print_form(form)
        except Exception as e:
            print(f"❌ Failed to parse '{stmt}': {e}")


def demo_logical_types():
    """Demo 3: Different logical types."""
    print_section("Demo 3: Logical Type Classification")

    parser = LLMLogicalParser(provider='ollama')

    typed_statements = [
        ("All employees must complete training", "UNIVERSAL_RULE"),
        ("Some employees work remotely", "EXISTENTIAL_CLAIM"),
        ("If server crashes, it restarts", "CONDITIONAL_LOGIC"),
        ("Bob is a developer", "GROUND_FACT")
    ]

    for stmt, expected_type in typed_statements:
        try:
            form = parser.parse(stmt, context_id="demo-3")
            actual_type = form.logical_type.value.upper()
            match = "✓" if expected_type in actual_type else "✗"
            print(f"\n{match} '{stmt}'")
            print(f"   Expected: {expected_type}")
            print(f"   Actual: {form.logical_type.value}")
            print(f"   Confidence: {form.confidence_score:.2f}")
        except Exception as e:
            print(f"❌ Failed: {e}")


def demo_polarity_detection():
    """Demo 4: Positive vs negative statements."""
    print_section("Demo 4: Polarity Detection")

    parser = LLMLogicalParser(provider='ollama')

    polarized_statements = [
        ("Alice is a manager", "POSITIVE"),
        ("Alice is not a manager", "NEGATIVE"),
        ("Bob cannot access the database", "NEGATIVE"),
        ("Charlie has admin privileges", "POSITIVE")
    ]

    for stmt, expected_polarity in polarized_statements:
        try:
            form = parser.parse(stmt, context_id="demo-4")
            actual_polarity = form.polarity.value.upper()
            match = "✓" if expected_polarity == actual_polarity else "✗"
            print(f"\n{match} '{stmt}'")
            print(f"   Expected: {expected_polarity}")
            print(f"   Actual: {form.polarity.value}")
            print(f"   Confidence: {form.confidence_score:.2f}")
        except Exception as e:
            print(f"❌ Failed: {e}")


def demo_caching():
    """Demo 5: Caching mechanism."""
    print_section("Demo 5: Caching for Performance")

    parser = LLMLogicalParser(provider='ollama', cache_enabled=True)

    statement = "John is a senior engineer"

    print(f"\n📝 Parsing: '{statement}'")
    print("\n🔄 First parse (cache miss - calls LLM)...")
    form1 = parser.parse(statement, context_id="ctx-1")
    print(f"   ✓ Parsed with confidence: {form1.confidence_score:.2f}")

    print("\n⚡ Second parse (cache hit - instant, no LLM call)...")
    form2 = parser.parse(statement, context_id="ctx-2")
    print(f"   ✓ Retrieved from cache")

    stats = parser.get_cache_stats()
    print(f"\n📊 Cache stats:")
    print(f"   Enabled: {stats['enabled']}")
    print(f"   Size: {stats['size']} entries")
    print(f"   Provider: {stats['provider']}")

    print(f"\n🗑️  Clearing cache...")
    cleared = parser.clear_cache()
    print(f"   ✓ Cleared {cleared} entries")


def demo_batch_processing():
    """Demo 6: Batch processing."""
    print_section("Demo 6: Batch Processing")

    parser = LLMLogicalParser(provider='ollama')

    statements = [
        "Alice is a developer",
        "Bob is a designer",
        "Charlie is a manager",
        "All developers must code review",
        "If tests fail, notify the team"
    ]

    print(f"\n📦 Batch parsing {len(statements)} statements...")
    forms = parser.parse_batch(statements, context_id="team-kb")

    print(f"\n✓ Successfully parsed {len(forms)}/{len(statements)} statements")
    for i, form in enumerate(forms, 1):
        print(f"\n{i}. {form.source_text}")
        print(f"   → {form.logical_type.value} (confidence: {form.confidence_score:.2f})")


def demo_provider_comparison():
    """Demo 7: Compare different providers."""
    print_section("Demo 7: Provider Comparison")

    statement = "All managers must approve budgets over $10,000"
    print(f"\n📝 Parsing: '{statement}'")

    providers = [
        ('ollama', 'qwen2.5:0.5b'),
        # Uncomment if you have API keys:
        # ('openai', 'gpt-4o-mini'),
        # ('anthropic', 'claude-3-haiku'),
    ]

    print("\n🔄 Comparing providers:")
    for provider, model in providers:
        try:
            parser = LLMLogicalParser(provider=provider, model=model)
            form = parser.parse(statement, context_id="comparison")

            print(f"\n✓ {provider.upper()} ({model}):")
            print(f"   Type: {form.logical_type.value}")
            print(f"   Subject: {form.subject.name}")
            print(f"   Confidence: {form.confidence_score:.2f}")
        except Exception as e:
            print(f"\n❌ {provider.upper()} failed: {e}")


def demo_confidence_handling():
    """Demo 8: Handling low-confidence parses."""
    print_section("Demo 8: Confidence-Based Quality Control")

    parser = LLMLogicalParser(provider='ollama')

    statements = [
        "John is a manager",  # Clear, high confidence
        "The thing is like, you know, complicated",  # Vague, low confidence
        "Maybe Alice might possibly be an engineer",  # Uncertain, medium confidence
    ]

    CONFIDENCE_THRESHOLD = 0.7

    for stmt in statements:
        try:
            form = parser.parse(stmt, context_id="quality-check")
            confidence = form.confidence_score

            if confidence >= CONFIDENCE_THRESHOLD:
                print(f"\n✅ HIGH CONFIDENCE ({confidence:.2f})")
                print(f"   '{stmt}'")
                print(f"   → Parsed as: {form.logical_type.value}")
            else:
                print(f"\n⚠️  LOW CONFIDENCE ({confidence:.2f})")
                print(f"   '{stmt}'")
                print(f"   → May need manual verification or clarification")

        except Exception as e:
            print(f"\n❌ Failed to parse: {e}")


def main():
    """Run all demos."""
    print("\n" + "🚀" * 35)
    print("  LLM-Based Logical Parser - Interactive Demo")
    print("🚀" * 35)

    print("\nThis demo showcases the advanced LLM parser capabilities:")
    print("  • Simple statement parsing")
    print("  • Complex sentence understanding")
    print("  • Logical type classification")
    print("  • Polarity detection")
    print("  • Caching mechanism")
    print("  • Batch processing")
    print("  • Provider comparison")
    print("  • Confidence-based quality control")

    print("\n⚠️  Note: Make sure Ollama is running (ollama serve)")
    input("\nPress Enter to start the demo...")

    try:
        demo_simple_statements()
        input("\nPress Enter for next demo...")

        demo_complex_sentences()
        input("\nPress Enter for next demo...")

        demo_logical_types()
        input("\nPress Enter for next demo...")

        demo_polarity_detection()
        input("\nPress Enter for next demo...")

        demo_caching()
        input("\nPress Enter for next demo...")

        demo_batch_processing()
        input("\nPress Enter for next demo...")

        demo_provider_comparison()
        input("\nPress Enter for next demo...")

        demo_confidence_handling()

        print_section("Demo Complete!")
        print("\n✨ All demos completed successfully!")
        print("\nNext steps:")
        print("  1. Try advanced_glcs_demo.py for full pipeline integration")
        print("  2. Read docs/LLM_PARSER_GUIDE.md for detailed documentation")
        print("  3. Explore provider switching for your use case")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("  • Make sure Ollama is running: ollama serve")
        print("  • Check that qwen2.5:0.5b model is installed: ollama pull qwen2.5:0.5b")
        print("  • See docs/LLM_PARSER_GUIDE.md for more help")


if __name__ == "__main__":
    main()
