"""Excepciones de dominio de la app identity."""

from apps.core.exceptions import DomainError


class IdentityError(DomainError):
    """Error de dominio de identity."""


class EmailAlreadyRegistered(IdentityError):
    """El email ya está registrado."""


class PendingKYCExists(IdentityError):
    """El usuario ya tiene una verificación KYC pendiente."""


class KYCAlreadyResolved(IdentityError):
    """La verificación KYC ya fue resuelta."""


class InvalidKYCResolution(IdentityError):
    """La resolución de KYC no es válida."""


class InvalidDocuments(IdentityError):
    """Los documentos enviados no son un objeto JSON de metadata."""


class InvalidProfileField(IdentityError):
    """Se intentó modificar un campo que no pertenece al perfil."""


class InvalidProfileKind(IdentityError):
    """El perfil de Presto indicado no existe o no le pertenece al usuario."""


class InvalidBiometricSample(IdentityError):
    """La muestra biométrica enviada no es válida (no es un objeto JSON)."""


class WeakPassword(IdentityError):
    """La contraseña no pasa los validadores de Django."""


class InvalidToken(IdentityError):
    """El token de un enlace no es válido o venció."""


class InvalidCurrentPassword(IdentityError):
    """La contraseña actual no coincide."""


class BackupAccountNotFound(IdentityError):
    """La cuenta de respaldo no existe o no pertenece al usuario."""


class BackupAccountAlreadyExists(IdentityError):
    """Ya hay una cuenta de respaldo con ese proveedor y referencia."""


class InvalidBackupAccount(IdentityError):
    """Los datos de la cuenta de respaldo no son válidos."""


class InvalidBackupVerification(IdentityError):
    """El código de verificación de la cuenta de respaldo no es válido."""


class BackupAccountRequired(IdentityError):
    """El prestatario necesita una cuenta de respaldo verificada."""


class InsufficientRepaymentCapacity(IdentityError):
    """La cuenta de respaldo no cubre la primera cuota del préstamo."""


class ActiveLoanBlocksAction(IdentityError):
    """Hay un préstamo activo que impide desvincular la cuenta."""


class AccountClosureBlocked(IdentityError):
    """La cuenta no se puede cerrar porque tiene operaciones activas."""
