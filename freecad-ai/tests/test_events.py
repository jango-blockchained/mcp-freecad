"""
Test suite for the events system.

This module contains tests for all event providers, the event manager,
and MCP integration components.
"""

import pytest
import time
from unittest.mock import Mock, patch

# Import the events system components
try:
    from ..events import (
        EventManager,
        EventRouter,
        MCPEventIntegration,
        DocumentEventProvider,
        CommandExecutionEventProvider,
        ErrorEventProvider,
        create_event_system,
        initialize_event_system,
    )
except ImportError:
    import sys
    import os

    # Add the parent directory to the path
    parent_dir = os.path.dirname(os.path.dirname(__file__))
    sys.path.insert(0, parent_dir)

    from events import (
        EventManager,
        EventRouter,
        MCPEventIntegration,
        DocumentEventProvider,
        CommandExecutionEventProvider,
        ErrorEventProvider,
        create_event_system,
        initialize_event_system,
    )


class TestEventRouter:
    """Test cases for the EventRouter class."""

    @pytest.fixture
    def event_router(self):
        """Create an EventRouter instance for testing."""
        return EventRouter()

    @pytest.mark.asyncio
    async def test_add_remove_listener(self, event_router):
        """Test adding and removing event listeners."""
        client_id = "test_client_1"
        event_types = ["document_changed", "command_executed"]

        # Add listener
        await event_router.add_listener(client_id, event_types)

        # Check that listener was added
        listeners = await event_router.get_active_listeners()
        assert client_id in listeners["clients"]
        assert set(listeners["clients"][client_id]) == set(event_types)

        # Remove listener
        await event_router.remove_listener(client_id, event_types)

        # Check that listener was removed
        listeners = await event_router.get_active_listeners()
        assert client_id not in listeners["clients"]

    @pytest.mark.asyncio
    async def test_broadcast_event(self, event_router):
        """Test broadcasting events to listeners."""
        client_id = "test_client_1"
        event_type = "test_event"
        event_data = {"test": "data", "value": 42}

        # Add listener
        await event_router.add_listener(client_id, [event_type])

        # Broadcast event
        await event_router.broadcast_event(event_type, event_data)

        # Check event history
        history = await event_router.get_event_history(limit=1)
        assert len(history) == 1
        assert history[0]["type"] == event_type
        assert history[0]["data"]["test"] == "data"
        assert history[0]["listeners_notified"] == 1

    @pytest.mark.asyncio
    async def test_event_history(self, event_router):
        """Test event history functionality."""
        client_id = "test_client_1"

        # Add listener for all events
        await event_router.add_listener(client_id, ["*"])

        # Broadcast multiple events
        for i in range(5):
            await event_router.broadcast_event(f"event_{i}", {"index": i})

        # Get all history
        history = await event_router.get_event_history()
        assert len(history) == 5

        # Get limited history
        limited_history = await event_router.get_event_history(limit=3)
        assert len(limited_history) == 3

        # Get filtered history
        filtered_history = await event_router.get_event_history(
            event_types=["event_1", "event_3"]
        )
        assert len(filtered_history) == 2


class TestEventManager:
    """Test cases for the EventManager class."""

    @pytest.fixture
    def mock_freecad(self):
        """Create a mock FreeCAD application."""
        mock_app = Mock()
        mock_app.signalDocumentChanged = Mock()
        mock_app.signalNewDocument = Mock()
        mock_app.signalDeleteDocument = Mock()
        mock_app.signalActiveDocument = Mock()

        # Mock GUI
        mock_gui = Mock()
        mock_selection = Mock()
        mock_selection.signalSelectionChanged = Mock()
        mock_gui.Selection = mock_selection
        mock_gui.Command = Mock()
        mock_gui.Command.CommandExecuted = Mock()
        mock_app.Gui = mock_gui

        return mock_app

    @pytest.fixture
    def event_manager(self, mock_freecad):
        """Create an EventManager instance for testing."""
        return EventManager(mock_freecad)

    @pytest.mark.asyncio
    async def test_initialization(self, event_manager):
        """Test event manager initialization."""
        # Should not be initialized initially
        assert not event_manager.is_initialized

        # Initialize
        success = await event_manager.initialize()
        assert success
        assert event_manager.is_initialized

        # Check that providers were created
        assert "document" in event_manager.providers
        assert "command" in event_manager.providers
        assert "error" in event_manager.providers

    @pytest.mark.asyncio
    async def test_add_remove_listeners(self, event_manager):
        """Test adding and removing event listeners."""
        await event_manager.initialize()

        client_id = "test_client_1"
        event_types = ["document_changed"]

        # Add listener
        success = await event_manager.add_event_listener(client_id, event_types)
        assert success

        # Remove listener
        success = await event_manager.remove_event_listener(client_id, event_types)
        assert success

    @pytest.mark.asyncio
    async def test_get_system_status(self, event_manager):
        """Test getting system status."""
        await event_manager.initialize()

        status = await event_manager.get_system_status()

        assert status["initialized"] is True
        assert status["freecad_available"] is True
        assert "providers" in status
        assert "router_stats" in status
        assert "active_listeners" in status

    @pytest.mark.asyncio
    async def test_custom_event_emission(self, event_manager):
        """Test emitting custom events."""
        await event_manager.initialize()

        event_type = "custom_test_event"
        event_data = {"custom": "data"}

        success = await event_manager.emit_custom_event(event_type, event_data)
        assert success

    @pytest.mark.asyncio
    async def test_shutdown(self, event_manager):
        """Test event manager shutdown."""
        await event_manager.initialize()
        assert event_manager.is_initialized

        await event_manager.shutdown()
        assert not event_manager.is_initialized


