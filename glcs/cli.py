"""
Command Line Interface (CLI) for GLCS.
"""

import argparse
import sys
import json
from typing import List, Optional

from glcs import AdvancedGLCS
from glcs.utils.logger import setup_logging


def print_report(report):
    """Print consistency report to console."""
    if report.is_consistent:
        print(f"✅ CONSISTENT (Checked {report.total_forms_checked} forms)")
    else:
        print(f"❌ INCONSISTENT ({len(report.violations)} violations found)")
        for i, violation in enumerate(report.violations, 1):
            print(f"  {i}. [{violation.violation_type}] {violation.explanation} (Severity: {violation.severity})")


def handle_process(args, glcs: AdvancedGLCS):
    """Handle the 'process' command."""
    if not args.text:
        print("Error: No text provided to process.")
        return 1
    
    print(f"Processing: '{args.text}' in context '{args.context}'...")
    report = glcs.process_statement(args.text, args.context, auto_store=not args.no_store)
    print_report(report)
    return 0 if report.is_consistent else 1


def handle_verify(args, glcs: AdvancedGLCS):
    """Handle the 'verify' command."""
    print(f"Verifying consistency of context '{args.context}'...")
    report = glcs.verify_context(args.context)
    print_report(report)
    return 0 if report.is_consistent else 1


def handle_search(args, glcs: AdvancedGLCS):
    """Handle the 'search' command."""
    print(f"Searching for similarities to: '{args.query}'...")
    results = glcs.search_similar(args.query, context_id=args.context, top_k=args.top_k)
    
    if not results:
        print("No similar statements found.")
    else:
        print(f"Found {len(results)} matches:")
        for i, res in enumerate(results, 1):
            print(f"  {i}. {res.source_text}")
            print(f"     (Type: {res.logical_type.value}, Confidence: {res.confidence_score:.2f})")
    return 0


def handle_list_contexts(args, glcs: AdvancedGLCS):
    """Handle the 'list-contexts' command."""
    contexts = glcs.memory.list_contexts()
    if not contexts:
        print("No contexts found in memory store.")
    else:
        print(f"Found {len(contexts)} contexts:")
        for ctx in contexts:
            stats = glcs.memory.get_context_stats(ctx)
            print(f"  - {ctx} ({stats['total_forms']} statements)")
    return 0


def handle_clear(args, glcs: AdvancedGLCS):
    """Handle the 'clear' command."""
    if args.all:
        if not args.yes:
            confirm = input("Are you sure you want to clear ALL contexts? (y/N): ")
            if confirm.lower() != 'y':
                print("Aborted.")
                return 0
        
        count = glcs.clear_all()
        print(f"Cleared all {count} statements from storage.")
    elif args.context:
        count = glcs.clear_context(args.context)
        print(f"Cleared {count} statements from context '{args.context}'.")
    else:
        print("Error: Specify --context or --all to clear.")
        return 1
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="GLCS - Global Logical Context Store CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Global options
    parser.add_argument("--provider", help="LLM provider (ollama, openai, anthropic, groq, gemini)")
    parser.add_argument("--model", help="Model name override")
    parser.add_argument("--memory-path", help="Path to ChromaDB persistence")
    parser.add_argument("--in-memory", action="store_true", help="Use in-memory storage (non-persistent)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Process command
    proc_parser = subparsers.add_parser("process", help="Process and store a natural language statement")
    proc_parser.add_argument("text", help="Statement to process")
    proc_parser.add_argument("--context", default="default", help="Context/session ID")
    proc_parser.add_argument("--no-store", action="store_true", help="Do not store the statement even if consistent")
    
    # Verify command
    ver_parser = subparsers.add_parser("verify", help="Verify internal consistency of a context")
    ver_parser.add_argument("--context", default="default", help="Context/session ID")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search for semantically similar statements")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--context", help="Filter by context ID")
    search_parser.add_argument("--top-k", type=int, default=5, help="Number of results to return")
    
    # Contexts command
    subparsers.add_parser("list-contexts", help="List all available contexts and their stats")
    
    # Clear command
    clear_parser = subparsers.add_parser("clear", help="Clear stored statements")
    clear_parser.add_argument("--context", help="Clear a specific context")
    clear_parser.add_argument("--all", action="store_true", help="Clear all contexts")
    clear_parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0

    # Setup logging
    setup_logging()
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize GLCS
        glcs = AdvancedGLCS(
            parser_provider=args.provider or 'ollama',
            parser_model=args.model,
            memory_path=args.memory_path,
            in_memory=args.in_memory
        )
        
        # Dispatch command
        handlers = {
            "process": handle_process,
            "verify": handle_verify,
            "search": handle_search,
            "list-contexts": handle_list_contexts,
            "clear": handle_clear
        }
        
        return handlers[args.command](args, glcs)
        
    except Exception as e:
        print(f"Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
