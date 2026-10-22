import type { SVGProps } from "react";

type MascotProps = SVGProps<SVGSVGElement> & {
  /** Estado de ánimo: cambia la expresión y el brillo de la bola. */
  mood?: "idle" | "talking" | "happy";
};

/**
 * "Mago Presti" — mascota del asistente IA de Presto.
 * Un mago que te habla desde su bola de cristal. SVG propio, sin dependencias.
 */
export default function Mascot({
  mood = "idle",
  className,
  ...props
}: MascotProps) {
  const orbGlow = mood === "talking" ? 0.95 : mood === "happy" ? 0.8 : 0.55;
  const eyeOpen = mood === "happy";
  const smile = mood === "happy";

  return (
    <svg
      viewBox="0 0 200 220"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      role="img"
      aria-label="Presti, el asistente"
      {...props}
    >
      <defs>
        <radialGradient id="presti-orb" cx="38%" cy="32%" r="75%">
          <stop offset="0%" stopColor="#dbe9ff" />
          <stop offset="45%" stopColor="#8bb4ff" />
          <stop offset="100%" stopColor="#465fff" />
        </radialGradient>
        <radialGradient id="presti-glow" cx="50%" cy="55%" r="55%">
          <stop offset="0%" stopColor="#9db8ff" stopOpacity="0.9" />
          <stop offset="100%" stopColor="#465fff" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="presti-hat" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#5a3df0" />
          <stop offset="100%" stopColor="#3a24c9" />
        </linearGradient>
        <linearGradient id="presti-beard" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f4f6fb" />
          <stop offset="100%" stopColor="#c9d2e6" />
        </linearGradient>
      </defs>

      {/* brillo mágico detrás de la bola */}
      <circle
        cx="100"
        cy="140"
        r="80"
        fill="url(#presti-glow)"
        opacity={orbGlow}
      />
      <circle
        className="presti-twinkle presti-twinkle-1"
        cx="34"
        cy="70"
        r="2.4"
        fill="#8bb4ff"
      />
      <circle
        className="presti-twinkle presti-twinkle-2"
        cx="170"
        cy="96"
        r="2"
        fill="#b6c8ff"
      />
      <circle
        className="presti-twinkle presti-twinkle-3"
        cx="158"
        cy="40"
        r="1.6"
        fill="#8bb4ff"
      />

      {/* bola de cristal */}
      <circle cx="100" cy="140" r="62" fill="url(#presti-orb)" opacity="0.92" />
      <circle
        cx="100"
        cy="140"
        r="62"
        stroke="#c9d6ff"
        strokeWidth="1.5"
        opacity="0.6"
      />
      <ellipse cx="82" cy="112" rx="20" ry="13" fill="#ffffff" opacity="0.35" />

      {/* ojos dentro de la bola */}
      {eyeOpen ? (
        <>
          <path
            d="M76 132c5-6 13-6 18 0"
            stroke="#1e2a5a"
            strokeWidth="3.4"
            strokeLinecap="round"
          />
          <path
            d="M106 132c5-6 13-6 18 0"
            stroke="#1e2a5a"
            strokeWidth="3.4"
            strokeLinecap="round"
          />
        </>
      ) : (
        <>
          <ellipse cx="85" cy="132" rx="5.5" ry="6.5" fill="#1e2a5a" />
          <ellipse cx="115" cy="132" rx="5.5" ry="6.5" fill="#1e2a5a" />
          <circle cx="87" cy="130" r="1.8" fill="#ffffff" />
          <circle cx="117" cy="130" r="1.8" fill="#ffffff" />
        </>
      )}

      {/* boca */}
      {smile ? (
        <path
          d="M88 156c6 8 18 8 24 0"
          stroke="#1e2a5a"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      ) : (
        <path
          d="M91 158c4 3 14 3 18 0"
          stroke="#1e2a5a"
          strokeWidth="3"
          strokeLinecap="round"
          fill="none"
        />
      )}

      {/* base de la bola */}
      <ellipse cx="100" cy="204" rx="46" ry="10" fill="#2c2f6b" />
      <path d="M68 200c0-10 14-18 32-18s32 8 32 18z" fill="#3a24c9" />

      {/* barba */}
      <path
        d="M74 118c0 24 10 42 26 42s26-18 26-42c-8 6-18 9-26 9s-18-3-26-9z"
        fill="url(#presti-beard)"
        opacity="0.95"
      />
      <path d="M100 160c-4 6-4 10 0 14 4-4 4-8 0-14z" fill="#c9d2e6" />

      {/* sombrero de mago */}
      <path
        d="M100 24c14 0 26 10 29 24h-58c3-14 15-24 29-24z"
        fill="url(#presti-hat)"
      />
      <path
        d="M58 52h84c4 0 7 3 7 7v4c0 4-3 7-7 7H58c-4 0-7-3-7-7v-4c0-4 3-7 7-7z"
        fill="#465fff"
      />
      <circle cx="100" cy="66" r="6" fill="#ffd66b" />
      <path d="M100 24l9-14 5 16" fill="#ffd66b" opacity="0.9" />
    </svg>
  );
}