class TestMCPEventIntegration:
    """Test cases for the MCPEventIntegration class."""

    @pytest.fixture
    def mock_event_manager(self):
        """Create a mock EventManager."""
        manager = Mock()
        manager.add_event_listener = Mock(return_value=True)
        manager.remove_event_listener = Mock(return_value=True)
        manager.get_system_status = Mock(
            return_value={
                "initialized": True,
                "providers": {},
                "router_stats": {},
                "active_listeners": {},
            }
        )
        return manager

    @pytest.fixture
    def mcp_integration(self, mock_event_manager):
        """Create an MCPEventIntegration instance for testing."""
        return MCPEventIntegration(mock_event_manager)

    @pytest.mark.asyncio
    async def test_client_registration(self, mcp_integration):
        """Test MCP client registration and unregistration."""
        client_id = "mcp_test_client"
        client_info = {"version": "1.0", "name": "Test Client"}

        # Register client
        success = await mcp_integration.register_mcp_client(client_id, client_info)
        assert success

        # Check client info
        info = await mcp_integration.get_client_info(client_id)
        assert info["info"] == client_info

        # Unregister client
        success = await mcp_integration.unregister_mcp_client(client_id)
        assert success

        # Check client is gone
        info = await mcp_integration.get_client_info(client_id)
        assert info == {}

    @pytest.mark.asyncio
    async def test_event_subscriptions(self, mcp_integration):
        """Test event subscription management."""
        client_id = "mcp_test_client"

        # Register client first
        await mcp_integration.register_mcp_client(client_id)

        # Subscribe to events
        event_types = ["document_changed", "error"]
        success = await mcp_integration.subscribe_to_events(client_id, event_types)
        assert success

        # Check subscription
        info = await mcp_integration.get_client_info(client_id)
        assert set(info["subscriptions"]) == set(event_types)

        # Unsubscribe
        success = await mcp_integration.unsubscribe_from_events(client_id, ["error"])
        assert success

        # Check subscription updated
        info = await mcp_integration.get_client_info(client_id)
        assert "document_changed" in info["subscriptions"]
        assert "error" not in info["subscriptions"]

    @pytest.mark.asyncio
    async def test_notification_handling(self, mcp_integration):
        """Test event notification handling."""
        client_id = "mcp_test_client"

        # Register client
        await mcp_integration.register_mcp_client(client_id)

        # Set up custom handler
        handled_events = []

        def custom_handler(client_id, event_type, event_data):
            handled_events.append((client_id, event_type, event_data))

        mcp_integration.set_notification_handler("test_event", custom_handler)

        # Handle notification
        event_data = {"test": "notification"}
        success = await mcp_integration.handle_event_notification(
            client_id, "test_event", event_data
        )
        assert success

        # Check handler was called
        assert len(handled_events) == 1
        assert handled_events[0] == (client_id, "test_event", event_data)

    @pytest.mark.asyncio
    async def test_cleanup_inactive_clients(self, mcp_integration):
        """Test cleanup of inactive clients."""
        client_id = "inactive_client"

        # Register client
        await mcp_integration.register_mcp_client(client_id)

        # Simulate passage of time by modifying last_activity
        async with mcp_integration._lock:
            mcp_integration.mcp_clients[client_id]["last_activity"] = (
                time.time() - 7200
            )  # 2 hours ago

        # Cleanup with 1 hour timeout
        cleaned_up = await mcp_integration.cleanup_inactive_clients(timeout=3600)
        assert cleaned_up == 1

        # Check client was removed
        info = await mcp_integration.get_client_info(client_id)
        assert info == {}


