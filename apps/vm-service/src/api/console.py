"""Console API endpoints for VM console access management."""

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import Optional

from core.logging import get_logger
from core.console_service import console_service
from models.base import DatabaseSession
from schemas.console import ConsoleSessionRequest, ConsoleSessionResponse, ConsoleStatusResponse

logger = get_logger("console_api")

router = APIRouter(prefix="/api/vm", tags=["console"])

@router.post("/{vm_id}/console/request", response_model=ConsoleSessionResponse)
async def request_console_access(
    vm_id: int,
    request_data: ConsoleSessionRequest,
    request: Request,
    db: Session = Depends(DatabaseSession.get_session)
):
    """Request console access for a VM.
    
    Creates a new console session with time-limited access token.
    One session per VM per user - existing sessions are terminated.
    """
    try:
        # TODO: Get user_id from JWT token authentication
        user_id = request_data.user_id or 1  # Placeholder for now
        
        # Create console session
        session = await console_service.create_console_session(
            vm_id=vm_id,
            user_id=user_id,
            protocol=request_data.protocol,
            expires_minutes=request_data.expires_minutes or 15
        )
        
        if not session:
            raise HTTPException(
                status_code=500,
                detail="Failed to create console session"
            )
        
        # Build WebSocket URL
        ws_url = f"ws://localhost:8000/ws/console/{session.session_token}"
        
        response = ConsoleSessionResponse(
            session_token=session.session_token,
            vm_id=vm_id,
            protocol=session.protocol,
            websocket_url=ws_url,
            expires_at=session.expires_at,
            vnc_port=session.vnc_port,
            spice_port=session.spice_port
        )
        
        logger.info(f"Console access granted for VM {vm_id}, user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Failed to request console access for VM {vm_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to request console access: {str(e)}"
        )

@router.get("/{vm_id}/console/status", response_model=ConsoleStatusResponse)
async def get_console_status(
    vm_id: int,
    user_id: Optional[int] = None,  # TODO: Get from JWT token
    db: Session = Depends(DatabaseSession.get_session)
):
    """Check console availability and active sessions for a VM."""
    try:
        # TODO: Get user_id from JWT token authentication
        user_id = user_id or 1  # Placeholder for now
        
        # Check for active session
        from models.console_session import ConsoleSession
        from datetime import datetime
        
        active_session = db.query(ConsoleSession).filter(
            ConsoleSession.vm_id == vm_id,
            ConsoleSession.user_id == user_id,
            ConsoleSession.is_active == True,
            ConsoleSession.expires_at > datetime.utcnow()
        ).first()
        
        # Check if VM exists and is accessible
        # TODO: Add VM existence check
        vm_accessible = True  # Placeholder
        
        status = ConsoleStatusResponse(
            vm_id=vm_id,
            available=vm_accessible,
            has_active_session=active_session is not None,
            session_token=active_session.session_token if active_session else None,
            expires_at=active_session.expires_at if active_session else None,
            protocol=active_session.protocol if active_session else None
        )
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get console status for VM {vm_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get console status: {str(e)}"
        )

@router.delete("/{vm_id}/console/session")
async def terminate_console_session(
    vm_id: int,
    session_token: Optional[str] = None,
    user_id: Optional[int] = None,  # TODO: Get from JWT token
    db: Session = Depends(DatabaseSession.get_session)
):
    """Terminate console session for a VM."""
    try:
        # TODO: Get user_id from JWT token authentication
        user_id = user_id or 1  # Placeholder for now
        
        if session_token:
            # Terminate specific session by token
            success = await console_service.terminate_session(session_token)
        else:
            # Terminate all active sessions for this VM and user
            from models.console_session import ConsoleSession
            from datetime import datetime
            
            active_sessions = db.query(ConsoleSession).filter(
                ConsoleSession.vm_id == vm_id,
                ConsoleSession.user_id == user_id,
                ConsoleSession.is_active == True
            ).all()
            
            success = True
            for session in active_sessions:
                result = await console_service.terminate_session(session.session_token)
                success = success and result
        
        if success:
            logger.info(f"Console session terminated for VM {vm_id}")
            return {"message": "Console session terminated successfully"}
        else:
            raise HTTPException(
                status_code=404,
                detail="Console session not found"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate console session for VM {vm_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to terminate console session: {str(e)}"
        )

@router.post("/{vm_id}/console/extend")
async def extend_console_session(
    vm_id: int,
    session_token: str,
    minutes: int = 15,
    db: Session = Depends(DatabaseSession.get_session)
):
    """Extend console session expiration time."""
    try:
        session = await console_service.get_session_by_token(session_token)
        
        if not session or session.vm_id != vm_id:
            raise HTTPException(
                status_code=404,
                detail="Console session not found"
            )
        
        # Update expiration time
        session.extend_session(minutes)
        db.commit()
        
        logger.info(f"Console session {session_token} extended by {minutes} minutes")
        return {
            "message": "Console session extended successfully",
            "expires_at": session.expires_at
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to extend console session {session_token}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extend console session: {str(e)}"
        )