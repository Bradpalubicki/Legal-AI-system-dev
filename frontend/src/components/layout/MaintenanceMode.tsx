'use client'

import { AlertTriangle, Shield, Clock, Settings } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface MaintenanceModeProps {
  reason?: string
  estimatedTime?: string
  contactEmail?: string
}

export function MaintenanceMode({ 
  reason = "Critical legal compliance updates",
  estimatedTime = "2-4 hours", 
  contactEmail = "admin@legalai.com" 
}: MaintenanceModeProps) {
  
  return (
    <div className="min-h-screen bg-red-50 flex items-center justify-center p-4">
      <div className="max-w-2xl w-full space-y-6">
        
        {/* Critical Alert Header */}
        <Alert className="border-red-500 bg-red-100">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          <AlertDescription className="text-red-800 font-semibold text-lg">
            SYSTEM UNDER MAINTENANCE - ALL ACCESS SUSPENDED
          </AlertDescription>
        </Alert>

        {/* Main Maintenance Card */}
        <Card className="border-red-300 shadow-lg">
          <CardHeader className="text-center pb-4">
            <div className="mx-auto mb-4 p-3 bg-red-100 rounded-full w-fit">
              <Settings className="h-12 w-12 text-red-600" />
            </div>
            <CardTitle className="text-2xl text-red-700">
              Legal AI System Maintenance
            </CardTitle>
            <CardDescription className="text-red-600 font-medium">
              System temporarily unavailable for critical compliance updates
            </CardDescription>
          </CardHeader>
          
          <CardContent className="space-y-6">
            
            {/* Maintenance Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Shield className="h-5 w-5 text-amber-600" />
                  <h3 className="font-semibold text-amber-800">Reason</h3>
                </div>
                <p className="text-amber-700 text-sm">{reason}</p>
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="h-5 w-5 text-blue-600" />
                  <h3 className="font-semibold text-blue-800">Estimated Duration</h3>
                </div>
                <p className="text-blue-700 text-sm">{estimatedTime}</p>
              </div>
            </div>

            {/* Status Information */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-800 mb-3">Current Status</h3>
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">User Access</span>
                  <span className="text-sm font-medium text-red-600">SUSPENDED</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">API Endpoints</span>
                  <span className="text-sm font-medium text-red-600">DISABLED</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Data Integrity</span>
                  <span className="text-sm font-medium text-green-600">PROTECTED</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Maintenance Progress</span>
                  <span className="text-sm font-medium text-blue-600">IN PROGRESS</span>
                </div>
              </div>
            </div>

            {/* Legal Notice */}
            <Alert className="border-yellow-300 bg-yellow-50">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                <strong>Legal Notice:</strong> This maintenance is being performed to ensure full legal compliance. 
                The system will not be available until all compliance requirements are verified and restored.
              </AlertDescription>
            </Alert>

            {/* Contact Information */}
            <div className="text-center pt-4 border-t border-gray-200">
              <p className="text-sm text-gray-600 mb-2">
                For urgent matters or questions, please contact:
              </p>
              <p className="font-semibold text-gray-800">{contactEmail}</p>
              <p className="text-xs text-gray-500 mt-4">
                Maintenance started: {new Date().toLocaleString()}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Hidden compliance marker for monitoring */}
        <div 
          id="maintenance-mode-active"
          className="hidden"
          data-maintenance-active="true"
          data-reason={reason}
          data-started={new Date().toISOString()}
          data-estimated-duration={estimatedTime}
        />
      </div>
    </div>
  )
}