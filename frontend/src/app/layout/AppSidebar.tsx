import { useSidebar } from "@/app/providers/SidebarContext";
import { cn } from "@/shared/lib";
import { ENABLE_ASSISTANT } from "@/shared/lib/features";
import { NavLink } from "react-router-dom";
import {
  CartIcon,
  CheckCircleIcon,
  DollarLineIcon,
  FileIcon,
  GridIcon,
  HorizontalDotsIcon,
  PieChartIcon,
  SendIcon,
  SparkIcon,
  UserCircleIcon,
  UserMoneyIcon,
} from "@/shared/ui/icons";

type NavItem = {
  name: string;
  icon: (active: boolean) => React.ReactNode;
  path: string;
};

const navItems: NavItem[] = [
  {
    name: "Dashboard",
    icon: (a) => (
      <GridIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/dashboard",
  },
  {
    name: "Billetera",
    icon: (a) => (
      <DollarLineIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/billetera",
  },
  {
    name: "Pagos",
    icon: (a) => (
      <SendIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/pagos",
  },
  {
    name: "Presupuestos",
    icon: (a) => (
      <CheckCircleIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/presupuestos",
  },
  {
    name: "Marketplace",
    icon: (a) => (
      <CartIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/marketplace",
  },
  {
    name: "Mis ofertas",
    icon: (a) => (
      <FileIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/ofertas",
  },
  {
    name: "Préstamos",
    icon: (a) => (
      <UserMoneyIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/prestamos",
  },
  {
    name: "Inversiones",
    icon: (a) => (
      <PieChartIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/inversiones",
  },
  {
    name: "Presti",
    icon: (a) => (
      <SparkIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/asistente",
  },
  {
    name: "Perfil y KYC",
    icon: (a) => (
      <UserCircleIcon
        className={
          a ? "text-brand-500" : "text-gray-500 group-hover:text-gray-700"
        }
      />
    ),
    path: "/perfil",
  },
];

// El asistente solo existe contra el mock: se oculta si el backend es real.
const visibleNavItems: NavItem[] = ENABLE_ASSISTANT
  ? navItems
  : navItems.filter((nav) => nav.path !== "/asistente");

const AppSidebar: React.FC = () => {
  const { isExpanded, isMobileOpen, isHovered, setIsHovered } = useSidebar();

  const showLabels = isExpanded || isHovered || isMobileOpen;

  return (
    <aside
      className={cn(
        "fixed inset-s-0 top-0 z-50 flex h-screen flex-col border-e border-gray-200 bg-white px-5 text-gray-900 transition-all duration-300 ease-in-out xl:translate-x-0",
        isExpanded || isMobileOpen ? "w-72.5" : isHovered ? "w-72.5" : "w-22.5",
        isMobileOpen ? "translate-x-0" : "-translate-x-full",
      )}
      onMouseEnter={() => !isExpanded && setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <div
        className={cn(
          "flex py-8",
          showLabels ? "justify-start" : "xl:justify-center",
        )}
      >
        <NavLink to="/dashboard" className="flex items-center gap-2">
          {showLabels ? (
            <span className="text-title-sm font-semibold text-gray-800">
              Presto<span className="text-brand-500">.</span>
            </span>
          ) : (
            <span className="flex size-8 items-center justify-center rounded-lg bg-brand-500 text-lg font-semibold text-white">
              P
            </span>
          )}
        </NavLink>
      </div>

      <div className="no-scrollbar flex flex-col overflow-y-auto duration-300 ease-linear">
        <nav className="mb-6">
          <div>
            <h2
              className={cn(
                "mb-4 flex text-xs leading-5 text-gray-400 uppercase",
                showLabels ? "justify-start" : "xl:justify-center",
              )}
            >
              {showLabels ? "Menú" : <HorizontalDotsIcon className="size-6" />}
            </h2>
            <ul className="flex flex-col gap-1">
              {visibleNavItems.map((nav) => (
                <li key={nav.path}>
                  <NavLink
                    to={nav.path}
                    className={({ isActive }) =>
                      cn(
                        "group menu-item",
                        isActive ? "menu-item-active" : "menu-item-inactive",
                        showLabels ? "xl:justify-start" : "xl:justify-center",
                      )
                    }
                  >
                    {({ isActive }) => (
                      <>
                        {nav.icon(isActive)}
                        {showLabels && (
                          <span className="menu-item-text">{nav.name}</span>
                        )}
                      </>
                    )}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        </nav>
      </div>
    </aside>
  );
};

export default AppSidebar;
