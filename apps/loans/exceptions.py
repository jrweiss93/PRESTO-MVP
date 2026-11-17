"""Excepciones de dominio de la app loans."""

from apps.core.exceptions import DomainError


class LoansError(DomainError):
    """Error de dominio de loans."""


class LoanNotFound(LoansError):
    """El préstamo no existe."""


class NotTheBorrower(LoansError):
    """Solo el prestatario puede pagar las cuotas."""


class InstallmentOutOfOrder(LoansError):
    """Las cuotas se pagan en orden."""


class InstallmentAlreadyPaid(LoansError):
    """La cuota ya está pagada."""


class InvalidLoanTransition(LoansError):
    """La transición de estado del préstamo no es válida."""


class InvalidLoanMessage(LoansError):
    """El mensaje del chat está vacío o supera el largo permitido."""


class InvalidLoanReview(LoansError):
    """La reseña no cumple las reglas del préstamo."""


class DuplicateLoanReview(LoansError):
    """El usuario ya dejó una reseña para este préstamo."""
