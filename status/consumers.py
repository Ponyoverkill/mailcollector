from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from collector.services import get_service
from collector.models import Mail


class StatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add(self.scope['query_string'][6:].decode('utf-8'),
                                           self.channel_name)
        await self.accept()

        mail = await self.get_mail(self.scope['query_string'][6:])
        service = get_service(mail.service)(mail.username, mail.password)

        await service.get_unsaved_messages(mail)

    async def disconnect(self, code):
        await self.channel_layer.group_discard(
            self.scope['query_string'][6:].decode('utf-8'),
            self.channel_name
        )

    @database_sync_to_async
    def get_mail(self, token):
        # print(str(token))
        return Mail.objects.get(token=token.decode('utf-8'))

    async def load_message(self, event):
        await self.send_json(event)

    async def finding_last(self, event):
        await self.send_json(event)

