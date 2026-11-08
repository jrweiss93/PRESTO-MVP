import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/features/auth/AuthContext";
import { cn } from "@/shared/lib";
import { PROFILE_KINDS, PROFILE_LABELS } from "@/shared/lib/profiles";
import type { ProfileKind } from "@/shared/api/types";
import { CheckCircleIcon, ChevronDownIcon } from "@/shared/ui/icons";

/**
 * Selector del perfil activo de Presto. El usuario alterna entre prestatario,
 * prestamista e inversor; el menú y los permisos siguen al perfil elegido.
 */
export default function ProfileSwitcher() {
  const { activeProfile, switchProfile } = useAuth();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function select(kind: ProfileKind) {
    setOpen(false);
    await switchProfile(kind);
  }

  const label = activeProfile ? PROFILE_LABELS[activeProfile] : "Elegí tu perfil";

  return (
    <div className="relative hidden sm:block" ref={ref}>
      <button
        onClick={() => setOpen((prev) => !prev)}
        className="flex items-center gap-1.5 rounded-full border border-gray-200 bg-gray-50 px-3 py-1.5 text-theme-sm font-medium text-gray-700 hover:bg-gray-100"
      >
        <span className="max-w-32 truncate">{label}</span>
        <ChevronDownIcon
          className={cn(
            "size-4 stroke-gray-500 transition-transform duration-200",
            open ? "rotate-180" : "",
          )}
        />
      </button>

      {open && (
        <div className="absolute end-0 mt-2 w-52 rounded-2xl border border-gray-200 bg-white p-2 shadow-theme-lg">
          <p className="px-3 pb-2 pt-1 text-theme-xs text-gray-500">
            Perfil con el que operás
          </p>
          <ul className="flex flex-col gap-1">
            {PROFILE_KINDS.map((kind) => {
              const isActive = kind === activeProfile;
              return (
                <li key={kind}>
                  <button
                    onClick={() => select(kind)}
                    disabled={isActive}
                    className={cn(
                      "flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-theme-sm font-medium",
                      isActive
                        ? "cursor-default bg-brand-50 text-brand-700"
                        : "text-gray-700 hover:bg-gray-100",
                    )}
                  >
                    <span>{PROFILE_LABELS[kind]}</span>
                    {isActive && (
                      <CheckCircleIcon className="size-4 fill-brand-500" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
