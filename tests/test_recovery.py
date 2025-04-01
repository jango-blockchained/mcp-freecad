import pytest
import asyncio
from unittest.mock import Mock, patch
from mcp_freecad.core.recovery import (
    RecoveryConfig,
    ConnectionRecovery,
    FreeCADConnectionManager
)
from mcp_freecad.core.exceptions import ConnectionError

@pytest.fixture
def recovery_config():
    return RecoveryConfig(
        max_retries=3,
        retry_delay=0.1,
        backoff_factor=1.5,
        max_delay=0.5
    )

@pytest.fixture
def recovery(recovery_config):
    return ConnectionRecovery(config=recovery_config)

@pytest.fixture
def connection_manager(recovery_config):
    config = {"freecad": {"path": "/usr/bin/freecad"}}
    return FreeCADConnectionManager(config, ConnectionRecovery(config=recovery_config))

@pytest.mark.asyncio
async def test_recovery_success(recovery):
    """Test successful recovery after initial failures."""
    attempts = 0
    
    async def failing_operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise Exception("Temporary failure")
        return "success"
        
    result = await recovery.attempt_recovery(failing_operation)
    assert result == "success"
    assert attempts == 3
    assert recovery.retry_count == 0
    assert recovery.connected

@pytest.mark.asyncio
async def test_recovery_max_retries(recovery):
    """Test recovery fails after max retries."""
    attempts = 0
    
    async def always_failing_operation():
        nonlocal attempts
        attempts += 1
        raise Exception("Permanent failure")
        
    with pytest.raises(ConnectionError) as exc_info:
        await recovery.attempt_recovery(always_failing_operation)
        
    assert attempts == 3  # Initial try + 2 retries
    assert not recovery.connected
    assert "Failed to connect after 3 attempts" in str(exc_info.value)

@pytest.mark.asyncio
async def test_recovery_backoff(recovery):
    """Test exponential backoff timing."""
    start_times = []
    
    async def failing_operation():
        start_times.append(asyncio.get_event_loop().time())
        raise Exception("Failure")
        
    with pytest.raises(ConnectionError):
        await recovery.attempt_recovery(failing_operation)
        
    # Check delays between attempts
    delays = [start_times[i+1] - start_times[i] for i in range(len(start_times)-1)]
    assert len(delays) == 2  # 2 retries
    assert 0.1 <= delays[0] <= 0.15  # Initial delay
    assert 0.15 <= delays[1] <= 0.2  # First backoff

@pytest.mark.asyncio
async def test_connection_callbacks(recovery):
    """Test connection status callbacks."""
    callback_calls = []
    
    def status_callback(connected):
        callback_calls.append(connected)
        
    recovery.add_connection_callback(status_callback)
    
    # Simulate successful connection
    async def successful_operation():
        return "success"
        
    await recovery.attempt_recovery(successful_operation)
    assert callback_calls == [True]
    
    # Simulate failed connection
    async def failing_operation():
        raise Exception("Failure")
        
    with pytest.raises(ConnectionError):
        await recovery.attempt_recovery(failing_operation)
        
    assert callback_calls == [True, False]

@pytest.mark.asyncio
async def test_connection_manager_connect(connection_manager):
    """Test FreeCAD connection manager connection."""
    with patch("builtins.__import__", return_value=Mock()) as mock_import:
        await connection_manager.connect()
        assert connection_manager.connection is not None
        assert connection_manager.recovery.connected

@pytest.mark.asyncio
async def test_connection_manager_disconnect(connection_manager):
    """Test FreeCAD connection manager disconnection."""
    connection_manager.connection = Mock()
    await connection_manager.disconnect()
    assert connection_manager.connection is None
    assert not connection_manager.recovery.connected

@pytest.mark.asyncio
async def test_connection_manager_execute(connection_manager):
    """Test FreeCAD connection manager operation execution."""
    with patch("builtins.__import__", return_value=Mock()) as mock_import:
        async def test_operation():
            return "test_result"
            
        result = await connection_manager.execute_with_recovery(test_operation)
        assert result == "test_result"
        assert connection_manager.connection is not None

@pytest.mark.asyncio
async def test_connection_manager_status(connection_manager):
    """Test FreeCAD connection manager status reporting."""
    status = connection_manager.get_status()
    assert isinstance(status, dict)
    assert "connected" in status
    assert "recovery_status" in status
    assert "config" in status
    assert isinstance(status["recovery_status"], dict)
    assert "retry_count" in status["recovery_status"]
    assert "current_delay" in status["recovery_status"]
    assert "last_error" in status["recovery_status"]
    assert "max_retries" in status["recovery_status"]

@pytest.mark.asyncio
async def test_recovery_reset(recovery):
    """Test recovery state reset."""
    recovery.retry_count = 2
    recovery.current_delay = 0.5
    recovery.last_error = Exception("Test error")
    
    recovery.reset()
    assert recovery.retry_count == 0
    assert recovery.current_delay == recovery.config.retry_delay
    assert recovery.last_error is None 