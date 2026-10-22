"""Vistas de la API de identity."""

import logging

from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed, NotFound, ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from apps.identity.exceptions import (
    EmailAlreadyRegistered,
    InvalidToken,
    PendingKYCExists,
    WeakPassword,
)
from apps.identity.permissions import (
    EmailVerificationThrottle,
    LoginThrottle,
    PasswordResetThrottle,
    RegisterThrottle,
)
from apps.identity.selectors import get_kyc_by_id, get_kyc_for_user, get_profile
from apps.identity.serializers import (
    DetailMessageSerializer,
    EmailVerificationResponseSerializer,
    EmailVerificationSerializer,
    KYCRequestSerializer,
    KYCVerificationSerializer,
    LoginResponseSerializer,
    LoginSerializer,
    MeUpdateSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    ProfileSerializer,
    RegisterSerializer,
    TokenRefreshResponseSerializer,
    UserSerializer,
)
from apps.identity.services import (
    clear_refresh_cookie,
    confirm_email_verification,
    confirm_password_reset,
    get_refresh_token,
    register_user,
    request_password_reset,
    send_email_verification,
    set_refresh_cookie,
    submit_kyc,
    update_profile,
)

logger = logging.getLogger(__name__)


def build_me_payload(user) -> dict:
    """Arma la respuesta del perfil propio con los datos del usuario y su perfil."""
    payload = UserSerializer(user).data
    profile = get_profile(user_id=user.id)
    payload['profile'] = ProfileSerializer(profile).data if profile else None
    return payload


class RegisterView(APIView):
    """Alta de usuarios."""

    permission_classes = [AllowAny]
    throttle_classes = [RegisterThrottle]
    throttle_scope = 'register'

    @extend_schema(
        request=RegisterSerializer,
        responses={201: UserSerializer},
        summary='Registrar un usuario',
    )
    def post(self, request):
        """Registra un usuario nuevo y devuelve sus datos."""
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = register_user(
                email=serializer.validated_data['email'],
                password=serializer.validated_data['password'],
            )
        except EmailAlreadyRegistered as exc:
            raise ValidationError({'email': [str(exc)]}) from exc
        except WeakPassword as exc:
            raise ValidationError({'password': [str(exc)]}) from exc
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Autenticación con JWT."""

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]
    throttle_scope = 'login'

    @extend_schema(
        request=LoginSerializer,
        responses={200: LoginResponseSerializer},
        summary='Iniciar sesión y obtener el access token',
        description=(
            'Devuelve el access token en el cuerpo y deja el refresh token en '
            'una cookie httpOnly (`presto_refresh`). El refresh token no se '
            'devuelve en el cuerpo de la respuesta (ADR 0014).'
        ),
    )
    def post(self, request):
        """Valida las credenciales, devuelve el access y setea la cookie."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            raise AuthenticationFailed('Credenciales inválidas.')
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                'access': str(refresh.access_token),
                'user': UserSerializer(user).data,
            }
        )
        set_refresh_cookie(response, str(refresh))
        return response


class TokenRefreshView(APIView):
    """Renueva el access token rotando el refresh token."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={200: TokenRefreshResponseSerializer},
        summary='Renovar el access token rotando el refresh token',
        description=(
            'Lee el refresh token de la cookie httpOnly y lo rota: la cookie '
            'se reemplaza por una nueva y el token anterior queda '
            'blacklisted (ADR 0014).'
        ),
    )
    def post(self, request):
        """Rota el refresh de la cookie y devuelve el nuevo access token."""
        token = get_refresh_token(request)
        if not token:
            raise AuthenticationFailed('Falta el refresh token.')
        serializer = TokenRefreshSerializer(data={'refresh': token})
        try:
            serializer.is_valid(raise_exception=True)
        except TokenError as exc:
            raise AuthenticationFailed('El refresh token no es válido.') from exc
        data = serializer.validated_data
        response = Response({'access': data['access']})
        if 'refresh' in data:
            set_refresh_cookie(response, data['refresh'])
        return response


class LogoutView(APIView):
    """Cierre de sesión: blacklistea el refresh token y borra la cookie."""

    permission_classes = [AllowAny]

    @extend_schema(
        request=None,
        responses={204: None},
        summary='Cerrar sesión',
        description=(
            'Blacklistea el refresh token (de la cookie httpOnly o del cuerpo) '
            'y borra la cookie. Responde 204 aunque no haya sesión (ADR 0014).'
        ),
    )
    def post(self, request):
        """Invalida el refresh token y limpia la cookie."""
        token = get_refresh_token(request)
        if token:
            try:
                RefreshToken(token).blacklist()
            except TokenError:
                logger.info('Logout con un refresh token que no se pudo invalidar.')
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_refresh_cookie(response)
        return response


class MeView(APIView):
    """Perfil del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UserSerializer}, summary='Ver el propio perfil')
    def get(self, request):
        """Devuelve los datos del usuario autenticado y su perfil."""
        return Response(build_me_payload(request.user))

    @extend_schema(
        request=MeUpdateSerializer,
        responses={200: UserSerializer},
        summary='Actualizar el propio perfil',
    )
    def patch(self, request):
        """Actualiza los datos del perfil del usuario autenticado."""
        serializer = MeUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        update_profile(user=request.user, changes=serializer.validated_data)
        return Response(build_me_payload(request.user))


