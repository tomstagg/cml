import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import {
  ArrowRight,
  ClipboardList,
  PhoneCall,
  Scale,
  Search,
  Sparkles,
  Star,
} from "lucide-react";
import { HeroSearch } from "@/components/marketing/HeroSearch";
import { WhyChooseUsDemo } from "@/components/marketing/WhyChooseUsDemo";

const heroAvatars = [
  "/images/marketing/review-1.png",
  "/images/marketing/review-2.png",
  "/images/marketing/review-3.png",
  "/images/marketing/review-4.png",
  "/images/marketing/review-5.png",
];

export const metadata: Metadata = {
  title: "Choose My Lawyer | Find a conveyancing solicitor",
  description:
    "Compare residential conveyancing solicitors across the West Midlands. Independent, transparent quotes ranked on price, reputation, complaints, regulation and distance.",
};

const howItWorks = [
  {
    icon: ClipboardList,
    title: "Tell us about your property",
    body: "Answer a short, guided chat about your purchase or sale: price, tenure, postcode, mortgage. Takes about three minutes.",
  },
  {
    icon: Search,
    title: "Compare regulated firms",
    body: "Every in-scope SRA-authorised firm is ranked side-by-side on price, reputation, complaints, regulation, distance and offices.",
  },
  {
    icon: PhoneCall,
    title: "Proceed or request a callback",
    body: "Instruct a single firm, or ask up to five for a callback. The firm hears from you directly. No cold leads, no hard sell.",
  },
];

const valueProps = [
  {
    icon: Scale,
    title: "Whole-of-market ranking",
    body: "Every in-scope SRA-authorised firm appears in your results, not just the ones who pay us.",
  },
  {
    icon: Search,
    title: "Six-factor scorecard",
    body: "Price, reputation, complaints, regulation, distance and offices. Same inputs, same ranking, every time.",
  },
  {
    icon: PhoneCall,
    title: "Introductions in your name",
    body: "Proceed or request a callback and the firm emails you directly. No cold leads, no hard sell.",
  },
];

