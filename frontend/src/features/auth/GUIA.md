# Guía de código — frontend/src/features/auth

Sesión, login, registro con identidad simulada, recuperación, verificación y perfil/KYC.

## Archivos

| Archivo | Qué hace |
|---|---|
| `AuthContext.tsx` | Usuario, login/registro/logout, refresh, perfil activo y tipos de identidad simulada. |
| `components/AuthShell.tsx` | Layout compartido de auth con toggle de tema. |
| `pages/Login.tsx` | Formulario de login. |
| `pages/Register.tsx` | Alta en dos pasos y simulación de DNI/credencial/rostro. |
| `pages/ForgotPassword.tsx` | Solicitud de reseteo. |
| `pages/ResetPassword.tsx` | Nueva contraseña desde token. |
| `pages/VerifyEmail.tsx` | Confirmación de email. |
| `pages/Profile.tsx` | Perfil, KYC, biometría, respaldo, seguridad y reputación. |

---

Mapa general del repositorio: `docs/mapa-repositorio.md`.
