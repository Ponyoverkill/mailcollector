# from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework.mixins import (CreateModelMixin,
                                   UpdateModelMixin,
                                   ListModelMixin,
                                   RetrieveModelMixin,
                                   )


from collector.services import get_service
from collector.serializers import MailSerializer
from collector.models import Mail


class MailViewSet(GenericViewSet,
                  CreateModelMixin,
                  ):

    serializer_class = MailSerializer

    def get_queryset(self):
        queryset = Mail.objects.all()
        if "token" in self.request.data.keys():
            queryset = queryset.filter(token=self.request.data['token'])
            return queryset
        elif ("username" in self.request.data.keys()
              and "password" in self.request.data.keys()
              and "service" in self.request.data.keys()
            ):
            queryset = queryset.filter(username=self.request.data['username'],
                                       password=self.request.data['password'],
                                       service=self.request.data['service'])
            return queryset

        return Mail.objects.none()

    def create(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.exists():
            serializer = MailSerializer(instance=queryset.first())
            return Response(serializer.data, status=201)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = get_service(serializer.validated_data['service'])(
            serializer.validated_data['username'],
            serializer.validated_data['password']
        )

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=201, headers=headers)

