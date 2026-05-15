import { ArrowRight, Star } from "lucide-react";
import Link from "next/link";

const mockFirms = [
  {
    rank: 1,
    name: "Whitfield & Hart",
    area: "Birmingham · B15",
    price: 985,
    score: 92,
    gradient: "from-purple to-teal",
  },
  {
    rank: 2,
    name: "Caldwell Lyon",
    area: "Coventry · CV1",
    price: 1095,
    score: 88,
    gradient: "from-teal to-mint",
  },
  {
    rank: 3,
    name: "Greenhalgh Legal",
    area: "Wolverhampton · WV1",
    price: 1145,
    score: 84,
    gradient: "from-mint to-purple",
  },
];

export function WhyChooseUsDemo() {
  return (
    <section className="py-24 bg-white">
      <div className="section-container">
        <div className="grid lg:grid-cols-12 gap-12 lg:gap-16 items-center">
          <div className="lg:col-span-5">
            <span className="eyebrow mb-3">See it in action</span>
            <h2 className="font-bold text-navy mt-3 mb-5">
              Instant solicitor comparison
            </h2>
            <p className="text-ink-muted leading-relaxed mb-4">
              Every SRA-authorised conveyancing firm in your area, ranked side-by-side
              on price, reputation, complaints history, regulatory record, distance and
              number of offices. Same inputs, same ranking, every time.
            </p>
            <p className="text-ink-muted leading-relaxed mb-6">
              Pick a firm and we&rsquo;ll introduce you in your own name — no cold leads,
              no hard sell, no pay-to-rank.
            </p>
            <Link
              href="/chat"
              className="inline-flex items-center gap-2 font-semibold text-purple hover:text-navy transition-colors"
            >
              Try the comparison
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          <div className="lg:col-span-7 relative">
            <div className="relative rounded-3xl shadow-soft border border-gray-200 bg-gradient-to-br from-white to-surface-muted p-6 sm:p-8 overflow-hidden">
              <div className="flex items-center justify-between mb-5 gap-3">
                <div>
                  <p className="text-[11px] uppercase tracking-[0.18em] text-purple font-semibold">
                    5 results
                  </p>
                  <p className="text-sm text-ink-muted mt-1">
                    £350,000 purchase · Birmingham B15 · Freehold
                  </p>
                </div>
                <span className="inline-flex items-center gap-1 rounded-full bg-mint/20 text-navy text-xs font-semibold px-3 py-1.5 border border-mint/40 whitespace-nowrap">
                  Whole-of-market
                </span>
              </div>

              <ul className="space-y-3 relative">
                {mockFirms.map((f, i) => (
                  <li
                    key={f.rank}
                    className={`demo-row demo-row-${i} relative flex items-center gap-4 rounded-2xl bg-white border border-gray-200 p-4`}
                  >
                    <div
                      className={`w-10 h-10 rounded-xl bg-gradient-to-br ${f.gradient} flex items-center justify-center text-white font-bold flex-shrink-0`}
                    >
                      {f.rank}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-navy truncate">{f.name}</p>
                      <p className="text-xs text-ink-muted">{f.area}</p>
                    </div>
                    <div className="hidden sm:flex items-center gap-0.5 text-purple">
                      {[...Array(5)].map((_, j) => (
                        <Star key={j} className="w-3 h-3 fill-current" />
                      ))}
                    </div>
                    <div className="text-right flex-shrink-0">
                      <p className="text-sm font-bold text-navy">
                        £{f.price.toLocaleString()}
                      </p>
                      <p className="text-xs text-ink-muted">Score {f.score}</p>
                    </div>
                  </li>
                ))}
              </ul>

              <span aria-hidden className="demo-cursor pointer-events-none absolute" />
            </div>

            <div
              aria-hidden
              className="hidden md:flex absolute -left-4 top-6 items-center gap-1.5 rounded-full bg-white shadow-soft border border-gray-200 px-3 py-1.5 text-xs font-semibold text-navy"
            >
              Sorted by score
            </div>
            <div
              aria-hidden
              className="hidden md:flex absolute -right-3 -bottom-4 items-center gap-1.5 rounded-full bg-navy text-white px-3 py-1.5 text-xs font-semibold"
            >
              Click to proceed
              <ArrowRight className="w-3 h-3" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
