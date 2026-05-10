import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";
import { AnalyticsPageView } from "@/components/AnalyticsPageView";
import { CookieConsent } from "@/components/CookieConsent";
import { MetaPixel } from "@/components/MetaPixel";

const inter = Inter({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: {
    template: "%s | Choose My Lawyer",
    default: "Choose My Lawyer — Find a conveyancing solicitor",
  },
  description:
    "Compare residential conveyancing solicitors across the West Midlands. Independent, transparent quotes ranked on price, reputation, complaints, regulation and distance.",
  keywords: "conveyancing solicitor, conveyancing quotes, residential conveyancing, west midlands conveyancer, choose my lawyer",
  openGraph: {
    siteName: "Choose My Lawyer",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans">
        <MetaPixel />
        <AnalyticsPageView />
        {children}
        <CookieConsent />
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
