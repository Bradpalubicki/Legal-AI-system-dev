'use client';

import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  MapPin, 
  DollarSign,
  Phone,
  Mail,
  ExternalLink,
  AlertTriangle,
  Info,
  CheckCircle,
  Clock,
  Shield,
  Star,
  Heart,
  Scale,
  HelpCircle,
  Building,
  Globe,
  Filter,
  ArrowRight
} from 'lucide-react';
import Link from 'next/link';
import { useAuth, useCompliance } from '@/hooks';
import { DisclaimerBanner } from '@/components/compliance';
import { UserRole, DisclaimerType } from '@/types/legal-compliance';

interface AttorneyProfile {
  bar_number: string;
  first_name: string;
  last_name: string;
  firm_name?: string;
  email: string;
  phone: string;
  location: {
    city: string;
    state: string;
    zip_code: string;
  };
  practice_areas: string[];
  years_experience: number;
  fee_structures: string[];
  languages: string[];
  website?: string;
  bio?: string;
  hourly_rate_min?: number;
  hourly_rate_max?: number;
  consultation_fee?: number;
  free_consultation: boolean;
  accepting_new_clients: boolean;
  profile_completeness: number;
  distance_miles?: number;
}

interface LegalAidOrganization {
  id: string;
  name: string;
  state: string;
  phone: string;
  website: string;
  services: string[];
  languages: string[];
  emergency_services: boolean;
  match_reason: string;
}

interface BarAssociation {
  name: string;
  state: string;
  website: string;
  referral_phone: string;
  fee_for_referral?: number;
  languages_available: string[];
}

