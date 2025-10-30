'use client'
import { useState, useEffect } from 'react'
import { useVOS } from '../../contexts/VOSContext'
import api from '../../lib/api'

interface Gateway {
  gatewayName?: string
  gatewayType?: string
  ipAddress?: string
  port?: number
  protocol?: string
  isOnline?: boolean
  asr?: number
  acd?: number
  concurrentCalls?: number
  [key: string]: any
}

export default function GatewayPage() {
  const { currentVOS } = useVOS()
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState<'mapping' | 'routing'>('mapping')
  
  // 对接网关数据
  const [mappingGateways, setMappingGateways] = useState<Gateway[]>([])
  const [mappingLoading, setMappingLoading] = useState(false)
  
  // 落地网关数据
  const [routingGateways, setRoutingGateways] = useState<Gateway[]>([])
  const [routingLoading, setRoutingLoading] = useState(false)

  // 加载对接网关
  async function loadMappingGateways() {
    if (!currentVOS) {
      alert('请先选择VOS节点')
      return
    }
    
    setMappingLoading(true)
    try {
      // 后端 query_vos_api 会自动处理空数组参数，发送空对象 {} 到 VOS API
      const res = await api.post(`/vos-api/instances/${currentVOS.id}/GetGatewayMapping`, {
        names: []
      })
      
      // 后端返回格式：{ success, data, error, data_source, synced_at, instance_name }
      if (res.data.success === false) {
        throw new Error(res.data.error || '获取对接网关失败')
      }
      
      // res.data.data 是 VOS API 的原始响应
      const vosApiResponse = res.data.data || {}
      const gateways = vosApiResponse.gatewayMappings || 
                      vosApiResponse.infoGatewayMappings || 
                      []
      
      console.log(`加载对接网关成功: ${gateways.length}个 (来源: ${res.data.data_source})`)
      setMappingGateways(gateways)
    } catch (e: any) {
      console.error('加载对接网关失败:', e)
      alert(e.response?.data?.detail || e.message || '加载对接网关失败')
    } finally {
      setMappingLoading(false)
    }
  }

  // 加载落地网关
  async function loadRoutingGateways() {
    if (!currentVOS) {
      alert('请先选择VOS节点')
      return
    }
    
    setRoutingLoading(true)
    try {
      // 后端 query_vos_api 会自动处理空数组参数，发送空对象 {} 到 VOS API
      const res = await api.post(`/vos-api/instances/${currentVOS.id}/GetGatewayRouting`, {
        names: []
      })
      
      // 后端返回格式：{ success, data, error, data_source, synced_at, instance_name }
      if (res.data.success === false) {
        throw new Error(res.data.error || '获取落地网关失败')
      }
      
      // res.data.data 是 VOS API 的原始响应
      const vosApiResponse = res.data.data || {}
      const gateways = vosApiResponse.gatewayRoutings || 
                      vosApiResponse.infoGatewayRoutings || 
                      []
      
      console.log(`加载落地网关成功: ${gateways.length}个 (来源: ${res.data.data_source})`)
      setRoutingGateways(gateways)
    } catch (e: any) {
      console.error('加载落地网关失败:', e)
      alert(e.response?.data?.detail || e.message || '加载落地网关失败')
    } finally {
      setRoutingLoading(false)
    }
  }

  // 自动加载当前激活的网关数据
  useEffect(() => {
    if (currentVOS) {
      if (activeTab === 'mapping') {
        loadMappingGateways()
      } else {
        loadRoutingGateways()
      }
    }
  }, [currentVOS, activeTab])

  // 刷新当前标签页数据
  function handleRefresh() {
    if (activeTab === 'mapping') {
      loadMappingGateways()
    } else {
      loadRoutingGateways()
    }
  }

  // 渲染对接网关表格
  function renderMappingTable() {
    if (mappingLoading) {
      return (
        <div className='flex items-center justify-center py-20'>
          <svg className='animate-spin h-10 w-10 text-blue-600' fill='none' viewBox='0 0 24 24'>
            <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' />
            <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z' />
          </svg>
        </div>
      )
    }

    if (mappingGateways.length === 0) {
      return (
        <div className='text-center py-20 text-gray-500'>
          <svg className='mx-auto h-12 w-12 text-gray-400 mb-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' />
          </svg>
          <p className='text-lg'>暂无对接网关数据</p>
        </div>
      )
    }

    return (
      <div className='overflow-x-auto'>
        <table className='min-w-full divide-y divide-gray-200'>
          <thead className='bg-gray-50'>
            <tr>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>网关名称</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>IP地址</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>端口</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>协议</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>ASR</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>ACD</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>并发</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>状态</th>
            </tr>
          </thead>
          <tbody className='bg-white divide-y divide-gray-200'>
            {mappingGateways.map((gw, idx) => (
              <tr key={idx} className='hover:bg-gray-50'>
                <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                  {gw.gatewayName || gw.name || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.ipAddress || gw.ip || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.port || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.protocol || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.asr !== undefined ? `${gw.asr}%` : '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.acd !== undefined ? `${gw.acd}s` : '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.concurrentCalls || gw.concurrent || 0}
                </td>
                <td className='px-6 py-4 whitespace-nowrap'>
                  {gw.isOnline || gw.online ? (
                    <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800'>
                      在线
                    </span>
                  ) : (
                    <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
                      离线
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  // 渲染落地网关表格
  function renderRoutingTable() {
    if (routingLoading) {
      return (
        <div className='flex items-center justify-center py-20'>
          <svg className='animate-spin h-10 w-10 text-blue-600' fill='none' viewBox='0 0 24 24'>
            <circle className='opacity-25' cx='12' cy='12' r='10' stroke='currentColor' strokeWidth='4' />
            <path className='opacity-75' fill='currentColor' d='M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z' />
          </svg>
        </div>
      )
    }

    if (routingGateways.length === 0) {
      return (
        <div className='text-center py-20 text-gray-500'>
          <svg className='mx-auto h-12 w-12 text-gray-400 mb-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' />
          </svg>
          <p className='text-lg'>暂无落地网关数据</p>
        </div>
      )
    }

    return (
      <div className='overflow-x-auto'>
        <table className='min-w-full divide-y divide-gray-200'>
          <thead className='bg-gray-50'>
            <tr>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>网关名称</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>IP地址</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>端口</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>协议</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>ASR</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>ACD</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>并发</th>
              <th className='px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider'>状态</th>
            </tr>
          </thead>
          <tbody className='bg-white divide-y divide-gray-200'>
            {routingGateways.map((gw, idx) => (
              <tr key={idx} className='hover:bg-gray-50'>
                <td className='px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900'>
                  {gw.gatewayName || gw.name || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.ipAddress || gw.ip || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.port || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.protocol || '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.asr !== undefined ? `${gw.asr}%` : '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.acd !== undefined ? `${gw.acd}s` : '-'}
                </td>
                <td className='px-6 py-4 whitespace-nowrap text-sm text-gray-500'>
                  {gw.concurrentCalls || gw.concurrent || 0}
                </td>
                <td className='px-6 py-4 whitespace-nowrap'>
                  {gw.isOnline || gw.online ? (
                    <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800'>
                      在线
                    </span>
                  ) : (
                    <span className='inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800'>
                      离线
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <div className='space-y-6'>
      {/* 页面标题 */}
      <div className='flex items-center justify-between'>
        <h1 className='text-2xl font-bold text-gray-900'>网关管理</h1>
        <button
          onClick={handleRefresh}
          disabled={mappingLoading || routingLoading}
          className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 flex items-center gap-2 shadow-md hover:shadow-lg'
        >
          <svg 
            className={`w-4 h-4 ${(mappingLoading || routingLoading) ? 'animate-spin' : ''}`} 
            fill='none' 
            viewBox='0 0 24 24' 
            stroke='currentColor'
          >
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
          </svg>
          刷新数据
        </button>
      </div>

      {/* 节点提示 */}
      {!currentVOS && (
        <div className='bg-yellow-50 border-l-4 border-yellow-400 p-4 rounded'>
          <div className='flex'>
            <div className='flex-shrink-0'>
              <svg className='h-5 w-5 text-yellow-400' viewBox='0 0 20 20' fill='currentColor'>
                <path fillRule='evenodd' d='M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z' clipRule='evenodd' />
              </svg>
            </div>
            <div className='ml-3'>
              <p className='text-sm text-yellow-700'>
                请先在右上角选择一个VOS节点
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 标签页 */}
      <div className='bg-white rounded-xl shadow-lg overflow-hidden'>
        {/* Tab 头部 */}
        <div className='border-b border-gray-200'>
          <nav className='flex -mb-px'>
            <button
              onClick={() => setActiveTab('mapping')}
              className={`flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition ${
                activeTab === 'mapping'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className='flex items-center justify-center gap-2'>
                <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 7l5 5m0 0l-5 5m5-5H6' />
                </svg>
                <span>对接网关</span>
                {mappingGateways.length > 0 && (
                  <span className='ml-2 bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full text-xs font-semibold'>
                    {mappingGateways.length}
                  </span>
                )}
              </div>
            </button>
            <button
              onClick={() => setActiveTab('routing')}
              className={`flex-1 py-4 px-6 text-center border-b-2 font-medium text-sm transition ${
                activeTab === 'routing'
                  ? 'border-purple-500 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <div className='flex items-center justify-center gap-2'>
                <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M11 17l-5-5m0 0l5-5m-5 5h12' />
                </svg>
                <span>落地网关</span>
                {routingGateways.length > 0 && (
                  <span className='ml-2 bg-purple-100 text-purple-600 px-2 py-0.5 rounded-full text-xs font-semibold'>
                    {routingGateways.length}
                  </span>
                )}
              </div>
            </button>
          </nav>
        </div>

        {/* Tab 内容 */}
        <div className='p-6'>
          {activeTab === 'mapping' ? renderMappingTable() : renderRoutingTable()}
        </div>
      </div>

      {/* 统计信息 */}
      {(mappingGateways.length > 0 || routingGateways.length > 0) && (
        <div className='grid grid-cols-1 md:grid-cols-3 gap-4'>
          <div className='bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-5 text-white shadow-lg'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-blue-100 text-xs mb-1'>对接网关总数</p>
                <p className='text-2xl font-bold'>{mappingGateways.length}</p>
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
                <p className='text-2xl font-bold'>{routingGateways.length}</p>
              </div>
              <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
                <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M11 17l-5-5m0 0l5-5m-5 5h12' />
                </svg>
              </div>
            </div>
          </div>

          <div className='bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-5 text-white shadow-lg'>
            <div className='flex items-center justify-between'>
              <div>
                <p className='text-green-100 text-xs mb-1'>在线网关数</p>
                <p className='text-2xl font-bold'>
                  {[...mappingGateways, ...routingGateways].filter(gw => gw.isOnline || gw.online).length}
                </p>
              </div>
              <div className='w-10 h-10 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
                <svg className='w-5 h-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' />
                </svg>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

