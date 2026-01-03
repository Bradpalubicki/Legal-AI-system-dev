'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  XMarkIcon,
  ArrowDownTrayIcon,
  DevicePhoneMobileIcon,
  ComputerDesktopIcon,
  WifiIcon,
  BoltIcon,
  ShieldCheckIcon
} from '@heroicons/react/24/outline'
import { usePWA } from '../../hooks/usePWA'

interface InstallPromptProps {
  onInstall?: () => void
  onDismiss?: () => void
  autoShow?: boolean
  showAfterDelay?: number
}

const features = [
  {
    icon: WifiIcon,
    title: 'Work Offline',
    description: 'Access your documents and data even without internet'
  },
  {
    icon: BoltIcon,
    title: 'Lightning Fast',
    description: 'Native app performance with instant loading'
  },
  {
    icon: ShieldCheckIcon,
    title: 'Secure & Private',
    description: 'Your legal data stays protected on your device'
  }
]

export default function InstallPrompt({
  onInstall,
  onDismiss,
  autoShow = true,
  showAfterDelay = 30000 // 30 seconds
}: InstallPromptProps) {
  const [isVisible, setIsVisible] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)
  const [installStep, setInstallStep] = useState<'prompt' | 'installing' | 'success' | 'error'>('prompt')
  const [deviceType, setDeviceType] = useState<'mobile' | 'desktop'>('desktop')

  const { 
    isInstallable, 
    isInstalled, 
    isStandalone, 
    install,
    isSupported 
  } = usePWA()

  // Detect device type
  useEffect(() => {
    const checkDeviceType = () => {
      const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)
      setDeviceType(isMobile ? 'mobile' : 'desktop')
    }

    checkDeviceType()
  }, [])

  // Show prompt after delay if conditions are met
  useEffect(() => {
    if (!autoShow || !isSupported || isInstalled || isStandalone || !isInstallable) {
      return
    }

    // Check if user has previously dismissed
    const dismissed = localStorage.getItem('pwa-install-dismissed')
    if (dismissed) {
      const dismissedTime = parseInt(dismissed)
      const daysSinceDismissal = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24)
      
      // Show again after 7 days
      if (daysSinceDismissal < 7) {
        return
      }
    }

    const timer = setTimeout(() => {
      setIsVisible(true)
    }, showAfterDelay)

    return () => clearTimeout(timer)
  }, [autoShow, showAfterDelay, isSupported, isInstalled, isStandalone, isInstallable])

  // Handle install
  const handleInstall = async () => {
    setInstallStep('installing')
    
    try {
      const success = await install()
      
      if (success) {
        setInstallStep('success')
        onInstall?.()
        
        // Hide after success
        setTimeout(() => {
          setIsVisible(false)
        }, 3000)
      } else {
        setInstallStep('error')
        
        // Return to prompt after error
        setTimeout(() => {
          setInstallStep('prompt')
        }, 3000)
      }
    } catch (error) {
      console.error('Installation failed:', error)
      setInstallStep('error')
      
      setTimeout(() => {
        setInstallStep('prompt')
      }, 3000)
    }
  }

  // Handle dismiss
  const handleDismiss = () => {
    setIsVisible(false)
    setIsDismissed(true)
    
    // Remember dismissal
    localStorage.setItem('pwa-install-dismissed', Date.now().toString())
    
    onDismiss?.()
  }

  // Don't show if not supported or already installed
  if (!isSupported || isInstalled || isStandalone || !isInstallable) {
    return null
  }

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 100 }}
          className="fixed bottom-4 left-4 right-4 z-50 max-w-md mx-auto lg:left-auto lg:right-8 lg:bottom-8"
        >
          <div className="bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
            {/* Header */}
            <div className="relative bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4 text-white">
              <button
                onClick={handleDismiss}
                className="absolute top-4 right-4 p-1 hover:bg-white/20 rounded-lg transition-colors"
                aria-label="Close install prompt"
              >
                <XMarkIcon className="w-5 h-5" />
              </button>
              
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-white/20 rounded-xl flex items-center justify-center">
                  {deviceType === 'mobile' ? (
                    <DevicePhoneMobileIcon className="w-6 h-6" />
                  ) : (
                    <ComputerDesktopIcon className="w-6 h-6" />
                  )}
                </div>
                
                <div>
                  <h3 className="text-lg font-semibold">Install Legal AI</h3>
                  <p className="text-blue-100 text-sm">
                    Get the full app experience
                  </p>
                </div>
              </div>
            </div>

            {/* Content */}
            <div className="p-6">
              {installStep === 'prompt' && (
                <>
                  <div className="space-y-4 mb-6">
                    {features.map((feature, index) => {
                      const Icon = feature.icon
                      return (
                        <div key={index} className="flex items-start space-x-3">
                          <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                            <Icon className="w-4 h-4 text-blue-600" />
                          </div>
                          <div>
                            <h4 className="font-medium text-gray-900 text-sm">
                              {feature.title}
                            </h4>
                            <p className="text-gray-600 text-sm">
                              {feature.description}
                            </p>
                          </div>
                        </div>
                      )
                    })}
                  </div>

                  <div className="flex space-x-3">
                    <button
                      onClick={handleInstall}
                      className="flex-1 bg-blue-600 text-white px-4 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors flex items-center justify-center space-x-2"
                    >
                      <ArrowDownTrayIcon className="w-5 h-5" />
                      <span>Install App</span>
                    </button>
                    
                    <button
                      onClick={handleDismiss}
                      className="px-4 py-3 text-gray-600 hover:text-gray-800 font-medium"
                    >
                      Not now
                    </button>
                  </div>

                  <p className="text-xs text-gray-500 mt-3 text-center">
                    Free up space by installing instead of using the browser
                  </p>
                </>
              )}

              {installStep === 'installing' && (
                <div className="text-center py-8">
                  <div className="animate-spin w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    Installing Legal AI...
                  </h4>
                  <p className="text-gray-600 text-sm">
                    This will only take a moment
                  </p>
                </div>
              )}

              {installStep === 'success' && (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ type: 'spring', delay: 0.2 }}
                    >
                      <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </motion.div>
                  </div>
                  
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    Successfully Installed!
                  </h4>
                  <p className="text-gray-600 text-sm">
                    Legal AI is now available on your {deviceType}
                  </p>
                </div>
              )}

              {installStep === 'error' && (
                <div className="text-center py-8">
                  <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <XMarkIcon className="w-8 h-8 text-red-600" />
                  </div>
                  
                  <h4 className="text-lg font-medium text-gray-900 mb-2">
                    Installation Failed
                  </h4>
                  <p className="text-gray-600 text-sm mb-4">
                    Something went wrong. Please try again.
                  </p>
                  
                  <button
                    onClick={() => setInstallStep('prompt')}
                    className="text-blue-600 hover:text-blue-700 font-medium text-sm"
                  >
                    Try Again
                  </button>
                </div>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

// Manual install prompt component
export function ManualInstallPrompt() {
  const [isVisible, setIsVisible] = useState(false)
  const { isInstallable, install } = usePWA()

  const handleInstall = async () => {
    try {
      await install()
      setIsVisible(false)
    } catch (error) {
      console.error('Manual install failed:', error)
    }
  }

  if (!isInstallable) return null

  return (
    <>
      <button
        onClick={() => setIsVisible(true)}
        className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        <ArrowDownTrayIcon className="w-4 h-4" />
        <span>Install App</span>
      </button>

      <AnimatePresence>
        {isVisible && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
            onClick={() => setIsVisible(false)}
          >
            <motion.div
              initial={{ scale: 0.9, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.9, opacity: 0 }}
              onClick={(e) => e.stopPropagation()}
              className="bg-white rounded-2xl p-6 max-w-md w-full"
            >
              <div className="text-center">
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <ArrowDownTrayIcon className="w-8 h-8 text-blue-600" />
                </div>
                
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Install Legal AI
                </h3>
                
                <p className="text-gray-600 mb-6">
                  Get faster access, work offline, and enjoy a native app experience.
                </p>
                
                <div className="flex space-x-3">
                  <button
                    onClick={handleInstall}
                    className="flex-1 bg-blue-600 text-white px-4 py-3 rounded-xl font-medium hover:bg-blue-700 transition-colors"
                  >
                    Install Now
                  </button>
                  
                  <button
                    onClick={() => setIsVisible(false)}
                    className="px-4 py-3 text-gray-600 hover:text-gray-800 font-medium"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  )
}