'use client'
import React, {useEffect, useState} from 'react'
import api from '../lib/api'
import StatCard from '../components/ui/StatCard'
import Card from '../components/ui/Card'
import { useVOS } from '../contexts/VOSContext'

interface CustomerSummary {
  total_customers: number
  instances: Array<{
    instance_id: number
    instance_name: string
    customer_count: number
    error?: string
  }>
  instance_count: number
}

interface CDRSyncStatus {
  success: boolean
  status: string
  is_syncing: boolean
  total_cdrs: number
  last_sync_time: string | null
  instances_count: number
  instances: Array<{
    instance_id: number
    instance_name: string
    total_cdrs: number
    last_sync_time: string | null
    status: string
  }>
  next_sync: string
}

interface CDRSyncProgress {
  success: boolean
  is_syncing: boolean
  status?: string
  current_instance?: string
  current_instance_id?: number
  current_customer?: string
  current_customer_index?: number
  total_customers?: number
  synced_count?: number
  start_time?: string
  progress_percent?: number
  message?: string
}

export default function Page(){
  const { currentVOS } = useVOS()
  const [instances, setInstances] = useState<any[]>([])
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null)
  const [debtCustomers, setDebtCustomers] = useState(0)
  const [gatewaySummary, setGatewaySummary] = useState<any>(null)
  const [cdrSyncStatus, setCdrSyncStatus] = useState<CDRSyncStatus | null>(null)
  const [cdrSyncProgress, setCdrSyncProgress] = useState<CDRSyncProgress | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
    
    // 如果正在同步，定时刷新进度
    const interval = setInterval(() => {
      if (cdrSyncStatus?.is_syncing) {
        fetchCDRSyncProgress()
      }
    }, 3000) // 每3秒刷新一次
    
    return () => clearInterval(interval)
  }, [cdrSyncStatus?.is_syncing])

  async function fetchData() {
    setLoading(true)
    await Promise.all([
      fetchInstances(),
      fetchCustomerSummary(),
      fetchDebtCustomers(),
      fetchGatewaySummary(),
      fetchCDRSyncStatus()
    ])
    setLoading(false)
  }
  
  async function fetchGatewaySummary() {
    try {
      const res = await api.get('/vos/gateways/summary')
      setGatewaySummary(res.data)
    } catch (e) {
      console.error('获取网关统计失败:', e)
      setGatewaySummary({
        total_mapping_gateways: 0,
        total_routing_gateways: 0,
        total_online_gateways: 0,
        instances: []
      })
    }
  }

  async function fetchInstances() {
    try {
      const res = await api.get('/vos/instances')
      setInstances(res.data || [])
    } catch (e) {
      console.error('获取实例失败:', e)
    }
  }

  async function fetchCustomerSummary() {
    try {
      const res = await api.get('/vos/customers/summary')
      setCustomerSummary(res.data)
    } catch (e) {
      console.error('获取客户统计失败:', e)
      setCustomerSummary({ total_customers: 0, instances: [], instance_count: 0 })
    }
  }

  async function fetchDebtCustomers() {
    try {
      const res = await api.get('/vos/customers/debt-count')
      setDebtCustomers(res.data.debt_count || 0)
    } catch (e) {
      console.error('获取欠费客户失败:', e)
      setDebtCustomers(0)
    }
  }

  async function fetchCDRSyncStatus() {
    try {
      const res = await api.get('/tasks/cdr-sync-status')
      setCdrSyncStatus(res.data)
      
      // 如果正在同步，立即获取进度
      if (res.data.is_syncing) {
        fetchCDRSyncProgress()
      }
    } catch (e) {
      console.error('获取话单同步状态失败:', e)
      setCdrSyncStatus({
        success: false,
        status: 'error',
        is_syncing: false,
        total_cdrs: 0,
        last_sync_time: null,
        instances_count: 0,
        instances: [],
        next_sync: ''
      })
    }
  }
  
  async function fetchCDRSyncProgress() {
    try {
      const res = await api.get('/tasks/cdr-sync-progress')
      setCdrSyncProgress(res.data)
    } catch (e) {
      console.error('获取话单同步进度失败:', e)
      setCdrSyncProgress(null)
    }
  }
  
  function formatNumber(num: number): string {
    if (num >= 100000000) {
      return (num / 100000000).toFixed(1) + '亿'
    } else if (num >= 10000) {
      return (num / 10000).toFixed(1) + '万'
    }
    return num.toString()
  }
  
  function formatDateTime(dateStr: string | null): string {
    if (!dateStr) return '暂无数据'
    try {
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: false
      })
    } catch {
      return '无效时间'
    }
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          系统概览
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
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 mb-8'>
        <div className='bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-blue-100 text-xs mb-1'>VOS 实例</p>
              <p className='text-2xl font-bold'>{instances.length}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-green-100 text-xs mb-1'>客户总数</p>
              <p className='text-2xl font-bold'>{formatNumber(customerSummary?.total_customers || 0)}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-red-500 to-red-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-red-100 text-xs mb-1'>欠费客户</p>
              <p className='text-2xl font-bold'>{debtCustomers}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
            </div>
          </div>
        </div>

        <div className={`bg-gradient-to-br ${
          cdrSyncStatus?.is_syncing ? 'from-blue-500 to-blue-600' :
          cdrSyncStatus?.total_cdrs > 0 ? 'from-teal-500 to-teal-600' :
          'from-gray-500 to-gray-600'
        } rounded-xl p-5 text-white shadow-lg`}>
          <div className='flex items-center justify-between'>
            <div className='flex-1'>
              <p className='text-white text-opacity-90 text-xs mb-1'>话单同步</p>
              <p className='text-2xl font-bold'>
                {cdrSyncStatus?.is_syncing ? '同步中' : 
                 cdrSyncStatus?.total_cdrs ? formatNumber(cdrSyncStatus.total_cdrs) : '0'}
              </p>
              <p className='text-xs text-white text-opacity-75 mt-0.5 truncate' title={cdrSyncStatus?.last_sync_time || ''}>
                {cdrSyncStatus?.last_sync_time ? formatDateTime(cdrSyncStatus.last_sync_time) : '暂无记录'}
              </p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              {cdrSyncStatus?.is_syncing ? (
                <svg className='w-5 h-5 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                </svg>
              ) : (
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
              </svg>
              )}
            </div>
          </div>
        </div>
        
        {/* 新增网关统计卡片 */}
        <div className='bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-indigo-100 text-xs mb-1'>对接网关总数</p>
              <p className='text-2xl font-bold'>{gatewaySummary?.total_mapping_gateways || 0}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 7l5 5m0 0l-5 5m5-5H6' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-purple-100 text-xs mb-1'>落地网关总数</p>
              <p className='text-2xl font-bold'>{gatewaySummary?.total_routing_gateways || 0}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M11 17l-5-5m0 0l5-5m-5 5h12' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-5 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-emerald-100 text-xs mb-1'>在线网关数</p>
              <p className='text-2xl font-bold'>{gatewaySummary?.total_online_gateways || 0}</p>
            </div>
            <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
            </div>
          </div>
        </div>
      </div>


      {/* 同步进度卡片 */}
      {cdrSyncProgress?.is_syncing && (
        <section className='mb-8'>
          <div className='bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-5 text-white shadow-lg'>
            <div className='flex items-center justify-between mb-3'>
              <h2 className='text-lg font-bold flex items-center gap-2'>
                <svg className='w-5 h-5 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
            </svg>
                正在同步话单数据
              </h2>
              <span className='text-sm opacity-90'>
                进度: {cdrSyncProgress.progress_percent?.toFixed(1)}%
            </span>
            </div>

            <div className='grid grid-cols-1 md:grid-cols-3 gap-3 mb-3'>
              <div className='bg-white bg-opacity-20 rounded-lg p-3'>
                <p className='text-xs opacity-75 mb-1'>当前节点</p>
                <p className='text-base font-semibold'>{cdrSyncProgress.current_instance || '准备中...'}</p>
              </div>
              
              <div className='bg-white bg-opacity-20 rounded-lg p-3'>
                <p className='text-xs opacity-75 mb-1'>当前客户</p>
                <p className='text-base font-semibold'>
                  {cdrSyncProgress.current_customer || '准备中...'}
                  {cdrSyncProgress.current_customer_index && cdrSyncProgress.total_customers && (
                    <span className='text-xs ml-2'>
                      ({cdrSyncProgress.current_customer_index}/{cdrSyncProgress.total_customers})
                    </span>
                  )}
                </p>
              </div>
              
              <div className='bg-white bg-opacity-20 rounded-lg p-3'>
                <p className='text-xs opacity-75 mb-1'>已同步数据</p>
                <p className='text-base font-semibold'>{formatNumber(cdrSyncProgress.synced_count || 0)} 条</p>
              </div>
            </div>

            {/* 进度条 */}
            <div className='bg-white bg-opacity-20 rounded-full h-2 overflow-hidden'>
              <div 
                className='bg-white h-full transition-all duration-300 ease-out'
                style={{ width: `${cdrSyncProgress.progress_percent || 0}%` }}
              />
            </div>
          </div>
        </section>
      )}

      {/* 各实例客户分布 */}
      {customerSummary && customerSummary.instances.length > 0 && (
        <section className='mb-8'>
          <h2 className='text-xl font-bold mb-4 text-gray-800 flex items-center gap-2'>
            各实例客户分布
            <span className='text-sm font-normal text-gray-500'>(当前选中的实例会高亮显示)</span>
          </h2>
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {customerSummary.instances.map((inst) => {
              const isCurrentVOS = currentVOS?.id === inst.instance_id
              // 获取该实例的网关统计数据
              const gatewayStats = gatewaySummary?.instances?.find(
                (g: any) => g.instance_id === inst.instance_id
              ) || {
                mapping_gateway_count: 0,
                routing_gateway_count: 0,
                online_gateway_count: 0
              }
              
              return (
                <div 
                  key={inst.instance_id} 
                  className={`p-5 rounded-xl shadow-lg border transition-all ${
                    isCurrentVOS 
                      ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-300 border-2 ring-2 ring-blue-300' 
                      : 'bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg border-white border-opacity-30'
                  }`}
                >
                  <div className='flex items-center justify-between mb-4'>
                    <div className='flex items-center gap-2'>
                      <h3 className='font-semibold text-gray-800'>{inst.instance_name}</h3>
                      {isCurrentVOS && (
                        <span className='px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full'>
                          当前
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* 统计信息图标 */}
                  <div className='grid grid-cols-5 gap-3 mb-3'>
                    {/* 全部用户数 */}
                    <div 
                      className='flex flex-col items-center justify-center p-2 bg-gray-50 rounded-lg hover:bg-gray-100 transition cursor-help'
                      title='全部用户数'
                    >
                      <svg className='w-5 h-5 text-gray-600 mb-1' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' />
                      </svg>
                      <span className='text-xs font-bold text-gray-700'>{inst.customer_count || 0}</span>
                    </div>
                    
                    {/* 欠费用户数 */}
                    <div 
                      className='flex flex-col items-center justify-center p-2 bg-red-50 rounded-lg hover:bg-red-100 transition cursor-help'
                      title='欠费用户数'
                    >
                      <svg className='w-5 h-5 text-red-600 mb-1' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
                      </svg>
                      <span className='text-xs font-bold text-red-700'>{inst.debt_customer_count || 0}</span>
                    </div>
                    
                    {/* 落地网关数 */}
                    <div 
                      className='flex flex-col items-center justify-center p-2 bg-purple-50 rounded-lg hover:bg-purple-100 transition cursor-help'
                      title='落地网关数'
                    >
                      <svg className='w-5 h-5 text-purple-600 mb-1' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M11 17l-5-5m0 0l5-5m-5 5h12' />
                      </svg>
                      <span className='text-xs font-bold text-purple-700'>{gatewayStats.routing_gateway_count || 0}</span>
                    </div>
                    
                    {/* 对接网关数 */}
                    <div 
                      className='flex flex-col items-center justify-center p-2 bg-blue-50 rounded-lg hover:bg-blue-100 transition cursor-help'
                      title='对接网关数'
                    >
                      <svg className='w-5 h-5 text-blue-600 mb-1' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 7l5 5m0 0l-5 5m5-5H6' />
                      </svg>
                      <span className='text-xs font-bold text-blue-700'>{gatewayStats.mapping_gateway_count || 0}</span>
                    </div>
                    
                    {/* 在线网关数 */}
                    <div 
                      className='flex flex-col items-center justify-center p-2 bg-green-50 rounded-lg hover:bg-green-100 transition cursor-help'
                      title='在线网关数'
                    >
                      <svg className='w-5 h-5 text-green-600 mb-1' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                      </svg>
                      <span className='text-xs font-bold text-green-700'>{gatewayStats.online_gateway_count || 0}</span>
                    </div>
                  </div>
                  
                  {inst.error && (
                    <p className='text-xs text-red-600 mt-2'>⚠️ {inst.error}</p>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* 已注册实例 */}
      <section>
        <h2 className='text-xl font-bold mb-4 text-gray-800'>已注册 VOS 实例</h2>
        {instances.length === 0 ? (
          <div className='text-center py-16 bg-white bg-opacity-90 rounded-xl shadow-sm'>
            <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
            </svg>
            <h3 className='mt-2 text-lg font-medium text-gray-900'>暂无 VOS 实例</h3>
            <p className='mt-1 text-sm text-gray-500'>前往 VOS 节点页面添加第一个实例</p>
            <div className='mt-6'>
              <a
                href='/vos'
                className='inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition'
              >
                添加 VOS 节点
              </a>
            </div>
          </div>
        ) : (
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {instances.map((inst: any) => {
              const isCurrentVOS = currentVOS?.id === inst.id
              const healthStatus = inst.health_status || 'unknown'
              const healthStatusConfig = {
                healthy: { 
                  bg: 'bg-green-100', 
                  text: 'text-green-800', 
                  icon: '✓', 
                  label: '健康' 
                },
                unhealthy: { 
                  bg: 'bg-red-100', 
                  text: 'text-red-800', 
                  icon: '✗', 
                  label: '异常' 
                },
                unknown: { 
                  bg: 'bg-gray-100', 
                  text: 'text-gray-800', 
                  icon: '?', 
                  label: '未知' 
                }
              }
              const statusConfig = healthStatusConfig[healthStatus as keyof typeof healthStatusConfig] || healthStatusConfig.unknown
              
              return (
                <div 
                  key={inst.id}
                  className={`p-5 rounded-xl shadow-lg border transition-all ${
                    isCurrentVOS 
                      ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-300 border-2 ring-2 ring-blue-300' 
                      : 'bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg border-white border-opacity-30'
                  }`}
                >
                  <a href={`/vos/${inst.id}`} className='block'>
                    <div className='flex items-center gap-2 mb-2'>
                      <h3 className='text-lg font-semibold text-gray-900 hover:text-blue-600 transition'>
                        {inst.name}
                      </h3>
                      {isCurrentVOS && (
                        <span className='px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full'>
                          当前
                        </span>
                      )}
                    </div>
                    <p className='text-sm text-gray-600 mt-1 break-all'>{inst.base_url}</p>
                  {inst.vos_uuid && (
                    <p className='text-xs text-gray-500 mt-2 font-mono'>
                      UUID: {inst.vos_uuid}
                    </p>
                  )}
                  {inst.description && (
                    <p className='text-sm text-gray-500 mt-2'>{inst.description}</p>
                  )}
                  <div className='mt-3 pt-3 border-t flex items-center justify-between'>
                    <div className='flex items-center gap-2'>
                    <span className={`text-xs px-2 py-1 rounded-full ${inst.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {inst.enabled ? '✓ 启用中' : '○ 已禁用'}
                    </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${statusConfig.bg} ${statusConfig.text}`} title={inst.health_error || `响应时间: ${inst.health_response_time?.toFixed(0)}ms`}>
                        {statusConfig.icon} {statusConfig.label}
                      </span>
                    </div>
                    <span className='text-xs text-blue-600 hover:underline'>查看详情 →</span>
                  </div>
                </a>
              </div>
              )
            })}
          </div>
        )}
      </section>
    </div>
  )
}
