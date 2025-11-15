from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.contrib.auth import get_user_model
from .serializers import *
from .models import *
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django.db.models import Q
from rest_framework.permissions import IsAuthenticated

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        email = serializer.validated_data["email"]
        first_name = serializer.validated_data["first_name"]
        last_name = serializer.validated_data["last_name"]
        password = serializer.validated_data["password"]

        if User.objects.filter(username=username).exists():
            return Response({"username": "This username is already taken."}, status=400)

        if User.objects.filter(email=email).exists():
            return Response({"email": "This email is already in use."}, status=400)

        User.objects.create_user(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password
        )

        return Response({"message": "User created successfully."}, status=status.HTTP_201_CREATED)
    


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(Q(username=username) | Q(email=username)).first()
        if not user or not user.check_password(password):
            return Response({"detail": "Geçersiz kimlik bilgileri."}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        expire_minutes = int(getattr(settings, "SIMPLE_JWT", {}).get(
            "ACCESS_TOKEN_LIFETIME"
        ).total_seconds() // 60)

        return Response({
            "refresh": str(refresh),
            "access": str(access),
            "expire_minutes": expire_minutes
        }, status=status.HTTP_200_OK)
    


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()  # ← logout burada gerçekleşiyor
        except Exception:
            return Response({"detail": "Geçersiz token."}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Çıkış başarılı."}, status=status.HTTP_205_RESET_CONTENT)