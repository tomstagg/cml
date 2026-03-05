import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle, Shield, Star, Users } from "lucide-react";

export const metadata: Metadata = {
  title: "Choose My Lawyer — Find Your Probate Solicitor",
  description:
    "Compare probate solicitors in England & Wales. Instant quotes, verified reviews, and SRA-authorised firms — all in one place.",
};

const features = [
  {
    icon: Shield,
    title: "SRA Verified Firms",
    description: "Every solicitor is checked against the Solicitors Regulation Authority register.",
  },
  {
    icon: Star,
    title: "Real Client Reviews",
    description: "Verified reviews from real clients who used our platform to appoint their solicitor.",
  },
  {
    icon: CheckCircle,
    title: "Instant Quotes",
    description: "Get itemised quotes in minutes — no hidden fees, no obligation.",
  },
  {
    icon: Users,
    title: "Local & Remote",
    description: "Find local solicitors or work with firms across England & Wales remotely.",
  },
];

const steps = [
  {
    step: "01",
    title: "Answer a few questions",
    description:
      "Tell us about the estate — value, assets, whether there's a Will. Takes about 3 minutes.",
  },
  {
    step: "02",
    title: "Compare solicitors",
    description:
      "See a ranked list of SRA-authorised firms with transparent pricing, reviews, and location.",
  },
  {
    step: "03",
    title: "Appoint your solicitor",
    description:
      "Book directly through our platform. We'll send confirmation to you and the firm.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-950 via-brand-900 to-brand-800 text-white">
        <div className="section-container py-24 sm:py-32">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-brand-300 font-medium mb-4 tracking-wide uppercase text-sm">
              England & Wales · Probate Solicitors
            </p>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold leading-tight mb-6">
              Find the right probate solicitor.{" "}
              <span className="text-brand-300">Instantly.</span>
            </h1>
            <p className="text-xl text-brand-100 mb-10 leading-relaxed">
              Answer a few simple questions about the estate and get a ranked list of SRA-authorised
              solicitors with transparent quotes — in under 3 minutes.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/chat" className="btn-primary text-lg px-8 py-4 rounded-xl">
                Get Your Free Quote
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/how-it-works"
                className="btn-secondary text-lg px-8 py-4 rounded-xl border-brand-700 text-brand-100 hover:bg-brand-800"
              >
                How It Works
              </Link>
            </div>
            <p className="mt-6 text-brand-400 text-sm">
              Free to use · No obligation · 100% independent
            </p>
          </div>
        </div>
        {/* Decorative gradient */}
        <div className="absolute inset-0 -z-10 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-brand-700/30 via-transparent to-transparent" />
      </section>

      {/* Features */}
      <section className="py-20 bg-gray-50">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why choose Choose My Lawyer?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              We make finding a probate solicitor transparent, fast, and stress-free.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature) => (
              <div key={feature.title} className="card p-6 text-center">
                <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center mx-auto mb-4">
                  <feature.icon className="w-6 h-6 text-brand-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20">
        <div className="section-container">
          <div className="text-center mb-14">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">How it works</h2>
            <p className="text-lg text-gray-600">Three simple steps to finding your solicitor</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {steps.map((step, idx) => (
              <div key={step.step} className="relative text-center">
                <div className="text-6xl font-bold text-brand-100 mb-4">{step.step}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-3">{step.title}</h3>
                <p className="text-gray-600 leading-relaxed">{step.description}</p>
                {idx < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-[calc(100%_-_1rem)] w-8">
                    <ArrowRight className="w-6 h-6 text-gray-300" />
                  </div>
                )}
              </div>
            ))}
          </div>
          <div className="text-center mt-12">
            <Link href="/chat" className="btn-primary text-lg px-8 py-4 rounded-xl">
              Start Now — It&apos;s Free
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* For Law Firms CTA */}
      <section className="py-16 bg-brand-950 text-white">
        <div className="section-container text-center">
          <h2 className="text-2xl font-bold mb-4">Are you a solicitor firm?</h2>
          <p className="text-brand-200 mb-8 max-w-xl mx-auto">
            Join Choose My Lawyer and reach clients actively looking for probate solicitors. Free to
            join during our launch period.
          </p>
          <Link href="/for-firms" className="btn-secondary border-brand-700 text-brand-100 hover:bg-brand-800">
            Learn More for Firms
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>
    </>
  );
}
