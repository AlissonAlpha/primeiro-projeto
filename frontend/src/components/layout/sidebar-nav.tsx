"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Megaphone,
  Camera,
  Brain,
  TrendingUp,
  FileText,
  Settings,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

const navItems = [
  {
    label: "Dashboard",
    href: "/",
    icon: LayoutDashboard,
  },
  {
    label: "Agentes IA",
    items: [
      { label: "CEO Estrategista", href: "/agents/ceo", icon: Brain },
      { label: "Gestor de Tráfego", href: "/agents/traffic-manager", icon: Megaphone },
      { label: "Social Media", href: "/agents/social-media", icon: Camera },
    ],
  },
  {
    label: "Resultados",
    items: [
      { label: "Campanhas", href: "/campaigns", icon: TrendingUp },
      { label: "Postagens", href: "/posts", icon: FileText },
    ],
  },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 h-full w-64 flex flex-col z-40"
      style={{ background: "linear-gradient(180deg, #0d0d1a 0%, #111120 100%)" }}>

      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-white/10">
        <div className="w-9 h-9 rounded-xl bg-violet-600 flex items-center justify-center shadow-lg shadow-violet-900/50">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <p className="text-white font-bold text-sm leading-tight">Agência do</p>
          <p className="text-violet-400 font-bold text-sm leading-tight">Futuro IA</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
        {navItems.map((section) => (
          <div key={section.label}>
            {"items" in section ? (
              <>
                <p className="px-3 mb-1 text-xs font-semibold text-white/30 uppercase tracking-widest">
                  {section.label}
                </p>
                <div className="space-y-0.5">
                  {section.items?.map((item) => (
                    <NavItem key={item.href} item={item} pathname={pathname} />
                  ))}
                </div>
              </>
            ) : (
              <NavItem item={section as NavItemType} pathname={pathname} />
            )}
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="px-3 pb-4 border-t border-white/10 pt-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-white/50 hover:text-white hover:bg-white/5 transition-all text-sm"
        >
          <Settings className="w-4 h-4" />
          Configurações
        </Link>
      </div>
    </aside>
  );
}

type NavItemType = {
  label: string;
  href: string;
  icon: React.ElementType;
};

function NavItem({ item, pathname }: { item: NavItemType; pathname: string }) {
  const isActive = pathname === item.href;
  const Icon = item.icon;

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all",
        isActive
          ? "bg-violet-600/20 text-violet-300 border border-violet-500/30"
          : "text-white/60 hover:text-white hover:bg-white/5"
      )}
    >
      <Icon className={cn("w-4 h-4", isActive ? "text-violet-400" : "")} />
      {item.label}
      {isActive && (
        <span className="ml-auto w-1.5 h-1.5 rounded-full bg-violet-400" />
      )}
    </Link>
  );
}