const testimonials = [
  {
    quote:
      "I had quotes side-by-side in minutes, with no chasing firms for prices. The breakdown of disbursements was the clearest I'd seen.",
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

// Placeholder photography. Swap for licensed shots before launch.
const articles = [
  {
    tag: "Buying",
    title: "What to expect when buying a house in the West Midlands",
    meta: "CML Editorial · 6 min read",
    image: "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=800&q=70",
  },
  {
    tag: "Pricing",
    title: "Disbursements, demystified: what's really in your conveyancing quote",
    meta: "CML Editorial · 4 min read",
    image: "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=800&q=70",
  },
  {
    tag: "Regulation",
    title: "How the SRA and the Legal Ombudsman protect you",
    meta: "CML Editorial · 5 min read",
    image: "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=800&q=70",
  },
];

const faqs = [
  {
    q: "Is it free to use?",
    a: "Yes, completely free for consumers. There's no charge to get quotes, instruct a firm, or request a callback.",
  },
  {
    q: "How accurate are the quotes?",
    a: "Quotes are calculated from each firm's published price card against your specific matter: purchase price, tenure, mortgage, and so on. The number you see is the comparable Total Effective Price; the firm will confirm exact fees on instruction. Excluded disbursements (Stamp Duty, leasehold notice fees, ground rent apportionment, indemnity policies) are flagged separately.",
  },
  {
    q: "Are all the firms regulated?",
    a: "Yes. Every firm we list is authorised by the Solicitors Regulation Authority. Any firm with an active SRA intervention is removed from results entirely.",
  },
  {
    q: "How are firms ranked?",
    a: "By a six-factor scorecard: reputation 25%, price 25%, complaints history 15%, regulatory history 15%, distance 10%, and number of offices 10%. You can pick a different scorecard at intake to weight one factor at 40%, and the others rescale around it. Same inputs always produce the same rankings.",
  },
  {
    q: "Which areas do you cover?",
    a: "During the pilot we cover residential conveyancing across the West Midlands Combined Authority: Birmingham (B), Coventry (CV), Dudley (DY), Wolverhampton (WV), and Walsall (WS) postcodes.",
  },
  {
    q: "Can I save my comparison and come back later?",
    a: "Yes. During the chat, click Save for later and enter your email, and we'll send you a link to resume where you left off.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative isolate overflow-hidden bg-navy text-white">
        <Image
          src="/images/marketing/top-main.png"
          alt=""
          fill
          priority
          sizes="100vw"
          className="object-cover opacity-35"
        />
        <div aria-hidden className="absolute inset-0 bg-navy/70" />
        <div
          aria-hidden
          className="absolute inset-0 opacity-70 [background-image:radial-gradient(ellipse_at_top,rgba(151,71,255,0.55),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(10,229,246,0.25),transparent_45%)]"
        />
        <div aria-hidden className="absolute inset-0 decorative-lines opacity-30" />
        <div className="section-container relative pt-24 sm:pt-32 pb-20 sm:pb-24">
          <div className="max-w-3xl mx-auto text-center">
            <span className="eyebrow text-teal mb-5">
              West Midlands · Conveyancing solicitors
            </span>
            <h1 className="font-bold mt-4 mb-5">
              The smarter way to find, compare &amp;{" "}
              <span className="bg-gradient-to-r from-teal to-purple bg-clip-text text-transparent">
                appoint lawyers
              </span>
            </h1>
            <div className="flex justify-center mb-8">
              <span className="inline-flex items-center gap-2 rounded-full border border-white/25 bg-white/10 px-4 py-1.5 text-sm font-medium text-white/85 backdrop-blur">
                <Sparkles className="w-4 h-4 text-teal" />
                Powered by specialist AI
              </span>
            </div>
            <p className="text-lg sm:text-xl text-white/80 mb-10 leading-relaxed max-w-2xl mx-auto">
              Answer a few simple questions about your property purchase or sale and get a ranked
              list of SRA-authorised solicitors with transparent quotes, in under three minutes.
            </p>
            <HeroSearch />
            <p className="mt-7 text-white/60 text-sm">
              Free to use · No obligation · 100% independent
            </p>

            {/* Social proof: avatars + stars */}
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-5">
              <div className="flex -space-x-3">
                {heroAvatars.map((src, i) => (
                  <span
                    key={src}
                    className="relative w-10 h-10 rounded-full ring-2 ring-navy overflow-hidden bg-white/10"
                    style={{ zIndex: heroAvatars.length - i }}
                  >
                    <Image
                      src={src}
                      alt=""
                      fill
                      sizes="40px"
                      className="object-cover"
                    />
                  </span>
                ))}
              </div>
              <div className="flex flex-col items-center sm:items-start gap-1">
                <div className="flex items-center gap-1 text-teal">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-current" />
                  ))}
                </div>
                <p className="text-sm text-white/80">
                  Trusted by movers across the West Midlands
                </p>
              </div>
            </div>

            {/* Inline testimonial quote */}
            <figure className="mt-10 mx-auto max-w-2xl rounded-2xl border border-white/15 bg-white/5 backdrop-blur px-6 py-5 text-left">
              <blockquote className="text-white/90 leading-relaxed">
                &ldquo;I found and instructed my conveyancing solicitor in minutes, and
                saved £450 compared to local quotes.&rdquo;
              </blockquote>
              <figcaption className="mt-3 text-sm text-white/60">
                Hannah W. · Birmingham
              </figcaption>
            </figure>
          </div>

          {/* In-hero USP cards */}
          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-5 max-w-5xl mx-auto">
            {valueProps.map(({ icon: Icon, title, body }) => (
              <div
                key={title}
                className="rounded-2xl border border-white/15 bg-white/5 backdrop-blur p-6 text-left"
              >
                <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-purple to-teal flex items-center justify-center mb-4 shadow-soft">
                  <Icon className="w-5 h-5 text-white" />
                </div>
                <h3 className="font-bold text-white mb-1.5 text-lg">{title}</h3>
                <p className="text-white/70 text-sm leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 bg-surface-muted">
        <div className="section-container">
          <div className="text-center mb-14 max-w-2xl mx-auto">
            <span className="eyebrow mb-3">How it works</span>
            <h2 className="font-bold text-navy mt-3">From question to quote in three minutes</h2>
            <p className="text-ink-muted mt-4">
              No phone tag, no opaque pricing. Three short steps from a guided intake to a ranked
              shortlist of regulated solicitors.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {howItWorks.map(({ icon: Icon, title, body }, i) => (
              <div key={title} className="card p-7 relative">
                <span className="absolute right-6 top-6 text-5xl font-bold text-surface-muted leading-none select-none">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div className="w-12 h-12 rounded-2xl bg-surface-alt flex items-center justify-center mb-5">
                  <Icon className="w-6 h-6 text-navy" />
                </div>
                <h3 className="font-bold text-navy mb-2">{title}</h3>
                <p className="text-ink-muted leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-10">
            <Link
              href="/how-it-works"
              className="inline-flex items-center gap-2 font-semibold text-purple hover:text-navy transition-colors"
            >
              Read the full methodology
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* Why our customers trust us */}
      <section className="py-20 bg-surface-muted">
        <div className="section-container">
          <div className="text-center mb-12 max-w-2xl mx-auto">
            <span className="eyebrow mb-3">Customer stories</span>
            <h2 className="font-bold text-navy mt-3">Why our customers trust us</h2>
            <div className="flex items-center justify-center gap-1 text-purple mt-4">
              {[...Array(5)].map((_, i) => (
                <Star key={i} className="w-5 h-5 fill-current" />
              ))}
              <span className="ml-2 text-sm text-ink-muted">
                Real West Midlands clients, in their own words
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

      <WhyChooseUsDemo />

      {/* Making legal choice clearer and faster */}
      <section className="relative py-24 overflow-hidden bg-gradient-footer text-white">
        <div aria-hidden className="absolute inset-0 decorative-lines opacity-20" />
        <div className="section-container relative">
          <div className="grid lg:grid-cols-2 gap-10 lg:gap-16 items-center">
            <div className="lg:order-2 relative rounded-3xl overflow-hidden aspect-[16/10] lg:aspect-[4/5] shadow-soft">
              <Image
                src="https://images.unsplash.com/photo-1581094794329-c8112a89af12?auto=format&fit=crop&w=1200&q=70"
                alt="A couple receiving the keys to their new home"
                fill
                className="object-cover"
                sizes="(min-width: 1024px) 50vw, 100vw"
                unoptimized
              />
              <div className="absolute inset-0 bg-navy/20" />
            </div>
            <div className="lg:order-1">
              <span className="eyebrow text-teal mb-3">Our methodology</span>
              <h2 className="font-bold mt-3 mb-5">
                Making legal choice clearer and faster
              </h2>
              <p className="text-white/80 leading-relaxed mb-4">
                Six factors, weighted to a hundred. Reputation and price share the heaviest weights,
                with complaints and regulatory history giving you the safety net that other
                comparison sites quietly skip.
              </p>
              <p className="text-white/80 leading-relaxed mb-6">
                Pick a different priority (say, price first or regulatory record first) and the
                weights rescale around it. No black-box AI, no surprise fees, no pay-to-rank.
              </p>
              <Link
                href="/how-it-works#ranking"
                className="inline-flex items-center gap-2 font-semibold text-teal hover:text-white transition-colors"
              >
                See the methodology
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Legal knowledge that empowers you */}
      <section className="py-20 bg-white">
        <div className="section-container">
          <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between mb-10 gap-4">
            <div>
              <span className="eyebrow mb-3">Knowledge hub</span>
              <h2 className="font-bold text-navy mt-3">Legal knowledge that empowers you</h2>
            </div>
            <Link
              href="#"
              className="inline-flex items-center gap-2 font-semibold text-purple hover:text-navy transition-colors"
            >
              Browse all articles
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {articles.map((a) => (
              <Link
                key={a.title}
                href="#"
                className="card overflow-hidden flex flex-col hover:-translate-y-1 transition-transform"
              >
                <div className="relative aspect-[16/10]">
                  <Image
                    src={a.image}
                    alt=""
                    fill
                    className="object-cover"
                    sizes="(min-width: 768px) 33vw, 100vw"
                    unoptimized
                  />
                  <span className="absolute left-4 top-4 chip text-xs">{a.tag}</span>
                </div>
                <div className="p-6 flex flex-col gap-3 flex-1">
                  <h3 className="text-h5 md:text-h5-md font-bold text-navy leading-snug">
                    {a.title}
                  </h3>
                  <p className="text-sm text-ink-muted mt-auto">{a.meta}</p>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* FAQs */}
      <section id="faqs" className="py-20 bg-surface-muted scroll-mt-24">
        <div className="section-container max-w-3xl">
          <div className="text-center mb-12">
            <span className="eyebrow mb-3">FAQs</span>
            <h2 className="font-bold text-navy mt-3">Frequently asked questions</h2>
          </div>
          <div className="space-y-3">
            {faqs.map(({ q, a }) => (
              <details key={q} className="card px-6 py-5 group">
                <summary className="font-semibold text-navy cursor-pointer list-none flex justify-between items-center gap-4">
                  {q}
                  <span className="text-purple group-open:rotate-45 transition-transform text-2xl leading-none">
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
              className="absolute inset-0 opacity-50 [background-image:radial-gradient(ellipse_at_top_left,rgba(151,71,255,0.7),transparent_55%),radial-gradient(ellipse_at_bottom_right,rgba(10,229,246,0.3),transparent_50%)]"
            />
            <div aria-hidden className="absolute inset-0 decorative-lines opacity-20" />
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
