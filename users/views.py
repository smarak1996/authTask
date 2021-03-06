
from functools import partial
from django.shortcuts import render
from rest_framework.generics import GenericAPIView, ListCreateAPIView, UpdateAPIView, DestroyAPIView
from .models import User, UserType, Task
from users.serializers import UserSerializer, UserTypeSerializer, TaskSerailizer
from rest_framework.response import Response
from rest_framework.exceptions import AuthenticationFailed
from django.http import HttpResponse
import jwt
import datetime

from users import serializers


class RegisterView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class LoginView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        email = request.data['email']
        password = request.data['password']

        user = User.objects.filter(email=email).first()

        if user is None:
            raise AuthenticationFailed('User not found')

        if not user.check_password(password):
            raise AuthenticationFailed('Incorrect Password')

        payload = {
            'id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60),
            'iat': datetime.datetime.utcnow()
        }

        token = jwt.encode(payload, 'secret',
                           algorithm='HS256')

        response = Response()

        response.set_cookie(key='jwt', value=token, httponly=True)

        response.data = {
            'jwt': token
        }

        return response


class UserView(GenericAPIView):
    serializer_class = UserSerializer

    def get(self, request):
        token = request.COOKIES.get('jwt')

        if not token:
            raise AuthenticationFailed('UnAuthenticated')

        try:
            payload = jwt.decode(token, 'secret', algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('UnAuthenticated')

        user = User.objects.filter(id=payload['id']).first()
        serializer = UserSerializer(user)

        return Response(serializer.data)


class LogoutView(GenericAPIView):
    serializer_class = UserSerializer

    def post(self, request):
        response = Response()
        response.delete_cookie('jwt')
        response.data = {
            'message': 'Successfully Logged out'
        }
        return response


class UserTypeApiView(ListCreateAPIView):
    queryset = UserType.objects.all()
    serializer_class = UserTypeSerializer


class TaskListApiView(ListCreateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerailizer

    def create(self, validated_data):
        print(self.request.user)
        print("00000000000000000000000000000000")
        user = UserType.objects.filter(
            user_type='Client', user__username=self.request.user.username)
        print(user)
        if user:
            task = Task.objects.create(
                title=validated_data["title"],
                task_date=validated_data["task_date"],
                status=validated_data["status"],
                description=validated_data['description']
            )
            task.save()
            return task
        else:
            return HttpResponse('This user cannot create task')


class TaskDetailApiView(UpdateAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerailizer
    lookup_field = 'pk'

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        print('dddddddddddddd')
        user = UserType.objects.filter(
            user_type='Employee', user__username=self.request.user.username)

        if user:
            serializer = self.get_serializer(
                instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return HttpResponse("updated successfully")
        else:
            return HttpResponse('This user cannot complete task')


class TaskDeleteApiView(DestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskSerailizer

    def delete(self, request, *args, **kwargs):
        user = UserType.objects.filter(
            user_type='Manager', user__username=self.request.user.username)
        if user:
            return super().delete(request, *args, **kwargs)
        else:
            return HttpResponse('Only manager can delete')
