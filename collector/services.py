import base64
import email
from email.header import decode_header

from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from channels.layers import get_channel_layer
from rest_framework.exceptions import ValidationError
import imaplib

from collector.models import Message, File
from collector.serializers import MessageSerializer


class BaseMailService:
    imap_server = None

    def __init__(self, username, password):
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server)
            imap.login(username, password)
            self.driver = imap
        except imaplib.IMAP4.error:
            raise ValidationError(detail="wrong username or password")
        except Exception as e:
            print(e)
            raise ValueError("Wrong imap_server")

    def get_message_numbers(self):
        return (
            int(self.driver.select('INBOX')[1][0]),
            [int(i) for i in self.driver.search(None, "ALL")[1][0].decode("utf-8").split(" ")]
        )

    async def get_unsaved_messages(self, mail):
        count, numbers = self.get_message_numbers()
        last_number = max(numbers)
        found = False
        number = mail.last_message if mail.last_message is not None else numbers[0]
        for i, n in enumerate(numbers):
            if n <= number:
                content = {
                    "type": "finding_last",
                    "message": {
                        "count": last_number,
                        "number": n
                    }
                }
                await get_channel_layer().group_send(mail.token, content)
            else:
                if not found:
                    found = True
                    count = last_number - i
                _, msg = self.driver.fetch(str(n), '(RFC822)')
                message_serialized = await self.parse_message(msg, mail, n)

                data = await self.add_files_to_data(message_serialized)

                content = {
                    "type": "load_message",
                    "message": {
                        "count": count,
                        "number": i - count,
                        "data": data
                    }
                }
                await get_channel_layer().group_send(mail.token, content)

            await self.set_last_message_async(mail, number)

    async def parse_message(self, msg_bytes, mail, number):
        message = email.message_from_bytes(msg_bytes[0][1])
        charsets = message.get_charsets()

        subj = decode_header(message["Subject"])
        subject = subj[0][0].decode(subj[0][1])

        dispatch_date = decode_header(message["Date"])[0][0]
        receipt_date = decode_header(message["Received"])[0][0]

        files, text = await self.parse_payload(message, charsets)

        data = await self.save_message(mail,
                                       number,
                                       subject,
                                       dispatch_date,
                                       receipt_date,
                                       files,
                                       text)
        return data

    def set_last_message(self, mail, number):
        mail.last_message = number
        mail.save()

    @database_sync_to_async
    def add_files_to_data(self, data):
        db_files = File.objects.filter(message_id=data["id"])
        data["files"] = [file.file.url for file in db_files]

    @database_sync_to_async
    def set_last_message_async(self, mail, number):
        mail.last_message = number
        mail.save()

    @database_sync_to_async
    def save_message(self,
                     mail,
                     number,
                     subject,
                     dispatch_date,
                     receipt_date,
                     files,
                     text,
                     ):
        instance = Message.objects.create(
            subject=subject,
            dispatch_date=dispatch_date,
            receipt_date=receipt_date,
            text=text,
            mail=mail
        )

        db_files = File.objects.filter(id__in=files)
        for f in db_files:
            f.mail = mail
            f.save()

        self.set_last_message(mail, number)

        serializer = MessageSerializer(instance=instance)
        return serializer.data


    @database_sync_to_async
    def parse_payload(self, msg, charsets):
        text = ""
        files = list()
        for part in msg.walk():
            if part.get_content_maintype() in ('text', 'html'):
                for charset in charsets:
                    try:
                        text += base64.b64decode(part.get_payload()).decode("utf-8") + "\n"
                    except UnicodeDecodeError as e:
                        pass
            elif part.get_content_disposition() == 'attachment':
                filename = decode_header(part.get_filename())[0][0].decode()
                file = File()
                file.file.save(filename, ContentFile(part.get_payload(decode=True)))
                file.save()
                files.append(file.id)
        return files, text


class YandexService(BaseMailService):
    imap_server = 'mail.yandex.com'


class GoogleService(BaseMailService):
    imap_server = 'imap.gmail.com'


class MailService(BaseMailService):
    pass


def get_service(service):

    services = {
        'YANDEX': YandexService,
        'GOOGLE': GoogleService,
        'MAIL': MailService
    }
    if service in services.keys():
        return services[service]
    raise ValidationError(detail="Wrong service")
