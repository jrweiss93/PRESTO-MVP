"""Puntos de extensión para reglas de otros dominios sobre el ledger.

El ledger no puede importar los dominios que están por encima (contrato
`ledger-no-loans`). Para que préstamos pueda vetar un retiro sin romper la
dirección de dependencias, el ledger expone un registro de guardas que cada
app registra al arrancar. La guarda se ejecuta antes de mover dinero.
"""

import uuid
from collections.abc import Callable

# Una guarda recibe el usuario y lanza una excepción de dominio si la
# operación no está permitida.
WithdrawalGuard = Callable[[uuid.UUID], None]

_WITHDRAWAL_GUARDS: list[WithdrawalGuard] = []


def register_withdrawal_guard(guard: WithdrawalGuard) -> None:
    """Registra una guarda de retiro.

    Es idempotente por función: volver a registrar la misma guarda no la
    duplica, así los tests y los recargos de apps no la ejecutan dos veces.

    Args:
        guard: función que valida si el usuario puede retirar.
    """
    if guard not in _WITHDRAWAL_GUARDS:
        _WITHDRAWAL_GUARDS.append(guard)


def check_withdrawal_allowed(user_id: uuid.UUID) -> None:
    """Ejecuta las guardas registradas antes de un retiro.

    Args:
        user_id: usuario que quiere retirar.

    Raises:
        Exception: la excepción de dominio que lance la primera guarda que
            rechace la operación.
    """
    for guard in _WITHDRAWAL_GUARDS:
        guard(user_id)
