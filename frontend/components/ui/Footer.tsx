import Link from "next/link";
import { Scale } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-gray-950 text-gray-400 py-12">
      <div className="section-container">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-10">
          <div className="col-span-2 md:col-span-1">
            <Link href="/" className="flex items-center gap-2 font-bold text-white mb-3">
              <Scale className="w-5 h-5 text-brand-400" />
              <span>Choose My Lawyer</span>
            </Link>
            <p className="text-sm leading-relaxed">
              An independent legal comparison platform for England & Wales. Not regulated by the SRA.
            </p>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">Services</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/probate" className="hover:text-white transition-colors">Probate</Link></li>
              <li><Link href="/how-it-works" className="hover:text-white transition-colors">How It Works</Link></li>
              <li><Link href="/chat" className="hover:text-white transition-colors">Get Quotes</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">For Firms</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/for-firms" className="hover:text-white transition-colors">Why List With Us</Link></li>
              <li><Link href="/firm/login" className="hover:text-white transition-colors">Firm Login</Link></li>
              <li><Link href="/contact" className="hover:text-white transition-colors">Contact Us</Link></li>
            </ul>
          </div>
          <div>
            <h4 className="text-white font-semibold mb-3 text-sm">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/privacy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link href="/terms" className="hover:text-white transition-colors">Terms of Service</Link></li>
              <li><Link href="/cookies" className="hover:text-white transition-colors">Cookie Policy</Link></li>
            </ul>
          </div>
        </div>
        <div className="border-t border-gray-800 pt-8 text-sm text-center">
          <p>© {new Date().getFullYear()} Choose My Lawyer. All rights reserved.</p>
          <p className="mt-1 text-gray-600">
            Choose My Lawyer is an independent comparison service and is not regulated by the Solicitors Regulation Authority.
          </p>
        </div>
      </div>
    </footer>
  );
}
