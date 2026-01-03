/**
 * Legal AI System - Marketing Landing Page
 * Production-ready marketing website with conversion optimization
 */

import React from 'react';
import Head from 'next/head';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  CheckIcon,
  ArrowRightIcon,
  StarIcon,
  ShieldCheckIcon,
  ClockIcon,
  UsersIcon,
  DocumentTextIcon,
  ChartBarIcon,
  LightBulbIcon,
  CogIcon
} from '@heroicons/react/24/outline';

// Analytics tracking
const trackEvent = (eventName: string, properties?: any) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, properties);
  }
};

interface FeatureCardProps {
  icon: React.ReactNode;
  title: string;
  description: string;
  features: string[];
}

const FeatureCard: React.FC<FeatureCardProps> = ({ icon, title, description, features }) => (
  <Card className="h-full border-2 hover:border-blue-200 transition-colors">
    <CardHeader>
      <div className="flex items-center space-x-3">
        <div className="p-2 bg-blue-100 rounded-lg">
          {icon}
        </div>
        <CardTitle className="text-xl">{title}</CardTitle>
      </div>
    </CardHeader>
    <CardContent>
      <p className="text-gray-600 mb-4">{description}</p>
      <ul className="space-y-2">
        {features.map((feature, index) => (
          <li key={index} className="flex items-center space-x-2">
            <CheckIcon className="h-4 w-4 text-green-500" />
            <span className="text-sm">{feature}</span>
          </li>
        ))}
      </ul>
    </CardContent>
  </Card>
);

interface PricingTierProps {
  name: string;
  price: string;
  period: string;
  description: string;
  features: string[];
  highlighted?: boolean;
  cta: string;
  onSelect: () => void;
}

const PricingTier: React.FC<PricingTierProps> = ({
  name, price, period, description, features, highlighted, cta, onSelect
}) => (
  <Card className={`relative ${highlighted ? 'border-2 border-blue-500 scale-105' : 'border'}`}>
    {highlighted && (
      <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-500">
        Most Popular
      </Badge>
    )}
    <CardHeader>
      <CardTitle className="text-center">
        <div className="text-2xl font-bold">{name}</div>
        <div className="mt-2">
          <span className="text-4xl font-bold">{price}</span>
          <span className="text-gray-500">/{period}</span>
        </div>
      </CardTitle>
      <p className="text-center text-gray-600">{description}</p>
    </CardHeader>
    <CardContent className="space-y-4">
      <ul className="space-y-3">
        {features.map((feature, index) => (
          <li key={index} className="flex items-center space-x-2">
            <CheckIcon className="h-4 w-4 text-green-500 flex-shrink-0" />
            <span className="text-sm">{feature}</span>
          </li>
        ))}
      </ul>
      <Button
        className={`w-full ${highlighted ? 'bg-blue-600 hover:bg-blue-700' : ''}`}
        onClick={onSelect}
      >
        {cta}
      </Button>
    </CardContent>
  </Card>
);

