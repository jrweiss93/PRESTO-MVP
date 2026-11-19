# Guía de código — frontend/src/app

Composición de la SPA: entrada, rutas, layout y providers globales.

## Archivos

| Archivo | Qué hace |
|---|---|
| `main.tsx` | Monta React con `ThemeProvider`, `BrowserRouter` y `AuthProvider`. |
| `App.tsx` | Rutas públicas/privadas y guardas `Protected`/`ProfileOnly`. |
| `layout/AppLayout.tsx` | Shell con sidebar, header, banners y `Outlet`. |
| `layout/AppHeader.tsx` | Menú mobile, notificaciones, tema y menú de usuario. |
| `layout/AppSidebar.tsx` | Navegación por perfil, marca y tarjeta de Presti. |
| `layout/Backdrop.tsx` | Fondo del menú mobile. |
| `layout/NotificationsBell.tsx` | Polling de avisos sin leer y badge. |
| `layout/DemoModeBanner.tsx` | Aviso de dinero simulado según `/meta/`. |
| `layout/ComplianceBanner.tsx` | Aviso interno de revisión legal. |
| `providers/ThemeContext.tsx` | Tema claro/oscuro, persistencia y `prefers-color-scheme`. |
| `providers/SidebarContext.tsx` | Estado del sidebar desktop/mobile. |

## Subcarpetas

| Carpeta | Contenido |
|---|---|
| `layout/` | Header, sidebar, banners y campana. |
| `providers/` | Contextos globales de tema y sidebar. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
