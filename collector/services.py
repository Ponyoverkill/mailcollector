import base64
import email
from email.header import decode_header
from asyncio import sleep

from channels.db import database_sync_to_async
from django.core.files.base import ContentFile
from channels.layers import get_channel_layer
from rest_framework.exceptions import ValidationError
import imaplib

from collector.models import Message, File, Mail
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

    async def get_unsaved_messages(self, token, mail_id, mail_last_message, ev):
        count, numbers = self.get_message_numbers()
        last_number = len(numbers)
        found = False
        number = mail_last_message if mail_last_message is not None else numbers[0]

        async def async_generator(ls):
            for i, n in enumerate(ls):
                yield i, n

        async for i, n in async_generator(numbers):
            await sleep(0.2)
            if i + 1 <= number:
                content = {
                    "type": "finding_last",
                    "message": {
                        "count": last_number,
                        "number": i + 1
                    }
                }
                await ev.send_json(content)
            else:
                if not found:
                    found = True
                    count = last_number - i + 1
                _, msg = self.driver.fetch(str(n), '(RFC822)')
                message_serialized = await self.parse_message(msg, mail_id, i)

                content = {
                    "type": "load_message",
                    "message": {
                        "count": count,
                        "number": last_number - i,
                        "data": message_serialized
                    }
                }
                await ev.send_json(content)

            await self.set_last_message_async(mail_id, len(numbers))

    @database_sync_to_async
    def parse_message(self, msg_bytes, mail_id, index):
        message = email.message_from_bytes(msg_bytes[0][1])
        charsets = message.get_charsets()

        subj = decode_header(message["Subject"])
        subject = subj[0][0].decode(subj[0][1]) if isinstance(subj[0][0], bytes) else subj[0][0]

        dispatch_date = decode_header(message["Date"])[0][0]
        receipt_date = decode_header(message["Received"])[0][0]

        files, text = self.parse_payload(message, charsets)

        data = self.save_message(mail_id,
                                 index,
                                 subject,
                                 dispatch_date,
                                 receipt_date,
                                 files,
                                 text)
        return data

    @database_sync_to_async
    def set_last_message_async(self, mail_id, number):
        mail = Mail.objects.get(id=mail_id)
        mail.last_message = number
        mail.save()

    def set_last_message(self, mail_id, number):
        mail = Mail.objects.get(id=mail_id)
        mail.last_message = number
        mail.save()

    def save_message(self,
                     mail_id,
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
            mail_id=mail_id
        )

        db_files = File.objects.filter(id__in=files)
        for f in db_files:
            f.mail_id = mail_id
            f.save()

        self.set_last_message(mail_id, number)
        files = list()
        serializer = MessageSerializer(instance=instance)
        serialized_data = serializer.data
        for f in db_files:
            files.append(f.file.url)
        serialized_data["files"] = files
        return serialized_data

    def parse_payload(self, msg, charsets):
        text = ""
        files = list()
        for part in msg.walk():
            if part.get_content_maintype() in ('text', 'html'):
                payload = part.get_payload()
                if isinstance(payload, str):
                    text += payload
                else:
                    for charset in charsets:
                        try:
                            text += base64.b64decode(part.get_payload()).decode(charset) + "\n"
                        except UnicodeDecodeError as e:
                            pass
                        except TypeError as e:
                            pass
            elif part.get_content_disposition() == 'attachment':
                filename = decode_header(part.get_filename())[0][0]
                if isinstance(filename, bytes):
                    filename = filename.decode()
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
