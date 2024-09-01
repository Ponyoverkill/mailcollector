from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from collector.services import get_service
from collector.models import Mail


class StatusConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        token = self.scope['query_string'][6:].decode('utf-8')
        await self.channel_layer.group_add(token,
                                           self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        self.channel_layer.group_discard(
            self.scope['query_string'][6:].decode('utf-8'),
            self.channel_name
        )

    async def receive_json(self, content, **kwargs):
        token = self.scope['query_string'][6:].decode('utf-8')
        mail_id, serv, username, password, last_message = await self.get_mail(token)
        service = get_service(serv)(username, password)

        await service.get_unsaved_messages(token, mail_id, last_message, self)

    @database_sync_to_async
    def get_mail(self, token):
        mail = Mail.objects.get(token=token)
        return mail.id, mail.service, mail.username, mail.password, mail.last_message

    async def load_message(self, event):
        print("here!")
        await self.send_json(event)

    async def finding_last(self, event):
        print("finding last")
        await self.send_json(event)

