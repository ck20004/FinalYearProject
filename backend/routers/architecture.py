from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
import traceback
import os
from dotenv import load_dotenv
from models.schemas import ArchitectureRequest, ArchitectureResponse, StatusEnum, OptimizationRequest
from services.session_manager import session_manager
from agents.agent_manager import agent_manager
from agents.base_agent import AgentInput, AgentState
from redis_db.connection import redis_manager
from services.vector_db_service import vector_db_service

router = APIRouter()
load_dotenv()
limit = int(os.getenv("MAX_PAGES"))

# Initialize Redis connection on startup
async def startup_redis():
    """Initialize Redis connection for the router"""
    if not redis_manager.is_connected():
        await redis_manager.connect()

async def process_architecture_generation(request: ArchitectureRequest, session_id: str):
    """Background task to process architecture generation with better error handling"""
    try:
        print(f"🔄 Starting architecture generation for session {session_id}")
        
        if not redis_manager.is_connected():
            await redis_manager.connect()
        
        await session_manager.update_session(session_id, {
            "status": "processing",
            "current_step": "initializing_agents",
            "progress": 10
        })
        
        agent_input = AgentInput(
            prompt=request.prompt,
            context={
                "region": request.region,
                "max_cost": request.max_cost,
                "constraints": request.constraints or {}
            },
            session_id=session_id,
            previous_results={}
        )
        
        initial_state = AgentState(
            session_id=session_id,
            current_step="starting_workflow",
            status="processing"
        )
        
        print(f"🔄 Executing 'architecture_generation' workflow for session {session_id}")
        
        final_state = await agent_manager.execute_workflow(
            "architecture_generation",
            agent_input,
            initial_state
        )
        
        print(f"🔄 Workflow completed for session {session_id}, status: {final_state.status}")
        
        if final_state.status == "complete":
            architecture = final_state.context.get("architecture")
            if not architecture and final_state.result:
                architecture = final_state.result.get("architecture")
            
            await session_manager.update_session(session_id, {
                "status": "complete",
                "architecture": architecture,
                "workflow_complete": True,
                "current_step": "complete",
                "progress": 100,
                "final_state": final_state.dict() if hasattr(final_state, 'dict') else str(final_state)
            })
            print(f"✅ Architecture generation completed for session {session_id}")
        else:
            error_msg = final_state.error or "Unknown workflow error"
            await session_manager.update_session(session_id, {
                "status": "error",
                "error": error_msg,
                "current_step": "error",
                "progress": 0
            })
            print(f"❌ Architecture generation failed for session {session_id}: {error_msg}")
    
    except Exception as e:
        error_msg = f"Background task error: {str(e)}"
        print(f"❌ Exception in architecture generation: {error_msg}")
        print(f"Traceback: {traceback.format_exc()}")
        
        try:
            await session_manager.update_session(session_id, {
                "status": "error",
                "error": error_msg,
                "current_step": "error",
                "progress": 0,
                "traceback": traceback.format_exc()
            })
        except Exception as session_error:
            print(f"❌ Failed to update session with error: {session_error}")

async def process_architecture_optimization(session_id: str):
    """Background task to process architecture optimization."""
    try:
        print(f"🔄 Starting architecture optimization for session {session_id}")
        # 1. Retrieve the session data to get the user's prompt
        session_data = await session_manager.get_session(session_id)
        if not session_data:
            print(f"❌ Could not find session {session_id} for optimization.")
            return
            
        user_prompt = session_data.get("request", {}).get("description", "Optimize existing AWS architecture")
        
        await session_manager.update_session(session_id, {"status": "processing", "current_step": "starting_aws_scan"})

        agent_input = AgentInput(prompt=user_prompt, session_id=session_id)
        initial_state = AgentState(session_id=session_id, status="processing")

        print(f"🔄 Executing 'optimize_existing_architecture' workflow for session {session_id}")
        final_state = await agent_manager.execute_workflow(
            "optimize_existing_architecture",
            agent_input,
            initial_state
        )
        
        await session_manager.update_session(session_id, {
            "status": final_state.status,
            "final_state": final_state.dict() if hasattr(final_state, 'dict') else str(final_state),
            "optimization_results": final_state.context.get("optimization_summary"),
            "workflow_complete": True,
            "current_step": "complete"
        })
        print(f"✅ Optimization complete for session {session_id}")

    except Exception as e:
        error_msg = f"Background optimization task error: {str(e)}"
        print(f"❌ Exception in optimization: {error_msg}")
        await session_manager.update_session(session_id, {"status": "error", "error": error_msg})

