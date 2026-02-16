from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
from uuid import UUID, uuid4

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.sessions import SessionCreate, SessionUpdate, SessionStatus
from ..db.models import UserSession
from ..db.repositories import SessionRepository
from ..exceptions import SessionError, SessionNotFoundError


class SessionTrackerService:
    """Tracks and manages user engagement sessions."""
    
    def __init__(
        self,
        db: AsyncSession,
        redis: Redis,
        session_repository: SessionRepository
    ):
        self.db = db
        self.redis = redis
        self.session_repository = session_repository
        self.session_timeout = 1800  # 30 minutes
        self.max_session_duration = 14400  # 4 hours
    
    async def create_session(
        self,
        user_id: UUID,
        metadata: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Create a new user session."""
        try:
            session_id = str(uuid4())
            
            # Check for existing active session
            existing = await self._get_active_session(user_id)
            if existing:
                await self.end_session(existing.session_id)
            
            # Create session in database
            session_data = SessionCreate(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.utcnow(),
                status=SessionStatus.ACTIVE,
                metadata=metadata or {}
            )
            
            session = await self.session_repository.create(session_data.model_dump())
            
            # Initialize session in Redis
            await self._init_redis_session(session)
            
            return session
            
        except Exception as e:
            raise SessionError(f"Failed to create session: {str(e)}")
    
    async def update_session_activity(
        self,
        session_id: str,
        activity_data: Optional[Dict[str, Any]] = None
    ) -> UserSession:
        """Update session with latest activity."""
        # Get session from cache or database
        session = await self._get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Check if session is still active
        if session.status != SessionStatus.ACTIVE:
            raise SessionError(f"Session {session_id} is not active")
        
        # Update last activity time
        now = datetime.utcnow()
        update_data = SessionUpdate(
            last_activity=now,
            event_count=session.event_count + 1
        )
        
        # Update activity metadata if provided
        if activity_data:
            session.metadata["last_activity"] = activity_data
            update_data.metadata = session.metadata
        
        # Check session duration
        duration = (now - session.start_time).total_seconds()
        if duration > self.max_session_duration:
            return await self.end_session(session_id, reason="max_duration_reached")
        
        # Update in database
        updated = await self.session_repository.update(
            session_id,
            update_data.model_dump(exclude_unset=True)
        )
        
        # Update Redis
        await self._update_redis_session(updated)
        
        return updated
    
    async def end_session(
        self,
        session_id: str,
        reason: str = "user_action"
    ) -> UserSession:
        """End an active session."""
        session = await self._get_session(session_id)
        if not session:
            raise SessionNotFoundError(f"Session {session_id} not found")
        
        # Calculate session metrics
        end_time = datetime.utcnow()
        duration = (end_time - session.start_time).total_seconds()
        
        # Update session
        update_data = SessionUpdate(
            end_time=end_time,
            duration=duration,
            status=SessionStatus.ENDED
        )
        
        # Add end reason to metadata
        session.metadata["end_reason"] = reason
        update_data.metadata = session.metadata
        
        # Update in database
        updated = await self.session_repository.update(
            session_id,
            update_data.model_dump(exclude_unset=True)
        )
        
        # Clean up Redis
        await self._cleanup_redis_session(session_id)
        
        # Trigger session analytics
        await self._process_session_end(updated)
        
        return updated
    
    async def get_active_sessions(
        self,
        user_id: Optional[UUID] = None
    ) -> List[UserSession]:
        """Get all active sessions."""
        filters = {"status": SessionStatus.ACTIVE}
        if user_id:
            filters["user_id"] = user_id
        
        return await self.session_repository.get_many(filters=filters)
    
    async def get_session_stats(
        self,
        user_id: UUID,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get user session statistics."""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        stats = await self.session_repository.get_session_stats(
            user_id=user_id,
            start_date=start_date
        )
        
        return {
            "total_sessions": stats.get("count", 0),
            "avg_session_duration": stats.get("avg_duration", 0),
            "total_engagement_time": stats.get("total_duration", 0),
            "sessions_per_day": stats.get("per_day", {}),
            "avg_events_per_session": stats.get("avg_events", 0)
        }
    
    async def cleanup_inactive_sessions(self) -> int:
        """Clean up inactive sessions that have timed out."""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.session_timeout)
        
        # Get inactive sessions
        inactive = await self.session_repository.get_inactive_sessions(
            cutoff_time=cutoff_time
        )
        
        # End each inactive session
        count = 0
        for session in inactive:
            try:
                await self.end_session(session.session_id, reason="timeout")
                count += 1
            except Exception:
                continue
        
        return count
    
    async def _get_session(self, session_id: str) -> Optional[UserSession]:
        """Get session from cache or database."""
        # Check Redis first
        cache_key = f"session:{session_id}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            return UserSession(**json.loads(cached))
        
        # Fallback to database
        return await self.session_repository.get(session_id)
    
    async def _get_active_session(self, user_id: UUID) -> Optional[UserSession]:
        """Get active session for user."""
        sessions = await self.session_repository.get_many(
            filters={
                "user_id": user_id,
                "status": SessionStatus.ACTIVE
            },
            limit=1
        )
        return sessions[0] if sessions else None
    
    async def _init_redis_session(self, session: UserSession) -> None:
        """Initialize session in Redis."""
        cache_key = f"session:{session.session_id}"
        user_key = f"user_session:{session.user_id}"
        
        # Store session data
        await self.redis.setex(
            cache_key,
            self.session_timeout,
            json.dumps(session.model_dump(), default=str)
        )
        
        # Map user to session
        await self.redis.setex(user_key, self.session_timeout, session.session_id)
        
        # Add to active sessions set
        await self.redis.sadd("active_sessions", session.session_id)
    
    async def _update_redis_session(self, session: UserSession) -> None:
        """Update session in Redis."""
        cache_key = f"session:{session.session_id}"
        
        await self.redis.setex(
            cache_key,
            self.session_timeout,
            json.dumps(session.model_dump(), default=str)
        )
    
    async def _cleanup_redis_session(self, session_id: str) -> None:
        """Remove session from Redis."""
        await self.redis.delete(f"session:{session_id}")
        await self.redis.srem("active_sessions", session_id)
    
    async def _process_session_end(self, session: UserSession) -> None:
        """Process analytics when session ends."""
        # Publish session end event
        await self.redis.publish(
            "session:ended",
            json.dumps({
                "session_id": session.session_id,
                "user_id": str(session.user_id),
                "duration": session.duration,
                "event_count": session.event_count,
                "metadata": session.metadata
            }, default=str)
        )
