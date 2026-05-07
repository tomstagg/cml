"use client";

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { Menu, X } from "lucide-react";

const navLinks = [
  { href: "/how-it-works", label: "How it works" },
  { href: "/how-it-works#faqs", label: "FAQs" },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-gray-100">
      <div className="section-container">
        <div className="flex items-center justify-between h-20">
          <Link href="/" className="flex items-center" aria-label="Choose My Lawyer home">
            <Image
              src="/logo.png"
              alt="Choose My Lawyer"
              width={180}
              height={64}
              className="h-12 w-auto"
              priority
            />
          </Link>

          <nav className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-navy/80 hover:text-navy font-medium transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          <div className="hidden lg:flex items-center">
            <Link href="/chat" className="btn-primary text-sm">
              Find a lawyer
            </Link>
          </div>

          <button
            className="lg:hidden btn-ghost p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-100 bg-white">
          <div className="section-container py-4 space-y-2">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block text-navy font-medium py-2"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-3 border-t border-gray-100">
              <Link
                href="/chat"
                className="btn-primary w-full"
                onClick={() => setMobileOpen(false)}
              >
                Find a lawyer
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
