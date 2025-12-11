"""Pydantic schemas for request/response validation and state definition."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NodeDefinition(BaseModel):
    """Definition of a single node in the graph."""
    name: str = Field(..., description="Unique node identifier")
    type: str = Field(default="task", description="Node type: 'task', 'conditional', etc.")


class EdgeDefinition(BaseModel):
    """Definition of an edge connecting two nodes."""
    source: str = Field(..., description="Source node name")
    target: str = Field(..., description="Target node name")
    condition: Optional[str] = Field(default=None, description="Optional condition for conditional edges")


class GraphDefinition(BaseModel):
    """Complete graph definition with nodes and edges."""
    name: str = Field(..., description="Graph name")
    nodes: List[NodeDefinition] = Field(..., description="List of nodes")
    edges: List[EdgeDefinition] = Field(..., description="List of edges defining execution flow")


class CreateGraphRequest(BaseModel):
    """Request to create a new graph."""
    name: str = Field(..., description="Graph name")
    nodes: List[NodeDefinition] = Field(..., description="List of nodes")
    edges: List[EdgeDefinition] = Field(..., description="List of edges")


class CreateGraphResponse(BaseModel):
    """Response after creating a graph."""
    graph_id: str = Field(..., description="Unique graph identifier")
    message: str = Field(default="Graph created successfully")


class RunGraphRequest(BaseModel):
    """Request to execute a graph."""
    graph_id: str = Field(..., description="Graph identifier")
    initial_state: Dict[str, Any] = Field(default_factory=dict, description="Initial state dictionary")
    max_iterations: int = Field(default=100, ge=1, description="Maximum iterations for loops")


class ExecutionLog(BaseModel):
    """Log entry for a node execution."""
    node_name: str = Field(..., description="Name of the executed node")
    status: str = Field(..., description="Execution status: success, error, skipped")
    input_state: Dict[str, Any] = Field(default_factory=dict, description="State before execution")
    output_state: Dict[str, Any] = Field(default_factory=dict, description="State after execution")
    error_message: Optional[str] = Field(default=None, description="Error details if status is error")


class RunGraphResponse(BaseModel):
    """Response after executing a graph."""
    run_id: str = Field(..., description="Unique run identifier")
    final_state: Dict[str, Any] = Field(..., description="Final state after execution")
    execution_log: List[ExecutionLog] = Field(..., description="Log of all node executions")
    status: str = Field(..., description="Overall execution status: success, error, incomplete")


class GetStateResponse(BaseModel):
    """Response containing current state of a workflow run."""
    run_id: str = Field(..., description="Run identifier")
    graph_id: str = Field(..., description="Graph identifier")
    current_state: Dict[str, Any] = Field(..., description="Current state")
    execution_log: List[ExecutionLog] = Field(..., description="Execution log so far")
    status: str = Field(..., description="Current execution status")
