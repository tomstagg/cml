import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  PhoneCall,
  Search,
  ShieldCheck,
  Star,
} from "lucide-react";

export const metadata: Metadata = {
  title: "Choose My Lawyer — Find a conveyancing solicitor",
  description:
    "Compare residential conveyancing solicitors across the West Midlands. Independent, transparent quotes ranked on price, reputation, complaints, regulation and distance.",
};

const steps = [
  {
    n: "1",
    title: "Tell us about your property",
    body: [
      "Our guided chat asks a short set of questions about your purchase or sale: purchase price, tenure, postcode, mortgage, and a few extras (new build, Help to Buy ISA, shared ownership). Takes about 3 minutes.",
      "Your answers feed straight into the price and ranking calculations — there's no rough estimating.",
    ],
  },
  {
    n: "2",
    title: "Compare regulated firms side-by-side",
    body: [
      "We rank every in-scope SRA-authorised firm in the West Midlands using a deterministic six-factor scorecard: price, reputation, complaints history, regulatory history, distance and number of offices.",
      "Each result shows the comparable Total Effective Price (legal fees + applicable VAT + included disbursements), plus star ratings and complaints/regulatory bands. Sort the full table by any factor.",
    ],
  },
  {
    n: "3",
    title: "Proceed or request a callback",
    body: [
      "Click Proceed to instruct a single firm, or Request a callback with up to five. Both actions send an email introduction in your name — not from CML.",
      "We'll follow up by email to make sure the firm has been in touch, and again at the 5-working-day mark to flag any price drift.",
    ],
  },
];

const testimonials = [
  {
    quote:
      "I had quotes side-by-side in minutes — no chasing firms for prices. The breakdown of disbursements was the clearest I'd seen.",
    name: "Hannah W.",
    location: "Birmingham",
  },
  {
    quote:
      "Being able to filter by complaints and regulatory history was the bit that sold me. I'd never have spotted that on a comparison site.",
    name: "Marcus J.",
    location: "Coventry",
  },
  {
    quote:
      "Picked a firm on a Saturday morning and they called me back on Monday. Genuinely smoother than I expected.",
    name: "Priya S.",
    location: "Wolverhampton",
  },
];

