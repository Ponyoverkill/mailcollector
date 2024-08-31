from rest_framework.serializers import ModelSerializer

from collector.models import Mail, Message


class MailSerializer(ModelSerializer):
    class Meta:
        model = Mail
        fields = '__all__'


class MessageSerializer(ModelSerializer):
    class Meta:
        model = Message
        fields = '__all__'
