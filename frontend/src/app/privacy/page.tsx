'use client';

import React from 'react';
import Link from 'next/link';

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link
            href="/"
            className="text-blue-600 hover:text-blue-800 mb-4 inline-block"
          >
            ← Back to Home
          </Link>
          <h1 className="text-4xl font-bold text-gray-900 mb-2">
            Privacy Policy
          </h1>
          <p className="text-gray-600">
            Last Updated: {new Date().toLocaleDateString()}
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-md p-8 space-y-6">
          {/* Introduction */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Introduction
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Legal AI System ("we", "our", or "us") is committed to protecting your privacy.
              This Privacy Policy explains how we collect, use, disclose, and safeguard your
              information when you use our service. Please read this policy carefully.
            </p>
          </section>

          {/* Information We Collect */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              1. Information We Collect
            </h2>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">
              Personal Information
            </h3>
            <p className="text-gray-700 leading-relaxed mb-3">
              We may collect personal information that you provide directly to us, including:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Name and contact information (email address, phone number)</li>
              <li>Account credentials (username, password)</li>
              <li>Profile information</li>
              <li>Payment information (processed securely through third-party providers)</li>
              <li>Communication preferences</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              Document and Case Information
            </h3>
            <p className="text-gray-700 leading-relaxed mb-3">
              When you use our services, we collect:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Documents you upload for analysis</li>
              <li>Case information and legal research queries</li>
              <li>AI-generated analysis and insights</li>
              <li>Usage patterns and preferences</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              Technical Information
            </h3>
            <p className="text-gray-700 leading-relaxed mb-3">
              We automatically collect certain technical information:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>IP address and device information</li>
              <li>Browser type and version</li>
              <li>Operating system</li>
              <li>Access times and referring website addresses</li>
              <li>Usage data and analytics</li>
            </ul>
          </section>

          {/* How We Use Your Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              2. How We Use Your Information
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We use the information we collect to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Provide, maintain, and improve our services</li>
              <li>Process and analyze documents using AI technology</li>
              <li>Authenticate users and secure accounts</li>
              <li>Communicate with you about your account and our services</li>
              <li>Comply with legal obligations and protect legal rights</li>
              <li>Detect, prevent, and address technical issues and security threats</li>
              <li>Develop new features and improve user experience</li>
              <li>Send administrative information and service updates</li>
            </ul>
          </section>

          {/* Data Security */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              3. Data Security
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We implement appropriate technical and organizational security measures to protect
              your information:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Encryption of data in transit and at rest</li>
              <li>Secure authentication mechanisms</li>
              <li>Regular security audits and assessments</li>
              <li>Access controls and authorization systems</li>
              <li>Secure backup and disaster recovery procedures</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              However, no method of transmission over the Internet or electronic storage is 100%
              secure. While we strive to use commercially acceptable means to protect your
              information, we cannot guarantee absolute security.
            </p>
          </section>

          {/* AI and Third-Party Services */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              4. AI and Third-Party Services
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              Our service uses artificial intelligence from third-party providers (OpenAI, Anthropic)
              to analyze documents and generate insights. When you use our AI features:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Your documents may be processed by these AI service providers</li>
              <li>We take measures to anonymize and protect sensitive information</li>
              <li>These providers have their own privacy policies and data handling practices</li>
              <li>We recommend not uploading highly sensitive or confidential information</li>
            </ul>
          </section>

          {/* Data Retention */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              5. Data Retention
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We retain your information for as long as necessary to provide our services and
              comply with legal obligations. You may request deletion of your data at any time,
              subject to legal retention requirements. Documents and analysis results are retained
              according to your account settings and legal requirements.
            </p>
          </section>

          {/* Your Rights */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              6. Your Privacy Rights
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              Depending on your location, you may have certain rights regarding your personal
              information:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li><strong>Access:</strong> Request a copy of your personal information</li>
              <li><strong>Correction:</strong> Request correction of inaccurate information</li>
              <li><strong>Deletion:</strong> Request deletion of your information</li>
              <li><strong>Portability:</strong> Request transfer of your data</li>
              <li><strong>Objection:</strong> Object to certain processing of your data</li>
              <li><strong>Withdraw Consent:</strong> Withdraw previously given consent</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              To exercise these rights, please contact us using the information provided below.
            </p>
          </section>

          {/* GDPR and CCPA Compliance */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              7. GDPR and CCPA Compliance
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              For users in the European Union and California, we comply with GDPR and CCPA
              requirements:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Lawful basis for data processing</li>
              <li>Right to access and deletion</li>
              <li>Data portability rights</li>
              <li>Opt-out of data sales (we do not sell personal data)</li>
              <li>Non-discrimination for exercising privacy rights</li>
            </ul>
          </section>

          {/* Cookies and Tracking */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              8. Cookies and Tracking Technologies
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We use cookies and similar tracking technologies to track activity on our service
              and hold certain information. You can instruct your browser to refuse all cookies
              or indicate when a cookie is being sent. However, some parts of our service may
              not function properly without cookies.
            </p>
          </section>

          {/* Children's Privacy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              9. Children's Privacy
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Our service is not intended for individuals under the age of 18. We do not
              knowingly collect personal information from children. If you become aware that
              a child has provided us with personal information, please contact us immediately.
            </p>
          </section>

          {/* Changes to Privacy Policy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              10. Changes to This Privacy Policy
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We may update our Privacy Policy from time to time. We will notify you of any
              changes by posting the new Privacy Policy on this page and updating the "Last
              Updated" date. You are advised to review this Privacy Policy periodically for
              any changes.
            </p>
          </section>

          {/* Contact Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              11. Contact Us
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              If you have questions about this Privacy Policy or want to exercise your privacy
              rights, please contact us:
            </p>
            <div className="text-gray-700 space-y-1">
              <p>
                Email: <a href="mailto:privacy@legalaisystem.com" className="text-blue-600 hover:underline">
                  privacy@legalaisystem.com
                </a>
              </p>
              <p>
                Data Protection Officer: <a href="mailto:dpo@legalaisystem.com" className="text-blue-600 hover:underline">
                  dpo@legalaisystem.com
                </a>
              </p>
            </div>
          </section>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-center space-x-6 text-sm">
          <Link href="/terms" className="text-blue-600 hover:text-blue-800">
            Terms of Service
          </Link>
          <Link href="/acceptable-use" className="text-blue-600 hover:text-blue-800">
            Acceptable Use Policy
          </Link>
        </div>
      </div>
    </div>
  );
}
