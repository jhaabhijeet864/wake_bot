import queue
import threading
from typing import Callable, Dict, List, Any

class EventBus:
    """
    Thread-safe Pub/Sub coordinator for decoupling triggers and actions.
    Ensures that CV inference/audio threads do not block the main execution thread.
    """
    
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}
        self._event_queue = queue.Queue()
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread = threading.Thread(
            target=self._process_events, daemon=True, name="EventBusWorker"
        )
        self._worker_thread.start()

    def subscribe(self, event_type: str, callback: Callable):
        """Register a callback for a specific event type."""
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def emit(self, event_type: str, data: Any = None):
        """Asynchronously emit an event with optional payload."""
        self._event_queue.put((event_type, data))

    def _process_events(self):
        """Background loop to process events sequentially."""
        while not self._stop_event.is_set():
            try:
                event_type, data = self._event_queue.get(timeout=0.1)
                with self._lock:
                    # Copy the list of callbacks to avoid locking during execution
                    callbacks = list(self._subscribers.get(event_type, []))
                
                for callback in callbacks:
                    try:
                        if data is not None:
                            callback(data)
                        else:
                            callback()
                    except Exception as e:
                        print(f"Error in EventBus executing {event_type} callback: {e}")
                
                self._event_queue.task_done()
            except queue.Empty:
                continue

    def stop(self):
        """Stop the event bus worker gracefully."""
        self._stop_event.set()
        if self._worker_thread.is_alive():
            self._worker_thread.join(timeout=2.0)
