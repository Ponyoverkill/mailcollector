import uuid

from django.db import models
from django.conf import settings


def generate_filename():
    return str(uuid.uuid4()).replace('-', '')


class Mail(models.Model):
    username = models.CharField(max_length=255, null=False, blank=False)
    password = models.CharField(max_length=255, null=False, blank=False)


class Message(models.Model):
    subject = models.CharField(max_length=2048, blank=True, null=True)
    dispatch_date = models.DateTimeField(blank=False, null=False)
    receipt_date = models.DateTimeField(blank=False, null=False)
    text = models.CharField(max_length=16384, blank=True, null=True)

    mail = models.ForeignKey(Mail, null=True, blank=True, on_delete=models.SET_NULL)


class File(models.Model):
    file = models.FileField(storage=settings.FILE_STORAGE, upload_to=generate_filename,
                            blank=False, null=False)

    message = models.ForeignKey(Message,
                                blank=True,
                                null=True,
                                on_delete=models.SET_NULL,
                                related_name='files')
