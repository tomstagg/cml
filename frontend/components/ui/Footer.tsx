import Link from "next/link";
import Image from "next/image";
import { Instagram, Linkedin, Youtube } from "lucide-react";

export function Footer() {
  return (
    <footer className="relative overflow-hidden bg-gradient-footer text-white">
      <div
        aria-hidden
        className="pointer-events-none absolute -right-24 sm:-right-32 -bottom-32 sm:-bottom-40 h-[480px] w-[480px] sm:h-[720px] sm:w-[720px] bg-white/10"
        style={{
          WebkitMaskImage: "url('/logo-mark.svg')",
          maskImage: "url('/logo-mark.svg')",
          WebkitMaskRepeat: "no-repeat",
          maskRepeat: "no-repeat",
          WebkitMaskPosition: "center",
          maskPosition: "center",
          WebkitMaskSize: "contain",
          maskSize: "contain",
        }}
      />
      <div className="relative section-container py-14">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-12">
          <div>
            <Link href="/" className="inline-flex items-center mb-4" aria-label="Choose My Lawyer home">
              <Image
                src="/logo-dark.png"
                alt="Choose My Lawyer"
                width={180}
                height={64}
                className="h-12 w-auto"
              />
            </Link>
            <p className="text-sm leading-relaxed text-white/70 max-w-sm">
              We connect consumers with legal experts. Independent, transparent comparison for
              residential conveyancing across the West Midlands.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 md:col-span-1">
            <div>
              <h4 className="text-white font-semibold mb-3 text-sm">Explore</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li><Link href="/how-it-works" className="hover:text-white transition-colors">How it works</Link></li>
                <li><Link href="/how-it-works#faqs" className="hover:text-white transition-colors">FAQs</Link></li>
                <li><Link href="/conveyancing" className="hover:text-white transition-colors">Conveyancing</Link></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-3 text-sm">For firms</h4>
              <ul className="space-y-2 text-sm text-white/70">
                <li><Link href="/for-firms" className="hover:text-white transition-colors">Why list with us</Link></li>
                <li><Link href="/contact" className="hover:text-white transition-colors">Contact us</Link></li>
              </ul>
            </div>
          </div>

          <div className="md:text-right">
            <h4 className="text-white font-semibold mb-3 text-sm">Follow us</h4>
            <div className="flex gap-3 md:justify-end">
              <a
                href="https://instagram.com"
                aria-label="Instagram"
                className="w-9 h-9 rounded-full border border-white/30 flex items-center justify-center hover:bg-white/10 transition-colors"
              >
                <Instagram className="w-4 h-4" />
              </a>
              <a
                href="https://youtube.com"
                aria-label="YouTube"
                className="w-9 h-9 rounded-full border border-white/30 flex items-center justify-center hover:bg-white/10 transition-colors"
              >
                <Youtube className="w-4 h-4" />
              </a>
              <a
                href="https://linkedin.com"
                aria-label="LinkedIn"
                className="w-9 h-9 rounded-full border border-white/30 flex items-center justify-center hover:bg-white/10 transition-colors"
              >
                <Linkedin className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-white/15 pt-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4 text-xs text-white/60">
          <p>© {new Date().getFullYear()} Choose My Lawyer. All rights reserved.</p>
          <ul className="flex flex-wrap gap-x-6 gap-y-2">
            <li><Link href="/terms" className="hover:text-white transition-colors">Website Terms</Link></li>
            <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
            <li><Link href="/cookies" className="hover:text-white transition-colors">Cookie Policy</Link></li>
          </ul>
        </div>

        <p className="mt-6 text-xs text-white/50 max-w-3xl">
          Choose My Lawyer is an independent comparison service and is not regulated by the
          Solicitors Regulation Authority.
        </p>
        <p className="mt-3 text-xs text-white/50 max-w-3xl">
          However, we&apos;re not a legal firm and we don&apos;t offer legal advice. We provide
          helpful guides on our site, to give you an understanding of different services, but
          these can&apos;t be considered legal advice.
        </p>
      </div>
    </footer>
  );
}
