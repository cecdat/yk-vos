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

export default function SyncManagementPage() {
  const [activeTab, setActiveTab] = useState<'cdr' | 'customer'>('cdr')
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
  const [syncing, setSyncing] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

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

  async function handleManualSync(type: 'cdr' | 'customer') {
    if (type === 'cdr' && selectedInstance === 'all') {
      // 全部节点同步
      if (!confirm('确定要同步所有VOS节点的历史话单吗？')) return
    } else if (type === 'cdr' && selectedInstance !== 'all' && selectedCustomer === 'all') {
      // 指定节点全部客户
      const inst = instances.find(i => i.id === selectedInstance)
      if (!confirm(`确定要同步 ${inst?.name} 的所有客户历史话单吗？`)) return
    } else if (type === 'cdr' && selectedInstance !== 'all' && selectedCustomer !== 'all') {
      // 指定节点指定客户
      const inst = instances.find(i => i.id === selectedInstance)
      const cust = customers.find(c => c.id === selectedCustomer)
      if (!confirm(`确定要同步 ${inst?.name} - ${cust?.account} 的历史话单吗？`)) return
    } else if (type === 'customer') {
      if (!confirm('确定要同步所有VOS节点的客户数据吗？')) return
    }

    setSyncing(true)
    setMessage(null)
    
    try {
      let endpoint = ''
      let payload: any = {}

      if (type === 'cdr') {
        endpoint = '/sync/manual/cdr'
        payload = {
          instance_id: selectedInstance === 'all' ? null : selectedInstance,
          customer_id: selectedCustomer === 'all' ? null : selectedCustomer,
          days: syncConfig.cdr_sync_days
        }
      } else {
        endpoint = '/sync/manual/customer'
        payload = {
          instance_id: selectedInstance === 'all' ? null : selectedInstance
        }
      }

      const res = await api.post(endpoint, payload)
      
      if (res.data.success) {
        setMessage({ 
          type: 'success', 
          text: `同步任务已启动！${res.data.message || ''}` 
        })
      } else {
        setMessage({ 
          type: 'error', 
          text: res.data.message || '同步启动失败' 
        })
      }
    } catch (e: any) {
      console.error('触发同步失败:', e)
      setMessage({ 
        type: 'error', 
        text: e.response?.data?.detail || '触发同步失败' 
      })
    } finally {
      setSyncing(false)
    }
  }

  return (
    <div className='max-w-6xl mx-auto'>
      <h1 className='text-3xl font-bold mb-6 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
        同步管理
      </h1>

      {message && (
        <div className={`mb-6 p-4 rounded-lg ${
          message.type === 'success' ? 'bg-green-50 text-green-800 border border-green-200' : 'bg-red-50 text-red-800 border border-red-200'
        }`}>
          {message.text}
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
          onClick={() => setActiveTab('customer')}
          className={`px-6 py-3 font-medium transition ${
            activeTab === 'customer'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          客户数据同步
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
                  onChange={e => setSyncConfig({ ...syncConfig, cdr_sync_days: parseInt(e.target.value) || 1 })}
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
                </div>
              )}

              <button
                onClick={() => handleManualSync('cdr')}
                disabled={syncing || instances.length === 0}
                className='w-full px-6 py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 transition disabled:opacity-50 font-medium'
              >
                {syncing ? (
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

      {/* 客户数据同步 */}
      {activeTab === 'customer' && (
        <div className='space-y-6'>
          {/* 自动同步配置 */}
          <div className='bg-white rounded-xl p-6 shadow-lg border border-gray-200'>
            <h2 className='text-xl font-bold mb-4 flex items-center gap-2'>
              <svg className='w-6 h-6 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
              自动同步配置
            </h2>
            
            <div>
              <label className='block text-sm font-medium text-gray-700 mb-2'>
                每日同步时间
              </label>
              <input
                type='time'
                value={syncConfig.customer_sync_time}
                onChange={e => setSyncConfig({ ...syncConfig, customer_sync_time: e.target.value })}
                className='w-full max-w-xs px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              />
              <p className='text-xs text-gray-500 mt-1'>
                每天在此时间自动同步所有节点的客户数据
              </p>
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

              <button
                onClick={() => handleManualSync('customer')}
                disabled={syncing || instances.length === 0}
                className='w-full px-6 py-3 bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg hover:from-green-700 hover:to-teal-700 transition disabled:opacity-50 font-medium'
              >
                {syncing ? (
                  <span className='flex items-center justify-center gap-2'>
                    <svg className='w-5 h-5 animate-spin' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                    </svg>
                    同步中...
                  </span>
                ) : '立即同步客户数据'}
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
    </div>
  )
}

