import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  CheckCircle,
  ClipboardList,
  Mail,
  ShieldCheck,
  Sparkles,
  Users,
} from "lucide-react";

export const metadata: Metadata = {
  title: "For firms — Choose My Lawyer",
  description:
    "Join the Choose My Lawyer pilot for conveyancing solicitors across the West Midlands. Transparent ranking, lead delivery in the consumer's name, no monthly fee during the pilot.",
};

const benefits = [
  {
    icon: Users,
    title: "Pre-qualified leads",
    description:
      "Every Proceed and Callback comes from a consumer who has answered the full intake and seen your quote alongside the rest of the market.",
  },
  {
    icon: Mail,
    title: "Introductions in the consumer's name",
    description:
      "Lead emails are sent on behalf of the consumer, with their contact details and matter summary. You reply directly — CML stays out of the way.",
  },
  {
    icon: BarChart3,
    title: "Transparent ranking",
    description:
      "Six-factor scorecard, deterministic and published in full. Identical inputs always produce identical rankings — there is no pay-to-rank.",
  },
  {
    icon: ShieldCheck,
    title: "Built-in conflict-check workflow",
    description:
      "Flag a conflict and we'll email the consumer with a deep link back to results so they can pick another firm.",
  },
];

const enrollmentSteps = [
  {
    icon: Mail,
    title: "We invite you",
    desc: "Our team sends a personalised enrolment link tied to your firm's SRA record.",
  },
  {
    icon: ClipboardList,
    title: "Set up your firm",
    desc: "Confirm offices, then publish your conveyancing price card — bands by purchase price plus adjustments for tenure, mortgage, new build, HtB ISA, and shared ownership.",
  },
  {
    icon: Sparkles,
    title: "Start appearing in results",
    desc: "Enrolled firms appear in the top-5 contactable strip with Proceed and Callback buttons. Non-enrolled firms still appear in the full market view.",
  },
];

export default function ForFirmsPage() {
  return (
    <>
      <section className="bg-gradient-hero text-white">
        <div className="section-container py-24 text-center">
          <p className="text-sm uppercase tracking-wide text-white/70 mb-3">
            West Midlands · Residential conveyancing pilot
          </p>
          <h1 className="font-bold mb-5 max-w-3xl mx-auto">
            Reach West Midlands homebuyers and sellers actively comparing conveyancers
          </h1>
          <p className="text-lg text-white/85 mb-8 max-w-2xl mx-auto">
            Choose My Lawyer connects SRA-authorised conveyancing firms with consumers who have
            already chosen to compare. Free to join during the 90-day pilot.
          </p>
          <Link href="/contact" className="btn-secondary bg-white text-navy border-transparent">
            Register your interest
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="font-bold text-navy mb-3">Why list with us</h2>
            <p className="text-ink-muted max-w-2xl mx-auto">
              We're not a directory and we're not a lead farm. CML is a deterministic comparison
              engine — and the pilot is designed to prove it.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {benefits.map((b) => (
              <div key={b.title} className="card p-7 flex gap-4">
                <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-surface-alt flex items-center justify-center">
                  <b.icon className="w-6 h-6 text-navy" />
                </div>
                <div>
                  <h3 className="font-bold text-navy mb-2">{b.title}</h3>
                  <p className="text-ink-muted text-sm leading-relaxed">{b.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-surface-muted">
        <div className="section-container max-w-5xl">
          <div className="text-center mb-12">
            <h2 className="font-bold text-navy mb-3">How enrolment works</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {enrollmentSteps.map((s, i) => (
              <div key={s.title} className="card p-7">
                <div className="flex items-center gap-3 mb-4">
                  <span className="w-8 h-8 rounded-full bg-gradient-hero text-white text-sm font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <s.icon className="w-5 h-5 text-purple" />
                </div>
                <h3 className="font-bold text-navy mb-2">{s.title}</h3>
                <p className="text-sm text-ink-muted leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container max-w-4xl">
          <div className="rounded-3xl bg-surface-alt p-10 md:p-14 text-center">
            <h2 className="font-bold text-navy mb-4">Pilot pricing</h2>
            <p className="text-ink-muted mb-2">
              <strong className="text-navy">Free to join</strong> for the duration of the
              90-day West Midlands pilot.
            </p>
            <p className="text-ink-muted mb-8 max-w-2xl mx-auto">
              A referral fee will apply per chargeable Proceed or Callback after the pilot, billed
              manually with a delay window so you have time to make contact. We'll give 30 days'
              notice before this kicks in.
            </p>
            <div className="flex justify-center gap-4 flex-wrap">
              {["No monthly fee", "No setup cost", "No obligation", "Cancel anytime"].map((item) => (
                <span key={item} className="flex items-center gap-1.5 text-navy font-medium text-sm">
                  <CheckCircle className="w-4 h-4 text-purple" /> {item}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="section-container">
          <div className="rounded-3xl bg-gradient-hero p-10 md:p-14 text-white shadow-soft text-center">
            <h2 className="font-bold mb-3">Want to take part in the pilot?</h2>
            <p className="text-white/85 mb-7 max-w-xl mx-auto">
              We're enrolling West Midlands conveyancing firms ahead of the 1 June 2026 go-live.
              Drop us a message and we'll send your enrolment link.
            </p>
            <Link href="/contact" className="btn-secondary bg-white text-navy border-transparent">
              Get in touch
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
