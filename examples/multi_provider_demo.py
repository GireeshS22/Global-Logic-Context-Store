"""
Multi-Provider Demo for GLCS

This example demonstrates using multiple LLM providers with GLCS.
"""

import os
from glcs import GLCSWrapper


def demo_ollama():
    """Demo using Ollama (FREE, local)"""
    print("\n" + "="*60)
    print("OLLAMA DEMO (FREE, 100% Local)")
    print("="*60)

    try:
        wrapper = GLCSWrapper(provider='ollama')
        print(f"✅ Using: {wrapper.provider_name}")
        print(f"   Model: {wrapper.get_provider_info()['model']}")
        print(f"   Privacy: {wrapper.get_provider_info()['privacy']}")

        result = wrapper.generate("What is 2 + 2?")
        print(f"\nPrompt: What is 2 + 2?")
        print(f"Response: {result['response']}")

    except Exception as e:
        print(f"❌ Ollama Error: {e}")
        print("   Make sure Ollama is installed and running!")
        print("   Install: https://ollama.ai")
        print("   Then run: ollama serve")


def demo_openai():
    """Demo using OpenAI"""
    print("\n" + "="*60)
    print("OPENAI DEMO (GPT-4o-mini)")
    print("="*60)

    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OPENAI_API_KEY not set. Skipping.")
        print("   Get key from: https://platform.openai.com/api-keys")
        return

    try:
        wrapper = GLCSWrapper(provider='openai')
        print(f"✅ Using: {wrapper.provider_name}")
        print(f"   Model: {wrapper.get_provider_info()['model']}")

        result = wrapper.generate("What is the capital of France?")
        print(f"\nPrompt: What is the capital of France?")
        print(f"Response: {result['response']}")

    except Exception as e:
        print(f"❌ OpenAI Error: {e}")


def demo_gemini():
    """Demo using Google Gemini"""
    print("\n" + "="*60)
    print("GEMINI DEMO (Cheapest Cloud Option)")
    print("="*60)

    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not set. Skipping.")
        print("   Get key from: https://makersuite.google.com/app/apikey")
        return

    try:
        wrapper = GLCSWrapper(provider='gemini')
        print(f"✅ Using: {wrapper.provider_name}")
        print(f"   Model: {wrapper.get_provider_info()['model']}")

        result = wrapper.generate("Explain quantum computing in one sentence")
        print(f"\nPrompt: Explain quantum computing in one sentence")
        print(f"Response: {result['response']}")

    except Exception as e:
        print(f"❌ Gemini Error: {e}")


def demo_anthropic():
    """Demo using Anthropic Claude"""
    print("\n" + "="*60)
    print("ANTHROPIC DEMO (Claude)")
    print("="*60)

    if not os.getenv('ANTHROPIC_API_KEY'):
        print("❌ ANTHROPIC_API_KEY not set. Skipping.")
        print("   Get key from: https://console.anthropic.com/")
        return

    try:
        wrapper = GLCSWrapper(provider='anthropic')
        print(f"✅ Using: {wrapper.provider_name}")
        print(f"   Model: {wrapper.get_provider_info()['model']}")

        result = wrapper.generate("What is machine learning?")
        print(f"\nPrompt: What is machine learning?")
        print(f"Response: {result['response']}")

    except Exception as e:
        print(f"❌ Anthropic Error: {e}")


def demo_groq():
    """Demo using Groq (Ultra-fast)"""
    print("\n" + "="*60)
    print("GROQ DEMO (Ultra-Fast Inference)")
    print("="*60)

    if not os.getenv('GROQ_API_KEY'):
        print("❌ GROQ_API_KEY not set. Skipping.")
        print("   Get key from: https://console.groq.com/keys")
        return

    try:
        wrapper = GLCSWrapper(provider='groq')
        print(f"✅ Using: {wrapper.provider_name}")
        print(f"   Model: {wrapper.get_provider_info()['model']}")

        result = wrapper.generate("What is AI?")
        print(f"\nPrompt: What is AI?")
        print(f"Response: {result['response']}")

    except Exception as e:
        print(f"❌ Groq Error: {e}")


def demo_provider_switching():
    """Demo switching between providers"""
    print("\n" + "="*60)
    print("PROVIDER SWITCHING DEMO")
    print("="*60)

    try:
        # Start with Ollama
        wrapper = GLCSWrapper(provider='ollama')
        print(f"\n1. Starting with: {wrapper.provider_name}")

        # Try to switch to OpenAI if available
        if os.getenv('OPENAI_API_KEY'):
            wrapper.switch_provider('openai')
            print(f"2. Switched to: {wrapper.provider_name}")

            # Switch to Gemini if available
            if os.getenv('GOOGLE_API_KEY'):
                wrapper.switch_provider('gemini')
                print(f"3. Switched to: {wrapper.provider_name}")

            # Switch back to Ollama
            wrapper.switch_provider('ollama')
            print(f"4. Switched back to: {wrapper.provider_name}")

        print("\n✅ Provider switching works!")

    except Exception as e:
        print(f"❌ Error: {e}")


def demo_consistency_checking():
    """Demo consistency checking across providers"""
    print("\n" + "="*60)
    print("CONSISTENCY CHECKING DEMO")
    print("="*60)

    try:
        wrapper = GLCSWrapper(provider='ollama')
        print(f"Using: {wrapper.provider_name}\n")

        # Store a fact
        print("Storing fact: 'All birds can fly'")
        result1 = wrapper.generate("All birds can fly")
        print(f"Consistent: {result1['consistent']}\n")

        # Try contradictory statement
        print("Checking: 'Penguins cannot fly'")
        result2 = wrapper.generate("Penguins cannot fly")
        print(f"Consistent: {result2['consistent']}")

        if not result2['consistent']:
            print(f"Violations: {result2['violations']}")

        # Get memory stats
        stats = wrapper.memory.get_stats()
        print(f"\nMemory stats: {stats}")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run all demos"""
    print("\n")
    print("╔" + "="*58 + "╗")
    print("║" + " "*17 + "GLCS MULTI-PROVIDER DEMO" + " "*17 + "║")
    print("╚" + "="*58 + "╝")

    # Run demos
    demo_ollama()
    demo_openai()
    demo_gemini()
    demo_anthropic()
    demo_groq()
    demo_provider_switching()
    demo_consistency_checking()

    print("\n" + "="*60)
    print("DEMO COMPLETE!")
    print("="*60)
    print("\n💡 Tips:")
    print("   - Ollama is FREE and runs locally!")
    print("   - Gemini is the cheapest cloud option ($0.04 per 1K)")
    print("   - OpenAI has best reliability for production")
    print("   - See docs/PROVIDER_GUIDE.md for full comparison")
    print("\n")


if __name__ == "__main__":
    main()
