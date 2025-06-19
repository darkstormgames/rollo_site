"""Tests for console service functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta

from core.console_service import ConsoleService
from models.console_session import ConsoleSession


@pytest.fixture
def console_service():
    """Create a console service instance for testing."""
    return ConsoleService()


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock_session = MagicMock()
    mock_session.query.return_value.filter.return_value.first.return_value = None
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.close = MagicMock()
    return mock_session


class TestConsoleService:
    """Test console service functionality."""

    @pytest.mark.asyncio
    async def test_create_console_session(self, console_service, mock_db_session):
        """Test creating a new console session."""
        vm_id = 1
        user_id = 1
        protocol = "vnc"
        
        # Mock database session
        with patch('models.base.DatabaseSession.get_session', return_value=mock_db_session):
            with patch.object(console_service, '_get_vm_console_port', return_value=5901):
                session = await console_service.create_console_session(
                    vm_id=vm_id,
                    user_id=user_id,
                    protocol=protocol
                )
                
                assert session is not None
                assert session.vm_id == vm_id
                assert session.user_id == user_id
                assert session.protocol == protocol
                assert session.vnc_port == 5901
                assert session.is_active == True
                assert len(session.session_token) > 0

    @pytest.mark.asyncio
    async def test_get_session_by_token_valid(self, console_service, mock_db_session):
        """Test retrieving a valid session by token."""
        session_token = "test-token-123"
        
        # Create a mock session that is not expired
        mock_session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token=session_token,
            protocol="vnc",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        with patch('models.base.DatabaseSession.get_session', return_value=mock_db_session):
            result = await console_service.get_session_by_token(session_token)
            
            assert result is not None
            assert result.session_token == session_token
            assert result.is_active == True

    @pytest.mark.asyncio
    async def test_get_session_by_token_expired(self, console_service, mock_db_session):
        """Test retrieving an expired session returns None."""
        session_token = "expired-token-123"
        
        # Create a mock session that is expired
        mock_session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token=session_token,
            protocol="vnc",
            expires_at=datetime.utcnow() - timedelta(minutes=10),
            is_active=True
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        with patch('models.base.DatabaseSession.get_session', return_value=mock_db_session):
            with patch.object(console_service, 'cleanup_session', new=AsyncMock()) as mock_cleanup:
                result = await console_service.get_session_by_token(session_token)
                
                assert result is None
                mock_cleanup.assert_called_once_with(session_token)

    @pytest.mark.asyncio
    async def test_terminate_session(self, console_service, mock_db_session):
        """Test terminating a console session."""
        session_token = "test-token-123"
        
        mock_session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token=session_token,
            protocol="vnc",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        
        mock_db_session.query.return_value.filter.return_value.first.return_value = mock_session
        
        with patch('models.base.DatabaseSession.get_session', return_value=mock_db_session):
            with patch.object(console_service, 'cleanup_session', new=AsyncMock()) as mock_cleanup:
                result = await console_service.terminate_session(session_token)
                
                assert result == True
                assert mock_session.is_active == False
                mock_cleanup.assert_called_once_with(session_token)

    @pytest.mark.asyncio
    async def test_cleanup_session(self, console_service):
        """Test cleaning up session resources."""
        session_token = "test-token-123"
        
        # Add session to active connections
        console_service.active_connections[session_token] = {
            "websocket": MagicMock(),
            "session": MagicMock(),
            "target_port": 5901,
            "started_at": datetime.utcnow()
        }
        
        # Add a mock VNC proxy task
        mock_task = MagicMock()
        console_service.vnc_proxies[session_token] = mock_task
        
        await console_service.cleanup_session(session_token)
        
        # Verify cleanup
        assert session_token not in console_service.active_connections
        assert session_token not in console_service.vnc_proxies
        mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_vnc_proxy_valid_session(self, console_service):
        """Test starting VNC proxy with valid session."""
        session_token = "test-token-123"
        mock_websocket = MagicMock()
        
        mock_session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token=session_token,
            protocol="vnc",
            vnc_port=5901,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        
        with patch.object(console_service, 'get_session_by_token', return_value=mock_session):
            with patch('asyncio.create_task') as mock_create_task:
                result = await console_service.start_vnc_proxy(session_token, mock_websocket)
                
                assert result == True
                assert session_token in console_service.active_connections
                mock_create_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_vnc_proxy_invalid_session(self, console_service):
        """Test starting VNC proxy with invalid session."""
        session_token = "invalid-token"
        mock_websocket = MagicMock()
        
        with patch.object(console_service, 'get_session_by_token', return_value=None):
            result = await console_service.start_vnc_proxy(session_token, mock_websocket)
            
            assert result == False
            assert session_token not in console_service.active_connections

    @pytest.mark.asyncio
    async def test_get_vm_console_port(self, console_service):
        """Test getting VM console port."""
        vm_id = 5
        
        # Test VNC port
        vnc_port = await console_service._get_vm_console_port(vm_id, "vnc")
        assert vnc_port == 5905  # 5900 + vm_id
        
        # Test SPICE port
        spice_port = await console_service._get_vm_console_port(vm_id, "spice")
        assert spice_port == 5935  # 5930 + vm_id

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, console_service, mock_db_session):
        """Test cleaning up expired sessions."""
        # Create mock expired sessions
        expired_session1 = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token="expired-1",
            protocol="vnc",
            expires_at=datetime.utcnow() - timedelta(minutes=10),
            is_active=True
        )
        
        expired_session2 = ConsoleSession(
            vm_id=2,
            user_id=1,
            session_token="expired-2",
            protocol="vnc",
            expires_at=datetime.utcnow() - timedelta(minutes=5),
            is_active=True
        )
        
        mock_db_session.query.return_value.filter.return_value.all.return_value = [
            expired_session1, expired_session2
        ]
        
        with patch('models.base.DatabaseSession.get_session', return_value=mock_db_session):
            with patch.object(console_service, 'cleanup_session', new=AsyncMock()) as mock_cleanup:
                await console_service.cleanup_expired_sessions()
                
                # Verify sessions were terminated
                assert expired_session1.is_active == False
                assert expired_session2.is_active == False
                
                # Verify cleanup was called for each session
                assert mock_cleanup.call_count == 2
                mock_cleanup.assert_any_call("expired-1")
                mock_cleanup.assert_any_call("expired-2")


class TestConsoleSession:
    """Test console session model functionality."""

    def test_create_session(self):
        """Test creating a console session."""
        vm_id = 1
        user_id = 1
        session_token = "test-token-123"
        protocol = "vnc"
        
        session = ConsoleSession.create_session(
            vm_id=vm_id,
            user_id=user_id,
            session_token=session_token,
            protocol=protocol,
            expires_minutes=15
        )
        
        assert session.vm_id == vm_id
        assert session.user_id == user_id
        assert session.session_token == session_token
        assert session.protocol == protocol
        assert session.is_active == True
        assert session.expires_at > datetime.utcnow()

    def test_is_expired(self):
        """Test session expiration check."""
        # Create non-expired session
        session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token="test-token",
            protocol="vnc",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        assert session.is_expired() == False
        
        # Create expired session
        expired_session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token="expired-token",
            protocol="vnc",
            expires_at=datetime.utcnow() - timedelta(minutes=10),
            is_active=True
        )
        assert expired_session.is_expired() == True

    def test_extend_session(self):
        """Test extending session expiration."""
        session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token="test-token",
            protocol="vnc",
            expires_at=datetime.utcnow() + timedelta(minutes=5),
            is_active=True
        )
        
        original_expiry = session.expires_at
        session.extend_session(15)
        
        assert session.expires_at > original_expiry
        assert session.expires_at > datetime.utcnow() + timedelta(minutes=10)

    def test_terminate(self):
        """Test terminating a session."""
        session = ConsoleSession(
            vm_id=1,
            user_id=1,
            session_token="test-token",
            protocol="vnc",
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        
        session.terminate()
        assert session.is_active == False

    def test_to_dict(self):
        """Test converting session to dictionary."""
        session = ConsoleSession(
            id=1,
            vm_id=1,
            user_id=1,
            session_token="test-token",
            protocol="vnc",
            vnc_port=5901,
            expires_at=datetime.utcnow() + timedelta(minutes=10),
            is_active=True
        )
        
        session_dict = session.to_dict()
        
        assert session_dict["id"] == 1
        assert session_dict["vm_id"] == 1
        assert session_dict["user_id"] == 1
        assert session_dict["session_token"] == "test-token"
        assert session_dict["protocol"] == "vnc"
        assert session_dict["vnc_port"] == 5901
        assert session_dict["is_active"] == True
        assert "expires_at" in session_dict
        assert "created_at" in session_dict