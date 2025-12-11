"""Tool registry for helper functions that nodes can invoke."""

from typing import Any, Callable, Dict, Optional


class ToolRegistry:
    """Registry for managing tool functions that can be called from nodes."""
    
    def __init__(self):
        """Initialize the tool registry."""
        self._tools: Dict[str, Callable] = {}
    
    def register(self, name: str) -> Callable:
        """
        Decorator to register a tool function.
        
        Args:
            name: Unique identifier for the tool
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            self._tools[name] = func
            return func
        return decorator
    
    def call(self, tool_name: str, *args: Any, **kwargs: Any) -> Any:
        """
        Call a registered tool.
        
        Args:
            tool_name: Name of the tool to call
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Result from the tool function
            
        Raises:
            ValueError: If tool not found
        """
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' not found in registry")
        return self._tools[tool_name](*args, **kwargs)
    
    def get(self, tool_name: str) -> Optional[Callable]:
        """
        Get a tool function by name.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            Tool function or None if not found
        """
        return self._tools.get(tool_name)
    
    def list_tools(self) -> list[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())


# Global tool registry instance
tool_registry = ToolRegistry()


# ============================================================================
# Example Tools (for sample workflows)
# ============================================================================

@tool_registry.register("extract_text")
def extract_text(content: str, max_length: int = 500) -> str:
    """Extract text from content, limited to max_length."""
    return content[:max_length]


@tool_registry.register("count_words")
def count_words(text: str) -> int:
    """Count number of words in text."""
    return len(text.split())


@tool_registry.register("analyze_sentiment")
def analyze_sentiment(text: str) -> str:
    """Rule-based sentiment analysis (no ML)."""
    positive_words = {"good", "great", "excellent", "amazing", "wonderful"}
    negative_words = {"bad", "terrible", "awful", "horrible", "poor"}
    
    words = text.lower().split()
    pos_count = sum(1 for w in words if w in positive_words)
    neg_count = sum(1 for w in words if w in negative_words)
    
    if pos_count > neg_count:
        return "positive"
    elif neg_count > pos_count:
        return "negative"
    else:
        return "neutral"


@tool_registry.register("format_output")
def format_output(data: Any, format_type: str = "json") -> str:
    """Format data to specified format type."""
    if format_type == "json":
        import json
        return json.dumps(data, indent=2)
    return str(data)
