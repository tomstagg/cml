import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <div className="py-16">
      <div className="section-container max-w-3xl mx-auto prose prose-gray">
        <h1>Privacy Policy</h1>
        <p className="lead">Last updated: March 2026</p>

        <h2>1. Who we are</h2>
        <p>
          Choose My Lawyer (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) operates choosemylawyer.co.uk, a legal comparison
          platform for England and Wales.
        </p>

        <h2>2. What data we collect</h2>
        <p>We collect the following personal data:</p>
        <ul>
          <li>
            <strong>Chat session data:</strong> Your answers to questions about the estate (no names,
            postcode only)
          </li>
          <li>
            <strong>Contact details:</strong> Name, email, and phone number when you submit an
            appointment or callback request
          </li>
          <li>
            <strong>Firm user data:</strong> Email and hashed password for solicitor firm accounts
          </li>
          <li>
            <strong>Review data:</strong> Your name and review text if you submit a review
          </li>
        </ul>

        <h2>3. How we use your data</h2>
        <ul>
          <li>To provide the comparison service and calculate quotes</li>
          <li>To forward appointment/callback requests to solicitor firms</li>
          <li>To send review invitations after your appointment</li>
          <li>To improve our platform</li>
        </ul>

        <h2>4. Your rights</h2>
        <p>
          Under UK GDPR, you have the right to access, correct, or delete your data. Contact us at{" "}
          <a href="mailto:privacy@choosemylawyer.co.uk">privacy@choosemylawyer.co.uk</a>.
        </p>

        <h2>5. Data retention</h2>
        <p>Chat sessions are deleted after 30 days. Appointment records are retained for 7 years.</p>

        <h2>6. Third parties</h2>
        <p>
          We share your appointment details with the solicitor firm you select. We use Google Places
          API for firm reviews and Sparkpost for transactional emails.
        </p>

        <h2>7. Cookies</h2>
        <p>
          We use essential cookies only. See our{" "}
          <a href="/cookies">Cookie Policy</a> for details.
        </p>
      </div>
    </div>
  );
}
