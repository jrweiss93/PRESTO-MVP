# Guía de código — apps/core/tests

Pruebas automáticas de la app. Cada archivo cubre una garantía distinta; la suite completa corre contra PostgreSQL real.

## Archivos

| Archivo | Qué hace |
|---|---|
| `test_money.py` | Redondeo, cuota francesa, interés simple, TEA y costos. |
| `test_health.py` | Endpoint de salud. |
| `test_meta.py` | Metadata pública. |
| `test_exception_handler.py` | Formato uniforme de errores. |
| `test_openapi.py` | Contrato OpenAPI. |
| `test_cors.py` | CORS y credenciales. |
| `test_security_settings.py` | Cookies, HSTS y settings. |
| `test_demo_mode.py` | Modo demo y cabecera. |
| `test_compliance_checks.py` | Revisión legal pendiente. |
| `test_readme.py` | README sincronizado con endpoints/apps. |
| `test_docs.py` | Documentación sincronizada. |
| `test_celery.py` | Tareas y scheduler. |
| `test_email_backend.py` | Backend de email. |
| `test_deployment.py` | Configuración de despliegue. |
| `test_models.py` | Modelo base. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
