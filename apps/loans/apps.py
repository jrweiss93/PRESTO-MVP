from django.apps import AppConfig


class LoansConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.loans'
    verbose_name = 'Loans'

    def ready(self):
        """Registra la regla de retiro en el ledger.

        El ledger no puede importar loans (contrato `ledger-no-loans`), así que
        la dependencia se invierte: loans registra su guarda al arrancar y el
        ledger la ejecuta antes de cada retiro. Ver `apps/ledger/policies.py`.
        """
        from apps.ledger.policies import register_withdrawal_guard
        from apps.loans.policies import block_withdrawal_with_open_loan

        register_withdrawal_guard(block_withdrawal_with_open_loan)