class KycView(APIView):
    """Estado y solicitud de verificación KYC del usuario autenticado."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: KYCVerificationSerializer},
        summary='Ver el estado KYC propio',
        operation_id='kyc_list',
    )
    def get(self, request):
        """Devuelve la verificación KYC vigente del usuario, o null si no tiene."""
        verification = get_kyc_for_user(user_id=request.user.id)
        if verification is None:
            return Response(None, status=status.HTTP_200_OK)
        return Response(KYCVerificationSerializer(verification).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=KYCRequestSerializer,
        responses={201: KYCVerificationSerializer},
        summary='Solicitar la verificación KYC',
    )
    def post(self, request):
        """Crea una solicitud de verificación KYC en estado pending."""
        serializer = KYCRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            verification = submit_kyc(
                user=request.user,
                documents=serializer.validated_data['documents'],
            )
        except PendingKYCExists as exc:
            raise ValidationError({'documents': [str(exc)]}) from exc
        return Response(
            KYCVerificationSerializer(verification).data,
            status=status.HTTP_201_CREATED,
        )


class KycDetailView(APIView):
    """Detalle de una verificación KYC propia."""

    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={200: KYCVerificationSerializer},
        summary='Ver una verificación KYC propia',
        operation_id='kyc_retrieve',
    )
    def get(self, request, verification_id):
        """Devuelve la verificación KYC indicada si pertenece al usuario."""
        verification = get_kyc_by_id(verification_id=verification_id, user_id=request.user.id)
        if verification is None:
            raise NotFound('La verificación KYC no existe.')
        return Response(KYCVerificationSerializer(verification).data, status=status.HTTP_200_OK)


class PasswordResetRequestView(APIView):
    """Pedido de reseteo de contraseña (siempre responde 202)."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PasswordResetThrottle]
    throttle_scope = 'password_reset'

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={202: DetailMessageSerializer},
        summary='Pedir un enlace para restablecer la contraseña',
        operation_id='auth_password_reset_request',
    )
    def post(self, request):
        """Envía el enlace de reseteo si el email está registrado.

        La respuesta es la misma exista o no la cuenta: no se puede usar el
        endpoint para averiguar qué emails están registrados.
        """
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_password_reset(email=serializer.validated_data['email'])
        return Response(
            {
                'detail': (
                    'Si el email está registrado, te enviamos un enlace para '
                    'restablecer la contraseña.'
                )
            },
            status=status.HTTP_202_ACCEPTED,
        )


class PasswordResetConfirmView(APIView):
    """Confirmación del reseteo con el token del enlace."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [PasswordResetThrottle]
    throttle_scope = 'password_reset'

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: DetailMessageSerializer},
        summary='Restablecer la contraseña con el token del enlace',
        operation_id='auth_password_reset_confirm',
    )
    def post(self, request):
        """Cambia la contraseña si el token es válido."""
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            confirm_password_reset(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
                new_password=serializer.validated_data['new_password'],
            )
        except InvalidToken as exc:
            raise ValidationError({'token': [str(exc)]}) from exc
        except WeakPassword as exc:
            raise ValidationError({'new_password': [str(exc)]}) from exc
        return Response(
            {'detail': 'Contraseña actualizada. Ya podés iniciar sesión con la nueva.'},
            status=status.HTTP_200_OK,
        )


class EmailVerificationView(APIView):
    """Confirmación del email con el token del enlace."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_classes = [EmailVerificationThrottle]
    throttle_scope = 'email_verification'

    @extend_schema(
        request=EmailVerificationSerializer,
        responses={200: EmailVerificationResponseSerializer},
        summary='Confirmar el email con el token del enlace',
        operation_id='auth_email_verify',
    )
    def post(self, request):
        """Marca el email como verificado si el token es válido."""
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = confirm_email_verification(
                uid=serializer.validated_data['uid'],
                token=serializer.validated_data['token'],
            )
        except InvalidToken as exc:
            raise ValidationError({'token': [str(exc)]}) from exc
        return Response({'email': user.email, 'email_verified': True})


class EmailVerificationResendView(APIView):
    """Reenvío del correo de verificación para el usuario autenticado."""

    permission_classes = [IsAuthenticated]
    throttle_classes = [EmailVerificationThrottle]
    throttle_scope = 'email_verification'

    @extend_schema(
        request=None,
        responses={202: DetailMessageSerializer},
        summary='Reenviar el correo de verificación',
        operation_id='auth_email_resend',
    )
    def post(self, request):
        """Reenvía el enlace; si el email ya está verificado, lo informa."""
        sent = send_email_verification(request.user)
        detail = (
            'Te enviamos el correo de verificación.' if sent else 'Tu email ya está verificado.'
        )
        return Response({'detail': detail}, status=status.HTTP_202_ACCEPTED)