const MarketingHomePage: React.FC = () => {
  const handleGetStarted = () => {
    trackEvent('cta_click', { location: 'hero', action: 'get_started' });
    // Redirect to signup
    window.location.href = '/auth/signup';
  };

  const handleWatchDemo = () => {
    trackEvent('cta_click', { location: 'hero', action: 'watch_demo' });
    // Open demo modal or redirect
  };

  const handlePricingSelect = (tier: string) => {
    trackEvent('pricing_select', { tier });
    window.location.href = `/auth/signup?plan=${tier}`;
  };

  const features = [
    {
      icon: <DocumentTextIcon className="h-6 w-6 text-blue-600" />,
      title: "Document Analysis",
      description: "AI-powered analysis of contracts, legal briefs, and documents with instant insights.",
      features: [
        "Contract review and risk assessment",
        "Key clause extraction and highlighting",
        "Compliance checking and recommendations",
        "Multi-format support (PDF, DOCX, TXT)"
      ]
    },
    {
      icon: <LightBulbIcon className="h-6 w-6 text-blue-600" />,
      title: "Legal Research",
      description: "Comprehensive legal research with access to case law, statutes, and regulations.",
      features: [
        "Case law search and analysis",
        "Statute and regulation lookup",
        "Citation verification and formatting",
        "Legal precedent identification"
      ]
    },
    {
      icon: <ShieldCheckIcon className="h-6 w-6 text-blue-600" />,
      title: "Compliance Management",
      description: "Stay compliant with automated monitoring and alerts for regulatory changes.",
      features: [
        "Regulatory change notifications",
        "Compliance gap analysis",
        "Audit trail management",
        "Policy template library"
      ]
    },
    {
      icon: <UsersIcon className="h-6 w-6 text-blue-600" />,
      title: "Client Portal",
      description: "Secure client collaboration with document sharing and communication tools.",
      features: [
        "Secure document sharing",
        "Client communication hub",
        "Progress tracking and updates",
        "Branded client experience"
      ]
    },
    {
      icon: <ChartBarIcon className="h-6 w-6 text-blue-600" />,
      title: "Analytics & Reporting",
      description: "Comprehensive insights into your legal practice with detailed reporting.",
      features: [
        "Practice performance metrics",
        "Client satisfaction tracking",
        "Document processing analytics",
        "Custom report generation"
      ]
    },
    {
      icon: <CogIcon className="h-6 w-6 text-blue-600" />,
      title: "Workflow Automation",
      description: "Streamline repetitive tasks with intelligent automation and templates.",
      features: [
        "Document template automation",
        "Workflow process optimization",
        "Task scheduling and reminders",
        "Integration with existing tools"
      ]
    }
  ];

  const testimonials = [
    {
      name: "Sarah Johnson",
      role: "Partner, Johnson & Associates",
      content: "Legal AI has revolutionized our document review process. We're 60% faster and catch more issues than ever before.",
      rating: 5
    },
    {
      name: "Michael Chen",
      role: "General Counsel, TechCorp",
      content: "The compliance monitoring features have saved us countless hours and helped us avoid potential regulatory issues.",
      rating: 5
    },
    {
      name: "Emily Rodriguez",
      role: "Solo Practitioner",
      content: "As a solo attorney, Legal AI is like having a team of junior associates. The research capabilities are outstanding.",
      rating: 5
    }
  ];

  const stats = [
    { value: "10,000+", label: "Legal Documents Processed" },
    { value: "500+", label: "Law Firms Trust Us" },
    { value: "95%", label: "Client Satisfaction Rate" },
    { value: "60%", label: "Time Savings on Average" }
  ];

  return (
    <>
      <Head>
        <title>Legal AI - Intelligent Legal Document Analysis & Research Platform</title>
        <meta
          name="description"
          content="Transform your legal practice with AI-powered document analysis, legal research, and compliance management. Trusted by 500+ law firms worldwide."
        />
        <meta name="keywords" content="legal AI, document analysis, legal research, compliance, law firm software" />
        <meta property="og:title" content="Legal AI - Intelligent Legal Document Analysis Platform" />
        <meta property="og:description" content="Transform your legal practice with AI-powered document analysis and research." />
        <meta property="og:image" content="/images/legal-ai-og.jpg" />
        <meta property="og:url" content="https://legal-ai.com" />
        <meta name="twitter:card" content="summary_large_image" />
        <link rel="canonical" href="https://legal-ai.com" />

        {/* Analytics Scripts */}
        <script async src={`https://www.googletagmanager.com/gtag/js?id=${process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID}`}></script>
        <script
          dangerouslySetInnerHTML={{
            __html: `
              window.dataLayer = window.dataLayer || [];
              function gtag(){dataLayer.push(arguments);}
              gtag('js', new Date());
              gtag('config', '${process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID}');
            `,
          }}
        />

        {/* Facebook Pixel */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              !function(f,b,e,v,n,t,s)
              {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
              n.callMethod.apply(n,arguments):n.queue.push(arguments)};
              if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
              n.queue=[];t=b.createElement(e);t.async=!0;
              t.src=v;s=b.getElementsByTagName(e)[0];
              s.parentNode.insertBefore(t,s)}(window, document,'script',
              'https://connect.facebook.net/en_US/fbevents.js');
              fbq('init', '${process.env.NEXT_PUBLIC_FACEBOOK_PIXEL_ID}');
              fbq('track', 'PageView');
            `,
          }}
        />

        {/* Structured Data */}
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              "name": "Legal AI",
              "description": "AI-powered legal document analysis and research platform",
              "applicationCategory": "Legal Technology",
              "operatingSystem": "Web",
              "offers": {
                "@type": "Offer",
                "price": "99",
                "priceCurrency": "USD"
              },
              "aggregateRating": {
                "@type": "AggregateRating",
                "ratingValue": "4.9",
                "ratingCount": "247"
              }
            })
          }}
        />
      </Head>

      <div className="min-h-screen bg-white">
        {/* Navigation */}
        <nav className="fixed top-0 w-full bg-white/95 backdrop-blur-sm border-b z-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between items-center h-16">
              <div className="flex items-center space-x-8">
                <Link href="/" className="text-2xl font-bold text-blue-600">
                  Legal AI
                </Link>
                <div className="hidden md:flex space-x-6">
                  <Link href="#features" className="text-gray-600 hover:text-blue-600">Features</Link>
                  <Link href="#pricing" className="text-gray-600 hover:text-blue-600">Pricing</Link>
                  <Link href="#testimonials" className="text-gray-600 hover:text-blue-600">Reviews</Link>
                  <Link href="/support" className="text-gray-600 hover:text-blue-600">Support</Link>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <Link href="/auth/login" className="text-gray-600 hover:text-blue-600">
                  Log In
                </Link>
                <Button onClick={handleGetStarted}>
                  Get Started
                </Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Hero Section */}
        <section className="pt-20 pb-16 bg-gradient-to-br from-blue-50 to-indigo-100">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center">
              <Badge className="mb-4 bg-blue-100 text-blue-800">
                🚀 Now with GPT-4 Integration
              </Badge>
              <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
                Transform Your Legal Practice with
                <span className="text-blue-600"> AI Intelligence</span>
              </h1>
              <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
                Analyze legal documents 10x faster, conduct comprehensive research,
                and ensure compliance with our cutting-edge AI platform trusted by 500+ law firms.
              </p>

              <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
                <Button size="lg" onClick={handleGetStarted} className="bg-blue-600 hover:bg-blue-700">
                  Start Free Trial
                  <ArrowRightIcon className="ml-2 h-4 w-4" />
                </Button>
                <Button size="lg" variant="outline" onClick={handleWatchDemo}>
                  Watch Demo
                </Button>
              </div>

              {/* Trust Indicators */}
              <div className="flex justify-center items-center space-x-8 text-gray-500">
                <div className="flex items-center space-x-2">
                  <ShieldCheckIcon className="h-5 w-5" />
                  <span>SOC 2 Compliant</span>
                </div>
                <div className="flex items-center space-x-2">
                  <ClockIcon className="h-5 w-5" />
                  <span>99.9% Uptime</span>
                </div>
                <div className="flex items-center space-x-2">
                  <StarIcon className="h-5 w-5" />
                  <span>4.9/5 Rating</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Stats Section */}
        <section className="py-16 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {stats.map((stat, index) => (
                <div key={index}>
                  <div className="text-4xl font-bold text-blue-600">{stat.value}</div>
                  <div className="text-gray-600 mt-2">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Comprehensive Legal AI Solutions
              </h2>
              <p className="text-xl text-gray-600 max-w-2xl mx-auto">
                Everything you need to modernize your legal practice and deliver exceptional client service.
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <FeatureCard key={index} {...feature} />
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials Section */}
        <section id="testimonials" className="py-20 bg-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Trusted by Legal Professionals Worldwide
              </h2>
              <p className="text-xl text-gray-600">
                See what our clients say about transforming their practice with Legal AI.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8">
              {testimonials.map((testimonial, index) => (
                <Card key={index} className="h-full">
                  <CardContent className="p-6">
                    <div className="flex mb-4">
                      {[...Array(testimonial.rating)].map((_, i) => (
                        <StarIcon key={i} className="h-5 w-5 text-yellow-400 fill-current" />
                      ))}
                    </div>
                    <p className="text-gray-600 mb-4">"{testimonial.content}"</p>
                    <div>
                      <div className="font-semibold">{testimonial.name}</div>
                      <div className="text-sm text-gray-500">{testimonial.role}</div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 bg-gray-50">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-gray-900 mb-4">
                Simple, Transparent Pricing
              </h2>
              <p className="text-xl text-gray-600">
                Choose the plan that fits your practice. All plans include our core AI features.
              </p>
            </div>

            <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
              <PricingTier
                name="Starter"
                price="$99"
                period="month"
                description="Perfect for solo practitioners and small firms"
                features={[
                  "50 document analyses per month",
                  "Basic legal research access",
                  "Email support",
                  "Document storage (5GB)",
                  "Standard templates"
                ]}
                cta="Start Free Trial"
                onSelect={() => handlePricingSelect('starter')}
              />

              <PricingTier
                name="Professional"
                price="$299"
                period="month"
                description="Ideal for growing law firms"
                features={[
                  "200 document analyses per month",
                  "Advanced legal research",
                  "Priority support",
                  "Document storage (50GB)",
                  "Custom templates",
                  "Client portal access",
                  "Advanced analytics"
                ]}
                highlighted={true}
                cta="Start Free Trial"
                onSelect={() => handlePricingSelect('professional')}
              />

              <PricingTier
                name="Enterprise"
                price="Custom"
                period=""
                description="For large firms and organizations"
                features={[
                  "Unlimited document analyses",
                  "Full legal database access",
                  "Dedicated support manager",
                  "Unlimited document storage",
                  "Custom integrations",
                  "Advanced compliance tools",
                  "White-label options",
                  "SSO integration"
                ]}
                cta="Contact Sales"
                onSelect={() => handlePricingSelect('enterprise')}
              />
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-blue-600 text-white">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-4xl font-bold mb-4">
              Ready to Transform Your Legal Practice?
            </h2>
            <p className="text-xl mb-8">
              Join 500+ law firms already using Legal AI to work smarter, not harder.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100" onClick={handleGetStarted}>
                Start Your Free Trial
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                Schedule a Demo
              </Button>
            </div>
            <p className="text-sm mt-4 opacity-80">
              No credit card required • 14-day free trial • Cancel anytime
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="bg-gray-900 text-white py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid md:grid-cols-4 gap-8">
              <div>
                <h3 className="text-2xl font-bold mb-4">Legal AI</h3>
                <p className="text-gray-400 mb-4">
                  Transforming legal practice through intelligent AI solutions.
                </p>
                <div className="flex space-x-4">
                  {/* Social media icons would go here */}
                </div>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Product</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/features">Features</Link></li>
                  <li><Link href="/pricing">Pricing</Link></li>
                  <li><Link href="/integrations">Integrations</Link></li>
                  <li><Link href="/security">Security</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Company</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/about">About</Link></li>
                  <li><Link href="/careers">Careers</Link></li>
                  <li><Link href="/blog">Blog</Link></li>
                  <li><Link href="/press">Press</Link></li>
                </ul>
              </div>

              <div>
                <h4 className="font-semibold mb-4">Support</h4>
                <ul className="space-y-2 text-gray-400">
                  <li><Link href="/support">Help Center</Link></li>
                  <li><Link href="/contact">Contact</Link></li>
                  <li><Link href="/api-docs">API Docs</Link></li>
                  <li><Link href="/status">Status</Link></li>
                </ul>
              </div>
            </div>

            <div className="border-t border-gray-800 mt-12 pt-8 flex flex-col md:flex-row justify-between items-center">
              <p className="text-gray-400">
                © 2024 Legal AI. All rights reserved.
              </p>
              <div className="flex space-x-6 text-gray-400 mt-4 md:mt-0">
                <Link href="/privacy">Privacy Policy</Link>
                <Link href="/terms">Terms of Service</Link>
                <Link href="/cookies">Cookie Policy</Link>
              </div>
            </div>
          </div>
        </footer>
      </div>
    </>
  );
};

export default MarketingHomePage;