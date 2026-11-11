import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as api from "@/shared/api/endpoints";
import { BellIcon } from "@/shared/ui/icons";

/**
 * Campana de notificaciones: muestra cuántos avisos sin leer tiene el usuario
 * y lleva a la pantalla de notificaciones.
 */
export default function NotificationsBell() {
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    let active = true;
    const refresh = () => {
      api
        .getUnreadCount()
        .then((count) => {
          if (active) setUnread(count);
        })
        .catch(() => {
          // sin red el badge simplemente no se muestra
        });
    };
    refresh();
    const interval = window.setInterval(refresh, 20000);
    const onFocus = () => refresh();
    const onVisibility = () => {
      if (document.visibilityState === "visible") refresh();
    };
    window.addEventListener("focus", onFocus);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      active = false;
      window.clearInterval(interval);
      window.removeEventListener("focus", onFocus);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return (
    <Link
      to="/notificaciones"
      aria-label="Notificaciones"
      className="relative flex h-10 w-10 items-center justify-center rounded-lg border border-gray-200 text-gray-500 hover:bg-gray-50 hover:text-gray-700"
    >
      <BellIcon className="size-5" />
      {unread > 0 && (
        <span className="absolute -end-1 -top-1 flex h-5 min-w-5 items-center justify-center rounded-full bg-error-500 px-1 text-theme-xs font-semibold text-white">
          {unread > 99 ? "99+" : unread}
        </span>
      )}
    </Link>
  );
}
