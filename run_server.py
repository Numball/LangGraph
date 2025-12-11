"""
Quick start guide for running the LangGraph server locally.

Run this script: py run_server.py
Then in another terminal: py test_live_server.py
Or use curl commands as shown in the README
"""

import sys
import subprocess
import time

if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph - Workflow Engine Server")
    print("=" * 60)
    print("\nStarting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    sys.path.insert(0, r"c:\Projects\LangGraph")
    
    import uvicorn
    from app.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
