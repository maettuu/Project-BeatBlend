from __future__ import annotations

import asyncio

from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import Any, AsyncGenerator, AsyncIterator

from ws.database_broadcaster import DatabaseBroadcaster
from ws.event import Event


# This WS code is inspired by the encode/broadcaster package.
# If something needs to be fixed or changed, look at their GitHub repo.
class WebsocketManager:
    def __init__(self) -> None:
        self._broadcaster = DatabaseBroadcaster()
        self._subscribers: dict[str, set[asyncio.Queue[Event | None]]] = {}
        self._listener_task: asyncio.Task[None] | None = None

    async def __aenter__(self) -> WebsocketManager:
        await self.connect()
        return self

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self.disconnect()

    async def connect(self) -> None:
        await self._broadcaster.connect()
        self._listener_task = asyncio.create_task(self._listener())

    async def disconnect(self) -> None:
        if self._listener_task.done():
            self._listener_task.result()
        else:
            self._listener_task.cancel()
        await self._broadcaster.disconnect()

    async def _listener(self) -> None:
        while True:
            event = await self._broadcaster.next_published()
            for queue in list(self._subscribers.get(event.channel, [])):
                await queue.put(event)

    async def publish(self, channel: str, message: BaseModel) -> None:
        await self._broadcaster.publish(channel, message)

    @asynccontextmanager
    async def subscribe(self, channel: str) -> AsyncIterator[Subscriber]:
        queue: asyncio.Queue[Event | None] = asyncio.Queue()

        try:
            if not self._subscribers.get(channel):
                await self._broadcaster.subscribe(channel)
                self._subscribers[channel] = {queue}
            else:
                self._subscribers[channel].add(queue)

            yield Subscriber(queue)
        finally:
            self._subscribers[channel].remove(queue)
            if not self._subscribers.get(channel):
                del self._subscribers[channel]
                await self._broadcaster.unsubscribe(channel)
            await queue.put(None)


class Subscriber:
    def __init__(self, queue: asyncio.Queue[Event | None]) -> None:
        self._queue = queue

    async def __aiter__(self) -> AsyncGenerator[Event | None, None] | None:
        try:
            while True:
                yield await self.get()
        except Unsubscribed:
            pass

    async def get(self) -> Event:
        item = await self._queue.get()
        if item is None:
            raise Unsubscribed()
        return item


class Unsubscribed(Exception):
    pass