@router.post("/generate", response_model=ArchitectureResponse)
async def generate_architecture(request: ArchitectureRequest, background_tasks: BackgroundTasks):
    """Generate AWS architecture from prompt using AI agents"""
    if not redis_manager.is_connected():
        await startup_redis()
    
    session_id = str(uuid.uuid4())
    
    session_data = {
        "type": "architecture_generation",
        "request": request.dict(),
        "status": "pending",
        "workflow_complete": False,
        "current_step": "initialized",
        "progress": 0
    }

    success = await session_manager.store_session(session_id, session_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store session. Redis may be unavailable.")
    
    background_tasks.add_task(process_architecture_generation, request, session_id)
    
    return ArchitectureResponse(
        session_id=session_id,
        status=StatusEnum.pending
    )

@router.post("/optimize", response_model=ArchitectureResponse)
async def optimize_architecture(request: OptimizationRequest, background_tasks: BackgroundTasks):
    """
    Triggers a workflow to scan an existing AWS account and provide optimization suggestions.
    Credentials must be configured in the environment.
    """
    session_id = str(uuid.uuid4())
    
    session_data = {
        "type": "architecture_optimization",
        "request": request.dict(),
        "status": "pending",
        "workflow_complete": False
    }
    success = await session_manager.store_session(session_id, session_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create optimization session.")

    background_tasks.add_task(process_architecture_optimization, session_id)
    
    return ArchitectureResponse(
        session_id=session_id,
        status=StatusEnum.pending,
        suggestions=["Optimization process started. Check status using the session ID."]
    )

@router.get("/status/{session_id}", response_model=ArchitectureResponse)
async def get_process_status(session_id: str):
    """Get the status and result of a generation or optimization process."""
    if not redis_manager.is_connected():
        await startup_redis()
    
    session_data = await session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    status = session_data.get("status", "pending")
    session_type = session_data.get("type", "architecture_generation")
    
    response = ArchitectureResponse(
        session_id=session_id,
        status=StatusEnum(status)
    )
    
    # --- Logic for Generation Workflow ---
    if session_type == "architecture_generation":
        architecture = session_data.get("architecture")
        requirements = session_data.get("requirements_summary", {})
        
        if status == "complete" and architecture:
            response.architecture = architecture
            response.suggestions = ["Architecture successfully generated"]
        elif status == "processing":
            users = requirements.get('expected_users')
            user_text = f"{users:,}" if isinstance(users, int) else "N/A"
            response.suggestions = [
                f"Processing: {session_data.get('current_step', '...')}",
                f"Progress: {session_data.get('progress', 0)}%",
                f"Analyzing requirements for {user_text} users"
            ]

    # --- Logic for Optimization Workflow ---
    elif session_type == "architecture_optimization":
        if status == "complete":
            final_state = session_data.get("final_state", {})
            optimization_results = final_state.get("result", {})
            response.architecture = optimization_results
            response.suggestions = ["AWS optimization analysis complete."]
        elif status == "processing":
            response.suggestions = [
                f"Processing: {session_data.get('current_step', '...')}",
                "Scanning existing AWS infrastructure..."
            ]

    # --- Common Error Handling ---
    if status == "error":
        error_msg = session_data.get("error", "Unknown error")
        response.suggestions = [f"Error: {error_msg}"]
        if session_data.get("traceback"):
            response.suggestions.append("Check server logs for detailed error information")
    
    return response

@router.get("/debug/vector-db")
async def debug_vector_db():
    """
    Debug endpoint to inspect the contents of the Qdrant vector database.
    Returns all points (documents) currently stored.
    """
    try:
        points, _ = vector_db_service.client.scroll(
            collection_name=vector_db_service.collection_name,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        return {
            "collection_name": vector_db_service.collection_name,
            "total_points": len(points),
            "points": [
                {
                    "id": point.id,
                    "source": point.payload.get("source"),
                    "content_preview": point.payload.get("description", "")
                }
                for point in points
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query vector database: {str(e)}")

@router.get("/debug/{session_id}")
async def debug_session(session_id: str):
    """Debug endpoint to see full session data"""
    if not redis_manager.is_connected():
        await startup_redis()
    
    session_data = await session_manager.get_session(session_id)
    
    if not session_data:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "session_id": session_id,
        "full_session_data": session_data
    }