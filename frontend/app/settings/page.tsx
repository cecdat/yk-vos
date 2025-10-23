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
  const [activeTab, setActiveTab] = useState<'vos' | 'password'>('vos')

  useEffect(() => {
    fetchInstances()
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
    </div>
  )
}

