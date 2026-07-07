from __future__ import annotations

from collections import defaultdict
from typing import Any


class ConnectionManager:
    def __init__(self) -> None:
        self._topics: dict[str, set[Any]] = defaultdict(set)

    def subscribe(self, topic: str, ws: Any) -> None:
        self._topics[topic].add(ws)

    def unsubscribe(self, ws: Any) -> None:
        for subscribers in self._topics.values():
            subscribers.discard(ws)

    async def publish(self, topic: str, message: dict) -> None:
        dead: list[Any] = []
        for ws in list(self._topics.get(topic, ())):
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.unsubscribe(ws)


manager = ConnectionManager()
