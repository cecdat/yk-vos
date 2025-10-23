'use client'
import React, { useEffect, useState } from 'react'
import api from '../../lib/api'
import Card from '../../components/ui/Card'

interface VOSInstance {
  id: number
  name: string
  base_url: string
  description?: string
  enabled: boolean
}

export default function SettingsPage() {
  // VOS 节点相关状态
  const [instances, setInstances] = useState<VOSInstance[]>([])
  const [showVOSModal, setShowVOSModal] = useState(false)
  const [editingInstance, setEditingInstance] = useState<VOSInstance | null>(null)
  const [vosFormData, setVosFormData] = useState({
    name: '',
    base_url: '',
    description: '',
    enabled: true
  })
  
  // 修改密码相关状态
  const [passwordForm, setPasswordForm] = useState({
    old_password: '',
    new_password: '',
    confirm_password: ''
  })
  
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [activeTab, setActiveTab] = useState<'vos' | 'password' | 'sync'>('vos')
  
  // 同步配置相关状态
  const [syncConfigs, setSyncConfigs] = useState<any[]>([])
  const [showSyncModal, setShowSyncModal] = useState(false)
  const [editingSyncConfig, setEditingSyncConfig] = useState<any | null>(null)
  const [syncFormData, setSyncFormData] = useState({
    name: '',
    description: '',
    cron_expression: '*/10 * * * *',
    enabled: true,
    sync_type: 'customers'
  })

  useEffect(() => {
    fetchInstances()
    fetchSyncConfigs()
  }, [])

  async function fetchInstances() {
    try {
      const res = await api.get('/vos/instances')
      setInstances(res.data || [])
    } catch (e: any) {
      console.error(e)
      setMessage(e.response?.data?.detail || '获取节点列表失败')
    }
  }

  async function fetchSyncConfigs() {
    try {
      const res = await api.get('/sync-config/configs')
      setSyncConfigs(res.data?.configs || [])
    } catch (e: any) {
      console.error(e)
      setMessage(e.response?.data?.detail || '获取同步配置失败')
    }
  }

  // ===== VOS 节点管理功能 =====
  
  function openCreateVOSModal() {
    setEditingInstance(null)
    setVosFormData({ name: '', base_url: '', description: '', enabled: true })
    setShowVOSModal(true)
  }

  function openEditVOSModal(instance: VOSInstance) {
    setEditingInstance(instance)
    setVosFormData({
      name: instance.name,
      base_url: instance.base_url,
      description: instance.description || '',
      enabled: instance.enabled
    })
    setShowVOSModal(true)
  }

  async function handleVOSSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      if (editingInstance) {
        await api.put(`/vos/instances/${editingInstance.id}`, vosFormData)
        setMessage('VOS 节点更新成功')
      } else {
        await api.post('/vos/instances', vosFormData)
        setMessage('VOS 节点创建成功')
      }
      setShowVOSModal(false)
      fetchInstances()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleVOSDelete(id: number, name: string) {
    if (!confirm(`确定要删除 VOS 节点 "${name}" 吗？这将同时删除该节点下的所有电话记录。`)) {
      return
    }

    try {
      await api.delete(`/vos/instances/${id}`)
      setMessage('VOS 节点删除成功')
      fetchInstances()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '删除失败')
    }
  }

  // ===== 修改密码功能 =====
  
  async function handlePasswordChange(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    // 验证两次输入的新密码是否一致
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setMessage('两次输入的新密码不一致')
      setLoading(false)
      return
    }

    // 验证新密码长度
    if (passwordForm.new_password.length < 6) {
      setMessage('新密码长度至少为6位')
      setLoading(false)
      return
    }

    try {
      await api.post('/auth/change-password', {
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password
      })
      setMessage('密码修改成功，请重新登录')
      setPasswordForm({ old_password: '', new_password: '', confirm_password: '' })
      
      // 3秒后跳转到登录页
      setTimeout(() => {
        localStorage.removeItem('token')
        window.location.href = '/login'
      }, 3000)
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '密码修改失败')
    } finally {
      setLoading(false)
    }
  }

  // ===== 同步配置管理功能 =====
  
  function openCreateSyncModal() {
    setEditingSyncConfig(null)
    setSyncFormData({
      name: '',
      description: '',
      cron_expression: '*/10 * * * *',
      enabled: true,
      sync_type: 'customers'
    })
    setShowSyncModal(true)
  }

  function openEditSyncModal(config: any) {
    setEditingSyncConfig(config)
    setSyncFormData({
      name: config.name,
      description: config.description || '',
      cron_expression: config.cron_expression,
      enabled: config.enabled,
      sync_type: config.sync_type
    })
    setShowSyncModal(true)
  }

  async function handleSyncSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      if (editingSyncConfig) {
        await api.put(`/sync-config/configs/${editingSyncConfig.id}`, syncFormData)
        setMessage('同步配置更新成功')
      } else {
        await api.post('/sync-config/configs', syncFormData)
        setMessage('同步配置创建成功')
      }
      setShowSyncModal(false)
      fetchSyncConfigs()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleSyncDelete(id: number, name: string) {
    if (!confirm(`确定要删除同步配置 "${name}" 吗？`)) {
      return
    }

    try {
      await api.delete(`/sync-config/configs/${id}`)
      setMessage('同步配置删除成功')
      fetchSyncConfigs()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '删除失败')
    }
  }

  return (
    <div className='max-w-7xl'>
      <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-6'>
        系统设置
      </h1>

      {message && (
        <div className={`mb-4 p-4 rounded-lg ${message.includes('成功') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message}
        </div>
      )}

      {/* 标签切换 */}
      <div className='flex gap-2 mb-6'>
        <button
          onClick={() => setActiveTab('vos')}
          className={`px-6 py-3 rounded-lg font-medium transition ${
            activeTab === 'vos'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          VOS 节点管理
        </button>
        <button
          onClick={() => setActiveTab('sync')}
          className={`px-6 py-3 rounded-lg font-medium transition ${
            activeTab === 'sync'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          数据同步配置
        </button>
        <button
          onClick={() => setActiveTab('password')}
          className={`px-6 py-3 rounded-lg font-medium transition ${
            activeTab === 'password'
              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
              : 'bg-white text-gray-700 hover:bg-gray-50'
          }`}
        >
          修改密码
        </button>
      </div>

      {/* VOS 节点管理 */}
      {activeTab === 'vos' && (
        <div>
          <div className='flex justify-between items-center mb-4'>
            <h2 className='text-xl font-bold text-gray-800'>VOS 节点列表</h2>
            <button
              onClick={openCreateVOSModal}
              className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-medium'
            >
              + 添加节点
            </button>
          </div>

          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {instances.map(inst => (
              <Card key={inst.id}>
                <div className='flex justify-between items-start mb-3'>
                  <div className='flex-1'>
                    <h3 className='text-lg font-semibold text-gray-900'>{inst.name}</h3>
                    <div className='mt-1 text-sm text-gray-600 break-all'>{inst.base_url}</div>
                    {inst.description && (
                      <p className='mt-2 text-sm text-gray-500'>{inst.description}</p>
                    )}
                  </div>
                  <span className={`ml-2 px-2 py-1 text-xs rounded-full ${inst.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                    {inst.enabled ? '启用' : '禁用'}
                  </span>
                </div>
                <div className='flex gap-2 mt-4 pt-3 border-t'>
                  <button
                    onClick={() => openEditVOSModal(inst)}
                    className='flex-1 px-3 py-2 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition'
                  >
                    编辑
                  </button>
                  <button
                    onClick={() => handleVOSDelete(inst.id, inst.name)}
                    className='px-3 py-2 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100 transition'
                  >
                    删除
                  </button>
                </div>
              </Card>
            ))}
          </div>

          {instances.length === 0 && (
            <div className='text-center py-16 bg-white rounded-lg'>
              <p className='text-gray-500'>暂无 VOS 节点，请添加节点</p>
            </div>
          )}
        </div>
      )}

      {/* 数据同步配置 */}
      {activeTab === 'sync' && (
        <div>
          <div className='flex justify-between items-center mb-4'>
            <h2 className='text-xl font-bold text-gray-800'>数据同步配置</h2>
            <button
              onClick={openCreateSyncModal}
              className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-medium'
            >
              + 添加配置
            </button>
          </div>

          <div className='bg-white rounded-xl shadow-sm overflow-hidden'>
            <div className='overflow-x-auto'>
              <table className='w-full'>
                <thead className='bg-gradient-to-r from-gray-50 to-gray-100'>
                  <tr>
                    <th className='px-6 py-4 text-left text-sm font-semibold text-gray-700'>配置名称</th>
                    <th className='px-6 py-4 text-left text-sm font-semibold text-gray-700'>同步类型</th>
                    <th className='px-6 py-4 text-left text-sm font-semibold text-gray-700'>Cron表达式</th>
                    <th className='px-6 py-4 text-center text-sm font-semibold text-gray-700'>状态</th>
                    <th className='px-6 py-4 text-center text-sm font-semibold text-gray-700'>操作</th>
                  </tr>
                </thead>
                <tbody className='divide-y divide-gray-200'>
                  {syncConfigs.map(config => (
                    <tr key={config.id} className='hover:bg-gray-50 transition'>
                      <td className='px-6 py-4'>
                        <div className='font-medium text-gray-900'>{config.name}</div>
                        {config.description && (
                          <div className='text-sm text-gray-500 mt-1'>{config.description}</div>
                        )}
                      </td>
                      <td className='px-6 py-4'>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          config.sync_type === 'customers' ? 'bg-blue-100 text-blue-800' :
                          config.sync_type === 'phones' ? 'bg-green-100 text-green-800' :
                          config.sync_type === 'cdrs' ? 'bg-purple-100 text-purple-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {config.sync_type === 'customers' ? '客户数据' :
                           config.sync_type === 'phones' ? '话机状态' :
                           config.sync_type === 'cdrs' ? '话单记录' : '全部数据'}
                        </span>
                      </td>
                      <td className='px-6 py-4'>
                        <code className='text-sm bg-gray-100 px-2 py-1 rounded'>{config.cron_expression}</code>
                      </td>
                      <td className='px-6 py-4 text-center'>
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                          config.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                        }`}>
                          {config.enabled ? '启用' : '禁用'}
                        </span>
                      </td>
                      <td className='px-6 py-4'>
                        <div className='flex gap-2 justify-center'>
                          <button
                            onClick={() => openEditSyncModal(config)}
                            className='px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition'
                          >
                            编辑
                          </button>
                          <button
                            onClick={() => handleSyncDelete(config.id, config.name)}
                            className='px-3 py-1 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100 transition'
                          >
                            删除
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            {syncConfigs.length === 0 && (
              <div className='text-center py-16'>
                <p className='text-gray-500'>暂无同步配置，请添加配置</p>
              </div>
            )}
          </div>

          {/* Cron 表达式说明 */}
          <div className='mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200'>
            <h3 className='font-semibold text-blue-900 mb-2'>📘 Cron 表达式格式说明</h3>
            <p className='text-sm text-blue-800 mb-2'>格式：分 时 日 月 周 (5个字段)</p>
            <div className='grid grid-cols-2 gap-2 text-sm text-blue-700'>
              <div><code className='bg-white px-2 py-0.5 rounded'>*/5 * * * *</code> - 每5分钟</div>
              <div><code className='bg-white px-2 py-0.5 rounded'>*/10 * * * *</code> - 每10分钟</div>
              <div><code className='bg-white px-2 py-0.5 rounded'>0 * * * *</code> - 每小时</div>
              <div><code className='bg-white px-2 py-0.5 rounded'>0 2 * * *</code> - 每天凌晨2点</div>
              <div><code className='bg-white px-2 py-0.5 rounded'>30 1 * * *</code> - 每天凌晨1:30</div>
              <div><code className='bg-white px-2 py-0.5 rounded'>0 0 * * 0</code> - 每周日午夜</div>
            </div>
          </div>
        </div>
      )}

      {/* 修改密码 */}
      {activeTab === 'password' && (
        <div className='max-w-md'>
          <Card>
            <h2 className='text-xl font-bold mb-4'>修改登录密码</h2>
            <form onSubmit={handlePasswordChange} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-1'>当前密码</label>
                <input
                  type='password'
                  value={passwordForm.old_password}
                  onChange={e => setPasswordForm({ ...passwordForm, old_password: e.target.value })}
                  className='w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='请输入当前密码'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>新密码</label>
                <input
                  type='password'
                  value={passwordForm.new_password}
                  onChange={e => setPasswordForm({ ...passwordForm, new_password: e.target.value })}
                  className='w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='请输入新密码（至少6位）'
                  required
                  minLength={6}
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>确认新密码</label>
                <input
                  type='password'
                  value={passwordForm.confirm_password}
                  onChange={e => setPasswordForm({ ...passwordForm, confirm_password: e.target.value })}
                  className='w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='请再次输入新密码'
                  required
                  minLength={6}
                />
              </div>
              <button
                type='submit'
                disabled={loading}
                className='w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:opacity-50 transition'
              >
                {loading ? '处理中...' : '修改密码'}
              </button>
              <p className='text-sm text-gray-500 mt-2'>
                ⚠️ 修改密码后需要重新登录
              </p>
            </form>
          </Card>
        </div>
      )}

      {/* VOS 节点创建/编辑模态框 */}
      {showVOSModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50' onClick={() => setShowVOSModal(false)}>
          <div className='bg-white rounded-lg p-6 max-w-lg w-full mx-4' onClick={e => e.stopPropagation()}>
            <h2 className='text-2xl font-bold mb-4'>
              {editingInstance ? '编辑 VOS 节点' : '添加 VOS 节点'}
            </h2>
            <form onSubmit={handleVOSSubmit} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-1'>节点名称 *</label>
                <input
                  type='text'
                  value={vosFormData.name}
                  onChange={e => setVosFormData({ ...vosFormData, name: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='例如: 生产环境-VOS1'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>Base URL *</label>
                <input
                  type='url'
                  value={vosFormData.base_url}
                  onChange={e => setVosFormData({ ...vosFormData, base_url: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='https://vos.example.com'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>描述</label>
                <textarea
                  value={vosFormData.description}
                  onChange={e => setVosFormData({ ...vosFormData, description: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  rows={3}
                  placeholder='节点描述信息（可选）'
                />
              </div>
              <div className='flex items-center'>
                <input
                  type='checkbox'
                  id='enabled'
                  checked={vosFormData.enabled}
                  onChange={e => setVosFormData({ ...vosFormData, enabled: e.target.checked })}
                  className='w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
                />
                <label htmlFor='enabled' className='ml-2 text-sm font-medium'>启用此节点</label>
              </div>
              <div className='flex gap-2 pt-4'>
                <button
                  type='button'
                  onClick={() => setShowVOSModal(false)}
                  className='flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 transition'
                  disabled={loading}
                >
                  取消
                </button>
                <button
                  type='submit'
                  className='flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:bg-gray-400'
                  disabled={loading}
                >
                  {loading ? '处理中...' : (editingInstance ? '更新' : '创建')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* 同步配置创建/编辑模态框 */}
      {showSyncModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50' onClick={() => setShowSyncModal(false)}>
          <div className='bg-white rounded-lg p-6 max-w-lg w-full mx-4' onClick={e => e.stopPropagation()}>
            <h2 className='text-2xl font-bold mb-4'>
              {editingSyncConfig ? '编辑同步配置' : '添加同步配置'}
            </h2>
            <form onSubmit={handleSyncSubmit} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-1'>配置名称 *</label>
                <input
                  type='text'
                  value={syncFormData.name}
                  onChange={e => setSyncFormData({ ...syncFormData, name: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='例如: 客户数据同步'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>描述</label>
                <textarea
                  value={syncFormData.description}
                  onChange={e => setSyncFormData({ ...syncFormData, description: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  rows={2}
                  placeholder='配置描述信息（可选）'
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>同步类型 *</label>
                <select
                  value={syncFormData.sync_type}
                  onChange={e => setSyncFormData({ ...syncFormData, sync_type: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  required
                >
                  <option value='customers'>客户数据</option>
                  <option value='phones'>话机状态</option>
                  <option value='cdrs'>话单记录</option>
                  <option value='all'>全部数据</option>
                </select>
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>Cron 表达式 *</label>
                <input
                  type='text'
                  value={syncFormData.cron_expression}
                  onChange={e => setSyncFormData({ ...syncFormData, cron_expression: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none font-mono'
                  placeholder='*/10 * * * *'
                  required
                />
                <p className='text-xs text-gray-500 mt-1'>
                  格式：分 时 日 月 周 (例如: */10 * * * * 表示每10分钟)
                </p>
              </div>
              <div className='flex items-center'>
                <input
                  type='checkbox'
                  id='sync_enabled'
                  checked={syncFormData.enabled}
                  onChange={e => setSyncFormData({ ...syncFormData, enabled: e.target.checked })}
                  className='w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
                />
                <label htmlFor='sync_enabled' className='ml-2 text-sm font-medium'>启用此配置</label>
              </div>
              <div className='flex gap-2 pt-4'>
                <button
                  type='button'
                  onClick={() => setShowSyncModal(false)}
                  className='flex-1 px-4 py-2 border border-gray-300 rounded hover:bg-gray-50 transition'
                  disabled={loading}
                >
                  取消
                </button>
                <button
                  type='submit'
                  className='flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition disabled:bg-gray-400'
                  disabled={loading}
                >
                  {loading ? '处理中...' : (editingSyncConfig ? '更新' : '创建')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

