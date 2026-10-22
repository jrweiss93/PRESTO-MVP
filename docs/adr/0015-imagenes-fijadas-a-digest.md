# ADR 0015 — Las imágenes de producción se fijan a digest

- **Estado:** aceptado (decisión técnica tomada el 2026-10-22)
- **Fecha:** 2026-10-22
- **Ámbito:** despliegue (`docker-compose.yml`, `docker-compose.prod.yml`)
- **Resuelve:** D-9 — fijar `postgres`, `redis` y `caddy` a un digest o a un parche exacto

## Contexto

D-9 (de `docs/audit-final.md` §5) tenía que definir si las imágenes se fijan
a un **digest** o a un **parche exacto**. La auditoría recomienda el digest:

> "Fijar a digest: el tag mayor deja entrar parches de seguridad sin control."

Estado actual: `docker-compose.yml` y `docker-compose.prod.yml` usan tags
móviles (`postgres:16`, `redis:7-alpine`, `caddy:2-alpine`).

## Decisión

1. **Las tres imágenes de producción se fijan a digest**: la forma exacta
   (`postgres:16.15@sha256:...`) deja ver de qué versión se trata **y**
   garantiza que el contenido no cambia.
2. **El digest se resuelve contra el registro real** (Docker Hub) y se anota en
   el compose con un comentario que dice de qué versión es. Si el digest no
   está disponible para la plataforma, se cae al **parche exacto** de versión
   (`postgres:16.15`), nunca a un tag mayor.
3. **El `build` del backend se sigue construyendo localmente** (`build: .`): el
   código es del repo y el digest no aplica.
4. **Los digest se actualizan a mano**, en un commit propio, con el motivo en
   el mensaje. Actualizar un digest **no** es un cambio de código: es un
   cambio de despliegue.
5. **En desarrollo** (`docker-compose.yml`) se puede dejar el tag móvil para no
   depender de la red: la decisión de integridad aplica a **producción**.

## Digest fijados (2026-10-22)

Resueltos contra Docker Hub (manifest list) el 2026-10-22:

| Imagen | Versión | Digest |
| --- | --- | --- |
| `postgres` | 16.15 | `sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97` |
| `redis` | 7.4.11-alpine | `sha256:892022f9f18c26c92c30e15194d132f90044af87b94a491a75429bbc3982eab1` |
| `caddy` | 2.11.7-alpine | `sha256:24ec7b05bc532c7bb57f727030c5056e257ff7138b4b50460306819ff79362bd` |

## Consecuencias

**Positivas**

- La imagen que corre en producción es exactamente la que se probó.
- Un tag movido no puede cambiar de contenido entre un deploy y otro.

**Negativas / riesgos asumidos**

- Hay que actualizar los digest periódicamente (parches de seguridad).
- Si un digest no está disponible para la arquitectura, el deploy falla con un
  error poco claro: por eso va con la versión explícita en el tag.
- `docker compose pull` necesita red contra Docker Hub.

**Pendiente**

- Automatizar la actualización de digest (dependabot para Docker) cuando el
  repo tenga git.
- Fijar también la imagen base del `Dockerfile` (`python:3.12-slim`): es la
  cuarta imagen del despliegue y hoy sigue con tag móvil.
