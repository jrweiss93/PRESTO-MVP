"""Recorrido funcional completo contra la API local de Presto.

Uso (con el backend levantado y `manage.py seed_demo`):

    python scripts/demo_flow.py

Variables de entorno opcionales:

- ``PRESTO_API_URL``: base de la API (por defecto ``http://127.0.0.1:8000/api/v1``).
- ``PRESTO_DEMO_PASSWORD``: contraseña de las cuentas que crea el recorrido.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE = os.getenv('PRESTO_API_URL', 'http://127.0.0.1:8000/api/v1')
REPO = str(Path(__file__).resolve().parent.parent)
PASSWORD = os.getenv('PRESTO_DEMO_PASSWORD', 'Presto2026Demo!')
RUN = str(int(time.time()))


def mail(name):
    return f'{name}+{RUN}@demo.local'


def req(method, path, body=None, token=None, headers=None, raw=False, full=False):
    url = BASE + path
    data = json.dumps(body).encode('utf-8') if body is not None else None
    request_headers = {'Content-Type': 'application/json'}
    if token:
        request_headers['Authorization'] = f'Bearer {token}'
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = response.read()
            status = response.status
            response_headers = dict(response.headers)
    except urllib.error.HTTPError as error:
        payload = error.read()
        status = error.code
        response_headers = dict(error.headers)
    if raw:
        return status, payload, response_headers
    try:
        parsed = json.loads(payload or b'null')
    except json.JSONDecodeError:
        parsed = payload.decode('utf-8', errors='replace')
    return status, parsed, response_headers


def show(label, status, payload, keys=None):
    if isinstance(payload, dict) and keys:
        payload = {key: payload.get(key) for key in keys}
    print(f'  {label:<46} -> {status} {json.dumps(payload, ensure_ascii=False, default=str)}')


def shell(code):
    """Ejecuta código dentro del shell de Django."""
    result = subprocess.run(
        [sys.executable, 'manage.py', 'shell', '-c', code],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
    )
    if result.returncode != 0:
        print('  SHELL ERROR:', result.stderr[-2000:])
    return result.stdout.strip()


def register(email):
    status, payload, _ = req(
        'POST',
        '/auth/register/',
        {'email': email, 'password': PASSWORD},
    )
    show(f'register {email}', status, payload, ['id', 'email', 'detail'])
    status, payload, _ = req('POST', '/auth/login/', {'email': email, 'password': PASSWORD})
    show(f'login {email}', status, payload, ['detail'])
    return payload.get('access')


def kyc_and_approve(email):
    status, payload, _ = req(
        'POST', '/kyc/', {'documents': {'dni': 'front', 'selfie': 'url'}}, token=TOKENS[email]
    )
    show(f'kyc request {email}', status, payload, ['id', 'status', 'detail'])


print('\n=== 1. Identidad ===')
TOKENS = {}
for email in (mail('ana'), mail('bruno'), mail('carla')):
    TOKENS[email] = register(email)

for email in list(TOKENS):
    kyc_and_approve(email)

print('\n=== 2. KYC aprobado por staff (accion del admin) ===')
print(
    '  ',
    shell(
        'from apps.identity.models import KYCVerification, User\n'
        'from apps.identity.services import resolve_kyc\n'
        "staff = User.objects.filter(is_staff=True).first()\n"
        'if staff is None:\n'
        f"    staff = User.objects.create_superuser(email='staff@presto.demo', password='{PASSWORD}')\n"
        'n = 0\n'
        'for v in KYCVerification.objects.filter(status="pending"):\n'
        '    resolve_kyc(verification_id=v.id, status="approved", resolved_by_user_id=staff.id)\n'
        '    n += 1\n'
        'print(f"aprobadas: {n}")'
    ),
)

print('\n=== 3. Ledger: depositos simulados ===')
for email, amount in (
    (mail('ana'), '200000.00'),
    (mail('bruno'), '20000.00'),
    (mail('carla'), '80000.00'),
):
    status, payload, _ = req(
        'POST',
        '/ledger/transactions/',
        {'type': 'deposit', 'currency': 'ARS', 'amount': amount, 'description': 'Deposito demo'},
        token=TOKENS[email],
        headers={'Idempotency-Key': f'demo-dep-{email}-{amount}'},
    )
    show(f'deposit {email} {amount}', status, payload, ['id', 'type', 'idempotency_key', 'detail'])

status, payload, _ = req('GET', '/ledger/accounts/', token=TOKENS[mail('ana')])
show('cuentas de ana', status, payload, ['count', 'detail'])
print('   cuentas:', json.dumps(payload.get('results', []), ensure_ascii=False))

print('\n=== 4. Ofertas ===')
status, payload, _ = req(
    'POST',
    '/offers/',
    {
        'amount': '50000.00',
        'currency': 'ARS',
        'interest_rate': '24.00',
        'term_months': 12,
        'requirements': 'Sin garantia, buen historial.',
    },
    token=TOKENS[mail('ana')],
)
show(
    'create offer (ana)',
    status,
    payload,
    ['id', 'amount', 'currency', 'interest_rate', 'term_months', 'status', 'detail'],
)
offer_id = payload.get('id')

status, payload, _ = req(
    'POST',
    '/offers/',
    {
        'amount': '80000.00',
        'currency': 'ARS',
        'interest_rate': '18.50',
        'term_months': 6,
        'requirements': 'Entrega en 48hs.',
    },
    token=TOKENS[mail('ana')],
)
show(
    'create offer 2 (ana)',
    status,
    payload,
    ['id', 'interest_rate', 'term_months', 'status', 'detail'],
)
offer2_id = payload.get('id')

status, payload, _ = req('GET', '/offers/', token=TOKENS[mail('ana')])
show('list offers (ana)', status, payload, ['count', 'detail'])

print('\n=== 5. Matching: busqueda y comparacion ===')
status, payload, _ = req(
    'GET',
    '/matching/offers/?currency=ARS&amount_min=40000&amount_max=100000&ordering=rate',
    token=TOKENS[mail('bruno')],
)
show('search offers', status, payload, ['count', 'detail'])
for offer in payload.get('results', []):
    print('   ', json.dumps(offer, ensure_ascii=False))

status, payload, _ = req(
    'POST',
    '/matching/comparisons/',
    {'offer_ids': [offer_id, offer2_id]},
    token=TOKENS[mail('bruno')],
)
show('compare offers', status, payload, ['detail'])
for comparison in payload if isinstance(payload, list) else payload.get('results', []):
    print('   ', json.dumps(comparison, ensure_ascii=False))

print('\n=== 6. Prestamo ===')
status, payload, _ = req(
    'POST',
    '/loans/',
    {'offer_id': offer_id},
    token=TOKENS[mail('bruno')],
    headers={'Idempotency-Key': f'demo-loan-{RUN}'},
)
show(
    'accept offer (bruno)',
    status,
    payload,
    ['id', 'principal', 'currency', 'interest_rate', 'term_months', 'status', 'detail'],
)
loan_id = payload.get('id')

status, payload, _ = req('GET', f'/loans/{loan_id}/', token=TOKENS[mail('bruno')])
show('loan detail', status, payload, ['detail'])
print('    installments:')
for installment in payload.get('installments', []):
    print('     ', json.dumps(installment, ensure_ascii=False))
print('    snapshot:', json.dumps(payload.get('terms_snapshot'), ensure_ascii=False))

status, payload, _ = req('GET', '/loans/', token=TOKENS[mail('bruno')])
show('loans de bruno', status, payload, ['count', 'detail'])

status, payload, _ = req('GET', f'/loans/{loan_id}/', token=TOKENS[mail('carla')])
show('loan detail (tercero)', status, payload, ['detail'])

print('\n=== 7. Pago de cuota ===')
status, payload, _ = req(
    'POST', f'/loans/{loan_id}/installments/1/pay/', token=TOKENS[mail('bruno')]
)
show('pay installment 1', status, payload, ['id', 'detail'])
status, payload, _ = req(
    'POST', f'/loans/{loan_id}/installments/2/pay/', token=TOKENS[mail('bruno')]
)
show('pay installment 2 (fuera de orden)', status, payload, ['detail'])
status, payload, _ = req('GET', f'/loans/{loan_id}/', token=TOKENS[mail('bruno')])
print('    cuotas:', [(i['number'], i['status']) for i in payload.get('installments', [])])

print('\n=== 8. Inversiones ===')
print(
    '  ',
    shell(
        'from apps.investments.models import InvestmentProduct\n'
        'p, _ = InvestmentProduct.objects.get_or_create(\n'
        '    type="fixed_term", currency="ARS", term_days=90, annual_rate_tna="18.00", min_amount="5000.00",\n'
        '    defaults={"status": "active"})\n'
        'print(p.id)'
    ),
)
status, payload, _ = req('GET', '/investments/products/', token=TOKENS[mail('carla')])
show('products', status, payload, ['count', 'detail'])
print('   ', json.dumps(payload.get('results', []), ensure_ascii=False))
product_id = payload['results'][0]['id']

status, payload, _ = req(
    'POST',
    '/investments/positions/',
    {'product_id': product_id, 'amount': '50000.00'},
    token=TOKENS[mail('carla')],
    headers={'Idempotency-Key': f'demo-position-{RUN}'},
)
show(
    'open position (carla)',
    status,
    payload,
    ['id', 'amount', 'status', 'interest_amount', 'maturity_date', 'detail'],
)
position_id = payload.get('id')
status, payload, _ = req(
    'GET', f'/investments/positions/{position_id}/', token=TOKENS[mail('carla')]
)
show('position detail', status, payload, ['detail'])
print('   ', json.dumps(payload.get('product_detail'), ensure_ascii=False))

print('\n=== 9. Presupuestos y gastos ===')
status, payload, _ = req(
    'POST', '/budgets/categories/', {'name': 'Alimentacion'}, token=TOKENS[mail('bruno')]
)
show('create category', status, payload, ['id', 'name', 'detail'])
category_id = payload.get('id')

status, payload, _ = req(
    'POST',
    '/budgets/',
    {
        'category_id': category_id,
        'limit_amount': '5000.00',
        'currency': 'ARS',
        'alert_threshold': 50,
    },
    token=TOKENS[mail('bruno')],
)
show(
    'create budget',
    status,
    payload,
    ['id', 'limit_amount', 'currency', 'alert_threshold', 'detail'],
)
budget_id = payload.get('id')

status, payload, _ = req(
    'POST',
    '/ledger/transactions/',
    {'type': 'withdrawal', 'currency': 'ARS', 'amount': '3000.00', 'description': 'Supermercado'},
    token=TOKENS[mail('bruno')],
    headers={'Idempotency-Key': f'demo-wd-{RUN}'},
)
show('withdrawal (gasto)', status, payload, ['id', 'type', 'detail'])
withdrawal_id = payload.get('id')

status, payload, _ = req(
    'POST',
    '/budgets/expenses/',
    {'category_id': category_id, 'ledger_transaction_id': withdrawal_id},
    token=TOKENS[mail('bruno')],
)
show('categorize expense', status, payload, ['id', 'ledger_transaction_id', 'detail'])

status, payload, _ = req('GET', f'/budgets/{budget_id}/status/', token=TOKENS[mail('bruno')])
show(
    'budget status',
    status,
    payload,
    [
        'limit_amount',
        'spent_amount',
        'remaining_amount',
        'threshold_amount',
        'alert_triggered',
        'detail',
    ],
)

status, payload, _ = req('GET', '/budgets/expenses/', token=TOKENS[mail('bruno')])
show('expenses', status, payload, ['count', 'detail'])

print('\n=== 10. Reportes ===')
for report in ('spending', 'loans', 'investments', 'movements'):
    status, payload, _ = req('GET', f'/reports/{report}/?currency=ARS', token=TOKENS[mail('bruno')])
    show(f'report {report}', status, payload, ['detail'])
    if report == 'spending' and isinstance(payload, dict) and payload.get('results'):
        print('   ', json.dumps(payload['results'], ensure_ascii=False)[:400])

status, payload, headers = req(
    'GET', '/reports/spending/?currency=ARS&export=csv', token=TOKENS[mail('bruno')], raw=True
)
print(
    f'  export csv spending -> {status} {headers.get("Content-Type")} {headers.get("Content-Disposition")}'
)
print('   ', payload.decode('utf-8', errors='replace')[:300].replace('\n', ' | '))

print('\n=== 11. Notificaciones ===')
status, payload, _ = req('GET', '/notifications/', token=TOKENS[mail('bruno')])
show('notifications', status, payload, ['count', 'detail'])
for notification in payload.get('results', []):
    print('   ', json.dumps(notification, ensure_ascii=False))
status, payload, _ = req('GET', '/notifications/preferences/', token=TOKENS[mail('bruno')])
show('preferences', status, payload, ['detail'])

print('\n=== 12. Aislamiento y errores ===')
status, payload, _ = req('GET', '/ledger/transactions/', token=None)
show('sin token', status, payload, ['detail'])
status, payload, _ = req(
    'POST',
    '/ledger/transactions/',
    {'type': 'deposit', 'currency': 'ARS', 'amount': '10.00'},
    token=TOKENS[mail('bruno')],
)
show('deposit sin Idempotency-Key', status, payload, ['detail'])
status, payload, _ = req(
    'POST',
    '/ledger/transactions/',
    {'type': 'deposit', 'currency': 'ARS', 'amount': '10.00'},
    token=TOKENS[mail('bruno')],
    headers={'Idempotency-Key': f'demo-dep-{RUN}-bruno-20000.00'},
)
show('misma key + mismo payload (idempotente)', status, payload, ['id', 'detail'])
status, payload, _ = req(
    'POST',
    '/ledger/transactions/',
    {'type': 'deposit', 'currency': 'ARS', 'amount': '99.00'},
    token=TOKENS[mail('bruno')],
    headers={'Idempotency-Key': f'demo-dep-{RUN}-bruno-20000.00'},
)
show('misma key + payload distinto (409)', status, payload, ['detail'])

print('\n=== 13. Invariante del ledger ===')
print(
    '  ',
    shell(
        'from apps.ledger.models import Account\n'
        'from django.db.models import Sum\n'
        'for currency in ("ARS", "USD"):\n'
        '    total = Account.objects.filter(currency=currency).aggregate(s=Sum("balance"))["s"] or 0\n'
        '    print(f"suma de saldos {currency}: {total}")'
    ),
)
print('\n=== 3b. Pagos (app payments) ===')
status, payload, _ = req(
    'POST',
    '/payments/',
    {
        'direction': 'deposit',
        'amount': '5000.00',
        'currency': 'ARS',
        'description': 'Deposito por la API de pagos',
    },
    token=TOKENS[mail('ana')],
    headers={'Idempotency-Key': f'demo-pay-dep-1-{RUN}'},
)
show(
    'payment deposit (ana)',
    status,
    payload,
    ['id', 'direction', 'amount', 'status', 'ledger_transaction_id', 'detail'],
)
payment_id = payload.get('id')

status, payload, _ = req(
    'POST',
    '/payments/',
    {
        'direction': 'deposit',
        'amount': '5000.00',
        'currency': 'ARS',
        'description': 'Deposito por la API de pagos',
    },
    token=TOKENS[mail('ana')],
    headers={'Idempotency-Key': f'demo-pay-dep-1-{RUN}'},
)
show('payment deposit repetido (idempotente)', status, payload, ['id', 'status', 'detail'])

status, payload, _ = req(
    'POST',
    '/payments/',
    {'direction': 'deposit', 'amount': '10.00', 'currency': 'ARS'},
    token=TOKENS[mail('ana')],
)
show('payment sin Idempotency-Key', status, payload, ['detail'])

status, payload, _ = req('GET', '/payments/', token=TOKENS[mail('ana')])
show('list payments (ana)', status, payload, ['count', 'detail'])
print('   ', json.dumps(payload.get('results', [])[:2], ensure_ascii=False))

if payment_id:
    status, payload, _ = req('GET', f'/payments/{payment_id}/', token=TOKENS[mail('ana')])
    show('payment detail', status, payload, ['id', 'status', 'detail'])

bruno_id = (
    shell(
        'from apps.identity.models import User\n'
        'print(User.objects.get(email="' + mail('bruno') + '").id)'
    )
    .splitlines()[-1]
    .strip()
)
status, payload, _ = req(
    'POST',
    '/payments/',
    {
        'direction': 'transfer',
        'amount': '1000.00',
        'currency': 'ARS',
        'destination_user_id': bruno_id,
    },
    token=TOKENS[mail('ana')],
    headers={'Idempotency-Key': f'demo-pay-tr-1-{RUN}'},
)
show('payment transfer (ana -> bruno)', status, payload, ['id', 'direction', 'status', 'detail'])

status, payload, _ = req(
    'POST',
    '/payments/',
    {'direction': 'transfer', 'amount': '1000.00', 'currency': 'ARS'},
    token=TOKENS[mail('ana')],
    headers={'Idempotency-Key': f'demo-pay-tr-2-{RUN}'},
)
show('payment transfer sin destino', status, payload, ['detail'])

status, payload, _ = req(
    'POST',
    '/payments/webhooks/simulated/',
    {'id': 'evt-demo-1', 'status': 'confirmed', 'action': 'payment.approved'},
)
show('webhook sin pago asociado', status, payload, ['status', 'payment_id', 'detail'])
print('\n=== FIN ===')
