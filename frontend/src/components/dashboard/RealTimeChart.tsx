'use client'

import { useState, useEffect, useRef } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { Card, CardHeader, CardBody } from '../ui'
import { useWebSocketConnection } from '../../hooks/useWebSocket'

interface DataPoint {
  timestamp: string
  time: string
  value: number
  isRealTime?: boolean
}

interface RealTimeChartProps {
  title: string
  dataKey: string
  color?: string
  maxDataPoints?: number
  updateInterval?: number
  initialData?: DataPoint[]
  formatValue?: (value: number) => string
  showReferenceLine?: boolean
  referenceValue?: number
}

export default function RealTimeChart({
  title,
  dataKey,
  color = '#3b82f6',
  maxDataPoints = 20,
  updateInterval = 5000,
  initialData = [],
  formatValue = (value) => value.toString(),
  showReferenceLine = false,
  referenceValue = 0
}: RealTimeChartProps) {
  const [data, setData] = useState<DataPoint[]>(initialData)
  const [isUpdating, setIsUpdating] = useState(false)
  const intervalRef = useRef<NodeJS.Timeout>()
  const { isConnected } = useWebSocketConnection(false)

  // Generate mock real-time data
  const generateDataPoint = (): DataPoint => {
    const now = new Date()
    const baseValue = 100
    const variance = Math.random() * 40 - 20 // -20 to +20
    const trend = Math.sin(Date.now() / 10000) * 10 // Slow sine wave
    
    return {
      timestamp: now.toISOString(),
      time: now.toLocaleTimeString('en-US', { 
        hour12: false, 
        minute: '2-digit', 
        second: '2-digit' 
      }),
      value: Math.max(0, baseValue + variance + trend),
      isRealTime: true
    }
  }

  // Add new data point
  const addDataPoint = () => {
    setIsUpdating(true)
    
    setData(prevData => {
      const newPoint = generateDataPoint()
      const updatedData = [...prevData, newPoint]
      
      // Keep only the most recent points
      if (updatedData.length > maxDataPoints) {
        return updatedData.slice(-maxDataPoints)
      }
      
      return updatedData
    })

    // Animation feedback
    setTimeout(() => setIsUpdating(false), 300)
  }

  // Start/stop real-time updates
  useEffect(() => {
    if (isConnected) {
      intervalRef.current = setInterval(addDataPoint, updateInterval)
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
      }
    }
  }, [isConnected, updateInterval])

  // Initialize with some data points
  useEffect(() => {
    if (data.length === 0) {
      const initialPoints: DataPoint[] = []
      for (let i = maxDataPoints - 5; i < maxDataPoints; i++) {
        const time = new Date(Date.now() - (maxDataPoints - i) * updateInterval)
        initialPoints.push({
          timestamp: time.toISOString(),
          time: time.toLocaleTimeString('en-US', { 
            hour12: false, 
            minute: '2-digit', 
            second: '2-digit' 
          }),
          value: 80 + Math.random() * 40,
          isRealTime: false
        })
      }
      setData(initialPoints)
    }
  }, [])

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const dataPoint = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="text-sm font-medium text-gray-900">{label}</p>
          <p className="text-sm text-gray-600">
            Value: <span className="font-medium text-gray-900">
              {formatValue(payload[0].value)}
            </span>
          </p>
          {dataPoint.isRealTime && (
            <p className="text-xs text-green-600 font-medium">Live</p>
          )}
        </div>
      )
    }
    return null
  }

  const latestValue = data.length > 0 ? data[data.length - 1].value : 0
  const previousValue = data.length > 1 ? data[data.length - 2].value : latestValue
  const changePercent = previousValue ? ((latestValue - previousValue) / previousValue) * 100 : 0

  return (
    <Card className={`transition-all duration-300 ${
      isUpdating ? 'ring-2 ring-green-500 ring-opacity-30' : ''
    }`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-medium text-gray-900">{title}</h3>
            <div className="flex items-center space-x-3 mt-1">
              <div className="text-2xl font-bold text-gray-900">
                {formatValue(latestValue)}
              </div>
              <div className={`text-sm font-medium ${
                changePercent > 0 ? 'text-green-600' : 
                changePercent < 0 ? 'text-red-600' : 'text-gray-600'
              }`}>
                {changePercent > 0 ? '+' : ''}{changePercent.toFixed(1)}%
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${
              isConnected ? 'bg-green-500' : 'bg-gray-400'
            } ${isUpdating ? 'animate-ping' : ''}`} />
            <span className="text-xs text-gray-500">
              {isConnected ? 'Live' : 'Offline'}
            </span>
          </div>
        </div>
      </CardHeader>
      
      <CardBody>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="time" 
                stroke="#6b7280"
                fontSize={12}
                tick={{ fontSize: 10 }}
              />
              <YAxis 
                stroke="#6b7280"
                fontSize={12}
                tickFormatter={(value) => formatValue(value)}
                tick={{ fontSize: 10 }}
              />
              <Tooltip content={<CustomTooltip />} />
              
              {showReferenceLine && referenceValue > 0 && (
                <ReferenceLine 
                  y={referenceValue} 
                  stroke="#ef4444" 
                  strokeDasharray="5 5"
                  label={{ value: "Target", position: "insideTopRight" }}
                />
              )}
              
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke={color}
                strokeWidth={2}
                dot={(props: any) => {
                  if (props.payload?.isRealTime) {
                    return (
                      <circle 
                        cx={props.cx} 
                        cy={props.cy} 
                        r={4} 
                        fill={color}
                        stroke="#fff"
                        strokeWidth={2}
                        className="animate-pulse"
                      />
                    )
                  }
                  return (
                    <circle 
                      cx={props.cx} 
                      cy={props.cy} 
                      r={2} 
                      fill={color}
                    />
                  )
                }}
                activeDot={{ r: 6, fill: color, stroke: '#fff', strokeWidth: 2 }}
                connectNulls={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
        
        {/* Data point indicators */}
        <div className="flex justify-between items-center mt-3 pt-3 border-t border-gray-100">
          <div className="text-xs text-gray-500">
            {data.length} data points
          </div>
          <div className="text-xs text-gray-500">
            Updated every {updateInterval / 1000}s
          </div>
        </div>
      </CardBody>
    </Card>
  )
}