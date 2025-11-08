'use client'
import React, { useState, useEffect } from 'react'
import { useVOS } from '../../contexts/VOSContext'
import api from '../../lib/api'

interface AccountDetailReport {
  id: number
  account: string
  account_name: string
  begin_time: number
  end_time: number
  begin_datetime: string
  end_datetime: string
  report_date: string
  cdr_count: number
  total_fee: number
  total_time: number
  total_suite_fee: number
  total_suite_fee_time: number
  net_fee: number
  net_time: number
  net_count: number
  local_fee: number
  local_time: number
  local_count: number
  domestic_fee: number
  domestic_time: number
  domestic_count: number
  international_fee: number
  international_time: number
  international_count: number
  created_at: string
  updated_at: string
}

interface AccountDetailReportsResponse {
  instance_id: number
  instance_name: string
  reports: AccountDetailReport[]
  total_count: number
}

export default function AccountDetailReportsPage() {
  const { currentVOS } = useVOS()
  const [reports, setReports] = useState<AccountDetailReport[]>([])
  const [loading, setLoading] = useState(false)
  const [startDate, setStartDate] = useState<string>('')
  const [endDate, setEndDate] = useState<string>('')
  const [selectedAccount, setSelectedAccount] = useState<string>('')
  const [accounts, setAccounts] = useState<string[]>([])
  const [summary, setSummary] = useState({
    total_cdr_count: 0,
    total_fee: 0,
    total_time: 0,
    total_domestic_fee: 0,
    total_domestic_time: 0,
    total_domestic_count: 0
  })

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
      if (startDate <= endDate) {
        fetchReports()
      }
    } else {
      setReports([])
      setLoading(false)
    }
  }, [currentVOS, startDate, endDate, selectedAccount])

  async function fetchReports() {
    if (!currentVOS) return

    setLoading(true)
    try {
      const params: any = {}
      if (startDate) params.start_date = startDate
      if (endDate) params.end_date = endDate
      if (selectedAccount) params.account = selectedAccount

      const res = await api.get<AccountDetailReportsResponse>(
        `/vos/instances/${currentVOS.id}/account-detail-reports`,
        { params }
      )
      
      const reportsData = res.data?.reports || []
      setReports(reportsData)
      
      // 提取账户列表
      const uniqueAccounts = Array.from(new Set(reportsData.map(r => r.account))).sort()
      setAccounts(uniqueAccounts)
      
      // 计算汇总数据
      const summaryData = reportsData.reduce((acc, report) => {
        acc.total_cdr_count += report.cdr_count
        acc.total_fee += report.total_fee
        acc.total_time += report.total_time
        acc.total_domestic_fee += report.domestic_fee
        acc.total_domestic_time += report.domestic_time
        acc.total_domestic_count += report.domestic_count
        return acc
      }, {
        total_cdr_count: 0,
        total_fee: 0,
        total_time: 0,
        total_domestic_fee: 0,
        total_domestic_time: 0,
        total_domestic_count: 0
      })
      setSummary(summaryData)
      
    } catch (e: any) {
      console.error('获取账户明细报表失败:', e)
      setReports([])
      setSummary({
        total_cdr_count: 0,
        total_fee: 0,
        total_time: 0,
        total_domestic_fee: 0,
        total_domestic_time: 0,
        total_domestic_count: 0
      })
    } finally {
      setLoading(false)
    }
  }

  // 格式化费用
  function formatFee(fee: number): string {
    return `¥${fee.toFixed(2)}`
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

  // 格式化日期
  function formatDate(dateStr: string): string {
    if (!dateStr) return ''
    return dateStr.substring(0, 10)
  }

  // 按账户分组统计
  const accountSummary = React.useMemo(() => {
    const accountMap = new Map<string, {
      account: string
      account_name: string
      total_cdr_count: number
      total_fee: number
      total_time: number
      total_domestic_fee: number
      total_domestic_time: number
      total_domestic_count: number
      report_count: number
    }>()

    reports.forEach(report => {
      const existing = accountMap.get(report.account) || {
        account: report.account,
        account_name: report.account_name,
        total_cdr_count: 0,
        total_fee: 0,
        total_time: 0,
        total_domestic_fee: 0,
        total_domestic_time: 0,
        total_domestic_count: 0,
        report_count: 0
      }

      existing.total_cdr_count += report.cdr_count
      existing.total_fee += report.total_fee
      existing.total_time += report.total_time
      existing.total_domestic_fee += report.domestic_fee
      existing.total_domestic_time += report.domestic_time
      existing.total_domestic_count += report.domestic_count
      existing.report_count += 1

      accountMap.set(report.account, existing)
    })

    return Array.from(accountMap.values()).sort((a, b) => b.total_fee - a.total_fee)
  }, [reports])

  return (
    <div className='max-w-7xl mx-auto p-6'>
      <h1 className='text-3xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
        账户明细报表
      </h1>

      {!currentVOS ? (
        <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
          <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' />
          </svg>
          <p className='mt-4 text-gray-500'>请先选择VOS节点</p>
        </div>
      ) : (
        <div className='space-y-6'>
          {/* 筛选条件 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <div className='grid grid-cols-1 md:grid-cols-4 gap-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>开始日期</label>
                <input
                  type='date'
                  value={startDate}
                  onChange={(e) => {
                    const newStartDate = e.target.value
                    setStartDate(newStartDate)
                    if (endDate && newStartDate > endDate) {
                      setEndDate(newStartDate)
                    }
                  }}
                  className='w-full px-3 py-2 border rounded-lg bg-white'
                />
              </div>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>结束日期</label>
                <input
                  type='date'
                  value={endDate}
                  onChange={(e) => {
                    const newEndDate = e.target.value
                    setEndDate(newEndDate)
                    if (startDate && newEndDate < startDate) {
                      setStartDate(newEndDate)
                    }
                  }}
                  min={startDate || undefined}
                  className='w-full px-3 py-2 border rounded-lg bg-white'
                />
              </div>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>账户筛选</label>
                <select
                  value={selectedAccount}
                  onChange={(e) => setSelectedAccount(e.target.value)}
                  className='w-full px-3 py-2 border rounded-lg bg-white'
                >
                  <option value=''>全部账户</option>
                  {accounts.map(account => (
                    <option key={account} value={account}>{account}</option>
                  ))}
                </select>
              </div>
              <div className='flex items-end'>
                <button
                  onClick={fetchReports}
                  disabled={loading || !startDate || !endDate}
                  className='w-full px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition flex items-center justify-center gap-2 disabled:opacity-50'
                >
                  <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                  </svg>
                  刷新数据
                </button>
              </div>
            </div>
          </div>

          {/* 汇总统计 */}
          <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
            <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>总话单数</p>
                  <p className='text-2xl font-bold text-gray-800 mt-1'>{summary.total_cdr_count.toLocaleString()}</p>
                </div>
                <div className='w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center'>
                  <svg className='w-6 h-6 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
                  </svg>
                </div>
              </div>
            </div>
            <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>总费用</p>
                  <p className='text-2xl font-bold text-green-600 mt-1'>{formatFee(summary.total_fee)}</p>
                </div>
                <div className='w-12 h-12 bg-green-100 rounded-full flex items-center justify-center'>
                  <svg className='w-6 h-6 text-green-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
                  </svg>
                </div>
              </div>
            </div>
            <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
              <div className='flex items-center justify-between'>
                <div>
                  <p className='text-sm text-gray-500'>总通话时长</p>
                  <p className='text-2xl font-bold text-purple-600 mt-1'>{formatDuration(summary.total_time)}</p>
                </div>
                <div className='w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center'>
                  <svg className='w-6 h-6 text-purple-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* 账户汇总表格 */}
          {accountSummary.length > 0 && (
            <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
              <h2 className='text-xl font-bold mb-4'>账户汇总统计</h2>
              <div className='overflow-x-auto'>
                <table className='w-full'>
                  <thead>
                    <tr className='bg-gray-50 border-b'>
                      <th className='px-4 py-3 text-left text-sm font-medium text-gray-700'>账户号码</th>
                      <th className='px-4 py-3 text-left text-sm font-medium text-gray-700'>账户名称</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>话单数</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>总费用</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>通话时长</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内费用</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内时长</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内数量</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>报表数</th>
                    </tr>
                  </thead>
                  <tbody>
                    {accountSummary.map((account, index) => (
                      <tr key={account.account} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className='px-4 py-3 text-sm text-gray-900'>{account.account}</td>
                        <td className='px-4 py-3 text-sm text-gray-700'>{account.account_name || '-'}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-900'>{account.total_cdr_count.toLocaleString()}</td>
                        <td className='px-4 py-3 text-sm text-right text-green-600 font-medium'>{formatFee(account.total_fee)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-700'>{formatDuration(account.total_time)}</td>
                        <td className='px-4 py-3 text-sm text-right text-blue-600'>{formatFee(account.total_domestic_fee)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-700'>{formatDuration(account.total_domestic_time)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-900'>{account.total_domestic_count.toLocaleString()}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-700'>{account.report_count}</td>
                      </tr>
                    ))}
                    {/* 合计行 */}
                    <tr className='bg-blue-50 font-bold border-t-2 border-blue-200'>
                      <td colSpan={2} className='px-4 py-3 text-sm text-gray-900'>合计</td>
                      <td className='px-4 py-3 text-sm text-right text-gray-900'>{summary.total_cdr_count.toLocaleString()}</td>
                      <td className='px-4 py-3 text-sm text-right text-green-600'>{formatFee(summary.total_fee)}</td>
                      <td className='px-4 py-3 text-sm text-right text-gray-900'>{formatDuration(summary.total_time)}</td>
                      <td className='px-4 py-3 text-sm text-right text-blue-600'>{formatFee(summary.total_domestic_fee)}</td>
                      <td className='px-4 py-3 text-sm text-right text-gray-900'>{formatDuration(summary.total_domestic_time)}</td>
                      <td className='px-4 py-3 text-sm text-right text-gray-900'>{summary.total_domestic_count.toLocaleString()}</td>
                      <td className='px-4 py-3 text-sm text-right text-gray-900'>{reports.length}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* 详细报表列表 */}
          {reports.length > 0 ? (
            <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
              <h2 className='text-xl font-bold mb-4'>详细报表</h2>
              <div className='overflow-x-auto'>
                <table className='w-full'>
                  <thead>
                    <tr className='bg-gray-50 border-b'>
                      <th className='px-4 py-3 text-left text-sm font-medium text-gray-700'>日期</th>
                      <th className='px-4 py-3 text-left text-sm font-medium text-gray-700'>账户</th>
                      <th className='px-4 py-3 text-left text-sm font-medium text-gray-700'>账户名称</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>话单数</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>总费用</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>通话时长</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内费用</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内时长</th>
                      <th className='px-4 py-3 text-right text-sm font-medium text-gray-700'>国内数量</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reports.map((report, index) => (
                      <tr key={report.id} className={index % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className='px-4 py-3 text-sm text-gray-900'>{formatDate(report.report_date)}</td>
                        <td className='px-4 py-3 text-sm text-gray-900'>{report.account}</td>
                        <td className='px-4 py-3 text-sm text-gray-700'>{report.account_name || '-'}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-900'>{report.cdr_count.toLocaleString()}</td>
                        <td className='px-4 py-3 text-sm text-right text-green-600 font-medium'>{formatFee(report.total_fee)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-700'>{formatDuration(report.total_time)}</td>
                        <td className='px-4 py-3 text-sm text-right text-blue-600'>{formatFee(report.domestic_fee)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-700'>{formatDuration(report.domestic_time)}</td>
                        <td className='px-4 py-3 text-sm text-right text-gray-900'>{report.domestic_count.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            !loading && (
              <div className='bg-white rounded-xl p-12 shadow-lg border border-gray-200 text-center'>
                <svg className='mx-auto h-16 w-16 text-gray-400 mb-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
                </svg>
                <p className='text-gray-500 text-lg'>暂无数据</p>
                <p className='text-gray-400 text-sm mt-2'>请选择日期范围或账户后查询</p>
              </div>
            )
          )}

          {loading && (
            <div className='text-center py-12'>
              <svg className='mx-auto h-12 w-12 text-blue-600 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
              </svg>
              <p className='mt-4 text-gray-500'>加载中...</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

