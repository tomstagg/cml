import type { Metadata } from "next";

export const metadata: Metadata = { title: "Privacy Policy" };

export default function PrivacyPage() {
  return (
    <div className="py-16">
      <div className="section-container max-w-3xl mx-auto prose prose-gray">
        <h1>Privacy Policy</h1>
        <p className="lead">Last updated: May 2026</p>

        <h2>1. Who we are</h2>
        <p>
          Choose My Lawyer (&quot;we&quot;, &quot;us&quot;, &quot;our&quot;) operates choosemylawyer.co.uk, an
          independent legal comparison platform. During the pilot we cover residential conveyancing
          across the West Midlands Combined Authority (Birmingham, Coventry, Dudley, Wolverhampton,
          and Walsall).
        </p>

        <h2>2. What data we collect</h2>
        <p>We collect the following personal data:</p>
        <ul>
          <li>
            <strong>Chat session data:</strong> Your answers about the property matter (purchase
            price, tenure, postcode, mortgage status, and similar conveyancing details)
          </li>
          <li>
            <strong>Contact details:</strong> Name, email, and phone number when you Proceed with a
            firm or request a callback
          </li>
          <li>
            <strong>Firm user data:</strong> Email and hashed password for solicitor firm accounts
          </li>
          <li>
            <strong>Review data:</strong> Your name and review text if you submit a review
          </li>
          <li>
            <strong>Analytics data:</strong> Funnel and conversion events captured via Meta Pixel and
            our backend analytics log
          </li>
        </ul>

        <h2>3. How we use your data</h2>
        <ul>
          <li>To provide the comparison service and calculate quotes</li>
          <li>To forward Proceed and Callback introductions to solicitor firms in your name</li>
          <li>To send follow-up emails confirming whether the firm has been in touch</li>
          <li>To send a feedback request two months after a Proceed action</li>
          <li>To improve our platform</li>
        </ul>

        <h2>4. Your rights</h2>
        <p>
          Under UK GDPR, you have the right to access, correct, or delete your data. Contact us at{" "}
          <a href="mailto:privacy@choosemylawyer.co.uk">privacy@choosemylawyer.co.uk</a>.
        </p>

        <h2>5. Data retention</h2>
        <p>Chat sessions are deleted after 30 days. Proceed and Callback records are retained for 7 years.</p>

        <h2>6. Third parties</h2>
        <p>
          We share your matter details with the solicitor firm(s) you select via Proceed or
          Callback. We use Google Places API for firm reviews, Fetchify for postcode lookup, Meta
          Pixel for marketing analytics, and Sparkpost for transactional emails.
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
