# Guía de código — apps/identity

Usuarios, login JWT, perfiles de Presto, KYC, biometría simulada, cuentas de respaldo y cierre de cuenta.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `admin.py` | Admin de usuarios, perfiles, KYC, biometría y cuentas de respaldo. |
| `emails.py` | Armado y envío de emails de reseteo y verificación con enlaces al front. |
| `exceptions.py` | Errores de identidad, KYC, perfiles, tokens, respaldo y cierre. |
| `models.py` | `UserManager`, `User`, `Profile`, `PrestoProfile`, `KYCVerification`, `BiometricCheck`, `BackupAccount`. |
| `permissions.py` | Throttles de login/registro/reset y permisos de KYC, perfil activo y respaldo. |
| `selectors.py` | Lecturas de perfil, KYC, biométricos, respaldo y operaciones activas; aíslan por usuario. |
| `serializers.py` | Registro (con simulación de DNI/credencial/rostro), login, perfil, KYC, backup y tokens. |
| `services.py` | Escritura de registro, perfil, KYC, biometría, reseteo, verificación, backup, cierre y contraseña. |
| `signals.py` | Señal `kyc_approved`; `demo` la usa para el bono de bienvenida. |
| `tokens.py` | Tokens de un solo uso para verificación de email, sin `last_login` en el hash. |
| `urls.py` | Rutas `/auth/...`, `/kyc/...`, `/backup-accounts/...` y cierre de cuenta. |
| `views.py` | Vistas de registro, login, refresh, logout, perfil, KYC, biometría, reset, backup y cierre. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Registro con identidad simulada, auth, KYC, perfiles, backup, biometría, emails, reset y admin. |
| `migrations/` | Historial de usuarios, perfiles, KYC, biometría, términos y cuentas de respaldo. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
