"""Simple test script to verify the workflow engine works."""

import sys
from typing import Dict, Any

# Add the project root to the path so we can import app module
sys.path.insert(0, r"c:\Projects\LangGraph")

# Import the engine and workflow
from app.engine import WorkflowEngine
from app.workflows.code_review import (
    extract_code,
    check_syntax,
    analyze_style,
    generate_report,
    should_generate_report,
)


def test_code_review_workflow():
    """Test the code review workflow."""
    print("=" * 60)
    print("Testing Code Review Workflow")
    print("=" * 60)
    
    # Create engine
    engine = WorkflowEngine()
    
    # Create graph
    graph = engine.create_graph("CodeReview")
    print(f"✓ Created graph: {graph.id}")
    
    # Add nodes
    graph.add_node("extract", extract_code)
    graph.add_node("check_syntax", check_syntax)
    graph.add_node("analyze_style", analyze_style)
    graph.add_node("generate_report", generate_report)
    print("✓ Added 4 nodes")
    
    # Add edges with conditions
    graph.add_edge("extract", "check_syntax")
    graph.add_edge("check_syntax", "analyze_style")
    graph.add_edge("analyze_style", "generate_report", condition=should_generate_report)
    print("✓ Added edges with branching logic")
    
    # Test input
    test_code = """
def hello_world():
    print("Hello, World!")
    return True
"""
    
    initial_state = {
        "code_content": test_code,
    }
    
    # Execute the graph
    print("\nExecuting workflow...")
    run_id, final_state, execution_log = engine.run_graph(graph.id, initial_state)
    
    print(f"\n✓ Execution completed!")
    print(f"  Run ID: {run_id}")
    print(f"  Nodes executed: {len(execution_log)}")
    
    # Print execution log
    print("\nExecution Log:")
    print("-" * 60)
    for i, entry in enumerate(execution_log, 1):
        status_symbol = "✓" if entry.status.value == "success" else "✗"
        print(f"{i}. {status_symbol} {entry.node_name}: {entry.status.value}")
        if entry.error_message:
            print(f"   Error: {entry.error_message}")
    
    # Print final state
    print("\nFinal State:")
    print("-" * 60)
    for key, value in final_state.items():
        if isinstance(value, (dict, list)):
            print(f"{key}: {type(value).__name__} (length: {len(value)})")
        else:
            print(f"{key}: {value}")
    
    # Check results
    print("\nResults:")
    print("-" * 60)
    print(f"Code extracted: {len(final_state.get('extracted_code', ''))} chars")
    print(f"Syntax issues: {len(final_state.get('syntax_issues', []))}")
    print(f"Style warnings: {len(final_state.get('style_warnings', []))}")
    print(f"Review complete: {final_state.get('review_complete', False)}")
    
    print("\n" + "=" * 60)
    print("✓ Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_code_review_workflow()
    except Exception as e:
        print(f"\nX Error during test: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