const AttorneyReferralHub = () => {
  const { user } = useAuth();
  const { complianceStatus } = useCompliance();

  const [attorneys, setAttorneys] = useState<AttorneyProfile[]>([]);
  const [legalAidOrgs, setLegalAidOrgs] = useState<LegalAidOrganization[]>([]);
  const [barAssociations, setBarAssociations] = useState<BarAssociation[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'attorneys' | 'legal-aid' | 'bar-associations' | 'pro-bono'>('attorneys');
  const [searchFilters, setSearchFilters] = useState({
    location: { city: '', state: '', zip_code: '' },
    practice_areas: [] as string[],
    max_distance: 50,
    fee_structure: [] as string[],
    languages: [] as string[],
    free_consultation_only: false,
    case_description: ''
  });

  // Mock data for demonstration - replace with actual API calls
  useEffect(() => {
    loadReferralData();
  }, []);

  const loadReferralData = async () => {
    setIsLoading(true);
    
    // Simulate API calls
    setTimeout(() => {
      // Mock attorney data
      setAttorneys([
        {
          bar_number: "CA123456",
          first_name: "Sarah",
          last_name: "Johnson",
          firm_name: "Johnson & Associates",
          email: "sarah@johnsonlaw.com",
          phone: "(555) 123-4567",
          location: { city: "Los Angeles", state: "CA", zip_code: "90210" },
          practice_areas: ["Personal Injury", "Medical Malpractice"],
          years_experience: 12,
          fee_structures: ["Contingency", "Hourly"],
          languages: ["English", "Spanish"],
          website: "https://johnsonlaw.com",
          bio: "Experienced personal injury attorney with a track record of successful settlements and trials.",
          hourly_rate_min: 400,
          hourly_rate_max: 500,
          free_consultation: true,
          accepting_new_clients: true,
          profile_completeness: 0.95,
          distance_miles: 5.2
        },
        {
          bar_number: "CA789012",
          first_name: "Michael",
          last_name: "Chen",
          firm_name: "Chen Family Law Group",
          email: "mchen@chenfamilylaw.com",
          phone: "(555) 987-6543",
          location: { city: "San Francisco", state: "CA", zip_code: "94102" },
          practice_areas: ["Family Law", "Divorce", "Child Custody"],
          years_experience: 8,
          fee_structures: ["Hourly", "Flat Fee"],
          languages: ["English", "Mandarin"],
          website: "https://chenfamilylaw.com",
          hourly_rate_min: 300,
          hourly_rate_max: 400,
          consultation_fee: 150,
          free_consultation: false,
          accepting_new_clients: true,
          profile_completeness: 0.88,
          distance_miles: 385.7
        }
      ]);

      // Mock legal aid data
      setLegalAidOrgs([
        {
          id: "legal_aid_california",
          name: "Legal Aid Foundation of Los Angeles",
          state: "CA",
          phone: "(213) 640-3200",
          website: "https://lafla.org",
          services: ["Housing law", "Immigration", "Family law", "Consumer protection"],
          languages: ["English", "Spanish", "Korean"],
          emergency_services: true,
          match_reason: "Serves Los Angeles County, income-eligible"
        },
        {
          id: "public_counsel",
          name: "Public Counsel",
          state: "CA",
          phone: "(213) 385-2977",
          website: "https://publiccounsel.org",
          services: ["Immigration", "Homelessness", "Veterans", "Children's rights"],
          languages: ["English", "Spanish"],
          emergency_services: false,
          match_reason: "Pro bono services available"
        }
      ]);

      // Mock bar association data
      setBarAssociations([
        {
          name: "State Bar of California",
          state: "CA",
          website: "https://www.calbar.ca.gov",
          referral_phone: "1-866-442-2529",
          fee_for_referral: 25.0,
          languages_available: ["English", "Spanish", "Chinese"]
        },
        {
          name: "Los Angeles County Bar Association",
          state: "CA",
          website: "https://lacba.org",
          referral_phone: "(213) 627-2727",
          fee_for_referral: 39.0,
          languages_available: ["English", "Spanish", "Korean", "Chinese"]
        }
      ]);

      setIsLoading(false);
    }, 1000);
  };

  const handleSearch = async () => {
    setIsLoading(true);
    // Simulate search API call
    setTimeout(() => {
      setIsLoading(false);
    }, 800);
  };

  const getFeeStructureDisplay = (feeStructures: string[]) => {
    return feeStructures.map(fee => {
      switch (fee.toLowerCase()) {
        case 'contingency': return 'No Fee Unless We Win';
        case 'hourly': return 'Hourly Rate';
        case 'flat_fee': return 'Fixed Fee';
        case 'pro_bono': return 'Free Services';
        default: return fee;
      }
    }).join(', ');
  };

  const getExperienceLevel = (years: number) => {
    if (years >= 15) return { label: 'Very Experienced', color: 'text-green-700 bg-green-100' };
    if (years >= 10) return { label: 'Experienced', color: 'text-blue-700 bg-blue-100' };
    if (years >= 5) return { label: 'Mid-Level', color: 'text-yellow-700 bg-yellow-100' };
    return { label: 'Newer Attorney', color: 'text-gray-700 bg-gray-100' };
  };

  if (isLoading && attorneys.length === 0) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading referral information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-legal-600 mr-3" />
              <h1 className="text-2xl font-bold text-gray-900">
                Attorney Referral Service
              </h1>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-600">
                Find qualified legal representation
              </span>
              <Link
                href="/referrals/request"
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
              >
                <Search className="h-4 w-4 mr-2" />
                Request Referral
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Referral Disclaimer */}
        <div className="mb-8">
          <DisclaimerBanner
            disclaimer={{
              id: 'referral-disclaimer',
              type: DisclaimerType.NO_LEGAL_ADVICE,
              title: 'Important Notice - Referrals Are Not Endorsements',
              content: 'Attorney referrals are provided for informational purposes only and do not constitute endorsements. You must independently verify attorney credentials and make your own hiring decisions.',
              displayFormat: 'header_banner' as any,
              isRequired: false,
              showForRoles: [UserRole.CLIENT, UserRole.ATTORNEY],
              context: ['referrals'],
              priority: 1,
              isActive: true,
              requiresAcknowledgment: false,
              dismissible: true
            }}
          />
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Users className="h-8 w-8 text-blue-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Attorneys Available
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {attorneys.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Heart className="h-8 w-8 text-red-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Legal Aid Organizations
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {legalAidOrgs.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Shield className="h-8 w-8 text-green-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Bar Referral Services
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {barAssociations.length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white overflow-hidden shadow rounded-lg">
            <div className="p-5">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <CheckCircle className="h-8 w-8 text-purple-600" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-500 truncate">
                      Accepting New Clients
                    </dt>
                    <dd className="text-lg font-medium text-gray-900">
                      {attorneys.filter(a => a.accepting_new_clients).length}
                    </dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Search Filters */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Find Legal Help</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Location
              </label>
              <div className="relative">
                <MapPin className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="City, State or ZIP"
                  value={`${searchFilters.location.city} ${searchFilters.location.state} ${searchFilters.location.zip_code}`.trim()}
                  onChange={(e) => {
                    const parts = e.target.value.split(' ');
                    setSearchFilters(prev => ({
                      ...prev,
                      location: {
                        city: parts[0] || '',
                        state: parts[1] || '',
                        zip_code: parts[2] || ''
                      }
                    }));
                  }}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Legal Issue
              </label>
              <select
                value={searchFilters.practice_areas[0] || ''}
                onChange={(e) => setSearchFilters(prev => ({
                  ...prev,
                  practice_areas: e.target.value ? [e.target.value] : []
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">All Practice Areas</option>
                <option value="Personal Injury">Personal Injury</option>
                <option value="Family Law">Family Law</option>
                <option value="Criminal Defense">Criminal Defense</option>
                <option value="Business Law">Business Law</option>
                <option value="Real Estate">Real Estate</option>
                <option value="Immigration">Immigration</option>
                <option value="Bankruptcy">Bankruptcy</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Fee Type
              </label>
              <select
                value={searchFilters.fee_structure[0] || ''}
                onChange={(e) => setSearchFilters(prev => ({
                  ...prev,
                  fee_structure: e.target.value ? [e.target.value] : []
                }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
              >
                <option value="">Any Fee Structure</option>
                <option value="Contingency">No Fee Unless We Win</option>
                <option value="Hourly">Hourly Rate</option>
                <option value="Flat Fee">Fixed Fee</option>
                <option value="Pro Bono">Free Services</option>
              </select>
            </div>
            
            <div className="flex items-end">
              <button
                onClick={handleSearch}
                disabled={isLoading}
                className="w-full inline-flex items-center justify-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 disabled:opacity-50"
              >
                <Search className="h-4 w-4 mr-2" />
                {isLoading ? 'Searching...' : 'Search'}
              </button>
            </div>
          </div>
          
          <div className="flex items-center mt-4">
            <input
              type="checkbox"
              id="free-consultation"
              checked={searchFilters.free_consultation_only}
              onChange={(e) => setSearchFilters(prev => ({
                ...prev,
                free_consultation_only: e.target.checked
              }))}
              className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
            />
            <label htmlFor="free-consultation" className="ml-2 block text-sm text-gray-900">
              Free consultation only
            </label>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              <button
                onClick={() => setActiveTab('attorneys')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'attorneys'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Users className="h-4 w-4 inline mr-2" />
                Private Attorneys ({attorneys.length})
              </button>
              <button
                onClick={() => setActiveTab('legal-aid')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'legal-aid'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Heart className="h-4 w-4 inline mr-2" />
                Legal Aid ({legalAidOrgs.length})
              </button>
              <button
                onClick={() => setActiveTab('bar-associations')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'bar-associations'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <Shield className="h-4 w-4 inline mr-2" />
                Bar Referrals ({barAssociations.length})
              </button>
              <button
                onClick={() => setActiveTab('pro-bono')}
                className={`py-4 px-1 border-b-2 font-medium text-sm ${
                  activeTab === 'pro-bono'
                    ? 'border-primary-500 text-primary-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                <HelpCircle className="h-4 w-4 inline mr-2" />
                Pro Bono & Clinics
              </button>
            </nav>
          </div>

          {/* Tab Content */}
          <div className="p-6">
            {activeTab === 'attorneys' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-gray-900">Private Attorneys</h3>
                  <div className="text-sm text-gray-600">
                    {attorneys.filter(a => a.accepting_new_clients).length} accepting new clients
                  </div>
                </div>
                
                {attorneys.map((attorney) => {
                  const experienceLevel = getExperienceLevel(attorney.years_experience);
                  
                  return (
                    <div key={attorney.bar_number} className="border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-start justify-between mb-4">
                            <div>
                              <h4 className="text-xl font-semibold text-gray-900">
                                {attorney.first_name} {attorney.last_name}
                                {attorney.firm_name && (
                                  <span className="text-base font-normal text-gray-600 ml-2">
                                    at {attorney.firm_name}
                                  </span>
                                )}
                              </h4>
                              <div className="flex items-center mt-2 space-x-4">
                                <div className="flex items-center text-sm text-gray-600">
                                  <MapPin className="h-4 w-4 mr-1" />
                                  {attorney.location.city}, {attorney.location.state}
                                  {attorney.distance_miles && (
                                    <span className="ml-2 text-primary-600">
                                      ({attorney.distance_miles.toFixed(1)} miles)
                                    </span>
                                  )}
                                </div>
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${experienceLevel.color}`}>
                                  {attorney.years_experience} years • {experienceLevel.label}
                                </span>
                              </div>
                            </div>
                            <div className="text-right">
                              {attorney.accepting_new_clients ? (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                  <CheckCircle className="h-3 w-3 mr-1" />
                                  Accepting Clients
                                </span>
                              ) : (
                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                  Not Available
                                </span>
                              )}
                            </div>
                          </div>
                          
                          {attorney.bio && (
                            <p className="text-gray-600 mb-4">{attorney.bio}</p>
                          )}
                          
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                            <div>
                              <h5 className="font-medium text-gray-900 mb-2">Practice Areas</h5>
                              <div className="flex flex-wrap gap-2">
                                {attorney.practice_areas.map((area) => (
                                  <span key={area} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                                    {area}
                                  </span>
                                ))}
                              </div>
                            </div>
                            
                            <div>
                              <h5 className="font-medium text-gray-900 mb-2">Fee Structure</h5>
                              <p className="text-sm text-gray-600">
                                {getFeeStructureDisplay(attorney.fee_structures)}
                              </p>
                              {attorney.hourly_rate_min && attorney.hourly_rate_max && (
                                <p className="text-sm text-gray-600">
                                  ${attorney.hourly_rate_min}-${attorney.hourly_rate_max}/hour
                                </p>
                              )}
                              {attorney.free_consultation && (
                                <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800 mt-1">
                                  Free Consultation
                                </span>
                              )}
                            </div>
                          </div>
                          
                          <div className="flex items-center justify-between">
                            <div className="flex items-center space-x-4">
                              <div className="flex items-center text-sm text-gray-600">
                                <Phone className="h-4 w-4 mr-1" />
                                {attorney.phone}
                              </div>
                              <div className="flex items-center text-sm text-gray-600">
                                <Mail className="h-4 w-4 mr-1" />
                                {attorney.email}
                              </div>
                              {attorney.languages.length > 1 && (
                                <div className="flex items-center text-sm text-gray-600">
                                  <Globe className="h-4 w-4 mr-1" />
                                  {attorney.languages.join(', ')}
                                </div>
                              )}
                            </div>
                            
                            <div className="flex items-center space-x-3">
                              {attorney.website && (
                                <a
                                  href={attorney.website}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center text-sm text-primary-600 hover:text-primary-500"
                                >
                                  <ExternalLink className="h-4 w-4 mr-1" />
                                  Website
                                </a>
                              )}
                              <Link
                                href={`/referrals/contact/${attorney.bar_number}`}
                                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                              >
                                Request Contact
                                <ArrowRight className="h-4 w-4 ml-2" />
                              </Link>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
                
                {attorneys.length === 0 && (
                  <div className="text-center py-8">
                    <Users className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No attorneys found</h3>
                    <p className="text-gray-600">Try adjusting your search filters to find more results.</p>
                  </div>
                )}
              </div>
            )}

            {activeTab === 'legal-aid' && (
              <div className="space-y-6">
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <Info className="h-5 w-5 text-blue-600 mt-0.5 mr-3" />
                    <div>
                      <h4 className="text-sm font-semibold text-blue-800">About Legal Aid</h4>
                      <p className="mt-1 text-sm text-blue-700">
                        Legal aid organizations provide free legal services to low-income individuals who qualify. 
                        Each organization has specific income guidelines and case type restrictions.
                      </p>
                    </div>
                  </div>
                </div>

                {legalAidOrgs.map((org) => (
                  <div key={org.id} className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-xl font-semibold text-gray-900">{org.name}</h4>
                        <p className="text-sm text-green-600 font-medium mt-1">{org.match_reason}</p>
                      </div>
                      {org.emergency_services && (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                          Emergency Services Available
                        </span>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Services Provided</h5>
                        <div className="flex flex-wrap gap-2">
                          {org.services.map((service) => (
                            <span key={service} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800">
                              {service}
                            </span>
                          ))}
                        </div>
                      </div>
                      
                      <div>
                        <h5 className="font-medium text-gray-900 mb-2">Languages Available</h5>
                        <p className="text-sm text-gray-600">{org.languages.join(', ')}</p>
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <Phone className="h-4 w-4 mr-1" />
                          {org.phone}
                        </div>
                        <a
                          href={org.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-primary-600 hover:text-primary-500"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Website
                        </a>
                      </div>
                      
                      <Link
                        href={`/referrals/eligibility?org=${org.id}`}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-600 bg-primary-50 hover:bg-primary-100"
                      >
                        Check Eligibility
                        <ArrowRight className="h-4 w-4 ml-2" />
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'bar-associations' && (
              <div className="space-y-6">
                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <Shield className="h-5 w-5 text-amber-600 mt-0.5 mr-3" />
                    <div>
                      <h4 className="text-sm font-semibold text-amber-800">State Bar Referral Services</h4>
                      <p className="mt-1 text-sm text-amber-700">
                        State and local bar associations maintain referral services with attorney screening requirements. 
                        Most charge a nominal referral fee and may guarantee initial consultation rates.
                      </p>
                    </div>
                  </div>
                </div>

                {barAssociations.map((barAssoc, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h4 className="text-xl font-semibold text-gray-900">{barAssoc.name}</h4>
                        <p className="text-sm text-gray-600 mt-1">Official state bar referral service</p>
                      </div>
                      {barAssoc.fee_for_referral && (
                        <div className="text-right">
                          <div className="text-sm font-medium text-gray-900">
                            Referral Fee: ${barAssoc.fee_for_referral}
                          </div>
                          <div className="text-xs text-gray-600">
                            Usually includes consultation
                          </div>
                        </div>
                      )}
                    </div>
                    
                    <div className="mb-4">
                      <h5 className="font-medium text-gray-900 mb-2">Available Languages</h5>
                      <div className="flex flex-wrap gap-2">
                        {barAssoc.languages_available.map((language) => (
                          <span key={language} className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-100 text-blue-800">
                            {language}
                          </span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="flex items-center text-sm text-gray-600">
                          <Phone className="h-4 w-4 mr-1" />
                          {barAssoc.referral_phone}
                        </div>
                        <a
                          href={barAssoc.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-sm text-primary-600 hover:text-primary-500"
                        >
                          <ExternalLink className="h-4 w-4 mr-1" />
                          Official Website
                        </a>
                      </div>
                      
                      <a
                        href={`tel:${barAssoc.referral_phone}`}
                        className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700"
                      >
                        <Phone className="h-4 w-4 mr-2" />
                        Call for Referral
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'pro-bono' && (
              <div className="space-y-6">
                <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                  <div className="flex items-start">
                    <Heart className="h-5 w-5 text-green-600 mt-0.5 mr-3" />
                    <div>
                      <h4 className="text-sm font-semibold text-green-800">Pro Bono and Law School Clinics</h4>
                      <p className="mt-1 text-sm text-green-700">
                        Pro bono programs offer free legal services through volunteer attorneys. Law school clinics 
                        provide services through supervised student attorneys at no or low cost.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="text-center py-8">
                  <HelpCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Pro Bono Resources Coming Soon</h3>
                  <p className="text-gray-600 mb-4">
                    We're working on expanding our pro bono and law school clinic directory. 
                    In the meantime, contact your local bar association for pro bono opportunities.
                  </p>
                  <Link
                    href="/referrals/request?type=pro-bono"
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-primary-600 bg-primary-50 hover:bg-primary-100"
                  >
                    Request Pro Bono Referral
                    <ArrowRight className="h-4 w-4 ml-2" />
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Important Notice */}
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-start">
            <AlertTriangle className="h-6 w-6 text-red-600 mt-0.5 mr-3" />
            <div>
              <h4 className="text-lg font-semibold text-red-800 mb-2">
                Important Referral Disclaimer
              </h4>
              <div className="text-sm text-red-700 space-y-2">
                <p>
                  <strong>Referrals are NOT endorsements.</strong> The inclusion of any attorney or organization 
                  in our referral service does not constitute an endorsement of their services, qualifications, or competence.
                </p>
                <p>
                  You are responsible for:
                </p>
                <ul className="list-disc ml-6 space-y-1">
                  <li>Independently verifying attorney credentials and bar membership status</li>
                  <li>Checking disciplinary records and reviews</li>
                  <li>Interviewing potential attorneys and discussing fees</li>
                  <li>Making your own informed hiring decision</li>
                </ul>
                <p>
                  Contact your state bar association for official referral services with additional screening requirements.
                </p>
              </div>
              <div className="mt-4">
                <Link
                  href="/referrals/disclaimer"
                  className="inline-flex items-center text-sm font-medium text-red-600 hover:text-red-500"
                >
                  Read Full Disclaimer
                  <ExternalLink className="h-4 w-4 ml-1" />
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AttorneyReferralHub;