import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle, Clock, FileText, Search, Shield, Star } from "lucide-react";

export const metadata: Metadata = {
  title: "How It Works",
  description: "Learn how Choose My Lawyer helps you find and compare probate solicitors in England and Wales.",
};

export default function HowItWorksPage() {
  return (
    <div className="py-16">
      <div className="section-container">
        <div className="max-w-3xl mx-auto">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">How Choose My Lawyer Works</h1>
          <p className="text-xl text-gray-600 mb-12">
            Finding a probate solicitor doesn't have to be complicated. Here's everything you need
            to know.
          </p>

          {/* Steps */}
          <div className="space-y-12 mb-16">
            <div className="flex gap-6">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-lg">
                1
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Answer questions about the estate
                </h2>
                <p className="text-gray-600 mb-4">
                  Our guided chat asks you simple questions about the estate: approximate value, whether there's a
                  Will, types of assets, and where you're based. This takes around 3 minutes.
                </p>
                <p className="text-gray-600">
                  Your answers are used to calculate accurate, itemised quotes from solicitors — not rough estimates.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-lg">
                2
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  See your personalised comparison
                </h2>
                <p className="text-gray-600 mb-4">
                  We rank SRA-authorised firms based on three factors: total cost (60%), client reviews (25%), and
                  distance from your postcode (15%). You can also sort by price, reviews, or location.
                </p>
                <p className="text-gray-600">
                  Each firm shows their regulatory status, aggregate rating, and a full itemised quote
                  including legal fees, disbursements, and VAT.
                </p>
              </div>
            </div>

            <div className="flex gap-6">
              <div className="flex-shrink-0 w-12 h-12 rounded-full bg-brand-600 text-white flex items-center justify-center font-bold text-lg">
                3
              </div>
              <div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">
                  Appoint your solicitor or request a callback
                </h2>
                <p className="text-gray-600 mb-4">
                  Click &quot;Appoint&quot; to submit your appointment request, or &quot;Request Callback&quot; for the firm to contact
                  you at a time that suits you. Both you and the firm receive instant email confirmation.
                </p>
              </div>
            </div>
          </div>

          {/* FAQs */}
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
          <div className="space-y-6 mb-12">
            {[
              {
                q: "Is it free to use?",
                a: "Yes, completely free for consumers. There is no charge to get quotes or appoint a solicitor through our platform.",
              },
              {
                q: "Are the quotes accurate?",
                a: "Quotes are based on pricing information entered by the solicitor firms themselves, matched to your specific circumstances. They are estimates — the exact fee will be confirmed by the firm.",
              },
              {
                q: "How are firms ranked?",
                a: "By a weighted score: 60% price (lower is better), 25% reputation (Google and CML reviews), and 15% distance from your postcode. You can also sort by any individual factor.",
              },
              {
                q: "Are all firms SRA-authorised?",
                a: "Yes. We only include firms authorised by the Solicitors Regulation Authority. We check authorisation status and display it clearly on each result.",
              },
              {
                q: "Can I save my comparison and come back later?",
                a: "Yes. During the chat, click 'Save for later' and enter your email. We'll send you a link to resume where you left off.",
              },
              {
                q: "What is probate?",
                a: "Probate (or 'grant of representation') is the legal process of administering a deceased person's estate. It involves proving the Will is valid, identifying assets and debts, and distributing the estate to beneficiaries.",
              },
            ].map(({ q, a }) => (
              <div key={q} className="card p-6">
                <h3 className="font-semibold text-gray-900 mb-2">{q}</h3>
                <p className="text-gray-600">{a}</p>
              </div>
            ))}
          </div>

          <div className="text-center">
            <Link href="/chat" className="btn-primary text-lg px-8 py-4 rounded-xl">
              Get Started — It's Free
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
