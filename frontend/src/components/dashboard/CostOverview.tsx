import { Card, CardHeader, CardBody } from '../ui'
import { BanknotesIcon, ArrowTrendingUpIcon, ArrowTrendingDownIcon } from '@heroicons/react/24/outline'
import type { DashboardData } from '../../types/cost'

interface CostOverviewProps {
  data: DashboardData
}

export default function CostOverview({ data }: CostOverviewProps) {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const calculateChange = (current: number, previous: number) => {
    if (previous === 0) return 0
    return ((current - previous) / previous) * 100
  }

  const monthlyChange = data.costTrends.length > 1 
    ? calculateChange(data.costTrends[0].amount, data.costTrends[1].amount)
    : 0

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {/* Total Cost */}
      <Card>
        <CardBody>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BanknotesIcon className="h-6 w-6 text-gray-400" />
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Total Cost (YTD)
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {formatCurrency(data.totalCost)}
                </dd>
              </dl>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Monthly Spend */}
      <Card>
        <CardBody>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-6 w-6 text-gray-400">💳</div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  This Month
                </dt>
                <dd className="flex items-baseline">
                  <div className="text-lg font-medium text-gray-900">
                    {formatCurrency(data.monthlySpend)}
                  </div>
                  <div className={`ml-2 flex items-baseline text-sm font-semibold ${
                    monthlyChange >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    {monthlyChange >= 0 ? (
                      <ArrowTrendingUpIcon className="self-center flex-shrink-0 h-4 w-4 text-green-500" />
                    ) : (
                      <ArrowTrendingDownIcon className="self-center flex-shrink-0 h-4 w-4 text-red-500" />
                    )}
                    <span className="sr-only">
                      {monthlyChange >= 0 ? 'Increased' : 'Decreased'} by
                    </span>
                    {Math.abs(monthlyChange).toFixed(1)}%
                  </div>
                </dd>
              </dl>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Budget Utilization */}
      <Card>
        <CardBody>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-6 w-6 text-gray-400">📊</div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Budget Used
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {data.budgetUtilization.toFixed(1)}%
                </dd>
              </dl>
              <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full ${
                    data.budgetUtilization > 90 ? 'bg-red-500' :
                    data.budgetUtilization > 75 ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                  style={{ width: `${Math.min(data.budgetUtilization, 100)}%` }}
                />
              </div>
            </div>
          </div>
        </CardBody>
      </Card>

      {/* Projected Spend */}
      <Card>
        <CardBody>
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="h-6 w-6 text-gray-400">🔮</div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="text-sm font-medium text-gray-500 truncate">
                  Projected (Month)
                </dt>
                <dd className="text-lg font-medium text-gray-900">
                  {formatCurrency(data.projectedSpend)}
                </dd>
              </dl>
            </div>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}