const faqs = [
  {
    q: "Is it free to use?",
    a: "Yes — completely free for consumers. There's no charge to get quotes, instruct a firm, or request a callback.",
  },
  {
    q: "How accurate are the quotes?",
    a: "Quotes are calculated from each firm's published price card against your specific matter — purchase price, tenure, mortgage, and so on. The number you see is the comparable Total Effective Price; the firm will confirm exact fees on instruction. Excluded disbursements (Stamp Duty, leasehold notice fees, ground rent apportionment, indemnity policies) are flagged separately.",
  },
  {
    q: "Are all the firms regulated?",
    a: "Yes. Every firm we list is authorised by the Solicitors Regulation Authority. Any firm with an active SRA intervention is removed from results entirely.",
  },
  {
    q: "How are firms ranked?",
    a: "By a six-factor scorecard: reputation 25%, price 25%, complaints history 15%, regulatory history 15%, distance 10%, and number of offices 10%. You can pick a different scorecard at intake to weight one factor at 40% — the others rescale around it. Same inputs always produce the same rankings.",
  },
  {
    q: "Which areas do you cover?",
    a: "During the pilot we cover residential conveyancing across the West Midlands Combined Authority — Birmingham (B), Coventry (CV), Dudley (DY), Wolverhampton (WV), and Walsall (WS) postcodes.",
  },
  {
    q: "Can I save my comparison and come back later?",
    a: "Yes. During the chat, click Save for later and enter your email — we'll send you a link to resume where you left off.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden bg-navy text-white">
        <div
          aria-hidden
          className="absolute inset-0 -z-10 opacity-40 [background-image:radial-gradient(ellipse_at_top,rgba(151,71,255,0.45),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(10,229,246,0.18),transparent_45%)]"
        />
        <div className="section-container py-24 sm:py-32">
          <div className="max-w-3xl mx-auto text-center">
            <p className="text-teal font-semibold mb-4 tracking-wide uppercase text-sm">
              West Midlands · Conveyancing solicitors
            </p>
            <h1 className="font-bold mb-6">
              Find the right conveyancer.{" "}
              <span className="text-white/60">Instantly.</span>
            </h1>
            <p className="text-lg sm:text-xl text-white/80 mb-10 leading-relaxed">
              Answer a few simple questions about your property purchase or sale and get a ranked
              list of SRA-authorised solicitors with transparent quotes — in under 3 minutes.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link href="/chat" className="btn-primary text-base">
                Get your free quote
                <ArrowRight className="w-5 h-5" />
              </Link>
              <Link
                href="/how-it-works"
                className="btn-secondary bg-transparent text-white border-white hover:bg-white/10"
              >
                How it works
              </Link>
            </div>
            <p className="mt-6 text-white/60 text-sm">
              Free to use · No obligation · 100% independent
            </p>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-white">
        <div className="section-container max-w-4xl">
          <div className="text-center mb-14">
            <h2 className="font-bold text-navy mb-3">How Choose My Lawyer works</h2>
            <p className="text-ink-muted max-w-2xl mx-auto">
              Buying or selling a home doesn't have to mean opaque pricing or endless phone calls.
              Here's how we make conveyancing simple.
            </p>
          </div>
          <div className="space-y-12">
            {steps.map((step) => (
              <div key={step.n} className="flex gap-6">
                <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-hero text-white flex items-center justify-center font-bold text-lg shadow-soft">
                  {step.n}
                </div>
                <div>
                  <h3 className="font-bold text-navy mb-3">{step.title}</h3>
                  {step.body.map((p) => (
                    <p key={p} className="text-ink-muted leading-relaxed mb-3">
                      {p}
                    </p>
                  ))}
                </div>
              </div>
            ))}
          </div>
          <div className="text-center mt-12">
            <Link href="/chat" className="btn-primary text-base">
              Start now — it&apos;s free
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </section>

      {/* Why trust us */}
      <section className="py-20 bg-surface-muted">
        <div className="section-container">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card p-7">
              <ShieldCheck className="w-8 h-8 text-purple mb-4" />
              <h3 className="font-bold text-navy mb-2">Whole-of-market</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                Every in-scope firm appears in your full results — whether they're enrolled with us
                or not. We never rank enrolled firms separately.
              </p>
            </div>
            <div className="card p-7">
              <Search className="w-8 h-8 text-purple mb-4" />
              <h3 className="font-bold text-navy mb-2">Deterministic ranking</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                Six factors, weighted to 100. No pay-to-rank, no AI guesswork. Same inputs always
                produce the same rankings — and the methodology is published in full.
              </p>
            </div>
            <div className="card p-7">
              <PhoneCall className="w-8 h-8 text-purple mb-4" />
              <h3 className="font-bold text-navy mb-2">Introductions in your name</h3>
              <p className="text-ink-muted text-sm leading-relaxed">
                When you Proceed or request a callback, the firm receives an email from you — not a
                cold lead from CML. We follow up to make sure they got back to you.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 bg-white">
        <div className="section-container">
          <div className="text-center mb-12">
            <h2 className="font-bold text-navy mb-3">Why our customers trust us</h2>
            <div className="flex items-center justify-center gap-1 text-purple">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
              <span className="ml-2 text-sm text-ink-muted">
                Trusted by movers across the West Midlands
              </span>
            </div>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {testimonials.map((t) => (
              <div key={t.name} className="card p-7">
                <div className="flex gap-0.5 text-purple mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <p className="text-navy leading-relaxed mb-5">&ldquo;{t.quote}&rdquo;</p>
                <p className="text-sm font-semibold text-navy">
                  {t.name} <span className="text-ink-muted font-normal">· {t.location}</span>
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section id="faqs" className="py-20 bg-surface-muted scroll-mt-24">
        <div className="section-container max-w-3xl">
          <div className="text-center mb-12">
            <p className="text-sm uppercase tracking-wide text-purple mb-3">FAQs</p>
            <h2 className="font-bold text-navy">Frequently asked questions</h2>
          </div>
          <div className="space-y-4">
            {faqs.map(({ q, a }) => (
              <details key={q} className="card p-6 group">
                <summary className="font-semibold text-navy cursor-pointer list-none flex justify-between items-center gap-4">
                  {q}
                  <span className="text-purple group-open:rotate-45 transition-transform text-xl leading-none">
                    +
                  </span>
                </summary>
                <p className="text-ink-muted mt-3 leading-relaxed">{a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* CTA banner */}
      <section className="py-20 bg-white">
        <div className="section-container">
          <div className="rounded-3xl bg-navy text-white p-10 md:p-14 shadow-soft text-center relative overflow-hidden">
            <div
              aria-hidden
              className="absolute inset-0 opacity-40 [background-image:radial-gradient(ellipse_at_top_left,rgba(151,71,255,0.6),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(10,229,246,0.25),transparent_50%)]"
            />
            <div className="relative">
              <h2 className="font-bold mb-3">Ready to find your conveyancer?</h2>
              <p className="text-white/80 mb-7 max-w-xl mx-auto">
                Free, no obligation. Get quotes from regulated West Midlands solicitors in under
                three minutes.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link href="/chat" className="btn-primary">
                  Get your free quote
                  <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/how-it-works"
                  className="btn-secondary bg-transparent text-white border-white hover:bg-white/10"
                >
                  How it works
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
