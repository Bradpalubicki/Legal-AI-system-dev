'use client';

import React, { useState } from 'react';
import {
  Heart,
  DollarSign,
  Users,
  Scale,
  Phone,
  MapPin,
  ExternalLink,
  Info,
  BookOpen,
  Building,
  Shield,
  Home,
  Briefcase,
  User
} from 'lucide-react';

interface LegalAidResource {
  id: string;
  name: string;
  description: string;
  serviceTypes: string[];
  eligibilityRequirements: string[];
  contactInfo: {
    phone?: string;
    website?: string;
    address?: string;
  };
  availability: string;
  cost: 'free' | 'sliding-scale' | 'low-cost';
  category: 'legal-aid' | 'pro-bono' | 'clinic' | 'self-help' | 'advocacy';
}

interface LegalAidResourcesProps {
  className?: string;
}

const LegalAidResources: React.FC<LegalAidResourcesProps> = ({ className = '' }) => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [expandedResource, setExpandedResource] = useState<string | null>(null);

  const categories = [
    { key: 'all', label: 'All Resources', icon: BookOpen },
    { key: 'legal-aid', label: 'Legal Aid', icon: Scale },
    { key: 'pro-bono', label: 'Pro Bono', icon: Heart },
    { key: 'clinic', label: 'Law Clinics', icon: Building },
    { key: 'self-help', label: 'Self-Help', icon: User },
    { key: 'advocacy', label: 'Advocacy Groups', icon: Users }
  ];

  const resources: LegalAidResource[] = [
    {
      id: '1',
      name: 'Legal Services Corporation (LSC)',
      description: 'National network providing free legal aid to low-income individuals and families for civil legal matters.',
      serviceTypes: [
        'Family law (divorce, custody, domestic violence)',
        'Housing issues (evictions, landlord disputes)',
        'Consumer protection',
        'Immigration assistance',
        'Benefits and government services'
      ],
      eligibilityRequirements: [
        'Household income at or below 125% of federal poverty guidelines',
        'Must be a U.S. citizen or eligible immigrant',
        'Case must involve civil (not criminal) legal matters'
      ],
      contactInfo: {
        phone: '1-800-LSC-FIND',
        website: 'https://www.lsc.gov/find-legal-aid',
        address: 'Locations nationwide - use website to find local office'
      },
      availability: 'Monday-Friday, hours vary by location',
      cost: 'free',
      category: 'legal-aid'
    },
    {
      id: '2',
      name: 'State Bar Pro Bono Programs',
      description: 'Volunteer attorney programs providing free legal services for qualifying individuals.',
      serviceTypes: [
        'Civil litigation and disputes',
        'Family law matters',
        'Estate planning and wills',
        'Business formation assistance',
        'Landlord-tenant issues'
      ],
      eligibilityRequirements: [
        'Income eligibility varies by program (typically 200-300% of poverty level)',
        'Case merit and complexity assessment',
        'Some programs prioritize specific demographics (seniors, veterans, etc.)'
      ],
      contactInfo: {
        website: 'Contact your state bar association for local programs',
        address: 'Available in most states'
      },
      availability: 'Varies by program and volunteer attorney availability',
      cost: 'free',
      category: 'pro-bono'
    },
    {
      id: '3',
      name: 'Law School Legal Clinics',
      description: 'Law students supervised by faculty provide legal services while gaining practical experience.',
      serviceTypes: [
        'Immigration law',
        'Tax assistance',
        'Small business legal issues',
        'Consumer protection',
        'Criminal defense (limited)',
        'Civil rights matters'
      ],
      eligibilityRequirements: [
        'Income guidelines vary by clinic',
        'Case must fit clinic\'s practice area',
        'Complexity suitable for student learning',
        'Geographic limitations may apply'
      ],
      contactInfo: {
        website: 'Search for law schools in your area with clinic programs',
        address: 'Available at most accredited law schools'
      },
      availability: 'Academic year schedule, limited summer availability',
      cost: 'free',
      category: 'clinic'
    },
    {
      id: '4',
      name: 'Court Self-Help Centers',
      description: 'Court-provided assistance for individuals representing themselves in legal proceedings.',
      serviceTypes: [
        'Form completion assistance',
        'Court procedure explanation',
        'Filing instruction guidance',
        'Basic legal information (not advice)',
        'Resource referrals'
      ],
      eligibilityRequirements: [
        'Open to all court users',
        'No income requirements',
        'Must be representing yourself (pro se)',
        'Cannot provide legal advice or representation'
      ],
      contactInfo: {
        website: 'Available at most county courthouses',
        address: 'Check with your local court system'
      },
      availability: 'Court business hours, varies by location',
      cost: 'free',
      category: 'self-help'
    },
    {
      id: '5',
      name: 'Legal Aid Clinics (Sliding Scale)',
      description: 'Reduced-fee legal services based on income and ability to pay.',
      serviceTypes: [
        'Comprehensive civil legal services',
        'Limited scope representation',
        'Document preparation and review',
        'Legal consultation and advice',
        'Mediation services'
      ],
      eligibilityRequirements: [
        'Income above legal aid limits but still low-to-moderate',
        'Typically 125-400% of federal poverty guidelines',
        'Sliding scale based on household size and income'
      ],
      contactInfo: {
        website: 'Search for "sliding scale legal services" in your area',
        address: 'Available in many metropolitan areas'
      },
      availability: 'Varies by organization',
      cost: 'sliding-scale',
      category: 'legal-aid'
    },
    {
      id: '6',
      name: 'Nonprofit Advocacy Organizations',
      description: 'Issue-specific organizations providing legal assistance and advocacy.',
      serviceTypes: [
        'Civil rights and discrimination',
        'Disability rights and accommodations',
        'Immigration and refugee assistance',
        'Domestic violence and family safety',
        'Environmental justice',
        'LGBTQ+ rights'
      ],
      eligibilityRequirements: [
        'Case must align with organization\'s mission',
        'Varies widely by organization',
        'May prioritize impact cases',
        'Some serve specific populations only'
      ],
      contactInfo: {
        website: 'Search by issue area and location',
        address: 'Nationwide, concentrated in urban areas'
      },
      availability: 'Varies significantly by organization',
      cost: 'free',
      category: 'advocacy'
    }
  ];

  const getCostBadge = (cost: string) => {
    switch (cost) {
      case 'free':
        return 'bg-success-100 text-success-800';
      case 'sliding-scale':
        return 'bg-blue-100 text-blue-800';
      case 'low-cost':
        return 'bg-warning-100 text-warning-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'legal-aid':
        return <Scale className="h-4 w-4" />;
      case 'pro-bono':
        return <Heart className="h-4 w-4" />;
      case 'clinic':
        return <Building className="h-4 w-4" />;
      case 'self-help':
        return <User className="h-4 w-4" />;
      case 'advocacy':
        return <Users className="h-4 w-4" />;
      default:
        return <BookOpen className="h-4 w-4" />;
    }
  };

  const filteredResources = selectedCategory === 'all' 
    ? resources 
    : resources.filter(r => r.category === selectedCategory);

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      <div className="flex items-center space-x-2 mb-4">
        <Heart className="h-5 w-5 text-red-600" />
        <h3 className="text-lg font-medium text-gray-900">Legal Aid & Resources</h3>
      </div>

      <div className="mb-4">
        <p className="text-sm text-gray-600">
          Free and low-cost legal assistance options for those who qualify. These resources provide 
          essential legal services to individuals who cannot afford private attorneys.
        </p>
      </div>

      {/* Category Filter */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category.key}
              onClick={() => setSelectedCategory(category.key)}
              className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                selectedCategory === category.key
                  ? 'bg-primary-100 text-primary-800 border border-primary-200'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <category.icon className="h-4 w-4" />
              <span>{category.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Resources List */}
      <div className="space-y-4">
        {filteredResources.map((resource) => (
          <div key={resource.id} className="border border-gray-200 rounded-lg">
            <div
              className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
              onClick={() => setExpandedResource(
                expandedResource === resource.id ? null : resource.id
              )}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start space-x-3">
                  <div className="text-blue-600 mt-1">
                    {getCategoryIcon(resource.category)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-1">
                      <h4 className="font-medium text-gray-900">{resource.name}</h4>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${getCostBadge(resource.cost)}`}>
                        {resource.cost === 'sliding-scale' ? 'Sliding Scale' : resource.cost.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm text-gray-600">{resource.description}</p>
                  </div>
                </div>
                <div className="text-gray-400">
                  {expandedResource === resource.id ? '−' : '+'}
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedResource === resource.id && (
              <div className="border-t border-gray-200 p-4 bg-gray-50">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Services */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2">Services Provided</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      {resource.serviceTypes.map((service, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-blue-600 mt-1">•</span>
                          <span>{service}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  {/* Eligibility */}
                  <div>
                    <h5 className="text-sm font-semibold text-gray-900 mb-2">Eligibility Requirements</h5>
                    <ul className="text-sm text-gray-700 space-y-1">
                      {resource.eligibilityRequirements.map((req, idx) => (
                        <li key={idx} className="flex items-start space-x-2">
                          <span className="text-green-600 mt-1">•</span>
                          <span>{req}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>

                {/* Contact Information */}
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <h5 className="text-sm font-semibold text-gray-900 mb-2">Contact Information</h5>
                  <div className="space-y-2">
                    {resource.contactInfo.phone && (
                      <div className="flex items-center space-x-2 text-sm text-gray-700">
                        <Phone className="h-4 w-4" />
                        <span>{resource.contactInfo.phone}</span>
                      </div>
                    )}
                    {resource.contactInfo.website && (
                      <div className="flex items-center space-x-2 text-sm">
                        <ExternalLink className="h-4 w-4" />
                        <a 
                          href={resource.contactInfo.website.startsWith('http') ? resource.contactInfo.website : '#'}
                          className="text-primary-600 hover:text-primary-700"
                          target={resource.contactInfo.website.startsWith('http') ? '_blank' : undefined}
                          rel={resource.contactInfo.website.startsWith('http') ? 'noopener noreferrer' : undefined}
                        >
                          {resource.contactInfo.website}
                        </a>
                      </div>
                    )}
                    {resource.contactInfo.address && (
                      <div className="flex items-start space-x-2 text-sm text-gray-700">
                        <MapPin className="h-4 w-4 mt-0.5" />
                        <span>{resource.contactInfo.address}</span>
                      </div>
                    )}
                  </div>
                  
                  <div className="mt-2 text-sm text-gray-600">
                    <strong>Availability:</strong> {resource.availability}
                  </div>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Income Guidelines Information */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Info className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-blue-900 mb-2">Understanding Income Guidelines</h5>
            <div className="text-sm text-blue-800 space-y-2">
              <p>Many legal aid programs use federal poverty guidelines to determine eligibility:</p>
              <ul className="space-y-1 ml-4">
                <li>• <strong>125% of poverty level:</strong> Most legal aid corporations</li>
                <li>• <strong>200-300% of poverty level:</strong> Many pro bono programs</li>
                <li>• <strong>Up to 400% of poverty level:</strong> Some sliding scale programs</li>
              </ul>
              <p className="mt-2">
                Guidelines are updated annually and vary by household size. Even if your income seems too high, 
                it's worth checking with programs as they may consider special circumstances.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Application Tips */}
      <div className="mt-4 bg-amber-50 border border-amber-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <BookOpen className="h-4 w-4 text-amber-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-amber-800 mb-2">Tips for Applying to Legal Aid Programs</h5>
            <ul className="text-sm text-amber-700 space-y-1">
              <li>• Apply early - many programs have waiting lists</li>
              <li>• Gather income documentation (pay stubs, benefit statements)</li>
              <li>• Be prepared to explain your legal issue clearly and concisely</li>
              <li>• Some programs prioritize certain case types (domestic violence, housing)</li>
              <li>• If denied at one program, try others - eligibility criteria vary</li>
              <li>• Keep records of all applications and communications</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Emergency Resources */}
      <div className="mt-4 bg-error-50 border border-error-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <Shield className="h-4 w-4 text-error-600 mt-0.5 flex-shrink-0" />
          <div>
            <h5 className="text-sm font-semibold text-error-900 mb-2">Emergency Legal Situations</h5>
            <p className="text-sm text-error-700 mb-2">
              For urgent situations requiring immediate legal assistance:
            </p>
            <ul className="text-sm text-error-700 space-y-1">
              <li>• <strong>Domestic Violence:</strong> National hotline 1-800-799-7233</li>
              <li>• <strong>Eviction/Housing Crisis:</strong> Contact local housing authority or legal aid immediately</li>
              <li>• <strong>Immigration Detention:</strong> Contact immigration legal aid organizations</li>
              <li>• <strong>Criminal Matters:</strong> Request a public defender if you cannot afford an attorney</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="bg-legal-50 border border-legal-200 rounded-lg p-3">
          <div className="flex items-start space-x-2">
            <Scale className="h-4 w-4 text-legal-600 mt-0.5 flex-shrink-0" />
            <div>
              <h5 className="text-xs font-semibold text-legal-900 mb-1">Legal Aid Resource Disclaimer</h5>
              <p className="text-xs text-legal-700">
                This information is provided for educational purposes only. Availability, eligibility requirements, 
                and services may change. Contact organizations directly to verify current information and application procedures. 
                This list is not exhaustive - additional resources may be available in your area.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LegalAidResources;