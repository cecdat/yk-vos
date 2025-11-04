'use client'
import { useState, useEffect } from 'react'
import React from 'react'
import { useVOS } from '../../contexts/VOSContext'
import api from '../../lib/api'
import Card from '../../components/ui/Card'
import SimpleLine from '../../components/charts/LineChart'
import SimplePie from '../../components/charts/PieChart'

interface Statistics {
  date: string
  total_fee: number
  total_duration: number
  total_calls: number
  connected_calls: number
  connection_rate: number
}

interface AccountStatistics extends Statistics {
  account_name: string
}

interface GatewayStatistics extends Statistics {
  gateway_name: string
}

interface InstanceStatistics {
  instance_id: number
  instance_name: string
  period_type: string
  vos_statistics: Statistics[]
  account_statistics: AccountStatistics[]
  gateway_statistics: GatewayStatistics[]
  loading?: boolean
  error?: string
}

export default function StatisticsPage() {
  const { currentVOS } = useVOS()
  const [instanceStats, setInstanceStats] = useState<InstanceStatistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [periodType, setPeriodType] = useState<'day' | 'month' | 'quarter' | 'year'>('day')

  useEffect(() => {
    if (currentVOS && currentVOS.vos_uuid) {
      fetchInstanceStatistics(currentVOS.id)
    } else {
      setInstanceStats(null)
      setLoading(false)
    }
  }, [currentVOS, periodType])

  async function fetchInstanceStatistics(instanceId: number) {
    setLoading(true)
    setInstanceStats(prev => ({ ...prev, loading: true, error: undefined } as InstanceStatistics | null))

    try {
      const res = await api.get(`/vos/instances/${instanceId}/statistics`, {
        params: { period_type: periodType }
      })
      setInstanceStats({
        instance_id: instanceId,
        instance_name: res.data?.instance_name || '',
        period_type: periodType,
        vos_statistics: res.data?.vos_statistics || [],
        account_statistics: res.data?.account_statistics || [],
        gateway_statistics: res.data?.gateway_statistics || [],
        loading: false
      })
    } catch (e: any) {
      console.error(`获取实例 ${instanceId} 统计数据失败:`, e)
      setInstanceStats({
        instance_id: instanceId,
        instance_name: currentVOS?.name || '',
        period_type: periodType,
        vos_statistics: [],
        account_statistics: [],
        gateway_statistics: [],
        loading: false,
        error: e.response?.data?.detail || e.message || '获取统计数据失败'
      })
    } finally {
      setLoading(false)
    }
  }

  // 格式化时长（秒转小时分钟）
  function formatDuration(seconds: number): string {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`
    }
    return `${minutes}分钟`
  }

  // 格式化费用
  function formatFee(fee: number): string {
    return `¥${fee.toFixed(2)}`
  }

  const periodLabels = {
    day: '日',
    month: '月',
    quarter: '季度',
    year: '年'
  }

  if (loading) {
    return (
      <div className='flex items-center justify-center py-20'>
        <svg className='animate-spin h-10 w-10 text-blue-600' fill='none' viewBox='0 0 24 24'>
          <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' />
          <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z' />
        </svg>
      </div>
    )
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          数据统计
        </h1>
        <div className='flex items-center gap-3'>
          <select
            value={periodType}
            onChange={(e) => setPeriodType(e.target.value as any)}
            className='px-3 py-2 border rounded-lg bg-white'
          >
            <option value='day'>日统计</option>
            <option value='month'>月统计</option>
            <option value='quarter'>季度统计</option>
            <option value='year'>年统计</option>
          </select>
          <button
            onClick={() => currentVOS && fetchInstanceStatistics(currentVOS.id)}
            disabled={loading || !currentVOS}
            className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition flex items-center gap-2 disabled:opacity-50'
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
            </svg>
            刷新数据
          </button>
        </div>
      </div>

      {/* 当前VOS节点统计 */}
      {!currentVOS ? (
        <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
          <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' />
          </svg>
          <h3 className='mt-2 text-lg font-medium text-gray-900'>请先选择 VOS 节点</h3>
          <p className='mt-1 text-sm text-gray-500'>在顶部导航栏选择要查看统计的 VOS 节点</p>
        </div>
      ) : !instanceStats ? (
        <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
          <p className='text-gray-500'>加载中...</p>
        </div>
      ) : instanceStats.error ? (
        <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
          <p className='text-red-600'>错误: {instanceStats.error}</p>
          {!currentVOS.enabled && <p className='text-sm text-gray-500 mt-2'>该实例未启用</p>}
          {!currentVOS.vos_uuid && <p className='text-sm text-gray-500 mt-2'>该实例缺少UUID</p>}
        </div>
      ) : instanceStats.vos_statistics.length === 0 ? (
        <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
          <p className='text-gray-500'>暂无统计数据，请先计算统计数据</p>
        </div>
      ) : (
        <div className='space-y-6'>
          {(() => {
            const vosStats = instanceStats.vos_statistics || []
            const accountStats = instanceStats.account_statistics || []
            const gatewayStats = instanceStats.gateway_statistics || []
            
            // 费用趋势图数据
            const feeChartData = vosStats.slice(0, 30).reverse().map((stat: Statistics) => ({
              name: stat.date.substring(5),
              value: stat.total_fee
            }))
            
            // 账户费用分布（Top 10）
            const accountMap = new Map<string, number>()
            accountStats.forEach((stat: AccountStatistics) => {
              const current = accountMap.get(stat.account_name) || 0
              accountMap.set(stat.account_name, current + stat.total_fee)
            })
            const accountPieData = Array.from(accountMap.entries())
              .map(([name, value]) => ({ name, value }))
              .sort((a, b) => b.value - a.value)
              .slice(0, 10)
            
            // 网关费用分布（Top 10）
            const gatewayMap = new Map<string, number>()
            gatewayStats.forEach((stat: GatewayStatistics) => {
              const current = gatewayMap.get(stat.gateway_name) || 0
              gatewayMap.set(stat.gateway_name, current + stat.total_fee)
            })
            const gatewayPieData = Array.from(gatewayMap.entries())
              .map(([name, value]) => ({ name, value }))
              .sort((a, b) => b.value - a.value)
              .slice(0, 10)
            
            return (
              <Card key={instanceStats.instance_id} className='overflow-hidden'>
                {/* 实例头部 */}
                <div className='p-5 bg-blue-50'>
                  <div className='flex items-center justify-between'>
                    <div className='flex items-center gap-3'>
                      <h2 className='text-xl font-bold text-gray-800'>{instanceStats.instance_name}</h2>
                      <span className='px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full'>当前节点</span>
                    </div>
                    <div className='flex items-center gap-4'>
                      {vosStats.length > 0 && (
                        <div className='text-right'>
                          <p className='text-xs text-gray-500'>总费用</p>
                          <p className='text-lg font-bold text-green-600'>
                            {formatFee(vosStats.reduce((sum, s) => sum + s.total_fee, 0))}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                  {currentVOS?.base_url && (
                    <p className='text-sm text-gray-500 mt-2'>{currentVOS.base_url}</p>
                  )}
                </div>
                
                {/* 统计数据内容 */}
                <div className='border-t border-gray-200 p-5'>
                  {/* 概览卡片 */}
                  <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
                    <div className='bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4'>
                      <h3 className='text-sm text-gray-600 mb-1'>总费用 ({periodLabels[periodType]})</h3>
                      <p className='text-2xl font-bold text-green-600'>
                        {formatFee(vosStats.reduce((sum, s) => sum + s.total_fee, 0))}
                      </p>
                    </div>
                    <div className='bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4'>
                      <h3 className='text-sm text-gray-600 mb-1'>总通话时长 ({periodLabels[periodType]})</h3>
                      <p className='text-2xl font-bold text-blue-600'>
                        {formatDuration(vosStats.reduce((sum, s) => sum + s.total_duration, 0))}
                      </p>
                    </div>
                    <div className='bg-gradient-to-br from-purple-50 to-purple-100 rounded-lg p-4'>
                      <h3 className='text-sm text-gray-600 mb-1'>平均接通率 ({periodLabels[periodType]})</h3>
                      <p className='text-2xl font-bold text-purple-600'>
                        {vosStats.length > 0
                          ? (vosStats.reduce((sum, s) => sum + s.connection_rate, 0) / vosStats.length).toFixed(1) + '%'
                          : '0%'}
                      </p>
                    </div>
                  </div>

                  {/* 费用趋势折线图 */}
                  {feeChartData.length > 0 && (
                    <div className='mb-6'>
                      <h3 className='text-lg font-bold mb-4'>费用趋势图</h3>
                      <SimpleLine data={feeChartData} />
                    </div>
                  )}

                  {/* 账户和网关统计饼图 */}
                  {(accountPieData.length > 0 || gatewayPieData.length > 0) && (
                    <div className='grid grid-cols-1 md:grid-cols-2 gap-4 mb-6'>
                      {accountPieData.length > 0 && (
                        <div>
                          <SimplePie data={accountPieData} title='账户费用分布（Top 10）' />
                        </div>
                      )}
                      {gatewayPieData.length > 0 && (
                        <div>
                          <SimplePie data={gatewayPieData} title='网关费用分布（Top 10）' />
                        </div>
                      )}
                    </div>
                  )}

                  {/* VOS节点统计表格 */}
                  <div className='mb-6'>
                    <h3 className='text-lg font-bold mb-4'>节点统计（{periodLabels[periodType]}）</h3>
                    <div className='overflow-x-auto'>
                      <table className='min-w-full divide-y divide-gray-200'>
                        <thead className='bg-gray-50'>
                          <tr>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>日期</th>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总费用</th>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>通话时长</th>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总通话数</th>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通数</th>
                            <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通率</th>
                          </tr>
                        </thead>
                        <tbody className='bg-white divide-y divide-gray-200'>
                          {vosStats.slice(0, 20).map((stat, idx) => (
                            <tr key={idx}>
                              <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.date}</td>
                              <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600'>
                                {formatFee(stat.total_fee)}
                              </td>
                              <td className='px-6 py-4 whitespace-nowrap text-sm'>{formatDuration(stat.total_duration)}</td>
                              <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.total_calls}</td>
                              <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.connected_calls}</td>
                              <td className='px-6 py-4 whitespace-nowrap text-sm font-medium'>
                                {stat.connection_rate.toFixed(1)}%
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    {vosStats.length > 20 && (
                      <p className='mt-2 text-sm text-gray-500 text-center'>显示前20条，共 {vosStats.length} 条记录</p>
                    )}
                  </div>
                </div>
              </Card>
            )
          })()}
        </div>
      )}
    </div>
  )
}

