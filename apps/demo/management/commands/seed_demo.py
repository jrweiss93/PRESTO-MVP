"""Command `seed_demo`: siembra el escenario de demostración.

Uso:

```sh
python manage.py seed_demo
```

El comando es **idempotente**: las claves de idempotencia son fijas, así que
se puede volver a sembrar sin duplicar ni un centavo. Necesita el dinero
simulado habilitado (`DEMO_MODE=true` o
`LEDGER_SIMULATED_DEPOSITS_ENABLED=true`), porque los depósitos del escenario
son simulados.
"""

from django.core.management.base import BaseCommand, CommandError

from apps.demo.seeds import DEMO_PASSWORD, seed_demo


class Command(BaseCommand):
    """Siembra el escenario de demostración de Presto."""

    help = 'Siembra un escenario de demostración: usuarios, préstamo, inversión y pagos.'

    def add_arguments(self, parser):
        """Agrega los argumentos del comando.

        Args:
            parser: el parser de argumentos.

        Returns:
            None.
        """
        parser.add_argument(
            '--currency',
            default='ARS',
            help='Moneda del escenario (ARS o USD).',
        )
        parser.add_argument(
            '--password',
            default=DEMO_PASSWORD,
            help='Contraseña de las personas de la demo.',
        )

    def handle(self, *args, **options):
        """Siembra el escenario y cuenta lo que quedó.

        Args:
            args: argumentos posicionales (no se usan).
            options: opciones del comando.

        Returns:
            None.

        Raises:
            CommandError: si el dinero simulado está deshabilitado.
        """
        from django.conf import settings

        if not settings.LEDGER_SIMULATED_DEPOSITS_ENABLED:
            raise CommandError(
                'El escenario usa dinero simulado: arrancá con DEMO_MODE=true '
                'o LEDGER_SIMULATED_DEPOSITS_ENABLED=true.'
            )

        summary = seed_demo(currency=options['currency'], password=options['password'])

        self.stdout.write(self.style.SUCCESS('Escenario de demostración sembrado.'))
        self.stdout.write('')
        self.stdout.write('Personas (la contraseña es la misma para todas):')
        for email in summary.users:
            self.stdout.write(f'  - {email} / {options["password"]}')
        if summary.offer_id:
            self.stdout.write(f'Oferta: {summary.offer_id}')
        if summary.loan_id:
            self.stdout.write(f'Préstamo: {summary.loan_id}')
        for payment_id in summary.payment_ids:
            self.stdout.write(f'Pago: {payment_id}')
        self.stdout.write('')
        self.stdout.write('Saldos:')
        for email, balance in summary.balances.items():
            self.stdout.write(f'  - {email}: {balance} {options["currency"]}')
        self.stdout.write('')
        self.stdout.write(
            self.style.WARNING(
                'Son usuarios de muestra: no los uses en un entorno real sin cambiar la contraseña.'
            )
        )
