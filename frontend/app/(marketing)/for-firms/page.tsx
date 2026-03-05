import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, BarChart2, Bell, CheckCircle, Star, Users } from "lucide-react";

export const metadata: Metadata = {
  title: "For Law Firms",
  description: "Join Choose My Lawyer and connect with clients actively looking for probate solicitors.",
};

const benefits = [
  {
    icon: Users,
    title: "Qualified client leads",
    description: "Every appointment comes from a consumer who has already answered questions about their estate and accepted your quote.",
  },
  {
    icon: Star,
    title: "Build your reputation",
    description: "Collect verified reviews from real clients. Respond to feedback and showcase your expertise.",
  },
  {
    icon: BarChart2,
    title: "Transparent pricing",
    description: "You set your own pricing. We calculate quotes automatically from your price card — no surprises.",
  },
  {
    icon: Bell,
    title: "Instant notifications",
    description: "Receive email alerts the moment a client requests an appointment or callback with your firm.",
  },
];

export default function ForFirmsPage() {
  return (
    <div className="py-16">
      {/* Hero */}
      <section className="bg-gradient-to-br from-brand-950 to-brand-800 text-white py-20 -mt-0">
        <div className="section-container text-center">
          <h1 className="text-4xl sm:text-5xl font-bold mb-6">
            Reach clients looking for probate solicitors
          </h1>
          <p className="text-xl text-brand-100 mb-8 max-w-2xl mx-auto">
            Choose My Lawyer connects SRA-authorised firms with consumers who are actively comparing
            probate solicitors. Join free during our launch period.
          </p>
          <p className="text-brand-300 mb-2">Interested? Contact us to register your firm.</p>
          <Link href="/contact" className="btn-secondary border-brand-700 text-brand-100 hover:bg-brand-800">
            Get In Touch
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </section>

      <div className="section-container py-16">
        {/* Benefits */}
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Why list with us?</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mb-16">
          {benefits.map((b) => (
            <div key={b.title} className="card p-6 flex gap-4">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-brand-50 flex items-center justify-center">
                <b.icon className="w-5 h-5 text-brand-600" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900 mb-1">{b.title}</h3>
                <p className="text-gray-600 text-sm">{b.description}</p>
              </div>
            </div>
          ))}
        </div>

        {/* How enrollment works */}
        <h2 className="text-2xl font-bold text-gray-900 mb-8">How enrollment works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {[
            { step: "1", title: "We invite you", desc: "Our team sends you a personalised enrollment link." },
            { step: "2", title: "Create your profile", desc: "Enter your firm details and set your probate pricing structure." },
            { step: "3", title: "Start appearing in results", desc: "Enrolled firms appear in the top 5 results with action buttons." },
          ].map((s) => (
            <div key={s.step} className="text-center">
              <div className="text-5xl font-bold text-brand-100 mb-3">{s.step}</div>
              <h3 className="font-semibold text-gray-900 mb-2">{s.title}</h3>
              <p className="text-gray-600 text-sm">{s.desc}</p>
            </div>
          ))}
        </div>

        {/* Pricing */}
        <div className="card p-8 text-center bg-brand-50 border-brand-100">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Simple pricing</h2>
          <p className="text-gray-600 mb-2">
            <strong>Free to join</strong> during our launch period.
          </p>
          <p className="text-gray-600 mb-6">
            A referral fee of <strong>£125 + VAT</strong> will apply per successful appointment in future — we'll give you 30 days' notice before this starts.
          </p>
          <div className="flex justify-center gap-3 flex-wrap">
            {["No monthly fee", "No setup cost", "No obligation"].map((item) => (
              <span key={item} className="flex items-center gap-1.5 text-brand-700 font-medium">
                <CheckCircle className="w-4 h-4" /> {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
