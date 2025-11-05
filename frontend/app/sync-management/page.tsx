'use client'
import { useState, useEffect } from 'react'
import api from '../../lib/api'

interface VOSInstance {
  id: number
  name: string
  base_url: string
  enabled: boolean
}

interface Customer {
  id: number
  account: string
  vos_instance_id: number
}

interface SyncConfig {
  cdr_sync_time: string
  customer_sync_time: string
  cdr_sync_days: number
}

interface SyncProgress {
  is_syncing: boolean
  current_instance?: string
  current_customer?: string
  synced_count?: number
  message?: string
}

export default function SyncManagementPage() {
  const [activeTab, setActiveTab] = useState<'cdr' | 'customer' | 'gateway'>('cdr')
  const [instances, setInstances] = useState<VOSInstance[]>([])
  const [customers, setCustomers] = useState<Customer[]>([])
  const [selectedInstance, setSelectedInstance] = useState<number | 'all'>('all')
  const [selectedCustomer, setSelectedCustomer] = useState<number | 'all'>('all')
  const [syncConfig, setSyncConfig] = useState<SyncConfig>({
    cdr_sync_time: '01:30',
    customer_sync_time: '01:00',
    cdr_sync_days: 1
  })
  const [loading, setLoading] = useState(false)
  const [syncProgress, setSyncProgress] = useState<SyncProgress>({ is_syncing: false })
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)
  const [showConfirmDialog, setShowConfirmDialog] = useState(false)
  const [confirmAction, setConfirmAction] = useState<{ type: 'cdr' | 'customer' | 'gateway', message: string } | null>(null)

  useEffect(() => {
    fetchInstances()
    fetchSyncConfig()
  }, [])

  useEffect(() => {
    if (selectedInstance !== 'all' && selectedInstance !== null) {
      fetchCustomers(selectedInstance as number)
    } else {
      setCustomers([])
      setSelectedCustomer('all')
    }
  }, [selectedInstance])

  // 定时轮询同步进度
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null
    if (syncProgress.is_syncing) {
      interval = setInterval(async () => {
        try {
          const res = await api.get('/tasks/cdr-sync-progress')
          if (res.data.is_syncing) {
            setSyncProgress({
              is_syncing: true,
              current_instance: res.data.current_instance,
              current_customer: res.data.current_customer,
              synced_count: res.data.synced_count,
              message: `正在同步 ${res.data.current_instance} - ${res.data.current_customer || '准备中'}`
            })
          } else {
            setSyncProgress({ is_syncing: false, message: '同步完成' })
            setMessage({ type: 'success', text: '同步任务已完成！' })
          }
        } catch (e) {
          console.error('获取同步进度失败:', e)
        }
      }, 3000)
    }
    
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [syncProgress.is_syncing])

  async function fetchInstances() {
    try {
      const res = await api.get('/vos/instances')
      setInstances(res.data || [])
    } catch (e) {
      console.error('获取VOS实例失败:', e)
    }
  }

  async function fetchCustomers(instanceId: number) {
    try {
      const res = await api.get(`/vos/customers/${instanceId}`)
      setCustomers(res.data || [])
    } catch (e) {
      console.error('获取客户列表失败:', e)
      setCustomers([])
    }
  }

  async function fetchSyncConfig() {
    try {
      const res = await api.get('/sync/config')
      if (res.data) {
        setSyncConfig(res.data)
      }
    } catch (e) {
      console.error('获取同步配置失败:', e)
    }
  }

  async function handleSaveConfig() {
    setLoading(true)
    setMessage(null)
    try {
      await api.post('/sync/config', syncConfig)
      setMessage({ type: 'success', text: '同步配置已保存' })
    } catch (e: any) {
      console.error('保存同步配置失败:', e)
      setMessage({ type: 'error', text: e.response?.data?.detail || '保存失败' })
    } finally {
      setLoading(false)
    }
  }

  function showConfirm(type: 'cdr' | 'customer' | 'gateway') {
    let confirmMessage = ''
    
    if (type === 'cdr' && selectedInstance === 'all') {
      confirmMessage = '确定要同步所有VOS节点的历史话单吗？'
    } else if (type === 'cdr' && selectedInstance !== 'all' && selectedCustomer === 'all') {
      const inst = instances.find(i => i.id === selectedInstance)
      confirmMessage = `确定要同步 ${inst?.name} 的所有客户历史话单吗？`
    } else if (type === 'cdr' && selectedInstance !== 'all' && selectedCustomer !== 'all') {
      const inst = instances.find(i => i.id === selectedInstance)
      const cust = customers.find(c => c.id === selectedCustomer)
      confirmMessage = `确定要同步 ${inst?.name} - ${cust?.account} 的历史话单吗？`
    } else if (type === 'customer') {
      if (selectedInstance === 'all') {
        confirmMessage = '确定要同步所有VOS节点的客户数据吗？'
      } else {
        const inst = instances.find(i => i.id === selectedInstance)
        confirmMessage = `确定要同步 ${inst?.name} 的客户数据吗？`
      }
    } else if (type === 'gateway') {
      if (selectedInstance === 'all') {
        confirmMessage = '确定要同步所有VOS节点的网关数据吗？'
      } else {
        const inst = instances.find(i => i.id === selectedInstance)
        confirmMessage = `确定要同步 ${inst?.name} 的网关数据吗？`
      }
    }
    
    setConfirmAction({ type, message: confirmMessage })
    setShowConfirmDialog(true)
  }

  async function executeSync() {
    if (!confirmAction) return
    
    setShowConfirmDialog(false)
    setSyncProgress({ is_syncing: true, message: '正在启动同步任务...' })
    setMessage(null)
    
    try {
      let endpoint = ''
      let payload: any = {}

      if (confirmAction.type === 'cdr') {
        endpoint = '/sync/manual/cdr'
        payload = {
          instance_id: selectedInstance === 'all' ? null : selectedInstance,
          customer_id: selectedCustomer === 'all' ? null : selectedCustomer,
          days: syncConfig.cdr_sync_days
        }
      } else if (confirmAction.type === 'customer') {
        endpoint = '/sync/manual/customer'
        payload = {
          instance_id: selectedInstance === 'all' ? null : selectedInstance
        }
      } else if (confirmAction.type === 'gateway') {
        endpoint = '/sync/manual/gateway'
        payload = {
          instance_id: selectedInstance === 'all' ? null : selectedInstance,
          gateway_type: 'both'
        }
      }

      const res = await api.post(endpoint, payload)
      
      if (res.data.success) {
        setSyncProgress({ 
          is_syncing: true, 
          message: res.data.message || '同步任务已启动'
        })
        setMessage({ 
          type: 'success', 
          text: `✅ ${res.data.message || '同步任务已启动'}` 
        })
      } else {
        setSyncProgress({ is_syncing: false })
        setMessage({ 
          type: 'error', 
          text: res.data.message || '同步启动失败' 
        })
      }
    } catch (e: any) {
      console.error('触发同步失败:', e)
      setSyncProgress({ is_syncing: false })
      setMessage({ 
        type: 'error', 
        text: e.response?.data?.detail || '触发同步失败' 
      })
    }
  }

  return (
    <div className='max-w-6xl mx-auto'>
      <h1 className='text-3xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
        同步管理
      </h1>

      {/* 消息提示 */}
      {message && (
        <div className={`mb-6 p-4 rounded-lg flex items-center justify-between ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          <span>{message.text}</span>
          <button onClick={() => setMessage(null)} className='text-gray-500 hover:text-gray-700'>
            <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M6 18L18 6M6 6l12 12' />
            </svg>
          </button>
        </div>
      )}

      {/* 同步进度卡片 */}
      {syncProgress.is_syncing && (
        <div className='mb-6 bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl p-6 text-white shadow-lg'>
          <div className='flex items-center gap-3 mb-3'>
            <svg className='w-6 h-6 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
            </svg>
            <h3 className='text-xl font-bold'>正在同步...</h3>
          </div>
          <div className='space-y-2'>
            {syncProgress.current_instance && (
              <p className='text-sm'>📍 当前节点: {syncProgress.current_instance}</p>
            )}
            {syncProgress.current_customer && (
              <p className='text-sm'>👤 当前客户: {syncProgress.current_customer}</p>
            )}
            {syncProgress.synced_count !== undefined && (
              <p className='text-sm'>📊 已同步: {syncProgress.synced_count} 条</p>
            )}
            <p className='text-sm opacity-90'>{syncProgress.message}</p>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className='flex gap-4 mb-6 border-b border-gray-200'>
        <button
          onClick={() => setActiveTab('cdr')}
          className={`px-6 py-3 font-medium transition ${
            activeTab === 'cdr'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          历史话单同步
        </button>
        <button
          onClick={() => setActiveTab('gateway')}
          className={`px-6 py-3 font-medium transition ${
            activeTab === 'gateway'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          网关数据同步
        </button>
      </div>

      {/* 历史话单同步 */}
      {activeTab === 'cdr' && (
        <div className='space-y-6'>
          {/* 自动同步配置 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <h2 className='text-xl font-bold mb-4 flex items-center gap-2'>
              <svg className='w-6 h-6 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
              自动同步配置
            </h2>
            
            <div className='grid grid-cols-1 md:grid-cols-2 gap-6'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  每日同步时间
                </label>
                <input
                  type='time'
                  value={syncConfig.cdr_sync_time}
                  onChange={e => setSyncConfig({ ...syncConfig, cdr_sync_time: e.target.value })}
                  className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                />
                <p className='text-xs text-gray-500 mt-1'>
                  每天在此时间自动同步所有节点的历史话单
                </p>
              </div>

              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  同步天数
                </label>
                <input
                  type='number'
                  min='1'
                  max='30'
                  value={syncConfig.cdr_sync_days}
                  onChange={e => {
                    const value = e.target.value
                    const numValue = parseInt(value, 10)
                    if (value === '') {
                      // 允许清空输入框
                      setSyncConfig({ ...syncConfig, cdr_sync_days: 1 })
                    } else if (!isNaN(numValue) && numValue >= 1 && numValue <= 30) {
                      setSyncConfig({ ...syncConfig, cdr_sync_days: numValue })
                    }
                  }}
                  onBlur={e => {
                    // 失去焦点时，如果值为空或无效，设置为默认值1
                    const value = e.target.value
                    const numValue = parseInt(value, 10)
                    if (value === '' || isNaN(numValue) || numValue < 1 || numValue > 30) {
                      setSyncConfig({ ...syncConfig, cdr_sync_days: 1 })
                    }
                  }}
                  className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                />
                <p className='text-xs text-gray-500 mt-1'>
                  每次同步最近N天的数据（1-30天）
                </p>
              </div>
            </div>

            <button
              onClick={handleSaveConfig}
              disabled={loading}
              className='mt-6 px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50'
            >
              {loading ? '保存中...' : '保存配置'}
            </button>
          </div>

          {/* 手动触发同步 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <h2 className='text-xl font-bold mb-4 flex items-center gap-2'>
              <svg className='w-6 h-6 text-purple-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 10V3L4 14h7v7l9-11h-7z' />
              </svg>
              手动触发同步
            </h2>

            <div className='space-y-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  选择VOS节点
                </label>
                <select
                  value={selectedInstance}
                  onChange={e => setSelectedInstance(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                  className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                >
                  <option value='all'>全部节点</option>
                  {instances.filter(i => i.enabled).map(inst => (
                    <option key={inst.id} value={inst.id}>{inst.name}</option>
                  ))}
                </select>
              </div>

              {selectedInstance !== 'all' && customers.length > 0 && (
                <div>
                  <label className='block text-sm font-medium text-gray-700 mb-2'>
                    选择客户（可选）
                  </label>
                  <select
                    value={selectedCustomer}
                    onChange={e => setSelectedCustomer(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                    className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                  >
                    <option value='all'>全部客户</option>
                    {customers.map(cust => (
                      <option key={cust.id} value={cust.id}>{cust.account}</option>
                    ))}
                  </select>
                  <p className='text-xs text-gray-500 mt-1'>
                    {selectedCustomer === 'all' ? '将同步该节点的所有客户' : '仅同步选中的客户'}
                  </p>
                </div>
              )}

              <button
                onClick={() => showConfirm('cdr')}
                disabled={syncProgress.is_syncing || instances.length === 0}
                className='w-full px-6 py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 transition disabled:opacity-50 font-medium'
              >
                {syncProgress.is_syncing ? (
                  <span className='flex items-center justify-center gap-2'>
                    <svg className='w-5 h-5 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                    </svg>
                    同步中...
                  </span>
                ) : '立即同步历史话单'}
              </button>

              {instances.length === 0 && (
                <p className='text-sm text-gray-500 text-center'>
                  暂无VOS节点，请先添加节点
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 网关数据同步 */}
      {activeTab === 'gateway' && (
        <div className='space-y-6'>
          {/* 自动同步配置 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <h2 className='text-xl font-bold mb-4 flex items-center gap-2'>
              <svg className='w-6 h-6 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
              自动同步配置
            </h2>
            
            <div className='bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg p-4 border border-blue-200'>
              <div className='flex items-center gap-3 mb-2'>
                <svg className='w-5 h-5 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
                </svg>
                <span className='font-semibold text-gray-800'>网关自动同步</span>
              </div>
              <p className='text-sm text-gray-600'>
                系统已配置网关自动同步任务，每分钟同步一次网关数据（对接网关 + 落地网关）
              </p>
              <div className='mt-3 text-xs text-gray-500'>
                <p>• 对接网关：每分钟同步配置和在线状态</p>
                <p>• 落地网关：每分钟同步配置和在线状态</p>
                <p>• 数据存储：同时更新缓存表和专用网关表</p>
              </div>
            </div>
          </div>

          {/* 手动触发同步 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <h2 className='text-xl font-bold mb-4 flex items-center gap-2'>
              <svg className='w-6 h-6 text-purple-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 10V3L4 14h7v7l9-11h-7z' />
              </svg>
              手动触发同步
            </h2>

            <div className='space-y-4'>
              <div>
                <label className='block text-sm font-medium text-gray-700 mb-2'>
                  选择VOS节点
                </label>
                <select
                  value={selectedInstance}
                  onChange={e => setSelectedInstance(e.target.value === 'all' ? 'all' : parseInt(e.target.value))}
                  className='w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
                >
                  <option value='all'>全部节点</option>
                  {instances.filter(i => i.enabled).map(inst => (
                    <option key={inst.id} value={inst.id}>{inst.name}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={() => showConfirm('gateway')}
                disabled={syncProgress.is_syncing || instances.length === 0}
                className='w-full px-6 py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 transition disabled:opacity-50 font-medium'
              >
                {syncProgress.is_syncing ? (
                  <span className='flex items-center justify-center gap-2'>
                    <svg className='w-5 h-5 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                    </svg>
                    同步中...
                  </span>
                ) : '立即同步网关数据'}
              </button>

              {instances.length === 0 && (
                <p className='text-sm text-gray-500 text-center'>
                  暂无VOS节点，请先添加节点
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 自定义确认对话框 */}
      {showConfirmDialog && confirmAction && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50'>
          <div className='bg-white rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl'>
            <div className='flex items-center gap-4 mb-6'>
              <div className='w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center flex-shrink-0'>
                <svg className='w-6 h-6 text-white' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' />
                </svg>
              </div>
              <h3 className='text-xl font-bold text-gray-900'>确认同步操作</h3>
            </div>
            
            <p className='text-gray-700 mb-8 leading-relaxed'>
              {confirmAction.message}
            </p>
            
            <div className='flex gap-4'>
              <button
                onClick={() => setShowConfirmDialog(false)}
                className='flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium'
              >
                取消
              </button>
              <button
                onClick={executeSync}
                className='flex-1 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-medium'
              >
                确认同步
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
