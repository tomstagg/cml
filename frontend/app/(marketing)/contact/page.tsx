import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Contact Us",
  description: "Get in touch with the Choose My Lawyer team.",
};

export default function ContactPage() {
  return (
    <div className="py-16">
      <div className="section-container max-w-2xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Contact Us</h1>
        <p className="text-gray-600 mb-8">
          Have a question? We'd love to hear from you. Send us a message and we'll respond as soon
          as possible.
        </p>

        <div className="card p-8">
          <div className="space-y-6">
            <div>
              <label className="label" htmlFor="name">
                Full Name
              </label>
              <input id="name" className="input" type="text" placeholder="Your name" />
            </div>
            <div>
              <label className="label" htmlFor="email">
                Email Address
              </label>
              <input id="email" className="input" type="email" placeholder="you@example.com" />
            </div>
            <div>
              <label className="label" htmlFor="subject">
                Subject
              </label>
              <input id="subject" className="input" type="text" placeholder="How can we help?" />
            </div>
            <div>
              <label className="label" htmlFor="message">
                Message
              </label>
              <textarea
                id="message"
                className="input min-h-[120px] resize-none"
                placeholder="Tell us more..."
              />
            </div>
            <button className="btn-primary w-full">Send Message</button>
          </div>
        </div>

        <div className="mt-8 text-gray-600 text-sm">
          <p>
            <strong>Email:</strong>{" "}
            <a href="mailto:hello@choosemylawyer.co.uk" className="text-brand-600 hover:underline">
              hello@choosemylawyer.co.uk
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
