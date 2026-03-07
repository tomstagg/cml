"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  BookOpen,
  LogOut,
  Settings,
  Star,
  User,
} from "lucide-react";
import { cn, clearStoredToken } from "@/lib/utils";
import { useRouter } from "next/navigation";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: BarChart2 },
  { href: "/profile", label: "Profile", icon: User },
  { href: "/pricing", label: "Pricing", icon: BookOpen },
  { href: "/reviews", label: "Reviews", icon: Star },
  { href: "/appointments", label: "Appointments", icon: Settings },
];

export function FirmLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  // Auth check pages (login, enroll) — no sidebar
  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/enroll");
  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="flex items-center justify-center p-4 h-16 bg-white border-b border-gray-200">
          <Link href="/">
            <Image
              src="/logo.png"
              alt="Choose My Lawyer"
              width={160}
              height={68}
              className="h-8 w-auto"
            />
          </Link>
        </div>
        <main>{children}</main>
      </div>
    );
  }

  function handleLogout() {
    clearStoredToken();
    router.push("/login");
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-brand-950 flex flex-col">
        <div className="p-4 border-b border-brand-900">
          <Link href="/dashboard" className="flex items-center">
            <Image
              src="/logo-dark.png"
              alt="Choose My Lawyer"
              width={140}
              height={49}
              className="h-7 w-auto"
            />
          </Link>
          <p className="text-brand-300 text-xs mt-2 font-medium">Firm Portal</p>
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
                    ? "bg-brand-800 text-white"
                    : "text-brand-200 hover:bg-brand-900 hover:text-white",
                )}
              >
                <item.icon className="w-4 h-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="p-4 border-t border-brand-900">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-brand-300 hover:bg-brand-900 hover:text-white w-full transition-colors"
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
