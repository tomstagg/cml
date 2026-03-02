"use client";

import Link from "next/link";
import { useState } from "react";
import { Menu, Scale, X } from "lucide-react";

const navLinks = [
  { href: "/probate", label: "Probate" },
  { href: "/how-it-works", label: "How It Works" },
  { href: "/for-firms", label: "For Firms" },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-gray-200 shadow-sm">
      <div className="section-container">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-gray-900">
            <Scale className="w-6 h-6 text-brand-600" />
            <span>
              Choose My <span className="text-brand-600">Lawyer</span>
            </span>
          </Link>

          {/* Desktop nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-gray-600 hover:text-gray-900 font-medium transition-colors"
              >
                {link.label}
              </Link>
            ))}
          </nav>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-3">
            <Link href="/login" className="btn-ghost text-sm">
              Firm Login
            </Link>
            <Link href="/chat" className="btn-primary text-sm px-4 py-2">
              Get Quotes
            </Link>
          </div>

          {/* Mobile menu button */}
          <button
            className="md:hidden btn-ghost p-2"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white">
          <div className="section-container py-4 space-y-3">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="block text-gray-700 font-medium py-2"
                onClick={() => setMobileOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-3 border-t border-gray-100 flex flex-col gap-2">
              <Link href="/login" className="btn-ghost w-full justify-center">
                Firm Login
              </Link>
              <Link href="/chat" className="btn-primary w-full justify-center">
                Get Quotes
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
