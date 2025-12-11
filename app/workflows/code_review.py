"""Sample Code Review Workflow (Option A)."""

from typing import Dict, Any
from app.tools import tool_registry


def extract_code(state: Dict[str, Any]) -> Dict[str, Any]:
    """Extract code snippet from input."""
    code_input = state.get("code_content", "")
    state["extracted_code"] = tool_registry.call("extract_text", code_input)
    return state


def check_syntax(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based syntax check (no actual parsing)."""
    code = state.get("extracted_code", "")
    
    # Simple rule-based checks
    issues = []
    
    if "{" in code and "}" not in code:
        issues.append("Unmatched braces")
    if code.count("(") != code.count(")"):
        issues.append("Unmatched parentheses")
    if "import" in code and len(code.split("import")) > 5:
        issues.append("Too many imports")
    
    state["syntax_issues"] = issues
    state["syntax_passed"] = len(issues) == 0
    
    return state


def analyze_style(state: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based style analysis."""
    code = state.get("extracted_code", "")
    
    warnings = []
    
    # Check line length
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if len(line) > 100:
            warnings.append(f"Line {i+1}: exceeds 100 characters")
    
    # Check naming conventions
    if "_" * 2 in code:
        warnings.append("Potential dunder usage without context")
    
    state["style_warnings"] = warnings
    state["style_passed"] = len(warnings) <= 2
    
    return state


def generate_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate code review report."""
    report = {
        "syntax_issues": state.get("syntax_issues", []),
        "style_warnings": state.get("style_warnings", []),
        "passed_checks": {
            "syntax": state.get("syntax_passed", False),
            "style": state.get("style_passed", False),
        },
    }
    
    state["review_report"] = report
    state["review_complete"] = True
    
    return state


# Conditional function for branching
def should_generate_report(state: Dict[str, Any]) -> bool:
    """Determine if we should generate a report."""
    return state.get("syntax_passed", False) and state.get("style_passed", False)
