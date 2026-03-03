"""
file: status.py

Defines API endpoint for retrieving basic server health status.
"""

from fastapi import APIRouter

# Router instance for status endpoint
router = APIRouter()

@router.get("/serverStatus")
def server_status():
    """
    Returns basic health status of the server.
    """
    
    print("endpoint: server_status")
    return {"message": "Server for multimodal transport planner is running",
            "status": "ok"}

# End of file status.py
