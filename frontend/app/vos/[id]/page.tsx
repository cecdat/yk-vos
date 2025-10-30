'use client'
import React, { useEffect, useState } from 'react'
import api from '../../../lib/api'
import Card from '../../../components/ui/Card'
import Table from '../../../components/ui/Table'
import SimpleLine from '../../../components/charts/LineChart'

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

export default function VosDetail({ params }: any) {
  const id = params?.id
  const [online, setOnline] = useState<any[]>([])
  const [cdrs, setCdrs] = useState<any[]>([])
  const [periodType, setPeriodType] = useState<'day' | 'month' | 'quarter' | 'year'>('day')
  const [vosStats, setVosStats] = useState<Statistics[]>([])
  const [accountStats, setAccountStats] = useState<AccountStatistics[]>([])
  const [gatewayStats, setGatewayStats] = useState<GatewayStatistics[]>([])
  const [loading, setLoading] = useState(false)
  const [instanceName, setInstanceName] = useState('')
  const [statMsg, setStatMsg] = useState<string | null>(null);
  const [statError, setStatError] = useState<string | null>(null);
  const [statPending, setStatPending] = useState<boolean>(false);

  useEffect(() => {
    if (id) {
      fetchOnline()
      fetchCdrs()
      fetchStatistics()
      fetchInstanceInfo()
    }
  }, [id, periodType])

  async function fetchInstanceInfo() {
    try {
      const res = await api.get(`/vos/instances/${id}`)
      setInstanceName(res.data?.name || `节点 ${id}`)
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchOnline() {
    try {
      const res = await api.get(`/vos/instances/${id}/phones/online`)
      const data = res.data || {}
      const list = data.infoPhoneOnlines || data || []
      setOnline(list)
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchCdrs() {
    try {
      const res = await api.get(`/cdr/history?vos_id=${id}&limit=50`)
      setCdrs(res.data || [])
    } catch (e) {
      console.error(e)
    }
  }

  async function fetchStatistics() {
    setLoading(true)
    try {
      const res = await api.get(`/vos/instances/${id}/statistics`, {
        params: { period_type: periodType }
      })
      setVosStats(res.data?.vos_statistics || [])
      setAccountStats(res.data?.account_statistics || [])
      setGatewayStats(res.data?.gateway_statistics || [])
    } catch (e) {
      console.error('获取统计数据失败:', e)
      setVosStats([])
      setAccountStats([])
      setGatewayStats([])
    } finally {
      setLoading(false)
    }
  }

  async function triggerStatisticsCalculation() {
    setStatPending(true);
    setStatMsg(null);
    setStatError(null);
    try {
      await api.post(`/vos/instances/${id}/statistics/calculate`, null, {
        params: { period_types: periodType }
      });
      setStatMsg('统计任务已提交，请稍后刷新查看结果');
      setTimeout(() => fetchStatistics(), 3000);
    } catch (e: any) {
      setStatError('触发统计失败: ' + (e.response?.data?.detail || e.message));
    } finally {
      setStatPending(false);
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

  // 生成图表数据（费用趋势）
  const feeChartData = vosStats.slice(0, 30).reverse().map(stat => ({
    name: stat.date.substring(5), // 显示 MM-DD
    value: stat.total_fee
  }))

  return (
    <div className='max-w-7xl'>
      <div className='flex justify-between items-center mb-6'>
        <h1 className='text-3xl font-bold text-gray-800'>VOS 节点详情 - {instanceName}</h1>
        {/* 统计周期、手动重算按钮 */}
        <div className='flex gap-2'>
          <select
            value={periodType}
            onChange={(e) => setPeriodType(e.target.value as any)}
            className='px-3 py-2 border rounded-lg'
          >
            <option value='day'>日统计</option>
            <option value='month'>月统计</option>
            <option value='quarter'>季度统计</option>
            <option value='year'>年统计</option>
          </select>
          <button
            onClick={triggerStatisticsCalculation}
            className={`px-4 py-2 rounded-lg text-white ${statPending ? 'bg-gray-300' : 'bg-blue-600 hover:bg-blue-700'}`}
            disabled={statPending}
          >
            {statPending ? '计算中...' : '重新计算统计'}
          </button>
        </div>
        {statMsg && <div className="mt-2 text-green-600">{statMsg}</div>}
        {statError && <div className="mt-2 text-red-600">{statError}</div>}
      </div>

      {/* 概览卡片 */}
      <div className='grid grid-cols-1 md:grid-cols-4 gap-4 mb-6'>
        <Card>
          <h3 className='text-sm text-gray-600 mb-1'>在线话机</h3>
          <p className='text-2xl font-bold'>{online.length}</p>
        </Card>
        <Card>
          <h3 className='text-sm text-gray-600 mb-1'>总费用 ({periodLabels[periodType]})</h3>
          <p className='text-2xl font-bold text-green-600'>
            {formatFee(vosStats.reduce((sum, s) => sum + s.total_fee, 0))}
          </p>
        </Card>
        <Card>
          <h3 className='text-sm text-gray-600 mb-1'>总通话时长 ({periodLabels[periodType]})</h3>
          <p className='text-2xl font-bold text-blue-600'>
            {formatDuration(vosStats.reduce((sum, s) => sum + s.total_duration, 0))}
          </p>
        </Card>
        <Card>
          <h3 className='text-sm text-gray-600 mb-1'>平均接通率 ({periodLabels[periodType]})</h3>
          <p className='text-2xl font-bold text-purple-600'>
            {vosStats.length > 0
              ? (vosStats.reduce((sum, s) => sum + s.connection_rate, 0) / vosStats.length).toFixed(1) + '%'
              : '0%'}
          </p>
        </Card>
      </div>

      {/* 费用趋势图 */}
      {feeChartData.length > 0 && (
        <Card className='mb-6'>
          <h2 className='text-xl font-bold mb-4'>费用趋势</h2>
          <SimpleLine data={feeChartData} />
        </Card>
      )}

      {/* VOS节点统计表格 */}
      <Card className='mb-6'>
        <h2 className='text-xl font-bold mb-4'>节点统计（{periodLabels[periodType]}）</h2>
        {loading ? (
          <div className='text-center py-8'>加载中...</div>
        ) : vosStats.length === 0 ? (
          <div className='text-center py-8 text-gray-500'>
            暂无统计数据，点击"重新计算统计"按钮生成数据
          </div>
        ) : (
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
                {vosStats.map((stat, idx) => (
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
        )}
      </Card>

      {/* 账户统计表格 */}
      {accountStats.length > 0 && (
        <Card className='mb-6'>
          <h2 className='text-xl font-bold mb-4'>账户统计（{periodLabels[periodType]}）</h2>
          <div className='overflow-x-auto'>
            <table className='min-w-full divide-y divide-gray-200'>
              <thead className='bg-gray-50'>
                <tr>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>账户名称</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>日期</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总费用</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>通话时长</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总通话数</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通数</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通率</th>
                </tr>
              </thead>
              <tbody className='bg-white divide-y divide-gray-200'>
                {accountStats.slice(0, 50).map((stat, idx) => (
                  <tr key={idx}>
                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium'>{stat.account_name}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.date}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm text-green-600'>
                      {formatFee(stat.total_fee)}
                    </td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{formatDuration(stat.total_duration)}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.total_calls}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.connected_calls}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.connection_rate.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {accountStats.length > 50 && (
            <div className='mt-4 text-sm text-gray-500 text-center'>
              显示前50条，共 {accountStats.length} 条记录
            </div>
          )}
        </Card>
      )}

      {/* 网关统计表格 */}
      {gatewayStats.length > 0 && (
        <Card className='mb-6'>
          <h2 className='text-xl font-bold mb-4'>网关统计（{periodLabels[periodType]}）</h2>
          <div className='overflow-x-auto'>
            <table className='min-w-full divide-y divide-gray-200'>
              <thead className='bg-gray-50'>
                <tr>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>落地网关</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>日期</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总费用</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>通话时长</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>总通话数</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通数</th>
                  <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase'>接通率</th>
                </tr>
              </thead>
              <tbody className='bg-white divide-y divide-gray-200'>
                {gatewayStats.slice(0, 50).map((stat, idx) => (
                  <tr key={idx}>
                    <td className='px-6 py-4 whitespace-nowrap text-sm font-medium'>{stat.gateway_name}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.date}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm text-green-600'>
                      {formatFee(stat.total_fee)}
                    </td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{formatDuration(stat.total_duration)}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.total_calls}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.connected_calls}</td>
                    <td className='px-6 py-4 whitespace-nowrap text-sm'>{stat.connection_rate.toFixed(1)}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {gatewayStats.length > 50 && (
            <div className='mt-4 text-sm text-gray-500 text-center'>
              显示前50条，共 {gatewayStats.length} 条记录
            </div>
          )}
        </Card>
      )}

      {/* 原始数据（在线话机、最近话单） */}
      <div className='mt-6 grid grid-cols-1 md:grid-cols-2 gap-4'>
        <Card>
          <h2 className='text-lg mb-2'>在线话机</h2>
          <Table columns={['详情']} rows={online.slice(0, 10)} />
          {online.length > 10 && (
            <div className='mt-2 text-sm text-gray-500 text-center'>
              显示前10条，共 {online.length} 条
            </div>
          )}
        </Card>
        <Card>
          <h2 className='text-lg mb-2'>最近话单（最近50）</h2>
          <Table columns={['开始时间', '呼叫方', '被叫方', '时长(s)', 'cost']} rows={cdrs} />
        </Card>
      </div>
    </div>
  )
}
