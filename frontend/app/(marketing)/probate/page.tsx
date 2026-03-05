import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight } from "lucide-react";

export const metadata: Metadata = {
  title: "Find a Probate Solicitor | England & Wales",
  description:
    "Compare probate solicitors across England and Wales. Get instant transparent quotes based on your estate details. SRA-authorised firms only.",
  keywords: "probate solicitor, grant of probate, estate administration, probate lawyer UK",
};

export default function ProbateLandingPage() {
  return (
    <div className="py-16">
      <div className="section-container max-w-4xl mx-auto">
        <h1 className="text-4xl font-bold text-gray-900 mb-6">
          Find a Probate Solicitor in England & Wales
        </h1>

        <p className="text-xl text-gray-600 mb-8">
          Dealing with a loved one's estate is difficult enough without having to navigate confusing
          legal fees. Choose My Lawyer makes it easy to find and compare SRA-authorised probate
          solicitors with instant, transparent quotes.
        </p>

        <div className="card p-8 bg-brand-50 border-brand-100 mb-12">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Get your free quote in 3 minutes</h2>
          <p className="text-gray-600 mb-6">
            Answer a few questions about the estate and we'll show you a ranked list of probate
            solicitors with itemised quotes — no obligation, completely free.
          </p>
          <Link href="/chat" className="btn-primary">
            Start My Comparison
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        <h2 className="text-2xl font-bold text-gray-900 mb-4">What is probate?</h2>
        <p className="text-gray-600 mb-6">
          Probate is the legal process of administering a deceased person's estate in England and
          Wales. It involves:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600 mb-8 ml-4">
          <li>Obtaining a grant of representation (grant of probate or letters of administration)</li>
          <li>Identifying and valuing assets and debts</li>
          <li>Paying any inheritance tax due to HMRC</li>
          <li>Collecting assets and settling debts</li>
          <li>Distributing the estate to beneficiaries</li>
        </ul>

        <h2 className="text-2xl font-bold text-gray-900 mb-4">Do I need a probate solicitor?</h2>
        <p className="text-gray-600 mb-4">
          You can apply for probate yourself, but a solicitor is strongly recommended if the estate:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600 mb-8 ml-4">
          <li>Is worth over £325,000 (the inheritance tax threshold)</li>
          <li>Includes property, shares, or complex investments</li>
          <li>Has no valid Will (intestacy)</li>
          <li>Involves overseas assets</li>
          <li>Is likely to be contested</li>
        </ul>

        <h2 className="text-2xl font-bold text-gray-900 mb-4">How much does probate cost?</h2>
        <p className="text-gray-600 mb-4">
          Probate costs typically include:
        </p>
        <ul className="list-disc list-inside space-y-2 text-gray-600 mb-4 ml-4">
          <li>Solicitor legal fees (fixed, banded by estate value, or a percentage)</li>
          <li>Probate Registry application fee (currently £273 for estates over £5,000)</li>
          <li>Other disbursements (Land Registry, bankruptcy searches, swearing fees)</li>
          <li>VAT at 20% on legal fees</li>
        </ul>
        <p className="text-gray-600 mb-8">
          Use our comparison tool to get itemised quotes based on your specific estate — so you can
          compare like for like.
        </p>

        <div className="text-center">
          <Link href="/chat" className="btn-primary text-lg px-8 py-4 rounded-xl">
            Compare Probate Solicitors Free
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
