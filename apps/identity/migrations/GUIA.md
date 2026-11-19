# Guía de código — apps/identity/migrations

Historial de esquema de la app. Las migraciones se generan con Django y no se editan a mano salvo una corrección puntual.

## Archivos

| Archivo | Qué hace |
|---|---|
| `0001_initial.py` | Tabla inicial de usuario. |
| `0002_alter_user_managers_remove_user_username.py` | Login por email y manager propio. |
| `0003_profile.py` | Perfil personal. |
| `0004_kycverification.py` | Solicitudes KYC. |
| `0005_user_email_verified_at.py` | Fecha de verificación de email. |
| `0006_prestoprofile.py` | Perfil operativo de Presto. |
| `0007_biometriccheck.py` | Validación biométrica simulada. |
| `0008_user_terms_accepted_at.py` | Aceptación de términos. |
| `0009_backupaccount.py` | Cuentas de respaldo. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
