# Guía de código — apps/identity/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_api.py` | Registro, login, refresh, perfil, KYC y backup. |
| `test_services.py` | Registro, reseteo, verificación, cierre y contraseña. |
| `test_models.py` | Usuarios, perfiles y constraints. |
| `test_selectors.py` | Consultas y aislamiento. |
| `test_profiles.py` | Perfiles fijos y activación. |
| `test_permissions.py` | KYC, perfil y respaldo. |
| `test_backup_accounts.py` | Cuentas de respaldo y guardas. |
| `test_biometric.py` | Biometría simulada. |
| `test_email_verification.py` | Verificación de email. |
| `test_password_reset.py` | Reseteo de contraseña. |
| `test_admin.py` | Admin. |
| `test_registration_identity.py` | DNI, credencial y rostro simulados en el alta. |
| `factories.py` | Fábricas de identidad. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
