"""Sitio de admin de Presto con un dashboard de métricas.

Las métricas se calculan con consultas de solo lectura (agregaciones). Se usan
`apps.get_model` para los conteos simples donde no hay selector, evitando
importar módulos `models` de otras apps de forma estática (el contrato
`reports-only-services-and-selectors` de import-linter). Los selectores
públicos se usan cuando existen.
"""

from __future__ import annotations

from decimal import Decimal

from django.apps import apps
from django.contrib import admin
from django.db.models import Count, Sum
from django.template.response import TemplateResponse
from django.urls import path
from django.utils import timezone

from apps.ledger.selectors import get_balance_breakdown


def _zero(value):
    """Devuelve 0 en lugar de None para sumas vacías."""
    return value if value is not None else Decimal('0.00')


def _collect_metrics():
    """Calcula las métricas del panel de administración.

    Returns:
        Un diccionario con secciones de métricas listas para la plantilla.
    """
    User = apps.get_model('identity', 'User')
    PrestoProfile = apps.get_model('identity', 'PrestoProfile')
    KYCVerification = apps.get_model('identity', 'KYCVerification')
    BiometricCheck = apps.get_model('identity', 'BiometricCheck')
    Offer = apps.get_model('offers', 'Offer')
    Loan = apps.get_model('loans', 'Loan')
    Installment = apps.get_model('loans', 'Installment')
    Position = apps.get_model('investments', 'Position')
    Payment = apps.get_model('payments', 'Payment')
    Notification = apps.get_model('notifications', 'Notification')

    today = timezone.localdate()

    users_total = User.objects.count()
    users_verified = User.objects.filter(email_verified_at__isnull=False).count()
    profiles = {
        row['kind']: row['total']
        for row in PrestoProfile.objects.filter(is_active=True)
        .values('kind')
        .annotate(total=Count('id'))
    }

    kyc = {
        row['status']: row['total']
        for row in KYCVerification.objects.values('status').annotate(total=Count('id'))
    }
    biometric_passed = BiometricCheck.objects.filter(status=BiometricCheck.Status.PASSED).count()

    loans = {
        row['status']: row['total']
        for row in Loan.objects.values('status').annotate(total=Count('id'))
    }
    active_principal_ars = _zero(
        Loan.objects.filter(status=Loan.Status.ACTIVE, currency='ARS').aggregate(
            total=Sum('principal')
        )['total']
    )
    overdue_installments = Installment.objects.filter(status=Installment.Status.OVERDUE).count()
    pending_due = Installment.objects.filter(
        status=Installment.Status.PENDING, due_date__lt=today
    ).count()

    offers = {
        row['status']: row['total']
        for row in Offer.objects.values('status').annotate(total=Count('id'))
    }

    positions = {
        row['status']: row['total']
        for row in Position.objects.values('status').annotate(total=Count('id'))
    }
    invested_ars = _zero(
        Position.objects.filter(status=Position.Status.ACTIVE, product__currency='ARS').aggregate(
            total=Sum('amount')
        )['total']
    )

    payments = {
        row['status']: row['total']
        for row in Payment.objects.values('status').annotate(total=Count('id'))
    }

    notifications = {
        row['status']: row['total']
        for row in Notification.objects.values('status').annotate(total=Count('id'))
    }

    try:
        ledger_ars = {str(k): v for k, v in get_balance_breakdown('ARS').items()}
    except Exception:
        ledger_ars = None
    try:
        ledger_usd = {str(k): v for k, v in get_balance_breakdown('USD').items()}
    except Exception:
        ledger_usd = None

    return {
        'generated_at': timezone.now(),
        'users': {
            'total': users_total,
            'verified': users_verified,
            'borrowers': profiles.get(PrestoProfile.Kind.BORROWER, 0),
            'lenders': profiles.get(PrestoProfile.Kind.LENDER, 0),
            'investors': profiles.get(PrestoProfile.Kind.INVESTOR, 0),
        },
        'kyc': {
            'pending': kyc.get(KYCVerification.Status.PENDING, 0),
            'approved': kyc.get(KYCVerification.Status.APPROVED, 0),
            'rejected': kyc.get(KYCVerification.Status.REJECTED, 0),
            'biometric_passed': biometric_passed,
        },
        'loans': {
            'active': loans.get(Loan.Status.ACTIVE, 0),
            'completed': loans.get(Loan.Status.PAID, 0),
            'defaulted': loans.get(Loan.Status.DEFAULTED, 0),
            'active_principal_ars': active_principal_ars,
            'overdue_installments': overdue_installments,
            'pending_past_due': pending_due,
        },
        'offers': {
            'active': offers.get(Offer.Status.ACTIVE, 0),
            'matched': offers.get(Offer.Status.ACCEPTED, 0),
            'cancelled': offers.get(Offer.Status.EXPIRED, 0),
        },
        'investments': {
            'active': positions.get(Position.Status.ACTIVE, 0),
            'settled': positions.get(Position.Status.MATURED, 0),
            'invested_ars': invested_ars,
        },
        'payments': payments,
        'notifications': notifications,
        'ledger_ars': ledger_ars,
        'ledger_usd': ledger_usd,
    }


class PrestoAdminSite(admin.AdminSite):
    """Admin de Django con un panel de métricas para la demo."""

    site_header = 'Presto administración'
    site_title = 'Presto admin'
    index_title = 'Panel de control'
    index_template = 'admin/reports/index.html'

    def get_urls(self):
        """Agrega la vista de métricas al admin."""
        urls = super().get_urls()
        custom = [
            path(
                'metrics/',
                self.admin_view(self.metrics_view),
                name='reports-metrics',
            ),
        ]
        return custom + urls

    def metrics_view(self, request):
        """Muestra el dashboard de métricas."""
        context = {
            **self.each_context(request),
            'title': 'Métricas',
            'metrics': _collect_metrics(),
        }
        return TemplateResponse(request, 'admin/reports/metrics.html', context)


site = PrestoAdminSite(name='admin')
