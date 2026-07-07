import asyncio

from app.core.websocket import ConnectionManager


class FakeWS:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send_json(self, message: dict) -> None:
        self.sent.append(message)


def test_publish_fans_out_to_all_subscribers():
    mgr = ConnectionManager()
    a, b, c = FakeWS(), FakeWS(), FakeWS()
    mgr.subscribe("combat:1", a)
    mgr.subscribe("combat:1", b)
    mgr.subscribe("other", c)

    asyncio.run(mgr.publish("combat:1", {"action": "ping"}))

    assert a.sent == [{"action": "ping"}]
    assert b.sent == [{"action": "ping"}]
    assert c.sent == []  # different topic


def test_unsubscribe_removes_from_all_topics():
    mgr = ConnectionManager()
    a = FakeWS()
    mgr.subscribe("t1", a)
    mgr.subscribe("t2", a)
    mgr.unsubscribe(a)

    asyncio.run(mgr.publish("t1", {"x": 1}))
    asyncio.run(mgr.publish("t2", {"x": 1}))
    assert a.sent == []


def test_publish_drops_broken_socket():
    class BrokenWS(FakeWS):
        async def send_json(self, message: dict) -> None:
            raise RuntimeError("closed")

    mgr = ConnectionManager()
    broken = BrokenWS()
    mgr.subscribe("t", broken)
    asyncio.run(mgr.publish("t", {"x": 1}))  # must not raise
    asyncio.run(mgr.publish("t", {"x": 2}))  # broken already dropped
