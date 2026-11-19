# Guía de código — apps/demo

Datos de demostración y comandos de siembra. No tiene modelos propios.

## Archivos

| Archivo | Qué hace |
|---|---|
| `__init__.py` | Marca el directorio como paquete Python. No contiene lógica de negocio. |
| `apps.py` | Configuración de la app para Django (`AppConfig`): nombre y etiqueta. |
| `receivers.py` | Escucha KYC aprobado y dispara el bono de bienvenida. |
| `seeds.py` | `seed_demo` idempotente: usuarios, KYC, depósitos, oferta, préstamo, inversión y pagos. |
| `welcome.py` | `grant_welcome_bonus`: acredita dinero simulado al prestatario una sola vez. |
| `management/commands/seed_demo.py` | Comando que ejecuta el escenario de demo. |
| `management/commands/create_demo_superuser.py` | Crea/actualiza el superusuario desde variables de entorno. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `tests/` | Seed, bono de bienvenida y creación del superusuario. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
