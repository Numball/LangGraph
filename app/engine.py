"""Core workflow engine with support for nodes, edges, branching, and looping."""

import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NodeStatus(str, Enum):
    """Status of a node execution."""
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ExecutionEntry:
    """Single execution log entry."""
    node_name: str
    status: NodeStatus
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    error_message: Optional[str] = None


class Node:
    """Represents a node in the workflow graph."""
    
    def __init__(self, name: str, func: Callable, node_type: str = "task"):
        """
        Initialize a node.
        
        Args:
            name: Unique identifier for the node
            func: Pure Python function that takes state dict and returns updated state
            node_type: Type of node (task, conditional, etc.)
        """
        self.name = name
        self.func = func
        self.node_type = node_type
    
    def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """
        Execute the node function.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple of (updated_state, error_message)
        """
        try:
            updated_state = self.func(state.copy())
            return updated_state, None
        except Exception as e:
            return state, str(e)


class Edge:
    """Represents an edge connecting two nodes."""
    
    def __init__(self, source: str, target: str, condition: Optional[Callable] = None):
        """
        Initialize an edge.
        
        Args:
            source: Source node name
            target: Target node name
            condition: Optional function that evaluates state to determine if edge should be taken
        """
        self.source = source
        self.target = target
        self.condition = condition
    
    def should_execute(self, state: Dict[str, Any]) -> bool:
        """Check if this edge should be traversed."""
        if self.condition is None:
            return True
        try:
            return self.condition(state)
        except Exception:
            return False


class Graph:
    """Directed acyclic graph for workflow execution."""
    
    def __init__(self, name: str):
        """
        Initialize a graph.
        
        Args:
            name: Graph identifier
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Edge]] = {}  # source_node -> list of outgoing edges
    
    def add_node(self, name: str, func: Callable, node_type: str = "task") -> None:
        """Add a node to the graph."""
        self.nodes[name] = Node(name, func, node_type)
        if name not in self.edges:
            self.edges[name] = []
    
    def add_edge(self, source: str, target: str, condition: Optional[Callable] = None) -> None:
        """
        Add an edge from source to target node.
        
        Args:
            source: Source node name
            target: Target node name
            condition: Optional condition function for conditional routing
        """
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Invalid edge: nodes must exist ({source} -> {target})")
        
        if source not in self.edges:
            self.edges[source] = []
        
        self.edges[source].append(Edge(source, target, condition))
    
    def _get_next_nodes(self, current_node: str, state: Dict[str, Any]) -> List[str]:
        """
        Get next nodes to execute based on edges and conditions.
        
        Args:
            current_node: Current node name
            state: Current workflow state
            
        Returns:
            List of next node names to execute
        """
        next_nodes = []
        if current_node in self.edges:
            for edge in self.edges[current_node]:
                if edge.should_execute(state):
                    next_nodes.append(edge.target)
        return next_nodes
    
    def execute(
        self,
        initial_state: Dict[str, Any],
        start_nodes: Optional[List[str]] = None,
        max_iterations: int = 100
    ) -> Tuple[Dict[str, Any], List[ExecutionEntry]]:
        """
        Execute the graph starting from specified nodes.
        
        Args:
            initial_state: Initial state dictionary
            start_nodes: List of node names to start from (defaults to all nodes with no incoming edges)
            max_iterations: Maximum iterations to prevent infinite loops
            
        Returns:
            Tuple of (final_state, execution_log)
        """
        if start_nodes is None:
            # Find nodes with no incoming edges
            incoming = set()
            for edges in self.edges.values():
                for edge in edges:
                    incoming.add(edge.target)
            start_nodes = [name for name in self.nodes.keys() if name not in incoming]
        
        state = initial_state.copy()
        execution_log: List[ExecutionEntry] = []
        queue = list(start_nodes)
        executed = set()
        iteration = 0
        
        while queue and iteration < max_iterations:
            iteration += 1
            node_name = queue.pop(0)
            
            # Prevent infinite loops by tracking executed nodes per iteration cycle
            if node_name in executed and iteration > len(self.nodes):
                continue
            
            if node_name not in self.nodes:
                continue
            
            node = self.nodes[node_name]
            input_state = state.copy()
            
            # Execute the node
            state, error = node.execute(state)
            
            status = NodeStatus.ERROR if error else NodeStatus.SUCCESS
            execution_log.append(ExecutionEntry(
                node_name=node_name,
                status=status,
                input_state=input_state,
                output_state=state,
                error_message=error
            ))
            
            executed.add(node_name)
            
            # Add next nodes to queue
            next_nodes = self._get_next_nodes(node_name, state)
            queue.extend(next_nodes)
        
        return state, execution_log


class WorkflowEngine:
    """High-level workflow execution engine."""
    
    def __init__(self):
        """Initialize the workflow engine."""
        self.graphs: Dict[str, Graph] = {}
        self.run_history: Dict[str, Tuple[Dict[str, Any], List[ExecutionEntry]]] = {}
    
    def create_graph(self, name: str) -> Graph:
        """Create a new graph."""
        graph = Graph(name)
        self.graphs[graph.id] = graph
        return graph
    
    def get_graph(self, graph_id: str) -> Optional[Graph]:
        """Retrieve a graph by ID."""
        return self.graphs.get(graph_id)
    
    def run_graph(
        self,
        graph_id: str,
        initial_state: Dict[str, Any],
        max_iterations: int = 100
    ) -> Tuple[str, Dict[str, Any], List[ExecutionEntry]]:
        """
        Execute a graph.
        
        Args:
            graph_id: Graph identifier
            initial_state: Initial workflow state
            max_iterations: Maximum iterations for loop prevention
            
        Returns:
            Tuple of (run_id, final_state, execution_log)
        """
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found")
        
        final_state, execution_log = graph.execute(initial_state, max_iterations=max_iterations)
        run_id = str(uuid.uuid4())
        self.run_history[run_id] = (final_state, execution_log)
        
        return run_id, final_state, execution_log
    
    def get_run_state(self, run_id: str) -> Optional[Tuple[Dict[str, Any], List[ExecutionEntry]]]:
        """Retrieve the final state and log of a run."""
        return self.run_history.get(run_id)
