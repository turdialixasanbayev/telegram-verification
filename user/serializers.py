from django.contrib.auth import authenticate
from django.utils import timezone

from rest_framework import serializers

from .models import User, PhoneNumberVerification
from .services.telegram_gateway import TelegramGatewayService


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "phone_number",
            "password",
        ]
        extra_kwargs = {
            "password": {
                "write_only": True,
                "min_length": 8,
            },
        }

    def create(self, validated_data):
        user = User.objects.create_user(
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
        )

        telegram = TelegramGatewayService()

        result = telegram.send_verification_code(
            phone_number=user.phone_number,
        )

        PhoneNumberVerification.objects.create(
            user=user,
            request_id=result["request_id"],
            expires_at=timezone.now() + timezone.timedelta(seconds=300),
        )

        return user


class VerifySerializer(serializers.Serializer):
    request_id = serializers.CharField()
    code = serializers.CharField(
        min_length=6,
        max_length=6,
    )

    def validate(self, attrs):
        request_id = attrs["request_id"]
        code = attrs["code"]

        try:
            verification = (
                PhoneNumberVerification.objects
                .select_related("user")
                .get(
                    request_id=request_id,
                    is_active=True,
                )
            )
        except PhoneNumberVerification.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or inactive verification request."
            )

        if verification.expires_at <= timezone.now():
            verification.is_active = False
            verification.save(update_fields=["is_active"])

            raise serializers.ValidationError(
                "Verification request has expired."
            )

        telegram = TelegramGatewayService()

        try:
            result = telegram.check_verification_code(
                request_id=request_id,
                code=code,
            )
        except RuntimeError:
            raise serializers.ValidationError(
                "Invalid verification code."
            )

        verification_status = result["verification_status"]["status"]

        if verification_status != "code_valid":
            raise serializers.ValidationError(
                "Invalid verification code."
            )

        verification.is_active = False
        verification.save(update_fields=["is_active"])

        user = verification.user
        user.phone_number_verified = True
        user.save(update_fields=["phone_number_verified"])

        return {
            "user": user,
        }


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(
        write_only=True,
    )

    def validate(self, attrs):
        phone_number = attrs["phone_number"]
        password = attrs["password"]

        user = authenticate(
            request=self.context.get("request"),
            phone_number=phone_number,
            password=password,
        )

        if user is None:
            raise serializers.ValidationError(
                "Invalid phone number or password."
            )

        if not user.phone_number_verified:
            raise serializers.ValidationError(
                "Phone number is not verified."
            )

        attrs["user"] = user

        return attrs


class ResendVerificationSerializer(serializers.Serializer):
    request_id = serializers.CharField()

    def validate(self, attrs):
        request_id = attrs["request_id"]

        try:
            verification = (
                PhoneNumberVerification.objects
                .select_related("user")
                .get(
                    request_id=request_id,
                    is_active=True,
                )
            )
        except PhoneNumberVerification.DoesNotExist:
            raise serializers.ValidationError(
                "Invalid or inactive verification request."
            )

        telegram = TelegramGatewayService()

        result = telegram.send_verification_code(
            phone_number=verification.user.phone_number,
        )

        verification.is_active = False
        verification.save(update_fields=["is_active"])

        new_verification = PhoneNumberVerification.objects.create(
            user=verification.user,
            request_id=result["request_id"],
            expires_at=timezone.now() + timezone.timedelta(seconds=300),
        )

        attrs["verification"] = new_verification

        return attrs
