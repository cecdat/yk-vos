'use client'
import React, { useEffect, useState } from 'react'
import api from '../../lib/api'
import { formatMoney } from '../../lib/utils'
import { useVOS } from '../../contexts/VOSContext'

interface Customer {
  account: string
  money: number
  limitMoney: number
}

interface CustomerResponse {
  customers: Customer[]
  count: number
  instance_id: number
  instance_name: string
  from_cache: boolean
  data_source: string
  last_synced_at?: string
}

export default function CustomersPage() {
  const { currentVOS } = useVOS()
  const [customersData, setCustomersData] = useState<Customer[]>([])
  const [lastSyncedAt, setLastSyncedAt] = useState<string | null>(null)
  const [dataSource, setDataSource] = useState<string>('database')
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'normal' | 'debt'>('all')
  const [error, setError] = useState<string | null>(null)
  
  // 分页状态
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // 当切换 VOS 时重新加载数据
  useEffect(() => {
    if (currentVOS) {
      fetchData()
    }
  }, [currentVOS])

  async function fetchData() {
    if (!currentVOS) {
      setLoading(false)
      return
    }

    setLoading(true)
    setError(null)
    
    try {
      // 只获取当前 VOS 的客户数据
      const res = await api.get(`/vos/instances/${currentVOS.id}/customers`)
      const responseData: CustomerResponse = res.data
      
      setCustomersData(responseData.customers || [])
      setLastSyncedAt(responseData.last_synced_at || null)
      setDataSource(responseData.data_source || 'database')
      
      if (res.data?.error) {
        setError(res.data.error)
      }
    } catch (e: any) {
      console.error('获取客户数据失败:', e)
      setError(e.response?.data?.detail || '获取客户数据失败')
      setCustomersData([])
      setLastSyncedAt(null)
    } finally {
      setLoading(false)
    }
  }

  // 过滤客户
  const filteredCustomers = customersData
    .filter(customer => 
      !searchTerm || 
      customer.account.toLowerCase().includes(searchTerm.toLowerCase())
    )
    .filter(customer => {
      // 状态过滤
      if (statusFilter === 'all') return true
      if (statusFilter === 'debt') return customer.money < 0
      if (statusFilter === 'normal') return customer.money >= 0
      return true
    })

  // 统计信息
  const totalCustomers = customersData.length
  const totalBalance = filteredCustomers.reduce((sum, c) => sum + c.money, 0)
  const debtCustomers = filteredCustomers.filter(c => c.money < 0).length
  // 总欠费金额：只计算欠费客户的欠费总额（绝对值）
  const totalDebtAmount = filteredCustomers
    .filter(c => c.money < 0)
    .reduce((sum, c) => sum + Math.abs(c.money), 0)

  // 分页
  const totalPages = Math.ceil(filteredCustomers.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedCustomers = filteredCustomers.slice(startIndex, endIndex)

  // 当过滤条件变化时，重置到第一页
  useEffect(() => {
    setCurrentPage(1)
  }, [searchTerm, statusFilter])

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          客户管理
        </h1>
        <button
          onClick={fetchData}
          disabled={loading}
          className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition flex items-center gap-2 disabled:opacity-50'
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
          </svg>
          刷新数据
        </button>
      </div>

      {/* 统计卡片 */}
      <div className='grid grid-cols-1 md:grid-cols-3 gap-4 mb-6'>
        <div className='bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg'>
          <p className='text-blue-100 text-sm mb-1'>客户总数</p>
          <p className='text-3xl font-bold'>{totalCustomers}</p>
        </div>
        <div className='bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg'>
          <p className='text-orange-100 text-sm mb-1'>总欠费金额</p>
          <p className='text-3xl font-bold'>¥{totalDebtAmount.toFixed(2)}</p>
        </div>
        <div className='bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-6 text-white shadow-lg'>
          <p className='text-red-100 text-sm mb-1'>欠费客户</p>
          <p className='text-3xl font-bold'>{debtCustomers}</p>
        </div>
      </div>

      {/* 当前 VOS 提示和错误信息 */}
      {currentVOS && (
        <div className='mb-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200'>
          <div className='flex items-center justify-between flex-wrap gap-2'>
            <div className='flex items-center gap-4'>
              <p className='text-sm text-gray-700'>
                <span className='font-semibold text-blue-600'>当前 VOS 节点:</span> {currentVOS.name}
              </p>
              {lastSyncedAt && (
                <p className='text-sm text-gray-600'>
                  <span className='font-semibold'>最后同步时间:</span>{' '}
                  {new Date(lastSyncedAt).toLocaleString('zh-CN', {
                    year: 'numeric',
                    month: '2-digit',
                    day: '2-digit',
                    hour: '2-digit',
                    minute: '2-digit',
                    second: '2-digit'
                  })}
                </p>
              )}
              <span className={`text-xs px-2 py-1 rounded-full ${
                dataSource === 'vos_api' ? 'bg-green-100 text-green-700' : 
                dataSource === 'database' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
              }`}>
                {dataSource === 'vos_api' ? '实时数据' : '缓存数据'}
              </span>
            </div>
            {error && <span className='text-sm text-red-600'>⚠️ {error}</span>}
          </div>
        </div>
      )}

      {/* 搜索和筛选 */}
      <div className='bg-white rounded-xl p-4 shadow-sm mb-6'>
        <div className='flex flex-wrap gap-4'>
          <div className='flex-1 min-w-[200px]'>
            <input
              type='text'
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className='w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='搜索客户名称...'
            />
          </div>
          <select
            value={statusFilter}
            onChange={e => setStatusFilter(e.target.value as 'all' | 'normal' | 'debt')}
            className='p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white min-w-[150px]'
          >
            <option value='all'>全部状态</option>
            <option value='normal'>正常客户</option>
            <option value='debt'>欠费客户</option>
          </select>
          <select
            value={pageSize}
            onChange={e => {
              setPageSize(Number(e.target.value))
              setCurrentPage(1)
            }}
            className='p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none bg-white min-w-[120px]'
          >
            <option value={10}>10条/页</option>
            <option value={20}>20条/页</option>
            <option value={50}>50条/页</option>
            <option value={100}>100条/页</option>
          </select>
        </div>
      </div>

      {/* 客户列表 */}
      {loading ? (
        <div className='text-center py-16 bg-white rounded-xl'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>加载中...</p>
        </div>
      ) : filteredCustomers.length === 0 ? (
        <div className='text-center py-16 bg-white rounded-xl'>
          <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' />
          </svg>
          <h3 className='mt-2 text-lg font-medium text-gray-900'>暂无客户数据</h3>
          <p className='mt-1 text-sm text-gray-500'>请先添加 VOS 节点</p>
        </div>
      ) : (
        <div className='bg-white rounded-xl shadow-sm overflow-hidden'>
          <div className='overflow-x-auto'>
            <table className='w-full'>
              <thead className='bg-gradient-to-r from-gray-50 to-gray-100'>
                <tr>
                  <th className='px-6 py-4 text-left text-sm font-semibold text-gray-700'>客户名称</th>
                  <th className='px-6 py-4 text-right text-sm font-semibold text-gray-700'>余额</th>
                  <th className='px-6 py-4 text-right text-sm font-semibold text-gray-700'>授信额度</th>
                  <th className='px-6 py-4 text-center text-sm font-semibold text-gray-700'>状态</th>
                </tr>
              </thead>
              <tbody className='divide-y divide-gray-200'>
                {paginatedCustomers.map((customer, index) => (
                  <tr key={index} className='hover:bg-gray-50 transition'>
                    <td className='px-6 py-4'>
                      <div className='font-medium text-gray-900'>{customer.account}</div>
                    </td>
                    <td className='px-6 py-4 text-right'>
                      <span className={`font-semibold ${
                        customer.money < 0 
                          ? 'text-red-600' 
                          : customer.money > 0 
                            ? 'text-green-600' 
                            : 'text-gray-600'
                      }`}>
                        {customer.money < 0 && '-'}¥{Math.abs(customer.money).toFixed(2)}
                      </span>
                    </td>
                    <td className='px-6 py-4 text-right'>
                      <span className='text-gray-700'>
                        ¥{customer.limitMoney.toFixed(2)}
                      </span>
                    </td>
                    <td className='px-6 py-4 text-center'>
                      {customer.money < 0 ? (
                        <span className='inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800'>
                          <svg className='w-3 h-3 mr-1' fill='currentColor' viewBox='0 0 20 20'>
                            <path fillRule='evenodd' d='M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z' clipRule='evenodd' />
                          </svg>
                          欠费
                        </span>
                      ) : (
                        <span className='inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800'>
                          <svg className='w-3 h-3 mr-1' fill='currentColor' viewBox='0 0 20 20'>
                            <path fillRule='evenodd' d='M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z' clipRule='evenodd' />
                          </svg>
                          正常
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          
          {/* 分页控制 */}
          <div className='px-6 py-4 bg-gray-50 border-t flex items-center justify-between'>
            <div className='flex items-center gap-2 text-sm text-gray-600'>
              <p>
                共 <span className='font-semibold text-gray-900'>{filteredCustomers.length}</span> 条记录
              </p>
              <span className='text-gray-400'>|</span>
              <p>
                第 <span className='font-semibold text-gray-900'>{currentPage}</span> / {totalPages} 页
              </p>
              <span className='text-gray-400'>|</span>
              <p>
                显示 {startIndex + 1} - {Math.min(endIndex, filteredCustomers.length)} 条
              </p>
            </div>
            
            <div className='flex items-center gap-2'>
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition'
              >
                首页
              </button>
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition'
              >
                上一页
              </button>
              
              {/* 页码 */}
              <div className='flex items-center gap-1'>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }
                  
                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-2 rounded-lg transition ${
                        currentPage === pageNum
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold'
                          : 'border hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition'
              >
                下一页
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition'
              >
                末页
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

