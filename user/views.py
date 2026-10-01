from django.contrib.auth import login

from rest_framework import status
from rest_framework.response import Response
from rest_framework.generics import GenericAPIView

from .serializers import (
    RegisterSerializer,
    VerifySerializer,
    LoginSerializer,
)


class RegisterView(GenericAPIView):
    serializer_class = RegisterSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.save()

        verification = user.phone_number_verifications.get(
            is_active=True,
        )

        return Response(
            {
                "message": "Verification code sent.",
                "request_id": verification.request_id,
                "redirect_url": "/api/v1/auth/verify/",
            },
            status=status.HTTP_201_CREATED,
        )


class VerifyView(GenericAPIView):
    serializer_class = VerifySerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
        )

        serializer.is_valid(raise_exception=True)

        return Response(
            {
                "message": "Phone number verified successfully.",
                "redirect_url": "/api/v1/auth/login/",
            },
            status=status.HTTP_200_OK,
        )


class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "request": request,
            },
        )

        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]

        login(request, user)

        return Response(
            {
                "message": "Login successful.",
            },
            status=status.HTTP_200_OK,
        )
