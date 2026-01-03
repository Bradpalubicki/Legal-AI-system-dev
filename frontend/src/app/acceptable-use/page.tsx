'use client';

import React from 'react';
import Link from 'next/link';

export default function AcceptableUsePolicyPage() {
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
            Acceptable Use Policy
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
              This Acceptable Use Policy ("Policy") governs your use of the Legal AI System
              ("Service"). By using the Service, you agree to comply with this Policy. Violation
              of this Policy may result in suspension or termination of your account.
            </p>
          </section>

          {/* Educational Purpose */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              Educational Purpose
            </h2>
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
              <p className="text-yellow-800 font-medium">
                This service is for educational purposes only and does not provide legal advice.
              </p>
            </div>
            <p className="text-gray-700 leading-relaxed">
              You acknowledge that the Service is designed for educational and informational
              purposes. Any analysis, insights, or recommendations provided by the Service
              should not be relied upon as legal advice. Always consult with a licensed attorney
              for specific legal matters.
            </p>
          </section>

          {/* Permitted Uses */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              1. Permitted Uses
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You may use the Service for the following purposes:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Learning about legal documents and processes</li>
              <li>Analyzing non-confidential legal documents for educational purposes</li>
              <li>Researching legal concepts and case law</li>
              <li>Understanding legal terminology and procedures</li>
              <li>Exploring AI-assisted legal analysis tools</li>
              <li>Professional development in legal technology</li>
            </ul>
          </section>

          {/* Prohibited Activities */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              2. Prohibited Activities
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You agree NOT to use the Service for any of the following:
            </p>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-4">
              Illegal or Harmful Activities
            </h3>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Any unlawful or illegal purpose</li>
              <li>Planning, facilitating, or engaging in criminal activity</li>
              <li>Fraud, misrepresentation, or deception</li>
              <li>Harassment, threats, or intimidation of any person</li>
              <li>Stalking or violating others' privacy</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              Misuse of AI Services
            </h3>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Attempting to reverse engineer or extract AI models</li>
              <li>Using the Service to train competing AI models</li>
              <li>Automated scraping or bulk data extraction</li>
              <li>Generating spam or malicious content</li>
              <li>Circumventing usage limits or access controls</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              Abuse of Service
            </h3>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Uploading malware, viruses, or malicious code</li>
              <li>Attempting to gain unauthorized access to systems</li>
              <li>Interfering with or disrupting the Service</li>
              <li>Overwhelming the Service with excessive requests</li>
              <li>Sharing account credentials or allowing unauthorized access</li>
            </ul>

            <h3 className="text-xl font-semibold text-gray-800 mb-3 mt-6">
              Intellectual Property Violations
            </h3>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Infringing on copyrights, trademarks, or patents</li>
              <li>Uploading content you don't have rights to use</li>
              <li>Distributing proprietary information without authorization</li>
              <li>Violating third-party intellectual property rights</li>
            </ul>
          </section>

          {/* Content Guidelines */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              3. Content Guidelines
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              When uploading documents or using the Service, you must ensure:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>You have the right to use and analyze the documents</li>
              <li>Documents do not contain malware or malicious content</li>
              <li>Content is appropriate for an educational platform</li>
              <li>Highly sensitive or confidential information is properly protected</li>
              <li>Documents comply with applicable laws and regulations</li>
            </ul>
          </section>

          {/* Data Handling Responsibilities */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              4. Data Handling Responsibilities
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You are responsible for:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Ensuring you have proper authorization for uploaded documents</li>
              <li>Anonymizing sensitive personal information before upload</li>
              <li>Complying with attorney-client privilege and confidentiality requirements</li>
              <li>Not uploading documents subject to court seal or protective orders</li>
              <li>Understanding that AI processing may not maintain confidentiality</li>
            </ul>
            <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mt-4">
              <p className="text-blue-800">
                <strong>Important:</strong> Do not upload highly sensitive or confidential
                documents. The Service uses third-party AI providers, and confidentiality
                cannot be guaranteed.
              </p>
            </div>
          </section>

          {/* Account Security */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              5. Account Security
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              You agree to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Maintain the security of your account credentials</li>
              <li>Use strong, unique passwords</li>
              <li>Not share your account with others</li>
              <li>Immediately report unauthorized access or security breaches</li>
              <li>Enable multi-factor authentication when available</li>
              <li>Log out from shared or public computers</li>
            </ul>
          </section>

          {/* Professional Conduct */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              6. Professional Conduct
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              When using the Service, you agree to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Be respectful and professional in all interactions</li>
              <li>Not discriminate based on protected characteristics</li>
              <li>Maintain ethical standards appropriate to the legal profession</li>
              <li>Comply with all applicable professional conduct rules</li>
              <li>Not use the Service to facilitate unauthorized practice of law</li>
            </ul>
          </section>

          {/* Monitoring and Enforcement */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              7. Monitoring and Enforcement
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              We reserve the right to:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Monitor use of the Service for policy violations</li>
              <li>Investigate suspected violations of this Policy</li>
              <li>Remove content that violates this Policy</li>
              <li>Suspend or terminate accounts for policy violations</li>
              <li>Report illegal activities to law enforcement</li>
              <li>Cooperate with legal investigations</li>
            </ul>
            <p className="text-gray-700 leading-relaxed mt-3">
              We do not routinely review user content, but we may do so in response to reports
              or suspected violations.
            </p>
          </section>

          {/* Consequences of Violations */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              8. Consequences of Violations
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              Violations of this Policy may result in:
            </p>
            <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
              <li>Warning and request to cease violating activities</li>
              <li>Temporary suspension of account access</li>
              <li>Permanent termination of account</li>
              <li>Removal of content and analysis results</li>
              <li>Legal action for damages or injunctive relief</li>
              <li>Reporting to appropriate authorities</li>
            </ul>
          </section>

          {/* Reporting Violations */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              9. Reporting Violations
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              If you become aware of any violation of this Policy, please report it to us:
            </p>
            <div className="text-gray-700 space-y-1">
              <p>
                Email: <a href="mailto:abuse@legalaisystem.com" className="text-blue-600 hover:underline">
                  abuse@legalaisystem.com
                </a>
              </p>
              <p>
                Security Issues: <a href="mailto:security@legalaisystem.com" className="text-blue-600 hover:underline">
                  security@legalaisystem.com
                </a>
              </p>
            </div>
          </section>

          {/* Changes to Policy */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              10. Changes to This Policy
            </h2>
            <p className="text-gray-700 leading-relaxed">
              We may update this Acceptable Use Policy from time to time. We will notify you
              of any material changes by posting the new policy on this page and updating the
              "Last Updated" date. Continued use of the Service after changes constitutes
              acceptance of the updated policy.
            </p>
          </section>

          {/* Contact Information */}
          <section>
            <h2 className="text-2xl font-semibold text-gray-900 mb-4">
              11. Contact Us
            </h2>
            <p className="text-gray-700 leading-relaxed mb-3">
              If you have questions about this Acceptable Use Policy, please contact us:
            </p>
            <p className="text-gray-700">
              Email: <a href="mailto:legal@legalaisystem.com" className="text-blue-600 hover:underline">
                legal@legalaisystem.com
              </a>
            </p>
          </section>
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 flex justify-center space-x-6 text-sm">
          <Link href="/terms" className="text-blue-600 hover:text-blue-800">
            Terms of Service
          </Link>
          <Link href="/privacy" className="text-blue-600 hover:text-blue-800">
            Privacy Policy
          </Link>
        </div>
      </div>
    </div>
  );
}
