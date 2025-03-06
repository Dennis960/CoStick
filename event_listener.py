import uuid
from typing import Callable, TypeVar, Generic

CallbackParameter = TypeVar("CallbackParameter")
EventTrigger = TypeVar("EventTrigger")


class EventListener(Generic[EventTrigger, CallbackParameter]):
    def __init__(self):
        self._event_listeners: dict[
            uuid.UUID, tuple[EventTrigger, Callable[[CallbackParameter], None]]
        ] = {}

    def add_event_listener(
        self, event_trigger: EventTrigger, listener: Callable[[CallbackParameter], None]
    ) -> uuid.UUID:
        """
        Add a listener for the given event.
        Returns the listener_id which can be used to remove the listener.
        """
        listener_id = uuid.uuid4()
        while listener_id in self._event_listeners:
            listener_id = uuid.uuid4()
        self._event_listeners[listener_id] = (event_trigger, listener)
        return listener_id

    def remove_event_listener(self, listener_id: uuid.UUID) -> None:
        """Remove a listener using the listener_id."""
        if listener_id in self._event_listeners:
            del self._event_listeners[listener_id]

    def get_event_listeners(
        self, event_trigger: EventTrigger
    ) -> list[Callable[[CallbackParameter], None]]:
        """Get all listeners for the given event."""
        return [
            listener
            for e_name, listener in self._event_listeners.values()
            if e_name == event_trigger
        ]

    def call_event_listeners(
        self, event_trigger: EventTrigger, instance: CallbackParameter | None = None
    ) -> None:
        """Call all listeners for the given event."""
        if instance is None:
            instance = self
        for listener in self.get_event_listeners(event_trigger):
            listener(instance)

    def remove_all_event_listeners(self) -> None:
        """Remove all event listeners."""
        self._event_listeners.clear()
