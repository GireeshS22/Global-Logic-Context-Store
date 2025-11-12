"""
Streamlit demo app for GLCS

This interactive web app allows you to:
- Enter logical statements
- See real-time contradiction detection
- Browse stored knowledge
- Visualize the knowledge base
"""

import streamlit as st
import os
from glcs import SimpleParser, SimpleMemory, ConsistencyChecker, GLCSWrapper
from glcs.core import LogicalType


# Page configuration
st.set_page_config(
    page_title="GLCS Demo",
    page_icon="🧠",
    layout="wide"
)


def init_glcs():
    """Initialize GLCS components"""
    if 'memory' not in st.session_state:
        st.session_state.parser = SimpleParser()
        st.session_state.memory = SimpleMemory(persist_path="streamlit_memory.json")
        st.session_state.checker = ConsistencyChecker(st.session_state.memory)
        st.session_state.history = []
        st.session_state.last_checked_stmt = None
        st.session_state.show_store_success = False


def main():
    """Main Streamlit app"""

    init_glcs()

    # Header
    st.title("🧠 GLCS: Global Logical Context Store")
    st.markdown("*Practical contradiction detection for logical statements*")

    # Sidebar
    with st.sidebar:
        st.header("📊 Knowledge Base Stats")

        stats = st.session_state.memory.get_stats()
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Universal Rules", stats['universal'])
            st.metric("Ground Facts", stats['ground'])

        with col2:
            st.metric("Conditionals", stats['conditional'])
            st.metric("Total", stats['total'])

        st.divider()

        # Actions
        st.header("⚙️ Actions")

        if st.button("🗑️ Clear Memory", use_container_width=True):
            st.session_state.memory.clear()
            st.session_state.history = []
            st.session_state.last_checked_stmt = None
            st.rerun()

        if st.button("✅ Verify Knowledge Base", use_container_width=True):
            is_consistent, inconsistencies = st.session_state.checker.verify_knowledge_base()
            if is_consistent:
                st.success("✓ Knowledge base is consistent!")
            else:
                st.error("✗ Inconsistencies found:")
                for inc in inconsistencies:
                    st.write(f"- {inc}")

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["💬 Interactive", "📚 Knowledge Base", "ℹ️ About"])

    # Tab 1: Interactive statement checking
    with tab1:
        st.header("Enter a Statement")

        # Show success message if we just stored something
        if st.session_state.show_store_success:
            st.success("✅ Statement stored successfully!")
            st.session_state.show_store_success = False

        statement = st.text_input(
            "Type a logical statement:",
            placeholder="e.g., 'All birds can fly' or 'John is a manager'",
            key="statement_input"
        )

        check_button = st.button("Check Statement", type="primary", use_container_width=True)

        if check_button and statement:
            # Parse the statement
            stmt = st.session_state.parser.parse(statement)

            if stmt is None:
                st.warning("⚠️ Could not parse this statement into logical form.")
                st.info("Try statements like: 'All X can Y', 'John is X', or 'If X then Y'")
                st.session_state.last_checked_stmt = None
            else:
                # Store in session state for the store button
                st.session_state.last_checked_stmt = {
                    'stmt': stmt,
                    'text': statement
                }

                # Display parsed information
                st.success(f"✓ Parsed as **{stmt.type.value}** statement")

                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Subject:** {stmt.subject}")
                with col2:
                    st.write(f"**Predicate:** {stmt.predicate}")
                with col3:
                    if stmt.object:
                        st.write(f"**Object:** {stmt.object}")

                # Check consistency
                is_consistent, confidence, violations = st.session_state.checker.check_consistency(stmt)

                st.divider()

                if is_consistent:
                    st.success(f"✅ Statement is consistent! (confidence: {confidence:.2%})")

                    # Show supporting facts
                    supporting = st.session_state.checker.get_supporting_facts(stmt)
                    if supporting:
                        with st.expander("📎 Related Facts"):
                            for fact in supporting:
                                st.write(f"- {fact.raw_text}")

                else:
                    st.error(f"❌ Contradiction detected! (confidence: {confidence:.2%})")

                    st.write("**Violations:**")
                    for violation in violations:
                        st.write(f"- {violation}")

                    # Suggestion
                    suggestion = st.session_state.checker.suggest_alternative(stmt, violations)
                    if suggestion:
                        st.info(f"💡 **Suggestion:** {suggestion}")

                    # Store history for inconsistent statements
                    st.session_state.history.append({
                        'statement': statement,
                        'consistent': False,
                        'violations': violations
                    })

        # Store button - shown if there's a last checked statement that was consistent
        if st.session_state.last_checked_stmt is not None:
            stmt = st.session_state.last_checked_stmt['stmt']
            is_consistent, _, _ = st.session_state.checker.check_consistency(stmt)

            if is_consistent:
                st.divider()
                if st.button("💾 Store in Memory", key="store_button", use_container_width=True, type="primary"):
                    success = st.session_state.memory.store(stmt)
                    if success:
                        st.session_state.history.append({
                            'statement': st.session_state.last_checked_stmt['text'],
                            'consistent': True,
                            'violations': []
                        })
                        st.session_state.show_store_success = True
                        st.session_state.last_checked_stmt = None
                        st.rerun()
                    else:
                        st.error("❌ Could not store (may already exist or conflict with existing facts)")

        # Show recent history
        if st.session_state.history:
            st.divider()
            st.subheader("📜 Recent Statements")

            for i, entry in enumerate(reversed(st.session_state.history[-5:])):
                with st.expander(f"{i+1}. {entry['statement'][:50]}..."):
                    if entry['consistent']:
                        st.success("✅ Consistent")
                    else:
                        st.error("❌ Inconsistent")
                        for v in entry['violations']:
                            st.write(f"- {v}")

    # Tab 2: Browse knowledge base
    with tab2:
        st.header("Stored Knowledge")

        view_type = st.selectbox(
            "View:",
            ["All Statements", "Universal Rules", "Conditionals", "Ground Facts"]
        )

        if view_type == "All Statements":
            all_stmts = st.session_state.memory.query()

            if all_stmts:
                for stmt in all_stmts:
                    with st.container():
                        col1, col2 = st.columns([1, 5])
                        with col1:
                            if stmt.type == LogicalType.UNIVERSAL:
                                st.write("🌐")
                            elif stmt.type == LogicalType.CONDITIONAL:
                                st.write("🔀")
                            else:
                                st.write("📌")
                        with col2:
                            st.write(f"**{stmt.raw_text}**")
                            st.caption(f"Type: {stmt.type.value} | Confidence: {stmt.confidence:.2%}")
            else:
                st.info("No statements in memory yet.")

        elif view_type == "Universal Rules":
            universals = st.session_state.memory.query(type=LogicalType.UNIVERSAL)

            if universals:
                for stmt in universals:
                    st.write(f"🌐 {stmt.raw_text}")
            else:
                st.info("No universal rules stored.")

        elif view_type == "Conditionals":
            conditionals = st.session_state.memory.query(type=LogicalType.CONDITIONAL)

            if conditionals:
                for stmt in conditionals:
                    st.write(f"🔀 {stmt.raw_text}")
            else:
                st.info("No conditional rules stored.")

        elif view_type == "Ground Facts":
            grounds = st.session_state.memory.query(type=LogicalType.GROUND)

            if grounds:
                for stmt in grounds:
                    st.write(f"📌 {stmt.raw_text}")
            else:
                st.info("No ground facts stored.")

    # Tab 3: About
    with tab3:
        st.header("About GLCS")

        st.markdown("""
        **Global Logical Context Store (GLCS)** is a practical tool for detecting logical
        contradictions in conversations and text.

        ### Features

        - **Simple Parsing**: Extract logical statements from natural language
        - **Contradiction Detection**: Catch 50-70% of common logical errors
        - **Memory Persistence**: Remember facts across sessions
        - **Fast**: <500ms latency for most operations

        ### Supported Statement Types

        1. **Universal Rules**: "All X are Y", "Every X has Y", "No X can Y"
        2. **Conditionals**: "If X then Y", "When X, Y"
        3. **Ground Facts**: "John is X", "Mary has Y"

        ### Examples

        Try these statements to see GLCS in action:

        - "All birds can fly"
        - "Penguins are birds"
        - "Penguins cannot fly" ← Contradiction!

        ### Limitations

        - Simplified ontology (limited knowledge of categories)
        - Rule-based parsing (may miss complex statements)
        - No deep logical reasoning chains
        - Focuses on practical use cases, not perfect logic

        ### Learn More

        - [GitHub Repository](https://github.com/GireeshS22/Global-Logic-Context-Store)
        - [Documentation](docs/getting_started.md)
        """)

        st.divider()

        st.caption("Built with ❤️ using Python and Streamlit")


if __name__ == "__main__":
    main()
