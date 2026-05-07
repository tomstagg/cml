import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, CheckCircle, Home, MapPin, ScrollText } from "lucide-react";

export const metadata: Metadata = {
  title: "Find a Conveyancing Solicitor in the West Midlands",
  description:
    "Compare residential conveyancing solicitors across Birmingham, Coventry, Dudley, Wolverhampton and Walsall. Independent ranking with transparent quotes.",
  keywords:
    "conveyancing solicitor, conveyancing quotes, residential conveyancing, west midlands conveyancer, birmingham conveyancing, leasehold conveyancing",
};

const wmcaAreas = [
  { name: "Birmingham", postcodes: "B postcodes" },
  { name: "Coventry", postcodes: "CV postcodes" },
  { name: "Dudley", postcodes: "DY postcodes" },
  { name: "Wolverhampton", postcodes: "WV postcodes" },
  { name: "Walsall", postcodes: "WS postcodes" },
];

const matterTypes = [
  "Purchase",
  "Sale",
  "Purchase and sale",
  "Remortgage",
  "Leasehold",
  "Freehold",
  "New build",
  "Help to Buy ISA",
  "Shared ownership",
];

export default function ConveyancingLandingPage() {
  return (
    <>
      <section className="bg-gradient-hero text-white">
        <div className="section-container py-20">
          <div className="max-w-3xl">
            <p className="text-sm uppercase tracking-wide text-white/80 mb-3">
              Residential conveyancing · West Midlands
            </p>
            <h1 className="font-bold mb-5">
              Find a conveyancing solicitor in the West Midlands
            </h1>
            <p className="text-lg text-white/85 mb-8">
              Compare regulated conveyancers on price, reputation, complaints, regulation, distance
              and number of offices. Quotes calculated against your specific matter — leasehold
              supplements, mortgage handling, and standard disbursements all included.
            </p>
            <Link href="/chat" className="btn-secondary bg-white text-navy border-transparent">
              Compare conveyancing quotes
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container max-w-4xl">
          <h2 className="font-bold text-navy mb-4">What is residential conveyancing?</h2>
          <p className="text-ink-muted mb-4 leading-relaxed">
            Conveyancing is the legal process of transferring ownership of a property from one
            party to another. Whether you're buying, selling, or remortgaging, a conveyancer (a
            specialist solicitor or licensed conveyancer) handles the searches, contracts, Land
            Registry filings, and transfer of funds on your behalf.
          </p>
          <p className="text-ink-muted leading-relaxed">
            For a typical purchase, your conveyancer will run local-authority, drainage,
            environmental, and bankruptcy searches; review the contract pack from the seller's
            solicitor; raise enquiries; coordinate with your mortgage lender; and lodge the
            registration with HM Land Registry.
          </p>
        </div>
      </section>

      <section className="py-20 bg-surface-muted">
        <div className="section-container max-w-5xl">
          <h2 className="font-bold text-navy mb-3">What does a conveyancing quote include?</h2>
          <p className="text-ink-muted mb-8 max-w-3xl">
            CML quotes show the Total Effective Price — the comparable, like-for-like figure across
            firms. It's calculated from each firm's published price card against your matter.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="card p-7">
              <h3 className="font-bold text-navy mb-3">Included in your quote</h3>
              <ul className="space-y-2 text-sm text-ink-muted">
                {[
                  "Legal fees (banded by purchase price)",
                  "VAT on legal fees (where applicable)",
                  "Local-authority search",
                  "Drainage & water search",
                  "Environmental search",
                  "Bankruptcy search",
                  "Land Registry priority search",
                  "Land Registry registration fee",
                  "Adjustments (leasehold, new build, mortgage handling, HtB ISA, shared ownership)",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <CheckCircle className="w-4 h-4 text-purple flex-shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="card p-7">
              <h3 className="font-bold text-navy mb-3">Excluded — flagged separately</h3>
              <p className="text-sm text-ink-muted mb-3">
                Some costs depend on the property and aren't determinable at intake. We flag them
                clearly so you know what's coming:
              </p>
              <ul className="space-y-2 text-sm text-ink-muted">
                {[
                  "Stamp Duty Land Tax",
                  "Leasehold notice fees",
                  "Ground rent apportionment",
                  "Indemnity policies",
                  "Lender-specific fees",
                ].map((item) => (
                  <li key={item} className="flex items-start gap-2">
                    <ScrollText className="w-4 h-4 text-ink-muted flex-shrink-0 mt-0.5" />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="section-container max-w-4xl">
          <h2 className="font-bold text-navy mb-3">Areas we cover</h2>
          <p className="text-ink-muted mb-8">
            We currently compare conveyancers serving the West Midlands Combined Authority — the
            five postcode areas below.
          </p>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {wmcaAreas.map((area) => (
              <div key={area.name} className="card p-5 text-center">
                <MapPin className="w-5 h-5 text-purple mx-auto mb-2" />
                <p className="font-semibold text-navy text-sm">{area.name}</p>
                <p className="text-xs text-ink-muted mt-1">{area.postcodes}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-surface-muted">
        <div className="section-container max-w-4xl">
          <h2 className="font-bold text-navy mb-3">Matters we cover</h2>
          <p className="text-ink-muted mb-8">
            From a straightforward freehold purchase to a leasehold sale with a Help to Buy ISA —
            CML handles the variations.
          </p>
          <div className="flex flex-wrap gap-3">
            {matterTypes.map((m) => (
              <span
                key={m}
                className="inline-flex items-center gap-1.5 rounded-full bg-white border border-gray-200 px-4 py-2 text-sm font-medium text-navy"
              >
                <Home className="w-3.5 h-3.5 text-purple" />
                {m}
              </span>
            ))}
          </div>
        </div>
      </section>

      <section className="py-16 bg-white">
        <div className="section-container">
          <div className="rounded-3xl bg-gradient-hero p-10 md:p-14 text-white shadow-soft text-center">
            <h2 className="font-bold mb-3">Ready to compare?</h2>
            <p className="text-white/85 mb-7 max-w-xl mx-auto">
              Get conveyancing quotes from regulated West Midlands solicitors in under three
              minutes. Free, no obligation.
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
