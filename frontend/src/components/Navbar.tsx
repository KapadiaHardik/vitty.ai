"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Sparkles, MessageSquare, CheckSquare } from "lucide-react";

export default function Navbar() {
  const pathname = usePathname();

  const navItems = [
    {
      name: "Documents & Chat",
      href: "/documents",
      icon: MessageSquare,
      active: pathname === "/documents",
    },
    {
      name: "Invoice Verification",
      href: "/workflows",
      icon: CheckSquare,
      active: pathname.startsWith("/workflows"),
    },
  ];

  return (
    <header className="sticky top-0 z-50 w-full backdrop-blur-xl bg-white/80 border-b border-slate-200/80 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-primary-600 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-primary-500/20 group-hover:scale-105 transition-transform">
            <Sparkles className="w-5 h-5" />
          </div>
          <span className="font-extrabold text-xl tracking-tight text-slate-900 group-hover:text-primary-600 transition-colors">
            Vitty<span className="text-primary-600">.ai</span>
          </span>
          <span className="ml-1.5 hidden sm:inline-block px-2 py-0.5 rounded-full text-[11px] font-semibold bg-primary-50 text-primary-700 border border-primary-200">
            Phase 2
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="flex items-center gap-2 sm:gap-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-sm font-semibold transition-all ${
                  item.active
                    ? "bg-primary-50 text-primary-700 border border-primary-200 shadow-xs"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-100/80"
                }`}
              >
                <Icon className={`w-4 h-4 ${item.active ? "text-primary-600" : "text-slate-500"}`} />
                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
