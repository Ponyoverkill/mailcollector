import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class StatusConsumer(AsyncJsonWebsocketConsumer):
    async def receive(self, text_data=None, bytes_data=None, **kwargs):
        pass
