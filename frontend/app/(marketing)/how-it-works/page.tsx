import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  Mail,
  PhoneCall,
  Search,
  ShieldCheck,
  Sliders,
} from "lucide-react";

export const metadata: Metadata = {
  title: "How it works — Choose My Lawyer",
  description:
    "How Choose My Lawyer compares residential conveyancing solicitors across the West Midlands — from intake to instruction.",
};

const steps = [
  {
    icon: ClipboardList,
    title: "Tell us about your matter",
    body: [
      "Our guided chat asks for a handful of facts about your purchase or sale: purchase price, tenure, postcode, mortgage, new build, Help to Buy ISA, and shared ownership.",
      "Takes about three minutes. Your answers feed into the price and ranking calculations — there's no rough estimating.",
    ],
  },
  {
    icon: Sliders,
    title: "Pick how you want firms ranked",
    body: [
      "Choose the Balanced scorecard, or prioritise one of: Reputation, Price, Complaints History, Regulatory History, Distance, or Number of offices.",
      "Whichever scorecard you pick, every in-scope firm in the West Midlands is ranked together. We never rank enrolled firms separately from non-enrolled.",
    ],
  },
  {
    icon: Search,
    title: "Compare side-by-side",
    body: [
      "See the full market alongside the top-5 contactable firms. Each result shows total effective price (legal fees + VAT + included disbursements), star ratings, complaints and regulatory history bands, distance, and office count.",
      "Sort the full table by any factor — sort is display-only and doesn't change the underlying ranking.",
    ],
  },
  {
    icon: PhoneCall,
    title: "Proceed or request a callback",
    body: [
      "Click Proceed to instruct a single firm, or Request a callback with up to five firms. Both actions send an email introduction in your name (not from CML).",
      "We'll follow up to check the firm contacted you, and at the 5-working-day mark to flag any price drift.",
    ],
  },
];

const factors = [
  { name: "Reputation", weight: "25%", note: "Aggregate review score, log-weighted by review volume." },
  { name: "Price", weight: "25%", note: "Total Effective Price — fees + applicable VAT + included disbursements." },
  { name: "Complaints history", weight: "15%", note: "Legal Ombudsman decisions, weighted by remedy severity and amount." },
  { name: "Regulatory history", weight: "15%", note: "SRA + SDT outcomes. Active interventions remove a firm entirely." },
  { name: "Distance", weight: "10%", note: "Geodesic distance to the firm's nearest office. Optional." },
  { name: "Number of offices", weight: "10%", note: "Banded score — more offices, slightly higher weight." },
];

const faqs = [
  {
    q: "Is it free?",
    a: "Yes. Free for consumers, with no obligation. We charge participating firms a referral fee per Proceed or Callback action — that's how we keep the lights on.",
  },
  {
    q: "How accurate are the quotes?",
    a: "Quotes are calculated from each firm's published price card against your specific matter — purchase price, tenure, mortgage, and so on. The number you see is the comparable Total Effective Price; the firm will confirm exact fees on instruction.",
  },
  {
    q: "Are all the firms regulated?",
    a: "Yes. Every firm we list is authorised by the Solicitors Regulation Authority. Any firm with an active SRA intervention is removed from results entirely.",
  },
  {
    q: "Can I save my comparison?",
    a: "Yes. Click Save for later in the chat and we'll email you a link to resume where you left off.",
  },
  {
    q: "What if a firm doesn't get back to me?",
    a: "We'll email you the same evening (for callbacks) and 5 working days after a Proceed action to ask whether the firm has been in touch. If they haven't, you can re-run the comparison or pick another firm.",
  },
];

