"""Serializers de la app identity: solo validan entrada y dan formato a la salida."""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.identity.models import BiometricCheck, KYCVerification, PrestoProfile, Profile, User
from apps.identity.selectors import (
    get_active_profile,
    get_latest_biometric_check,
    get_profile,
    list_profiles_for_user,
)


class RegisterSerializer(serializers.Serializer):
    """Datos necesarios para registrar un usuario."""

    email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )
    profile_kind = serializers.ChoiceField(
        choices=PrestoProfile.Kind.choices,
        required=False,
    )
    terms_accepted = serializers.BooleanField()

    def validate_terms_accepted(self, value):
        """Exige que el usuario haya aceptado los términos y condiciones."""
        if value is not True:
            raise serializers.ValidationError('Debés aceptar los términos y condiciones.')
        return value


class LoginSerializer(serializers.Serializer):
    """Credenciales de acceso."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})


class PrestoProfileSerializer(serializers.ModelSerializer):
    """Perfil de Presto que el usuario puede activar."""

    class Meta:
        model = PrestoProfile
        fields = ['kind', 'is_active']
        read_only_fields = fields


class ProfileSerializer(serializers.ModelSerializer):
    """Datos del perfil de un usuario."""

    class Meta:
        model = Profile
        fields = ['id', 'phone_number', 'date_of_birth', 'country']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    """Datos públicos de un usuario, con sus perfiles de Presto."""

    email_verified = serializers.BooleanField(read_only=True)
    profile = serializers.SerializerMethodField()
    profiles = serializers.SerializerMethodField()
    active_profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'email_verified',
            'terms_accepted_at',
            'profile',
            'profiles',
            'active_profile',
        ]
        read_only_fields = ['id', 'email', 'email_verified', 'terms_accepted_at']

    @extend_schema_field(ProfileSerializer(allow_null=True))
    def get_profile(self, obj):
        """Devuelve el perfil de identidad del usuario, o null si no tiene."""
        profile = get_profile(obj.id)
        return ProfileSerializer(profile).data if profile else None

    @extend_schema_field(PrestoProfileSerializer(many=True))
    def get_profiles(self, obj):
        """Devuelve los perfiles de Presto del usuario (con cuál está activo)."""
        return PrestoProfileSerializer(list_profiles_for_user(obj.id), many=True).data

    @extend_schema_field(serializers.CharField(allow_null=True))
    def get_active_profile(self, obj):
        """Devuelve el tipo del perfil activo, o null si no hay ninguno."""
        active = get_active_profile(obj.id)
        return active.kind if active else None


class MeUpdateSerializer(serializers.Serializer):
    """Campos del perfil que el usuario puede actualizar sobre sí mismo."""

    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=32,
    )
    date_of_birth = serializers.DateField(required=False, allow_null=True)
    country = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=2,
        validators=[Profile.country_validator],
    )


class KYCRequestSerializer(serializers.Serializer):
    """Metadata de documentos para solicitar la verificación KYC."""

    documents = serializers.JSONField()


class BiometricCheckSerializer(serializers.ModelSerializer):
    """Resultado de una validación biométrica simulada."""

    class Meta:
        model = BiometricCheck
        fields = [
            'id',
            'status',
            'liveness_score',
            'match_score',
            'provider',
            'checked_at',
            'result_details',
        ]
        read_only_fields = fields


class KYCVerificationSerializer(serializers.ModelSerializer):
    """Estado de una verificación KYC, con su validación biométrica más reciente."""

    biometric = serializers.SerializerMethodField()

    class Meta:
        model = KYCVerification
        fields = [
            'id',
            'status',
            'requested_at',
            'resolved_at',
            'resolved_by_user_id',
            'documents',
            'biometric',
        ]
        read_only_fields = fields

    @extend_schema_field(BiometricCheckSerializer(allow_null=True))
    def get_biometric(self, obj):
        """Devuelve la validación biométrica más reciente de la verificación."""
        check = get_latest_biometric_check(user_id=obj.user_id, verification_id=obj.id)
        return BiometricCheckSerializer(check).data if check else None


class BiometricCheckRequestSerializer(serializers.Serializer):
    """Muestra biométrica simulada (no se procesan datos reales)."""

    sample = serializers.JSONField()


class LoginResponseSerializer(serializers.Serializer):
    """Respuesta del login con el access token y los datos del usuario.

    El refresh token **no** va en el cuerpo: viaja en una cookie httpOnly
    (ADR 0014).
    """

    access = serializers.CharField()
    user = UserSerializer()


class TokenRefreshResponseSerializer(serializers.Serializer):
    """Respuesta del refresh: solo el access token nuevo."""

    access = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    """Email de la cuenta que quiere recuperar la contraseña."""

    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Datos del enlace de reseteo y la contraseña nueva."""

    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(
        write_only=True,
        min_length=8,
        style={'input_type': 'password'},
    )


class EmailVerificationSerializer(serializers.Serializer):
    """Datos del enlace de verificación de email."""

    uid = serializers.CharField()
    token = serializers.CharField()


class EmailVerificationResponseSerializer(serializers.Serializer):
    """Resultado de confirmar el email."""

    email = serializers.EmailField()
    email_verified = serializers.BooleanField()


class DetailMessageSerializer(serializers.Serializer):
    """Mensaje informativo de una operación sin más datos."""

    detail = serializers.CharField()
