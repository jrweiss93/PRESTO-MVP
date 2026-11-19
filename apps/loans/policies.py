"""Reglas de préstamos que el ledger consulta antes de un retiro."""

import uuid

from apps.ledger.exceptions import WithdrawalBlockedByActiveLoan
from apps.loans import selectors

BLOCKED_WITHDRAWAL_MESSAGE = (
    'No podés retirar dinero mientras tengas un préstamo vigente. '
    'Podés seguir depositando y pagar tus cuotas.'
)


def block_withdrawal_with_open_loan(user_id: uuid.UUID) -> None:
    """Impide retirar si el usuario debe un préstamo P2P vigente.

    Args:
        user_id: usuario que quiere retirar.

    Raises:
        WithdrawalBlockedByActiveLoan: si el usuario es prestatario de un
            préstamo activo o en mora.
    """
    if selectors.has_open_borrower_loan(user_id):
        raise WithdrawalBlockedByActiveLoan(BLOCKED_WITHDRAWAL_MESSAGE)
