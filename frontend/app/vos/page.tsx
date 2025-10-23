'use client'
import React, {useEffect, useState} from 'react'
import api from '../../lib/api'
import Card from '../../components/ui/Card'

interface VOSInstance {
  id: number
  name: string
  base_url: string
  description?: string
  enabled: boolean
}

export default function VosList(){
  const [instances, setInstances] = useState<VOSInstance[]>([])
  const [showModal, setShowModal] = useState(false)
  const [editingInstance, setEditingInstance] = useState<VOSInstance | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    base_url: '',
    description: '',
    enabled: true
  })
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

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

  function openCreateModal() {
    setEditingInstance(null)
    setFormData({ name: '', base_url: '', description: '', enabled: true })
    setShowModal(true)
  }

  function openEditModal(instance: VOSInstance) {
    setEditingInstance(instance)
    setFormData({
      name: instance.name,
      base_url: instance.base_url,
      description: instance.description || '',
      enabled: instance.enabled
    })
    setShowModal(true)
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      if (editingInstance) {
        // 更新
        await api.put(`/vos/instances/${editingInstance.id}`, formData)
        setMessage('节点更新成功')
      } else {
        // 创建
        await api.post('/vos/instances', formData)
        setMessage('节点创建成功')
      }
      setShowModal(false)
      fetchInstances()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '操作失败')
    } finally {
      setLoading(false)
    }
  }

  async function handleDelete(id: number, name: string) {
    if (!confirm(`确定要删除节点 "${name}" 吗？这将同时删除该节点下的所有电话记录。`)) {
      return
    }

    try {
      await api.delete(`/vos/instances/${id}`)
      setMessage('节点删除成功')
      fetchInstances()
    } catch (e: any) {
      setMessage(e.response?.data?.detail || '删除失败')
    }
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex justify-between items-center mb-6'>
        <h1 className='text-3xl font-bold text-gray-800'>VOS 节点管理</h1>
        <button
          onClick={openCreateModal}
          className='px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium'
        >
          + 添加节点
        </button>
      </div>

      {message && (
        <div className={`mb-4 p-4 rounded-lg ${message.includes('成功') ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'}`}>
          {message}
        </div>
      )}

      {instances.length === 0 ? (
        <div className='text-center py-16 bg-white rounded-lg shadow-sm'>
          <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
          </svg>
          <h3 className='mt-2 text-lg font-medium text-gray-900'>暂无 VOS 节点</h3>
          <p className='mt-1 text-sm text-gray-500'>点击"添加节点"按钮创建第一个 VOS 节点</p>
        </div>
      ) : (
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
                <a
                  href={`/vos/${inst.id}`}
                  className='flex-1 px-3 py-2 text-center text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition'
                >
                  查看详情
                </a>
                <button
                  onClick={() => openEditModal(inst)}
                  className='px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition'
                >
                  编辑
                </button>
                <button
                  onClick={() => handleDelete(inst.id, inst.name)}
                  className='px-3 py-2 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100 transition'
                >
                  删除
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 创建/编辑模态框 */}
      {showModal && (
        <div className='fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50' onClick={() => setShowModal(false)}>
          <div className='bg-white rounded-lg p-6 max-w-lg w-full mx-4' onClick={e => e.stopPropagation()}>
            <h2 className='text-2xl font-bold mb-4'>
              {editingInstance ? '编辑 VOS 节点' : '添加 VOS 节点'}
            </h2>
            <form onSubmit={handleSubmit} className='space-y-4'>
              <div>
                <label className='block text-sm font-medium mb-1'>节点名称 *</label>
                <input
                  type='text'
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='例如: 生产环境-VOS1'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>Base URL *</label>
                <input
                  type='url'
                  value={formData.base_url}
                  onChange={e => setFormData({ ...formData, base_url: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  placeholder='https://vos.example.com'
                  required
                />
              </div>
              <div>
                <label className='block text-sm font-medium mb-1'>描述</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({ ...formData, description: e.target.value })}
                  className='w-full p-2 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
                  rows={3}
                  placeholder='节点描述信息（可选）'
                />
              </div>
              <div className='flex items-center'>
                <input
                  type='checkbox'
                  id='enabled'
                  checked={formData.enabled}
                  onChange={e => setFormData({ ...formData, enabled: e.target.checked })}
                  className='w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
                />
                <label htmlFor='enabled' className='ml-2 text-sm font-medium'>启用此节点</label>
              </div>
              <div className='flex gap-2 pt-4'>
                <button
                  type='button'
                  onClick={() => setShowModal(false)}
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
