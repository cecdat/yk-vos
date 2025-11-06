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
  gateway_type: 'caller' | 'callee'
  gateway_type_label: string
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
  
  // 日期选择状态
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')

  // 初始化日期范围（默认最近30天）
  useEffect(() => {
    const today = new Date()
    const thirtyDaysAgo = new Date(today)
    thirtyDaysAgo.setDate(today.getDate() - 30)
    
    setEndDate(today.toISOString().split('T')[0])
    setStartDate(thirtyDaysAgo.toISOString().split('T')[0])
  }, [])

  useEffect(() => {
    if (currentVOS && currentVOS.vos_uuid && startDate && endDate) {
      fetchInstanceStatistics(currentVOS.id)
    } else {
      setInstanceStats(null)
      setLoading(false)
    }
  }, [currentVOS, periodType, startDate, endDate])

  async function fetchInstanceStatistics(instanceId: number) {
    setLoading(true)
    setInstanceStats(prev => prev ? ({ ...prev, loading: true, error: undefined } as InstanceStatistics) : null)

    try {
      const params: any = { period_type: periodType }
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate

      const res = await api.get(`/vos/instances/${instanceId}/statistics`, { params })
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

  // 快速选择日期范围
  function setQuickDateRange(days: number) {
    const today = new Date()
    const start = new Date(today)
    start.setDate(today.getDate() - days)
    setStartDate(start.toISOString().split('T')[0])
    setEndDate(today.toISOString().split('T')[0])
  }

  // 根据周期类型获取日期选择器的类型
  function getDateInputType(): 'date' | 'month' | undefined {
    if (periodType === 'month') return 'month'
    if (periodType === 'year') return undefined // 年份需要特殊处理
    return 'date'
  }

  // 年份选择器
  function renderYearSelector() {
    const currentYear = new Date().getFullYear()
    const years = Array.from({ length: 5 }, (_, i) => currentYear - i)
    
    return (
      <div className='flex items-center gap-2'>
        <select
          value={startDate ? startDate.substring(0, 4) : ''}
          onChange={(e) => {
            const year = e.target.value
            setStartDate(`${year}-01-01`)
            setEndDate(`${year}-12-31`)
          }}
          className='px-3 py-2 border rounded-lg bg-white'
        >
          <option value=''>选择年份</option>
          {years.map(year => (
            <option key={year} value={year}>{year}年</option>
          ))}
        </select>
      </div>
    )
  }

  // 季度选择器
  function renderQuarterSelector() {
    const currentYear = new Date().getFullYear()
    const quarters = [
      { label: 'Q1 (1-3月)', value: 'Q1', start: '01-01', end: '03-31' },
      { label: 'Q2 (4-6月)', value: 'Q2', start: '04-01', end: '06-30' },
      { label: 'Q3 (7-9月)', value: 'Q3', start: '07-01', end: '09-30' },
      { label: 'Q4 (10-12月)', value: 'Q4', start: '10-01', end: '12-31' },
    ]
    
    // 根据当前选择的日期范围反推季度
    let selectedQuarter = ''
    if (startDate && endDate) {
      const quarter = quarters.find(q => {
        const startStr = `${currentYear}-${q.start}`
        const endStr = `${currentYear}-${q.end}`
        return startDate.startsWith(`${currentYear}-${q.start.substring(0, 2)}`) && 
               endDate.startsWith(`${currentYear}-${q.end.substring(0, 2)}`)
      })
      if (quarter) {
        selectedQuarter = quarter.value
      }
    }
    
    return (
      <div className='flex items-center gap-2'>
        <select
          value={selectedQuarter}
          onChange={(e) => {
            const quarterValue = e.target.value
            if (quarterValue) {
              const quarter = quarters.find(q => q.value === quarterValue)
              if (quarter) {
                const year = currentYear
                setStartDate(`${year}-${quarter.start}`)
                setEndDate(`${year}-${quarter.end}`)
              }
            } else {
              setStartDate('')
              setEndDate('')
            }
          }}
          className='px-3 py-2 border rounded-lg bg-white'
        >
          <option value=''>选择季度</option>
          {quarters.map(q => (
            <option key={q.value} value={q.value}>{currentYear}年 {q.label}</option>
          ))}
        </select>
      </div>
    )
  }

  const periodLabels = {
    day: '日',
    month: '月',
    quarter: '季度',
    year: '年'
  }

  if (loading && !instanceStats) {
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
      <div className='flex items-center justify-between mb-6 flex-wrap gap-4'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          数据统计
        </h1>
        <div className='flex items-center gap-3 flex-wrap'>
          {/* 周期类型选择 */}
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

          {/* 日期选择器 */}
          {periodType === 'year' ? (
            renderYearSelector()
          ) : periodType === 'quarter' ? (
            renderQuarterSelector()
          ) : periodType === 'month' ? (
            <div className='flex items-center gap-2'>
              <input
                type='month'
                value={startDate ? startDate.substring(0, 7) : ''}
                onChange={(e) => {
                  const monthValue = e.target.value
                  if (monthValue) {
                    const [year, month] = monthValue.split('-')
                    const lastDay = new Date(parseInt(year), parseInt(month), 0).getDate()
                    setStartDate(`${monthValue}-01`)
                    setEndDate(`${monthValue}-${lastDay.toString().padStart(2, '0')}`)
                  }
                }}
                className='px-3 py-2 border rounded-lg bg-white'
              />
            </div>
          ) : (
            <div className='flex items-center gap-2'>
              <input
                type='date'
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className='px-3 py-2 border rounded-lg bg-white'
              />
              <span className='text-gray-500'>至</span>
              <input
                type='date'
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className='px-3 py-2 border rounded-lg bg-white'
              />
              {/* 快速选择 */}
              <div className='flex items-center gap-1 ml-2'>
                <button
                  onClick={() => setQuickDateRange(7)}
                  className='px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition'
                >
                  最近7天
                </button>
                <button
                  onClick={() => setQuickDateRange(30)}
                  className='px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition'
                >
                  最近30天
                </button>
                <button
                  onClick={() => setQuickDateRange(90)}
                  className='px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition'
                >
                  最近90天
                </button>
              </div>
            </div>
          )}

          <button
            onClick={() => currentVOS && fetchInstanceStatistics(currentVOS.id)}
            disabled={loading || !currentVOS || !startDate || !endDate}
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
      ) : !instanceStats.vos_statistics || instanceStats.vos_statistics.length === 0 ? (
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
            
            // 网关费用分布（Top 10，区分对接网关和落地网关）
            const gatewayMap = new Map<string, number>()
            gatewayStats.forEach((stat: GatewayStatistics) => {
              const key = `${stat.gateway_name} (${stat.gateway_type_label})`
              const current = gatewayMap.get(key) || 0
              gatewayMap.set(key, current + stat.total_fee)
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

                  {/* 网关统计表格（拆分为对接网关和落地网关两个独立表格） */}
                  {(() => {
                    // 按网关名称和类型汇总数据
                    const gatewayMap = new Map<string, {
                      gateway_name: string
                      gateway_type: 'caller' | 'callee'
                      gateway_type_label: string
                      total_fee: number
                      total_duration: number
                      total_calls: number
                      connected_calls: number
                      connection_rate: number
                      avg_duration: number
                    }>()
                    
                    gatewayStats.forEach((stat: GatewayStatistics) => {
                      const key = `${stat.gateway_name}_${stat.gateway_type}`
                      const existing = gatewayMap.get(key)
                      
                      if (existing) {
                        // 累加数据
                        existing.total_fee += stat.total_fee
                        existing.total_duration += stat.total_duration
                        existing.total_calls += stat.total_calls
                        existing.connected_calls += stat.connected_calls
                      } else {
                        // 新建记录
                        gatewayMap.set(key, {
                          gateway_name: stat.gateway_name,
                          gateway_type: stat.gateway_type,
                          gateway_type_label: stat.gateway_type_label,
                          total_fee: stat.total_fee,
                          total_duration: stat.total_duration,
                          total_calls: stat.total_calls,
                          connected_calls: stat.connected_calls,
                          connection_rate: 0, // 稍后计算
                          avg_duration: 0 // 稍后计算
                        })
                      }
                    })
                    
                    // 计算接通率和平均通话时长
                    const aggregatedStats = Array.from(gatewayMap.values()).map(gateway => {
                      const connection_rate = gateway.total_calls > 0
                        ? (gateway.connected_calls / gateway.total_calls) * 100
                        : 0
                      const avg_duration = gateway.connected_calls > 0
                        ? gateway.total_duration / gateway.connected_calls
                        : 0
                      
                      return {
                        ...gateway,
                        connection_rate: Math.round(connection_rate * 100) / 100,
                        avg_duration: Math.round(avg_duration)
                      }
                    }).sort((a, b) => b.total_fee - a.total_fee) // 按费用降序排序
                    
                    // 拆分为对接网关和落地网关
                    const callerGateways = aggregatedStats.filter(g => g.gateway_type === 'caller')
                    const calleeGateways = aggregatedStats.filter(g => g.gateway_type === 'callee')
                    
                    // 渲染单个网关表格的辅助函数
                    const renderGatewayTable = (gateways: typeof aggregatedStats, title: string, type: 'caller' | 'callee') => {
                      if (gateways.length === 0) {
                        return (
                          <div className='mb-6'>
                            <h3 className='text-lg font-bold mb-4'>{title}（{periodLabels[periodType]}）</h3>
                            <div className='overflow-x-auto'>
                              <div className='text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300'>
                                <svg className='mx-auto h-12 w-12 text-gray-400 mb-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
                                </svg>
                                <p className='text-gray-500 text-lg font-medium'>暂无{title}数据</p>
                                <p className='text-gray-400 text-sm mt-2'>请先计算统计数据或检查数据范围</p>
                              </div>
                            </div>
                          </div>
                        )
                      }
                      
                      return (
                        <div className='mb-6'>
                          <h3 className='text-lg font-bold mb-4'>{title}（{periodLabels[periodType]}）</h3>
                          <div className='overflow-x-auto'>
                            <table className='min-w-full divide-y divide-gray-200'>
                              <thead className='bg-gray-50'>
                                <tr>
                                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>网关名称</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>费用总计</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>通话时长总计</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>总通话数</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>接通数</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>接通率</th>
                                  <th className='px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase'>平均通话时长</th>
                                </tr>
                              </thead>
                              <tbody className='bg-white divide-y divide-gray-200'>
                                {gateways.map((gateway, idx) => (
                                  <tr key={idx} className='hover:bg-gray-50'>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium'>{gateway.gateway_name}</td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600 text-right'>
                                      {formatFee(gateway.total_fee)}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-right'>
                                      {formatDuration(gateway.total_duration)}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-right'>
                                      {gateway.total_calls.toLocaleString()}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-right'>
                                      {gateway.connected_calls.toLocaleString()}
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-right'>
                                      {gateway.connection_rate.toFixed(2)}%
                                    </td>
                                    <td className='px-6 py-4 whitespace-nowrap text-sm text-right'>
                                      {formatDuration(gateway.avg_duration)}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                              <tfoot className='bg-gray-50'>
                                <tr>
                                  <td className='px-6 py-3 text-sm font-bold text-gray-700'>合计</td>
                                  <td className='px-6 py-3 text-sm font-bold text-green-600 text-right'>
                                    {formatFee(gateways.reduce((sum, g) => sum + g.total_fee, 0))}
                                  </td>
                                  <td className='px-6 py-3 text-sm font-bold text-right'>
                                    {formatDuration(gateways.reduce((sum, g) => sum + g.total_duration, 0))}
                                  </td>
                                  <td className='px-6 py-3 text-sm font-bold text-right'>
                                    {gateways.reduce((sum, g) => sum + g.total_calls, 0).toLocaleString()}
                                  </td>
                                  <td className='px-6 py-3 text-sm font-bold text-right'>
                                    {gateways.reduce((sum, g) => sum + g.connected_calls, 0).toLocaleString()}
                                  </td>
                                  <td className='px-6 py-3 text-sm font-bold text-right'>
                                    {(() => {
                                      const totalCalls = gateways.reduce((sum, g) => sum + g.total_calls, 0)
                                      const connectedCalls = gateways.reduce((sum, g) => sum + g.connected_calls, 0)
                                      const overallRate = totalCalls > 0 ? (connectedCalls / totalCalls) * 100 : 0
                                      return overallRate.toFixed(2) + '%'
                                    })()}
                                  </td>
                                  <td className='px-6 py-3 text-sm font-bold text-right'>
                                    {(() => {
                                      const totalDuration = gateways.reduce((sum, g) => sum + g.total_duration, 0)
                                      const connectedCalls = gateways.reduce((sum, g) => sum + g.connected_calls, 0)
                                      const avgDuration = connectedCalls > 0 ? totalDuration / connectedCalls : 0
                                      return formatDuration(Math.round(avgDuration))
                                    })()}
                                  </td>
                                </tr>
                              </tfoot>
                            </table>
                          </div>
                          <p className='mt-2 text-sm text-gray-500 text-center'>
                            共 {gateways.length} 个{title}
                          </p>
                        </div>
                      )
                    }
                    
                    return (
                      <>
                        {/* 对接网关统计 */}
                        {renderGatewayTable(callerGateways, '对接网关统计', 'caller')}
                        
                        {/* 落地网关统计 */}
                        {renderGatewayTable(calleeGateways, '落地网关统计', 'callee')}
                      </>
                    )
                  })()}
                </div>
              </Card>
            )
          })()}
        </div>
      )}
    </div>
  )
}

