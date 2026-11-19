# Guía de código — deploy

Piezas de despliegue y operación.

## Archivos

| Archivo | Qué hace |
|---|---|
| `entrypoint.sh` | Aplica migraciones con reintentos si `RUN_MIGRATIONS=1` y arranca Gunicorn. |
| `Caddyfile` | Proxy inverso con TLS automático para el perfil `proxy`. |
| `backup-postgres.sh` | Backup diario de PostgreSQL y notas de restauración. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
