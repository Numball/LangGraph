"""Core workflow engine with support for nodes, edges, branching, and looping.

This module implements the fundamental building blocks of our minimal workflow engine:
- Node: A pure Python function that processes state
- Edge: A directed connection between nodes with optional conditional routing
- Graph: A container that manages nodes, edges, and orchestrates execution
- WorkflowEngine: High-level API for creating and executing workflow graphs

We use a queue-based execution model with state passing between nodes,
supporting both linear workflows and complex branching logic.
"""

import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class NodeStatus(str, Enum):
    """Possible outcomes of node execution: success, error, or skipped."""
    SUCCESS = "success"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class ExecutionEntry:
    """Record of a single node's execution in a workflow run."""
    node_name: str
    status: NodeStatus
    input_state: Dict[str, Any]
    output_state: Dict[str, Any]
    error_message: Optional[str] = None


class Node:
    """A single step in a workflow graph that wraps a pure Python function."""
    
    def __init__(self, name: str, func: Callable, node_type: str = "task"):
        """Initialize a workflow node.
        
        Args:
            name: Unique identifier for this node
            func: Pure Python function (state: Dict) -> Dict
            node_type: Classification of the node (default: "task")
        """
        self.name = name
        self.func = func
        self.node_type = node_type
    
    def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        """Execute the node function on the given state.
        
        Args:
            state: Current workflow state
            
        Returns:
            Tuple of (updated_state, error_message) where error_message is None on success
        """
        try:
            # Pass a copy to prevent accidental mutations
            updated_state = self.func(state.copy())
            return updated_state, None
        except Exception as e:
            # Catch and return errors for logging
            return state, str(e)


class Edge:
    """A directed connection between two nodes, optionally with conditional routing."""
    
    def __init__(self, source: str, target: str, condition: Optional[Callable] = None):
        """Create an edge between two nodes.
        
        Args:
            source: Name of the source node
            target: Name of the target node
            condition: Optional function (state: Dict) -> bool for conditional routing
        """
        self.source = source
        self.target = target
        self.condition = condition
    
    def should_execute(self, state: Dict[str, Any]) -> bool:
        """Check if we should traverse this edge based on its condition.
        
        Args:
            state: Current workflow state
            
        Returns:
            True if edge should be traversed, False otherwise
        """
        if self.condition is None:
            return True
        try:
            return self.condition(state)
        except Exception:
            # Handle condition errors gracefully
            return False


class Graph:
    """A workflow represented as a directed graph of nodes and edges."""
    
    def __init__(self, name: str):
        """Create a new workflow graph.
        
        Args:
            name: Human-readable name for the workflow
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, List[Edge]] = {}
    
    def add_node(self, name: str, func: Callable, node_type: str = "task") -> None:
        """Add a node to the graph.
        
        Args:
            name: Unique identifier for this node
            func: The function this node will execute
            node_type: Classification of the node
        """
        self.nodes[name] = Node(name, func, node_type)
        if name not in self.edges:
            self.edges[name] = []
    
    def add_edge(self, source: str, target: str, condition: Optional[Callable] = None) -> None:
        """Connect two nodes with a directed edge.
        
        Args:
            source: Source node name
            target: Target node name
            condition: Optional condition function for selective routing
            
        Raises:
            ValueError: If source or target nodes don't exist
        """
        if source not in self.nodes or target not in self.nodes:
            raise ValueError(f"Invalid edge: both nodes must exist ({source} -> {target})")
        
        if source not in self.edges:
            self.edges[source] = []
        
        self.edges[source].append(Edge(source, target, condition))
    
    def _get_next_nodes(self, current_node: str, state: Dict[str, Any]) -> List[str]:
        """Get next nodes to execute based on edge conditions.
        
        Args:
            current_node: The node that just completed
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
        """Execute the workflow graph using queue-based orchestration.
        
        Args:
            initial_state: Starting state for the workflow
            start_nodes: Nodes to begin execution from (auto-detects entry nodes if None)
            max_iterations: Safety limit to prevent infinite loops
            
        Returns:
            Tuple of (final_state, execution_log)
        """
        if start_nodes is None:
            # Auto-detect entry nodes (nodes with no incoming edges)
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
            
            # Prevent infinite loops: skip re-execution after seeing all nodes
            if node_name in executed and iteration > len(self.nodes):
                continue
            
            if node_name not in self.nodes:
                continue
            
            node = self.nodes[node_name]
            input_state = state.copy()
            
            # Execute the node and capture state transformation
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
            
            # Queue next nodes based on edge conditions
            next_nodes = self._get_next_nodes(node_name, state)
            queue.extend(next_nodes)
        
        return state, execution_log


class WorkflowEngine:
    """High-level API for creating and executing workflow graphs."""
    
    def __init__(self):
        """Initialize a workflow engine instance."""
        self.graphs: Dict[str, Graph] = {}
        self.run_history: Dict[str, Tuple[Dict[str, Any], List[ExecutionEntry]]] = {}
    
    def create_graph(self, name: str) -> Graph:
        """Create and register a new workflow graph.
        
        Args:
            name: Human-readable name for the workflow
            
        Returns:
            The newly created Graph object
        """
        graph = Graph(name)
        self.graphs[graph.id] = graph
        return graph
    
    def get_graph(self, graph_id: str) -> Optional[Graph]:
        """Retrieve a graph by its ID.
        
        Args:
            graph_id: The unique identifier of the graph
            
        Returns:
            The Graph object if found, None otherwise
        """
        return self.graphs.get(graph_id)
    
    def run_graph(
        self,
        graph_id: str,
        initial_state: Dict[str, Any],
        max_iterations: int = 100
    ) -> Tuple[str, Dict[str, Any], List[ExecutionEntry]]:
        """Execute a workflow graph and record results.
        
        Args:
            graph_id: The identifier of the graph to execute
            initial_state: The starting state for the workflow
            max_iterations: Safety limit on iterations
            
        Returns:
            Tuple of (run_id, final_state, execution_log)
            
        Raises:
            ValueError: If graph_id is not found
        """
        graph = self.graphs.get(graph_id)
        if not graph:
            raise ValueError(f"Graph {graph_id} not found in engine")
        
        final_state, execution_log = graph.execute(initial_state, max_iterations=max_iterations)
        run_id = str(uuid.uuid4())
        self.run_history[run_id] = (final_state, execution_log)
        
        return run_id, final_state, execution_log
    
    def get_run_state(self, run_id: str) -> Optional[Tuple[Dict[str, Any], List[ExecutionEntry]]]:
        """Retrieve the results of a previous workflow execution.
        
        Args:
            run_id: The identifier of the execution to query
            
        Returns:
            Tuple of (final_state, execution_log) if found, None otherwise
        """
        return self.run_history.get(run_id)
