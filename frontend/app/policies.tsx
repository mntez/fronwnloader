"use client";

import { siteConfig } from "../lib/site-config";

function Contact() {
  return (
    <a href={`mailto:${siteConfig.contactEmail}`}>{siteConfig.contactEmail}</a>
  );
}

export default function Policies() {
  return (
    <div className="policy-documents">
      <article className="policy-document" id="terms" aria-labelledby="terms-title">
        <p className="policy-updated">Last updated: {siteConfig.lastUpdated}</p>
        <h2 id="terms-title">Terms of Service</h2>
        <p>
          These Terms explain the rules for using {siteConfig.name} at {siteConfig.domain} (the “Service”).
          By using the Service, you agree to these Terms. If you do not agree, do not use it.
        </p>

        <h3>1. Who operates the Service</h3>
        <p>
          The Service is operated by {siteConfig.operator}, based in {siteConfig.country} (“we,” “us,” or “our”).
          Contact: <Contact />.
        </p>

        <h3>2. What the Service does</h3>
        <p>
          The Service processes video links submitted by users and may create temporary copies so users can
          download content they are legally entitled to save. We do not own or upload the source videos and do
          not offer them as a public video library. Availability depends on the source platform and the link.
        </p>

        <h3>3. Eligibility</h3>
        <p>You must be at least {siteConfig.minimumAge} years old to use the Service. By using it, you confirm that you meet this requirement.</p>

        <h3>4. Acceptable use</h3>
        <p>You must not use the Service to:</p>
        <ul>
          <li>Download copyrighted material without permission or another valid legal basis.</li>
          <li>Infringe intellectual property, privacy, publicity, or other rights.</li>
          <li>Violate a video platform’s terms, access controls, or other rules.</li>
          <li>Download illegal content, including child sexual abuse material, terrorist content, or content that incites violence.</li>
          <li>Scrape or make automated bulk requests, bypass limits, attack the Service, or overload its systems.</li>
          <li>Resell, sublicense, or redistribute the Service without our written permission.</li>
        </ul>

        <h3>5. Your responsibility</h3>
        <p>
          You are responsible for the links you submit, the material you download, and how you use it. You must
          have the rights and permissions required by applicable law and the source platform’s terms. We do not
          decide whether your use of a particular video is lawful.
        </p>

        <h3>6. Intellectual property</h3>
        <p>
          The source platforms and their users retain rights to third-party videos and related material. We do
          not claim ownership of that content. The Service’s own code, design, and branding belong to their
          respective owners and may not be copied or reused without permission, except where the law allows.
        </p>

        <h3>7. Copyright and takedown notices</h3>
        <p>
          Send copyright or other rights complaints to <Contact /> with the subject “Rights notice.” Include
          your name and contact details; identify the protected work; provide the exact URL at issue; explain
          your ownership or authority to act; and describe why you believe the use is unauthorized. If you are
          submitting a notice under the United States DMCA, include the statements and signature required by
          that law, including a good-faith belief statement and an accuracy and authority statement under
          penalty of perjury. Do not include sensitive personal information that is not needed to assess your
          notice.
        </p>
        <p>
          We may review notices, block links, restrict access, or terminate repeat infringers where appropriate.
          The Service does not host a public collection of source videos, so identify the specific Service URL
          or processing activity you are reporting.
        </p>

        <h3>8. Third-party platforms and links</h3>
        <p>
          The Service is independent and is not affiliated with, endorsed by, or sponsored by YouTube, Facebook,
          Instagram, TikTok, Discord, Pinterest, Reddit, Threads, X, or other source platforms. Their names and
          marks belong to their respective owners. We do not control third-party sites or services.
        </p>

        <h3>9. Availability and changes</h3>
        <p>
          The Service is provided “as is” and “as available.” A link may fail, formats may change, and a platform
          may restrict access. We may change, limit, suspend, or discontinue any part of the Service at any time.
        </p>

        <h3>10. Disclaimer of warranties</h3>
        <p>
          To the extent permitted by law, we disclaim implied warranties, including merchantability, fitness for
          a particular purpose, non-infringement, accuracy, and uninterrupted availability. Nothing in these
          Terms excludes a warranty or right that cannot legally be excluded.
        </p>

        <h3>11. Limitation of liability</h3>
        <p>
          To the extent permitted by law, we are not liable for indirect, incidental, special, consequential, or
          punitive losses, lost profits or data, or losses arising from third-party platforms, your downloads,
          or inability to use the Service. Where liability cannot be excluded, it is limited to the amount
          permitted by applicable law. These Terms do not limit liability that the law does not allow us to limit.
        </p>

        <h3>12. Indemnification</h3>
        <p>
          To the extent permitted by law, you agree to cover reasonable claims and costs arising from your
          unlawful use of the Service or your breach of these Terms, including infringement of another person’s
          rights. We will give you notice of a claim when reasonably possible.
        </p>

        <h3>13. Suspension and termination</h3>
        <p>
          We may limit or end your access, block a URL or IP address, or remove temporary files if we reasonably
          believe this is needed to protect the Service, comply with law, address abuse, or enforce these Terms.
        </p>

        <h3>14. Changes to these Terms</h3>
        <p>
          We may update these Terms. We will post the new version here and change the “Last updated” date. If a
          change is material, we will provide a notice through the Service where reasonably practical. Continued
          use after an update means you accept the revised Terms.
        </p>

        <h3>15. Governing law and disputes</h3>
        <p>
          These Terms are governed by the law of {siteConfig.governingLaw}, without regard to conflict-of-law
          rules. Disputes will be handled by the courts with jurisdiction in {siteConfig.governingLaw}, subject
          to any mandatory rights you have under local law.
        </p>

        <h3>16. Contact</h3>
        <p>Questions or notices about these Terms: <Contact />.</p>
        <p className="policy-back"><a href="#home">Back to home ↑</a></p>
      </article>

      <article className="policy-document" id="privacy" aria-labelledby="privacy-title">
        <p className="policy-updated">Last updated: {siteConfig.lastUpdated}</p>
        <h2 id="privacy-title">Privacy Policy</h2>
        <p>
          This Policy explains how {siteConfig.operator} (“we,” “us,” or “our”) handles information when you
          use {siteConfig.name} at {siteConfig.domain}. We do not sell personal data.
        </p>

        <h3>1. Who we are and how to contact us</h3>
        <p>
          The Service is operated by {siteConfig.operator}, based in {siteConfig.country}. For privacy questions
          or requests, email <Contact />.
        </p>

        <h3>2. Information we handle</h3>
        <ul>
          <li><strong>Links you submit:</strong> video URLs are sent to our service to inspect the link and prepare the requested download.</li>
          <li><strong>Messages:</strong> if you contact us, we receive the email address and information you include.</li>
          <li><strong>Technical and security data:</strong> the service uses a client IP address temporarily in memory to apply request limits. Hosting or infrastructure providers may also record IP address, browser/device details, timestamps, request and error logs. Their specific fields and retention period are <strong>{siteConfig.hostingIpRetention}</strong>.</li>
          <li><strong>Cookies and similar technologies:</strong> cookies are used. The names, purposes, durations, and essential or optional status are <strong>{siteConfig.cookieDetails}</strong>. Review and complete this item before launch.</li>
        </ul>

        <h3>3. How we use information</h3>
        <p>
          We use information to operate the requested video-link processing, deliver downloads, keep the Service
          secure, prevent abuse, apply rate limits, troubleshoot errors, respond to messages, and meet legal
          obligations. We do not use analytics, serve ads, or process payments through the Service.
        </p>

        <h3>4. Legal bases where GDPR applies</h3>
        <p>
          Where GDPR applies, we rely on performance of a service you request (processing links), legitimate
          interests (security, abuse prevention, and service reliability), legal obligations where relevant,
          and consent for optional cookies or other processing when required. You may withdraw consent at any
          time; this does not affect processing that occurred before withdrawal.
        </p>

        <h3>5. Retention</h3>
        <p>
          Downloaded files are temporary and are automatically deleted about one hour after a job completes.
          Temporary job information is held in service memory and expires as the job is cleaned up. Submitted
          URLs may remain in short-lived in-memory processing data for up to three minutes for format
          verification. The Service does not create user accounts. Hosting-provider log retention is not yet
          confirmed: {siteConfig.hostingIpRetention}.
        </p>

        <h3>6. Sharing and disclosure</h3>
        <p>
          We may share information with infrastructure and hosting providers that run the Service, with source
          platforms as needed to retrieve link metadata or media, or when disclosure is required by law or
          necessary to protect rights and safety. Provider names and locations should be added before launch:
          <strong> [HOSTING / INFRASTRUCTURE PROVIDERS AND COUNTRIES]</strong>. We do not sell personal data.
        </p>

        <h3>7. International transfers</h3>
        <p>
          Providers or source platforms may process information in countries outside your own. The countries
          and safeguards for those transfers depend on the providers selected and should be completed before
          launch: <strong>[PROVIDER COUNTRIES AND TRANSFER SAFEGUARDS]</strong>.
        </p>

        <h3>8. Security</h3>
        <p>
          We use HTTPS in production and restrict access to service systems as appropriate. No internet service
          or storage system is completely secure, so we cannot promise absolute security.
        </p>

        <h3>9. Your privacy rights</h3>
        <p>
          Depending on where you live and subject to applicable law, you may request access to, correction or
          deletion of personal information; object to or restrict certain processing; receive a portable copy;
          or withdraw consent. Email <Contact /> with your request and location. We may need to verify your
          identity and will respond as required by law.
        </p>
        <p>
          <strong>EEA, UK, and similar rights:</strong> where applicable, you may also complain to your local
          data-protection authority. <strong>California (CCPA/CPRA):</strong> California residents may have
          rights to know, access, correct, delete, and obtain information about disclosures, and to opt out of
          sale or sharing where applicable. We do not sell personal data. We will not discriminate against you
          for exercising applicable privacy rights.
        </p>

        <h3>10. Children’s privacy</h3>
        <p>
          The Service is for people aged {siteConfig.minimumAge} or older and is not intended for children. If
          you believe a child has provided personal information, contact us so we can review and take appropriate
          steps.
        </p>

        <h3>11. Third-party services and links</h3>
        <p>
          The Service processes links to third-party platforms. Those platforms have their own privacy terms
          and practices, which we do not control. Review their policies before using them.
        </p>

        <h3>12. Changes to this Policy</h3>
        <p>
          We may update this Policy and will post the revised version here with a new “Last updated” date. For
          material changes, we will provide a notice through the Service where reasonably practical.
        </p>

        <h3>13. Contact</h3>
        <p>Privacy requests and questions: <Contact />.</p>
        <p className="policy-back"><a href="#home">Back to home ↑</a></p>
      </article>
    </div>
  );
}
