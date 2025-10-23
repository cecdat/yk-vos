'use client'
import React, { useState, useEffect } from 'react'
import api from '../lib/api'

interface CacheStats {
  total: number
  valid: number
  expired: number
  invalid: number
  by_api: Array<{ api: string; count: number }>
}

interface Props {
  instanceId: number
  instanceName: string
}

export default function CacheManagement({ instanceId, instanceName }: Props) {
  const [stats, setStats] = useState<CacheStats | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    fetchStats()
  }, [instanceId])

  const fetchStats = async () => {
    setLoading(true)
    try {
      const res = await api.get(`/vos-api/instances/${instanceId}/cache/stats`)
      setStats(res.data?.stats)
    } catch (e) {
      console.error('获取缓存统计失败:', e)
    } finally {
      setLoading(false)
    }
  }

  const handleClearCache = async (apiPath?: string) => {
    const message = apiPath 
      ? `确定要清除 ${apiPath} 的缓存吗？`
      : '确定要清除所有缓存吗？'
    
    if (!confirm(message)) return

    try {
      const url = apiPath 
        ? `/vos-api/instances/${instanceId}/cache?api_path=${encodeURIComponent(apiPath)}`
        : `/vos-api/instances/${instanceId}/cache`
      
      await api.delete(url)
      alert('缓存已清除')
      await fetchStats()
    } catch (e) {
      console.error('清除缓存失败:', e)
      alert('清除缓存失败')
    }
  }

  if (loading && !stats) {
    return (
      <div className='bg-white rounded-xl shadow-lg p-6'>
        <div className='flex items-center justify-center py-8'>
          <svg className='animate-spin h-8 w-8 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
          </svg>
        </div>
      </div>
    )
  }

  if (!stats) return null

  const hitRate = stats.total > 0 ? ((stats.valid / stats.total) * 100).toFixed(1) : '0'

  return (
    <div className='bg-white rounded-xl shadow-lg p-6'>
      {/* 头部 */}
      <div className='flex items-center justify-between mb-6'>
        <div>
          <h2 className='text-2xl font-bold text-gray-800'>缓存管理</h2>
          <p className='text-sm text-gray-600 mt-1'>实例: {instanceName}</p>
        </div>
        <div className='flex gap-2'>
          <button
            onClick={fetchStats}
            disabled={loading}
            className='px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition disabled:opacity-50 flex items-center gap-2'
          >
            <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
            </svg>
            刷新
          </button>
          <button
            onClick={() => handleClearCache()}
            className='px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition'
          >
            清除所有缓存
          </button>
        </div>
      </div>

      {/* 统计卡片 */}
      <div className='grid grid-cols-2 md:grid-cols-4 gap-4 mb-6'>
        <div className='bg-gradient-to-br from-blue-50 to-blue-100 rounded-lg p-4 border border-blue-200'>
          <p className='text-sm text-blue-700 font-medium mb-1'>总缓存数</p>
          <p className='text-3xl font-bold text-blue-900'>{stats.total}</p>
        </div>
        
        <div className='bg-gradient-to-br from-green-50 to-green-100 rounded-lg p-4 border border-green-200'>
          <p className='text-sm text-green-700 font-medium mb-1'>有效缓存</p>
          <p className='text-3xl font-bold text-green-900'>{stats.valid}</p>
          <p className='text-xs text-green-600 mt-1'>命中率: {hitRate}%</p>
        </div>
        
        <div className='bg-gradient-to-br from-orange-50 to-orange-100 rounded-lg p-4 border border-orange-200'>
          <p className='text-sm text-orange-700 font-medium mb-1'>已过期</p>
          <p className='text-3xl font-bold text-orange-900'>{stats.expired}</p>
        </div>
        
        <div className='bg-gradient-to-br from-red-50 to-red-100 rounded-lg p-4 border border-red-200'>
          <p className='text-sm text-red-700 font-medium mb-1'>无效缓存</p>
          <p className='text-3xl font-bold text-red-900'>{stats.invalid}</p>
        </div>
      </div>

      {/* API 缓存分布 */}
      {stats.by_api && stats.by_api.length > 0 && (
        <div>
          <h3 className='text-lg font-semibold text-gray-800 mb-3'>各API缓存分布</h3>
          <div className='space-y-2 max-h-96 overflow-y-auto'>
            {stats.by_api
              .sort((a, b) => b.count - a.count)
              .map((item) => {
                const percentage = ((item.count / stats.total) * 100).toFixed(1)
                return (
                  <div 
                    key={item.api} 
                    className='flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition'
                  >
                    <div className='flex-1'>
                      <div className='flex items-center justify-between mb-1'>
                        <span className='font-medium text-gray-800 text-sm'>{item.api}</span>
                        <span className='text-sm text-gray-600'>{item.count} 条</span>
                      </div>
                      <div className='w-full bg-gray-200 rounded-full h-2'>
                        <div 
                          className='bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all'
                          style={{ width: `${percentage}%` }}
                        />
                      </div>
                    </div>
                    <button
                      onClick={() => handleClearCache(`/external/server/${item.api}`)}
                      className='ml-3 px-3 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 transition text-xs'
                    >
                      清除
                    </button>
                  </div>
                )
              })}
          </div>
        </div>
      )}

      {stats.total === 0 && (
        <div className='text-center py-12 text-gray-500'>
          <svg className='mx-auto h-12 w-12 text-gray-400 mb-3' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' />
          </svg>
          <p className='text-lg font-medium'>暂无缓存数据</p>
          <p className='text-sm mt-1'>开始使用 VOS API 查询后将自动生成缓存</p>
        </div>
      )}
    </div>
  )
}

