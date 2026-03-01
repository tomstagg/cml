"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  BookOpen,
  LogOut,
  Scale,
  Settings,
  Star,
  User,
} from "lucide-react";
import { cn, clearStoredToken } from "@/lib/utils";
import { useRouter } from "next/navigation";

const navItems = [
  { href: "/firm/dashboard", label: "Dashboard", icon: BarChart2 },
  { href: "/firm/profile", label: "Profile", icon: User },
  { href: "/firm/pricing", label: "Pricing", icon: BookOpen },
  { href: "/firm/reviews", label: "Reviews", icon: Star },
  { href: "/firm/appointments", label: "Appointments", icon: Settings },
];

export function FirmLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // Auth check pages (login, enroll) — no sidebar
  const isAuthPage = pathname.startsWith("/firm/login") || pathname.startsWith("/firm/enroll");
  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex items-center justify-center p-4 h-16 bg-white border-b border-gray-200">
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <Scale className="w-6 h-6 text-brand-600" />
            <span>Choose My <span className="text-brand-600">Lawyer</span></span>
          </Link>
        </div>
        <main>{children}</main>
      </div>
    );
  }

  function handleLogout() {
    clearStoredToken();
    router.push("/firm/login");
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Link href="/firm/dashboard" className="flex items-center gap-2 font-bold text-gray-900">
            <Scale className="w-5 h-5 text-brand-600" />
            <span className="text-sm">CML Firm Portal</span>
          </Link>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          {navItems.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-gray-200">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-500 hover:bg-gray-50 hover:text-gray-900 w-full transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Log Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