class TestEventProviders:
    """Test cases for individual event providers."""

    @pytest.fixture
    def mock_freecad(self):
        """Create a mock FreeCAD application."""
        mock_app = Mock()
        mock_app.signalDocumentChanged = Mock()
        mock_app.signalNewDocument = Mock()
        mock_app.signalDeleteDocument = Mock()
        mock_app.signalActiveDocument = Mock()

        # Mock GUI
        mock_gui = Mock()
        mock_selection = Mock()
        mock_selection.signalSelectionChanged = Mock()
        mock_selection.getSelection = Mock(return_value=[])
        mock_gui.Selection = mock_selection
        mock_gui.Command = Mock()
        mock_gui.Command.CommandExecuted = Mock()
        mock_app.Gui = mock_gui

        return mock_app

    @pytest.fixture
    def mock_event_router(self):
        """Create a mock event router."""
        router = Mock()
        router.broadcast_event = Mock()
        return router

    def test_document_event_provider_creation(self, mock_freecad, mock_event_router):
        """Test creating a DocumentEventProvider."""
        provider = DocumentEventProvider(mock_freecad, mock_event_router)

        assert provider.app == mock_freecad
        assert provider.event_router == mock_event_router

    def test_command_event_provider_creation(self, mock_freecad, mock_event_router):
        """Test creating a CommandExecutionEventProvider."""
        provider = CommandExecutionEventProvider(mock_freecad, mock_event_router)

        assert provider.app == mock_freecad
        assert provider.event_router == mock_event_router
        assert provider.command_history == []

    def test_error_event_provider_creation(self, mock_freecad, mock_event_router):
        """Test creating an ErrorEventProvider."""
        provider = ErrorEventProvider(mock_freecad, mock_event_router)

        assert provider.app == mock_freecad
        assert provider.event_router == mock_event_router
        assert provider.error_history == []

    def test_command_history(self, mock_freecad, mock_event_router):
        """Test command history functionality."""
        provider = CommandExecutionEventProvider(mock_freecad, mock_event_router)

        # Simulate command execution
        provider._on_command_executed("TestCommand")

        # Check history
        history = provider.get_command_history()
        assert len(history) == 1
        assert history[0]["command"] == "TestCommand"
        assert history[0]["type"] == "command_executed"

    def test_error_reporting(self, mock_freecad, mock_event_router):
        """Test manual error reporting."""
        provider = ErrorEventProvider(mock_freecad, mock_event_router)

        # Report an error
        provider.report_error("Test error", "manual", {"detail": "test"})

        # Check error history
        history = provider.get_error_history()
        assert len(history) == 1
        assert history[0]["message"] == "Test error"
        assert history[0]["error_type"] == "manual"
        assert history[0]["detail"] == "test"


class TestConvenienceFunctions:
    """Test cases for convenience functions."""

    @patch("events.EventManager")
    @patch("events.MCPEventIntegration")
    def test_create_event_system(self, mock_mcp_class, mock_manager_class):
        """Test create_event_system function."""
        mock_manager = Mock()
        mock_mcp = Mock()
        mock_manager_class.return_value = mock_manager
        mock_mcp_class.return_value = mock_mcp

        manager, mcp = create_event_system()

        assert manager == mock_manager
        assert mcp == mock_mcp

    @pytest.mark.asyncio
    @patch("events.EventManager")
    @patch("events.MCPEventIntegration")
    async def test_initialize_event_system(self, mock_mcp_class, mock_manager_class):
        """Test initialize_event_system function."""
        mock_manager = Mock()
        mock_manager.initialize = Mock(return_value=True)
        mock_mcp = Mock()
        mock_manager_class.return_value = mock_manager
        mock_mcp_class.return_value = mock_mcp

        manager, mcp = await initialize_event_system()

        assert manager == mock_manager
        assert mcp == mock_mcp
        mock_manager.initialize.assert_called_once()


if __name__ == "__main__":
    # Run tests if this file is executed directly
    pytest.main([__file__, "-v"])
