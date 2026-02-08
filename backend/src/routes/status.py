"""
file: status.py

API endpoint for getting the status of the server
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/serverStatus")
def server_status():
    print("endpoint: server_status")
    return {"message": "Server for multimodal transport planner is running",
            "status": "ok"}

# End of file status.py