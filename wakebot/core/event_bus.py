"""
WakeBot Event Bus
A thread-safe Pub/Sub system for decoupling triggers from actions.
"""

import threading
from typing import Callable, Dict, List, Any
from wakebot.core.logger import WakeBotLogger

class EventBus:
    """
    Central coordinator for system-wide events.
    Allows modules to emit signals without knowing who is listening.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EventBus, cls).__new__(cls)
                cls._instance._listeners: Dict[str, List[Callable]] = {}
                cls._instance._logger = WakeBotLogger()
            return cls._instance

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type."""
        with self._lock:
            if event_type not in self._listeners:
                self._listeners[event_type] = []
            if callback not in self._listeners[event_type]:
                self._listeners[event_type].append(callback)
                # self._logger.info(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type."""
        with self._lock:
            if event_type in self._listeners:
                if callback in self._listeners[event_type]:
                    self._listeners[event_type].remove(callback)

    def emit(self, event_type: str, data: Any = None):
        """Emit an event to all subscribers."""
        callbacks = []
        with self._lock:
            if event_type in self._listeners:
                callbacks = list(self._listeners[event_type])
        
        if callbacks:
            # self._logger.info(f"Emitting event: {event_type}")
            for callback in callbacks:
                try:
                    # Execute callback in a separate thread to prevent blocking the emitter
                    threading.Thread(
                        target=callback, 
                        args=(data,) if data is not None else (),
                        daemon=True
                    ).start()
                except Exception as e:
                    self._logger.error(f"Error in event callback for {event_type}: {e}")
