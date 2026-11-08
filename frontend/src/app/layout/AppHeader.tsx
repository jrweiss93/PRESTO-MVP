import { useSidebar } from "@/app/providers/SidebarContext";
import { useAuth } from "@/features/auth/AuthContext";
import { cn } from "@/shared/lib";
import { useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CloseIcon,
  LogoutIcon,
  MenuIcon,
  UserCircleIcon,
} from "@/shared/ui/icons";

export default function AppHeader() {
  const { isMobileOpen, toggleSidebar, toggleMobileSidebar } = useSidebar();
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isDropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const handleToggle = () => {
    if (window.innerWidth >= 1280) {
      toggleSidebar();
    } else {
      toggleMobileSidebar();
    }
  };

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setDropdownOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  const initials = (user?.first_name || user?.email || "?")
    .slice(0, 1)
    .toUpperCase();

  return (
    <header className="sticky top-0 z-99999 flex w-full border-gray-200 bg-white xl:border-b">
      <div className="flex grow flex-col items-center justify-between xl:flex-row xl:px-6">
        <div className="flex w-full items-center justify-between gap-2 border-b border-gray-200 px-3 py-3 sm:gap-4 xl:justify-normal xl:border-b-0 xl:px-0 xl:py-4">
          <button
            className={cn(
              "z-99999 flex h-10 w-10 items-center justify-center rounded-lg border-gray-200 text-gray-500 lg:h-11 lg:w-11 lg:bg-transparent xl:border",
              isMobileOpen ? "bg-gray-100" : "",
            )}
            onClick={handleToggle}
            aria-label="Alternar barra lateral"
          >
            {isMobileOpen ? (
              <CloseIcon className="text-gray-500" />
            ) : (
              <MenuIcon />
            )}
          </button>

          <Link
            to="/dashboard"
            className="text-title-sm font-semibold text-gray-800 xl:hidden"
          >
            Presto<span className="text-brand-500">.</span>
          </Link>

          <div className="hidden xl:block" />

          <div className="relative" ref={dropdownRef}>
            <button
              onClick={() => setDropdownOpen((prev) => !prev)}
              className="dropdown-toggle flex items-center text-gray-700"
            >
              <span className="me-3 flex h-11 w-11 items-center justify-center overflow-hidden rounded-full bg-brand-50 text-brand-500">
                <span className="text-theme-sm font-semibold">{initials}</span>
              </span>
              <span className="me-1 hidden block text-theme-sm font-medium sm:block">
                {user?.first_name || user?.email}
              </span>
              <svg
                className={cn(
                  "stroke-gray-500 transition-transform duration-200",
                  isDropdownOpen ? "rotate-180" : "",
                )}
                width="18"
                height="20"
                viewBox="0 0 18 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4.3125 8.65625L9 13.3437L13.6875 8.65625"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </button>

            {isDropdownOpen && (
              <div className="absolute inset-e-0 mt-4.25 flex w-65 flex-col rounded-2xl border border-gray-200 bg-white p-3 shadow-theme-lg">
                <div>
                  <span className="block text-theme-sm font-medium text-gray-700">
                    {user?.first_name || user?.email}
                  </span>
                  <span className="mt-0.5 block text-theme-xs text-gray-500">
                    {user?.email}
                  </span>
                </div>

                <ul className="mt-4 flex flex-col gap-1 border-b border-gray-200 pb-3">
                  <li>
                    <Link
                      to="/perfil"
                      onClick={() => setDropdownOpen(false)}
                      className="group flex items-center gap-3 rounded-lg px-3 py-2 text-theme-sm font-medium text-gray-700 hover:bg-gray-100"
                    >
                      <UserCircleIcon className="fill-gray-500 group-hover:fill-gray-700" />
                      Mi perfil
                    </Link>
                  </li>
                </ul>

                <ul className="flex flex-col gap-1 pt-3">
                  <li>
                    <button
                      onClick={handleLogout}
                      className="group flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-theme-sm font-medium text-error-500 hover:bg-error-50"
                    >
                      <LogoutIcon className="stroke-error-500" />
                      Cerrar sesión
                    </button>
                  </li>
                </ul>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
