"""
Advanced GLCS Demo - Complete Pipeline Integration

This example demonstrates the full Advanced GLCS pipeline:
LLM Parser → Semantic Encoder → Memory Manager → Consistency Checker

Run with: python examples/advanced_glcs_demo.py
"""

from glcs.advanced_wrapper import AdvancedGLCS


def print_section(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_report(report):
    """Print consistency report."""
    if report.is_consistent:
        print(f"   ✅ CONSISTENT")
    else:
        print(f"   ❌ INCONSISTENT ({len(report.violations)} violations)")
        for i, violation in enumerate(report.violations, 1):
            print(f"      {i}. {violation.violation_type}: {violation.explanation}")


def demo_basic_workflow():
    """Demo 1: Basic statement processing."""
    print_section("Demo 1: Basic Workflow")

    # Initialize Advanced GLCS
    print("\n🔧 Initializing Advanced GLCS...")
    glcs = AdvancedGLCS(
        parser_provider='ollama',
        encoder_model='all-mpnet-base-v2',
        in_memory=True,  # Use in-memory for demo
    )
    print("✓ System initialized")

    # Process first statement
    print("\n📝 Processing: 'John is a manager'")
    report = glcs.process_statement("John is a manager", "company-db")
    print_report(report)

    # Process second statement
    print("\n📝 Processing: 'Alice is an engineer'")
    report = glcs.process_statement("Alice is an engineer", "company-db")
    print_report(report)

    # Get summary
    summary = glcs.get_context_summary("company-db")
    print(f"\n📊 Context Summary:")
    print(f"   Total statements: {summary['total_forms']}")
    print(f"   Statements:")
    for stmt in summary['sample_statements']:
        print(f"      • {stmt}")


def demo_contradiction_detection():
    """Demo 2: Detecting contradictions."""
    print_section("Demo 2: Contradiction Detection")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    # Add consistent facts
    print("\n✅ Adding consistent facts:")

    statements = [
        "Bob is a developer",
        "Alice is a designer",
        "Charlie is a manager"
    ]

    for stmt in statements:
        print(f"   • {stmt}")
        report = glcs.process_statement(stmt, "team-db")
        print_report(report)

    # Try to add contradictory fact
    print("\n⚠️  Attempting to add contradictory fact:")
    print("   • Bob is a designer (contradicts 'Bob is a developer')")
    report = glcs.process_statement("Bob is not a developer", "team-db")
    print_report(report)


def demo_universal_rules():
    """Demo 3: Universal rules and violations."""
    print_section("Demo 3: Universal Rules")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    # Add universal rule
    print("\n📜 Adding universal rule:")
    print("   • All managers must approve budgets")
    report = glcs.process_statement("All managers must approve budgets", "policies")
    print_report(report)

    # Add compliant fact
    print("\n✅ Adding compliant fact:")
    print("   • John is a manager")
    report = glcs.process_statement("John is a manager", "policies")
    print_report(report)

    # Verify universal rule is followed
    print("\n🔍 Verifying context consistency...")
    report = glcs.verify_context("policies")
    print_report(report)


def demo_semantic_search():
    """Demo 4: Semantic similarity search."""
    print_section("Demo 4: Semantic Search")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    # Add various statements
    print("\n📥 Adding statements to knowledge base:")
    statements = [
        "John works in the engineering department",
        "Alice is a software developer",
        "Bob manages the sales team",
        "Charlie works remotely",
        "Diana is a senior engineer"
    ]

    for stmt in statements:
        print(f"   • {stmt}")
        glcs.process_statement(stmt, "company-kb")

    # Search for similar statements
    print("\n🔍 Searching for: 'Who works in engineering?'")
    similar = glcs.search_similar("Who works in engineering?", context_id="company-kb", top_k=3)

    print(f"\n📋 Found {len(similar)} similar statements:")
    for i, form in enumerate(similar, 1):
        print(f"   {i}. {form.source_text}")
        print(f"      (Subject: {form.subject.name}, Type: {form.logical_type.value})")


def demo_entity_search():
    """Demo 5: Search by entity."""
    print_section("Demo 5: Entity-Based Search")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    # Add facts about specific people
    print("\n📥 Adding facts about John:")
    john_facts = [
        "John is a manager",
        "John works in engineering",
        "John has 10 years of experience"
    ]

    for stmt in john_facts:
        print(f"   • {stmt}")
        glcs.process_statement(stmt, "employee-db")

    # Search for all facts about John
    print("\n🔍 Searching for all facts about 'john':")
    john_forms = glcs.get_forms_by_entity("john", context_id="employee-db")

    print(f"\n📋 Found {len(john_forms)} statements about John:")
    for i, form in enumerate(john_forms, 1):
        print(f"   {i}. {form.source_text}")


def demo_complex_sentences():
    """Demo 6: Handling complex sentences."""
    print_section("Demo 6: Complex Sentence Handling")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    print("\n🎯 Processing complex sentences (regex parser would fail):")

    complex_statements = [
        "Alice, who recently joined from Google, is our new technical lead",
        "The system automatically restarts when it detects a crash",
        "Employees working remotely must complete timesheets by Friday"
    ]

    for stmt in complex_statements:
        print(f"\n   📝 '{stmt}'")
        try:
            report = glcs.process_statement(stmt, "advanced-kb")
            print(f"      ✓ Parsed successfully")
            print_report(report)
        except Exception as e:
            print(f"      ❌ Failed: {e}")


def demo_batch_processing():
    """Demo 7: Batch processing."""
    print_section("Demo 7: Batch Processing")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    statements = [
        "All employees must complete safety training",
        "John is an employee",
        "Alice is an employee",
        "Bob is a contractor",
        "Charlie is an employee"
    ]

    print(f"\n📦 Processing {len(statements)} statements in batch:")
    for stmt in statements:
        print(f"   • {stmt}")

    reports = glcs.process_batch(statements, context_id="hr-db")

    print(f"\n✓ Processed: {len(reports)}/{len(statements)}")

    # Count consistent vs inconsistent
    consistent_count = sum(1 for r in reports if r.is_consistent)
    print(f"   ✅ Consistent: {consistent_count}")
    print(f"   ❌ Inconsistent: {len(reports) - consistent_count}")


def demo_system_info():
    """Demo 8: System information."""
    print_section("Demo 8: System Information")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    info = glcs.get_system_info()

    print("\n🔧 System Configuration:")
    print(f"\n   Parser:")
    print(f"      Provider: {info['parser']['provider']}")
    print(f"      Cache Enabled: {info['parser']['cache_enabled']}")
    print(f"      Cache Size: {info['parser']['cache_size']}")

    print(f"\n   Encoder:")
    print(f"      Model: {info['encoder']['model']}")
    print(f"      Dimensions: {info['encoder']['dimensions']}")

    print(f"\n   Memory:")
    print(f"      Collection: {info['memory']['collection']}")
    print(f"      Total Forms: {info['memory']['total_forms']}")

    print(f"\n   Checker:")
    print(f"      Redundancy Threshold: {info['checker']['redundancy_threshold']}")


def demo_provider_switching():
    """Demo 9: Switching parser providers."""
    print_section("Demo 9: Provider Switching")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    print(f"\n🔄 Initial provider: {glcs.parser.provider_name}")

    # Process with Ollama
    print("\n📝 Processing with Ollama:")
    report1 = glcs.process_statement("Test statement 1", "switch-demo")
    print(f"   ✓ Processed")

    # Switch to different provider (would need API key for real use)
    print("\n🔄 Switching to OpenAI (mock)...")
    print("   (In real use, you'd provide API key)")
    # glcs.switch_parser_provider('openai', model='gpt-4o-mini')
    # print(f"   ✓ Switched to: {glcs.parser.provider_name}")


def demo_full_scenario():
    """Demo 10: Complete realistic scenario."""
    print_section("Demo 10: Complete Scenario - Company Knowledge Base")

    glcs = AdvancedGLCS(parser_provider='ollama', in_memory=True)

    print("\n🏢 Building company knowledge base...")

    # 1. Add company policies
    print("\n1️⃣  Adding company policies:")
    policies = [
        "All employees must complete security training",
        "All managers must approve budgets over $5000",
        "Remote employees must attend weekly team meetings"
    ]
    for policy in policies:
        print(f"   • {policy}")
        glcs.process_statement(policy, "company")

    # 2. Add employee information
    print("\n2️⃣  Adding employee information:")
    employees = [
        "John is a manager in engineering",
        "Alice is a developer",
        "Bob works remotely",
        "Charlie is a manager in sales"
    ]
    for emp in employees:
        print(f"   • {emp}")
        glcs.process_statement(emp, "company")

    # 3. Try to add contradictory information
    print("\n3️⃣  Testing contradiction detection:")
    print("   • Attempting: 'John is a developer' (contradicts manager)")
    report = glcs.process_statement("John is a developer", "company")
    print_report(report)

    # 4. Search for managers
    print("\n4️⃣  Searching for all managers:")
    managers = glcs.search_similar("Who are the managers?", context_id="company", top_k=5)
    print(f"   Found {len(managers)} relevant statements:")
    for form in managers:
        print(f"      • {form.source_text}")

    # 5. Get context summary
    print("\n5️⃣  Final knowledge base summary:")
    summary = glcs.get_context_summary("company")
    print(f"   Total statements: {summary['total_forms']}")
    print("\n   All statements:")
    for stmt in summary['sample_statements']:
        print(f"      • {stmt}")

    # 6. Verify consistency
    print("\n6️⃣  Verifying knowledge base consistency:")
    report = glcs.verify_context("company")
    print_report(report)


def main():
    """Run all demos."""
    print("\n" + "🚀" * 35)
    print("  Advanced GLCS - Complete Pipeline Demo")
    print("🚀" * 35)

    print("\nThis demo showcases the full Advanced GLCS pipeline:")
    print("  • LLM-based parsing")
    print("  • 768-dimensional semantic embeddings")
    print("  • Vector-based memory storage (ChromaDB)")
    print("  • Advanced consistency checking")
    print("  • Semantic similarity search")
    print("  • Entity-based search")
    print("  • Batch processing")

    print("\n⚠️  Prerequisites:")
    print("  • Ollama must be running (ollama serve)")
    print("  • Model installed (ollama pull qwen2.5:0.5b)")
    print("  • ChromaDB installed (included in dependencies)")

    input("\nPress Enter to start the demo...")

    try:
        demo_basic_workflow()
        input("\nPress Enter for next demo...")

        demo_contradiction_detection()
        input("\nPress Enter for next demo...")

        demo_universal_rules()
        input("\nPress Enter for next demo...")

        demo_semantic_search()
        input("\nPress Enter for next demo...")

        demo_entity_search()
        input("\nPress Enter for next demo...")

        demo_complex_sentences()
        input("\nPress Enter for next demo...")

        demo_batch_processing()
        input("\nPress Enter for next demo...")

        demo_system_info()
        input("\nPress Enter for next demo...")

        demo_provider_switching()
        input("\nPress Enter for final scenario...")

        demo_full_scenario()

        print_section("Demo Complete!")
        print("\n✨ All demos completed successfully!")
        print("\n🎓 What you've learned:")
        print("  ✓ How to process statements with Advanced GLCS")
        print("  ✓ How contradiction detection works")
        print("  ✓ How to use semantic search")
        print("  ✓ How to search by entity")
        print("  ✓ How to handle complex sentences")
        print("  ✓ How to verify consistency")

        print("\n📚 Next steps:")
        print("  1. Read docs/LLM_PARSER_GUIDE.md for parser details")
        print("  2. Explore glcs/core/README.md for architecture")
        print("  3. Build your own GLCS-powered application!")

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        print("\nTroubleshooting:")
        print("  • Make sure Ollama is running: ollama serve")
        print("  • Check model is installed: ollama pull qwen2.5:0.5b")
        print("  • Verify dependencies: poetry install")
        print("  • See docs/LLM_PARSER_GUIDE.md for help")


if __name__ == "__main__":
    main()