export default function HowItWorksPage() {
  return (
    <>
      <section className="bg-gradient-hero text-white">
        <div className="section-container py-20">
          <div className="max-w-3xl">
            <h1 className="font-bold mb-4">How Choose My Lawyer works</h1>
            <p className="text-lg text-white/85">
              Independent, deterministic comparison for residential conveyancing across the West
              Midlands. Same inputs, same rankings, every time.
            </p>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container max-w-4xl">
          <div className="space-y-10">
            {steps.map((step, i) => (
              <div key={step.title} className="flex gap-6">
                <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-surface-alt flex items-center justify-center">
                  <step.icon className="w-6 h-6 text-navy" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-purple mb-1">Step {i + 1}</p>
                  <h2 className="font-bold text-navy mb-3">{step.title}</h2>
                  {step.body.map((p) => (
                    <p key={p} className="text-ink-muted leading-relaxed mb-3">
                      {p}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-surface-muted">
        <div className="section-container max-w-5xl">
          <div className="text-center mb-12">
            <h2 className="font-bold text-navy mb-3">The Balanced scorecard</h2>
            <p className="text-ink-muted max-w-2xl mx-auto">
              Six factors, weighted to 100. Pick a different scorecard at intake to weight one
              factor at 40% — the others rescale around it.
            </p>
          </div>
          <div className="card overflow-hidden">
            <table className="w-full">
              <thead className="bg-surface-alt">
                <tr>
                  <th className="text-left text-sm font-semibold text-navy py-4 px-6">Factor</th>
                  <th className="text-left text-sm font-semibold text-navy py-4 px-6">Weight</th>
                  <th className="text-left text-sm font-semibold text-navy py-4 px-6">How it's measured</th>
                </tr>
              </thead>
              <tbody>
                {factors.map((f) => (
                  <tr key={f.name} className="border-t border-gray-100">
                    <td className="py-4 px-6 font-semibold text-navy">{f.name}</td>
                    <td className="py-4 px-6 text-navy">{f.weight}</td>
                    <td className="py-4 px-6 text-ink-muted text-sm">{f.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container max-w-3xl">
          <div className="text-center mb-12">
            <h2 className="font-bold text-navy mb-3">After you take action</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-6 text-center">
              <Mail className="w-8 h-8 text-purple mx-auto mb-3" />
              <h3 className="font-bold text-navy mb-2">Introduction sent</h3>
              <p className="text-sm text-ink-muted">
                The firm receives an email in your name, with your matter details and contact
                preferences.
              </p>
            </div>
            <div className="card p-6 text-center">
              <ShieldCheck className="w-8 h-8 text-purple mx-auto mb-3" />
              <h3 className="font-bold text-navy mb-2">Conflict check</h3>
              <p className="text-sm text-ink-muted">
                If a firm flags a conflict, we email you immediately with a deep link back to
                results.
              </p>
            </div>
            <div className="card p-6 text-center">
              <PhoneCall className="w-8 h-8 text-purple mx-auto mb-3" />
              <h3 className="font-bold text-navy mb-2">Follow-up</h3>
              <p className="text-sm text-ink-muted">
                We check in by email so you can flag firms that didn't respond.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section id="faqs" className="py-20 bg-surface-muted scroll-mt-24">
        <div className="section-container max-w-3xl">
          <h2 className="font-bold text-navy mb-8">Frequently asked questions</h2>
          <div className="space-y-4">
            {faqs.map(({ q, a }) => (
              <details key={q} className="card p-6 group">
                <summary className="font-semibold text-navy cursor-pointer list-none flex justify-between items-center gap-4">
                  {q}
                  <span className="text-purple group-open:rotate-45 transition-transform text-xl leading-none">+</span>
                </summary>
                <p className="text-ink-muted mt-3 leading-relaxed">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="section-container">
          <div className="rounded-3xl bg-gradient-hero p-10 md:p-14 text-white shadow-soft text-center">
            <h2 className="font-bold mb-3">Ready to compare?</h2>
            <p className="text-white/85 mb-7 max-w-xl mx-auto">
              Get conveyancing quotes from regulated solicitors in under three minutes.
            </p>
            <Link href="/chat" className="btn-secondary bg-white text-navy border-transparent">
              Find a lawyer
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}
