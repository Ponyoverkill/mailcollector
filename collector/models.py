import uuid
from enum import Enum
from pathlib import Path

from django.db import models
from django.conf import settings


def generate_filename(instance, filename):
    path = Path(filename)
    suffix = ''
    for s in path.suffixes:
        suffix += s
    return str(uuid.uuid4()).replace('-', '') + suffix


class Mail(models.Model):
    class Services:
        YANDEX = "YANDEX"
        GOOGLE = "GOOGLE"
        MAIL = "MAIL"

    SERVICES = (
        (Services.YANDEX, Services.YANDEX),
        (Services.GOOGLE, Services.GOOGLE),
        (Services.MAIL, Services.MAIL)
    )

    service = models.CharField(max_length=30, choices=SERVICES, null=False, blank=False)
    username = models.CharField(max_length=255, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)
    last_message = models.IntegerField(null=True)
    token = models.CharField(max_length=36, default=generate_filename,
                             null=False, blank=False)

    class Meta:
        unique_together = ("service", "username", "password")


class Message(models.Model):
    subject = models.CharField(max_length=2048, blank=True, null=True)
    dispatch_date = models.CharField(max_length=255, blank=False, null=False)
    receipt_date = models.CharField(max_length=255, blank=False, null=False)
    text = models.TextField(max_length=64535, blank=True, null=True)

    mail = models.ForeignKey(Mail, null=True, blank=True, on_delete=models.SET_NULL)


class File(models.Model):
    file = models.FileField(storage=settings.FILE_STORAGE, upload_to=generate_filename,
                            blank=False, null=False)

    message = models.ForeignKey(Message,
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL,
                                related_name='files')
