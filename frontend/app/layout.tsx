import type { Metadata } from "next";
import { Nunito } from "next/font/google";
import "./globals.css";
import { Toaster } from "sonner";

const nunito = Nunito({ subsets: ["latin"], weight: ["400", "600", "700", "800"] });

export const metadata: Metadata = {
  title: {
    template: "%s | Choose My Lawyer",
    default: "Choose My Lawyer — Find Your Probate Solicitor",
  },
  description:
    "Compare probate solicitors in England & Wales. Get instant quotes, read reviews, and appoint a solicitor — all in one place.",
  keywords: "probate solicitor, estate administration, grant of probate, choose my lawyer",
  openGraph: {
    siteName: "Choose My Lawyer",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={nunito.className}>
        {children}
        <Toaster position="top-right" richColors />
      </body>
    </html>
  );
}
