'use client'
import { useState, useEffect } from 'react'
import { useVOS } from '../../contexts/VOSContext'
import api from '../../lib/api'

export default function StatisticsPage() {
  const { currentVOS } = useVOS()
  const [instances, setInstances] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInstances()
  }, [])

  async function fetchInstances() {
    setLoading(true)
    try {
      const res = await api.get('/vos/instances')
      setInstances(res.data || [])
    } catch (e) {
      console.error('获取实例失败:', e)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className='flex items-center justify-center py-20'>
        <svg className='animate-spin h-10 w-10 text-blue-600' fill='none' viewBox='0 0 24 24'>
          <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' />
          <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z' />
        </svg>
      </div>
    )
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          数据统计
        </h1>
        <button
          onClick={fetchInstances}
          disabled={loading}
          className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition flex items-center gap-2 disabled:opacity-50'
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
          </svg>
          刷新数据
        </button>
      </div>

      {/* 已注册 VOS 实例 */}
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

