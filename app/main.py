"""FastAPI application entry point for the Workflow Engine."""

from fastapi import FastAPI, HTTPException, status
from typing import Dict, Any

from app.schemas import (
    CreateGraphRequest,
    CreateGraphResponse,
    RunGraphRequest,
    RunGraphResponse,
    GetStateResponse,
    ExecutionLog,
)
from app.engine import WorkflowEngine, NodeStatus


# Initialize FastAPI app
app = FastAPI(
    title="LangGraph - Minimal Workflow Engine",
    description="A rule-based workflow engine with support for branching and looping",
    version="0.1.0",
)

# Initialize the workflow engine
engine = WorkflowEngine()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "LangGraph Workflow Engine",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.post("/graph/create", response_model=CreateGraphResponse)
async def create_graph(request: CreateGraphRequest) -> CreateGraphResponse:
    """
    Create a new workflow graph.
    
    Args:
        request: Graph definition with nodes and edges
        
    Returns:
        Graph ID and confirmation message
    """
    try:
        # Create the graph
        graph = engine.create_graph(request.name)
        
        # Add nodes
        for node_def in request.nodes:
            # For now, use a simple identity function as placeholder
            # In a real implementation, you would resolve the actual function
            def node_func(state: Dict[str, Any], node_name: str = node_def.name) -> Dict[str, Any]:
                state[f"{node_name}_executed"] = True
                return state
            
            graph.add_node(node_def.name, node_func, node_def.type)
        
        # Add edges
        for edge_def in request.edges:
            condition = None
            if edge_def.condition:
                # Parse simple condition strings (e.g., "status=='approved'")
                def make_condition(cond_str: str):
                    def cond(state: Dict[str, Any]) -> bool:
                        try:
                            return eval(cond_str, {"state": state})
                        except Exception:
                            return False
                    return cond
                condition = make_condition(edge_def.condition)
            
            graph.add_edge(edge_def.source, edge_def.target, condition)
        
        return CreateGraphResponse(graph_id=graph.id)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create graph: {str(e)}",
        )


@app.post("/graph/run", response_model=RunGraphResponse)
async def run_graph(request: RunGraphRequest) -> RunGraphResponse:
    """
    Execute a workflow graph.
    
    Args:
        request: Graph ID and initial state
        
    Returns:
        Final state and execution log
    """
    try:
        run_id, final_state, execution_log = engine.run_graph(
            request.graph_id,
            request.initial_state,
            request.max_iterations,
        )
        
        # Determine overall status
        has_errors = any(entry.status == NodeStatus.ERROR for entry in execution_log)
        status_str = "error" if has_errors else "success"
        
        # Convert execution log to response format
        log_entries = [
            ExecutionLog(
                node_name=entry.node_name,
                status=entry.status.value,
                input_state=entry.input_state,
                output_state=entry.output_state,
                error_message=entry.error_message,
            )
            for entry in execution_log
        ]
        
        return RunGraphResponse(
            run_id=run_id,
            final_state=final_state,
            execution_log=log_entries,
            status=status_str,
        )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error running graph: {str(e)}",
        )


@app.get("/graph/state/{run_id}", response_model=GetStateResponse)
async def get_state(run_id: str) -> GetStateResponse:
    """
    Get the current state of a workflow run.
    
    Args:
        run_id: Run identifier
        
    Returns:
        Current state and execution log
    """
    result = engine.get_run_state(run_id)
    
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} not found",
        )
    
    final_state, execution_log = result
    
    # Convert execution log to response format
    log_entries = [
        ExecutionLog(
            node_name=entry.node_name,
            status=entry.status.value,
            input_state=entry.input_state,
            output_state=entry.output_state,
            error_message=entry.error_message,
        )
        for entry in execution_log
    ]
    
    # Determine status
    has_errors = any(entry.status == NodeStatus.ERROR for entry in execution_log)
    status_str = "error" if has_errors else "success"
    
    return GetStateResponse(
        run_id=run_id,
        graph_id="unknown",  # Would need to track this separately
        current_state=final_state,
        execution_log=log_entries,
        status=status_str,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
