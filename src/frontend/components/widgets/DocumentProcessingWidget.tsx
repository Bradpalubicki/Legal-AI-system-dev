import React, { useEffect, useState } from 'react'
import { FileText, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import { DocumentStatus } from '../../hooks/useRealTimeData'

interface DocumentProcessingWidgetProps {
  filters: {
    timeRange: string
    caseType: string
    priority: string
  }
  realTimeData: any
  isSelected: boolean
}

export const DocumentProcessingWidget: React.FC<DocumentProcessingWidgetProps> = ({
  filters,
  realTimeData,
  isSelected
}) => {
  const [processingData, setProcessingData] = useState({
    processing: 0,
    completed: 0,
    failed: 0,
    queue: [] as DocumentStatus[]
  })

  useEffect(() => {
    if (realTimeData?.documents) {
      setProcessingData(realTimeData.documents)
    }
  }, [realTimeData])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'text-blue-600'
      case 'completed': return 'text-green-600'
      case 'failed': return 'text-red-600'
      default: return 'text-gray-600'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing': return <Clock className="w-4 h-4" />
      case 'completed': return <CheckCircle className="w-4 h-4" />
      case 'failed': return <XCircle className="w-4 h-4" />
      default: return <AlertCircle className="w-4 h-4" />
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'bg-red-100 text-red-800'
      case 'medium': return 'bg-yellow-100 text-yellow-800'
      case 'low': return 'bg-green-100 text-green-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="h-full flex flex-col">
      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-2 mb-4">
        <div className="bg-blue-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-blue-600">Processing</p>
              <p className="text-2xl font-bold text-blue-900">{processingData.processing}</p>
            </div>
            <Clock className="w-8 h-8 text-blue-500" />
          </div>
        </div>

        <div className="bg-green-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-green-600">Completed</p>
              <p className="text-2xl font-bold text-green-900">{processingData.completed}</p>
            </div>
            <CheckCircle className="w-8 h-8 text-green-500" />
          </div>
        </div>

        <div className="bg-red-50 p-3 rounded-lg">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-red-600">Failed</p>
              <p className="text-2xl font-bold text-red-900">{processingData.failed}</p>
            </div>
            <XCircle className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Processing Queue */}
      <div className="flex-1 overflow-auto">
        <h4 className="text-sm font-medium text-gray-700 mb-2">Processing Queue</h4>

        {processingData.queue.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>No documents in queue</p>
          </div>
        ) : (
          <div className="space-y-2">
            {processingData.queue.map((doc) => (
              <div key={doc.id} className="bg-gray-50 p-3 rounded-lg border">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1 min-w-0">
                    <h5 className="text-sm font-medium text-gray-900 truncate">
                      {doc.name}
                    </h5>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`flex items-center space-x-1 text-xs ${getStatusColor(doc.status)}`}>
                        {getStatusIcon(doc.status)}
                        <span className="capitalize">{doc.status}</span>
                      </span>
                      <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(doc.priority)}`}>
                        {doc.priority}
                      </span>
                    </div>
                  </div>
                </div>

                {doc.status === 'processing' && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-xs text-gray-600">
                      <span>Progress: {doc.progress}%</span>
                      <span>ETA: {formatTime(doc.estimatedTime)}</span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${doc.progress}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {isSelected && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          <div className="flex space-x-2">
            <button className="flex-1 px-3 py-2 text-xs bg-blue-500 text-white rounded hover:bg-blue-600">
              Upload Document
            </button>
            <button className="flex-1 px-3 py-2 text-xs bg-gray-500 text-white rounded hover:bg-gray-600">
              View All
            </button>
          </div>
        </div>
      )}
    </div>
  )
}