'use client';

import React from 'react';
import Link from 'next/link';

export default function TermsOfServicePage() {
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
            Terms of Service
          </h1>
          <p className="text-gray-600">
            Last Updated: {new Date().toLocaleDateString()}
          </p>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-md p-8 space-y-6">
          {/* Educational Disclaimer */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Educational Purpose Disclaimer
            </h2>
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
              <p className="text-yellow-800 font-medium">
                IMPORTANT: This platform is for educational purposes only and does not constitute legal advice.
              </p>
            </div>
            <p className="text-gray-700 leading-relaxed">
              All information, analysis, and recommendations provided by this system are intended
              solely for educational and informational purposes. This service does not create an
              attorney-client relationship, and no information provided should be construed as
              legal advice. Always consult with a licensed attorney for specific legal matters.
            </p>
          </section>

          {/* Acceptance of Terms */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              1. Acceptance of Terms
            </h2>
            <p className="text-gray-700 leading-relaxed">
              By accessing and using the Legal AI System ("Service"), you accept and agree to be
              bound by the terms and provisions of this agreement. If you do not agree to these
              terms, please do not use the Service.
            </p>
          </section>

          {/* Use of Service */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              2. Use of Service
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              The Service is designed to assist with legal document analysis and research for
              educational purposes. You agree to use the Service only for lawful purposes and in
              accordance with these Terms.
            </p>
            <p className="text-gray-700 leading-relaxed">
              You are responsible for maintaining the confidentiality of your account credentials
              and for all activities that occur under your account.
            </p>
          </section>

          {/* Intellectual Property */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              3. Intellectual Property
            </h2>
            <p className="text-gray-700 leading-relaxed">
              The Service and its original content, features, and functionality are owned by
              Legal AI System and are protected by international copyright, trademark, patent,
              trade secret, and other intellectual property laws.
            </p>
          </section>

          {/* User Data and Privacy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              4. User Data and Privacy
            </h2>
            <p className="text-gray-700 leading-relaxed">
              Your use of the Service is also governed by our Privacy Policy. Please review our
              Privacy Policy to understand how we collect, use, and protect your information.
            </p>
          </section>

          {/* Limitation of Liability */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              5. Limitation of Liability
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              The Service is provided on an "AS IS" and "AS AVAILABLE" basis. Legal AI System
              makes no warranties, expressed or implied, and hereby disclaims all warranties
              including without limitation, implied warranties of merchantability, fitness for
              a particular purpose, or non-infringement of intellectual property.
            </p>
            <p className="text-gray-700 leading-relaxed">
              Legal AI System shall not be liable for any indirect, incidental, special,
              consequential, or punitive damages resulting from your use of or inability to use
              the Service.
            </p>
          </section>

          {/* AI-Generated Content */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              6. AI-Generated Content
            </h2>
            <p className="text-gray-700 leading-relaxed">
              The Service uses artificial intelligence to analyze documents and provide insights.
              AI-generated content may contain errors or inaccuracies. Users should independently
              verify all information and consult with qualified legal professionals before making
              any decisions based on AI-generated content.
            </p>
          </section>

          {/* Prohibited Uses */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              7. Prohibited Uses
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You may not use the Service:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>For any unlawful purpose or to solicit others to perform unlawful acts</li>
              <li>To violate any international, federal, provincial, or state regulations</li>
              <li>To infringe upon or violate our intellectual property rights</li>
              <li>To harass, abuse, insult, harm, defame, slander, disparage, intimidate, or discriminate</li>
              <li>To submit false or misleading information</li>
              <li>To upload viruses or any other type of malicious code</li>
              <li>To interfere with or circumvent security features of the Service</li>
            </ul>
          </section>

          {/* Account Termination */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              8. Account Termination
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We may terminate or suspend your account and bar access to the Service immediately,
              without prior notice or liability, under our sole discretion, for any reason
              whatsoever, including without limitation if you breach the Terms.
            </p>
          </section>

          {/* Modifications to Terms */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              9. Modifications to Terms
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We reserve the right to modify or replace these Terms at any time. If a revision
              is material, we will provide at least 30 days notice prior to any new terms taking
              effect. What constitutes a material change will be determined at our sole discretion.
            </p>
          </section>

          {/* Governing Law */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              10. Governing Law
            </h2>
            <p className="text-gray-700 leading-relaxed">
              These Terms shall be governed and construed in accordance with the laws of the
              United States, without regard to its conflict of law provisions.
            </p>
          </section>

          {/* Contact Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              11. Contact Us
            </h2>
            <p className="text-gray-700 leading-relaxed">
              If you have any questions about these Terms, please contact us at:
            </p>
            <p className="text-gray-700 mt-2">
              Email: <a href="mailto:legal@legalaisystem.com" className="text-blue-600 hover:underline">
                legal@legalaisystem.com
              </a>
            </p>
          </section>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-center space-x-6 text-sm">
          <Link href="/privacy" className="text-blue-600 hover:text-blue-800">
            Privacy Policy
          </Link>
          <Link href="/acceptable-use" className="text-blue-600 hover:text-blue-800">
            Acceptable Use Policy
          </Link>
        </div>
      </div>
    </div>
  );
}
