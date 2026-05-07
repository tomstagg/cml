import type { Metadata } from "next";

export const metadata: Metadata = { title: "Terms of Service" };

export default function TermsPage() {
  return (
    <div className="py-16">
      <div className="section-container max-w-3xl mx-auto prose prose-gray">
        <h1>Terms of Service</h1>
        <p className="lead">Last updated: May 2026</p>

        <h2>1. Acceptance of terms</h2>
        <p>By using Choose My Lawyer, you agree to these terms. If you do not agree, please do not use our platform.</p>

        <h2>2. The service</h2>
        <p>Choose My Lawyer is an independent comparison platform for residential conveyancing across the West Midlands Combined Authority. We do not provide legal advice. We connect consumers with SRA-authorised solicitor firms via Proceed (instructing one firm) or Callback (up to five firms).</p>

        <h2>3. Quotes</h2>
        <p>Quotes displayed are calculated from each firm's published price card against the matter details you provide. Final fees are agreed between you and the solicitor firm directly. Excluded disbursements (Stamp Duty, leasehold notice fees, ground rent apportionment, indemnity policies, lender-specific fees) are flagged separately and are not included in the comparable Total Effective Price.</p>

        <h2>4. No guarantee of service</h2>
        <p>We do not guarantee that any firm will accept your Proceed or Callback request. Firms may decline at their discretion (for example, on conflict-of-interest grounds).</p>

        <h2>5. Consumer responsibilities</h2>
        <p>You must provide accurate information in the chat flow. Inaccurate information may result in incorrect quotes or rankings.</p>

        <h2>6. Firm responsibilities</h2>
        <p>Enrolled firms must keep their conveyancing pricing current and respond to Proceed and Callback introductions promptly.</p>

        <h2>7. Limitation of liability</h2>
        <p>Choose My Lawyer is not liable for the quality of legal services provided by listed firms. Our liability is limited to the amount you paid us (which is zero for consumers).</p>

        <h2>8. Governing law</h2>
        <p>These terms are governed by the laws of England and Wales.</p>

        <h2>9. Contact</h2>
        <p>Questions? Email <a href="mailto:legal@choosemylawyer.co.uk">legal@choosemylawyer.co.uk</a>.</p>
      </div>
    </div>
  );
}
