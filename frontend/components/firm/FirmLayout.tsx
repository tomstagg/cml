"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { firmProfileApi } from "@/lib/api";
import { cn, clearStoredToken, getStoredToken } from "@/lib/utils";

const navItems = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/profile", label: "Firm Details" },
  { href: "/pricing", label: "Fees & Service Offering" },
  { href: "/reviews", label: "Reviews" },
];

export function FirmLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [firmName, setFirmName] = useState<string | null>(null);

  const isAuthPage = pathname.startsWith("/login") || pathname.startsWith("/enroll");

  useEffect(() => {
    if (isAuthPage) return;
    const token = getStoredToken();
    if (!token) return;
    firmProfileApi
      .get(token)
      .then((data) => setFirmName((data as { name: string }).name))
      .catch(() => {});
  }, [isAuthPage]);

  if (isAuthPage) {
    return (
      <div className="min-h-screen bg-white">
        <div className="flex items-center justify-center h-20 border-b border-gray-100">
          <Link href="/">
            <Image
              src="/logo.png"
              alt="Choose My Lawyer"
              width={160}
              height={68}
              className="h-10 w-auto"
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
    <div className="min-h-screen bg-white">
      <header className="border-b border-gray-100">
        <div className="section-container flex items-center h-20">
          <Link href="/dashboard" className="flex items-center">
            <Image
              src="/logo.png"
              alt="Choose My Lawyer"
              width={160}
              height={68}
              className="h-10 w-auto"
              priority
            />
          </Link>
        </div>
      </header>

      <div className="section-container py-10">
        <div className="grid grid-cols-1 md:grid-cols-[240px_1fr] gap-10">
          <aside className="md:border-r md:border-gray-100 md:pr-8">
            {firmName && (
              <h2 className="text-navy font-bold text-lg leading-snug mb-6">{firmName}</h2>
            )}
            <nav className="flex flex-col gap-3 text-sm">
              {navItems.map((item) => {
                const active = pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "transition-colors",
                      active ? "text-navy font-semibold" : "text-navy/70 hover:text-navy",
                    )}
                  >
                    {item.label}
                  </Link>
                );
              })}
              <button
                onClick={handleLogout}
                className="text-left text-navy/70 hover:text-navy transition-colors"
              >
                Logout
              </button>
            </nav>
          </aside>
          <main className="min-w-0">{children}</main>
        </div>
      </div>
    </div>
  );
}
