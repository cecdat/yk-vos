'use client'
import React, { useState, useEffect } from 'react'
import { useVOS } from '../../contexts/VOSContext'
import api from '../../lib/api'
import VosApiParamForm from '../../components/VosApiParamForm'

// VOS API 接口配置（带参数定义）
const VOS_APIS = [
  {
    category: '账户管理',
    apis: [
      { 
        name: 'GetCustomer', 
        label: '查询账户', 
        description: '根据账户号码列表查询详细信息',
        params: [
          { name: 'accounts', type: 'array' as const, required: true, description: '账户列表' }
        ]
      },
      { 
        name: 'GetAllCustomers', 
        label: '获取所有账户', 
        description: '获取所有账户简要信息',
        params: [
          { name: 'type', type: 'integer' as const, required: true, description: '类型（0=账号列表, 1=简要信息）', default: 1 }
        ]
      },
      { 
        name: 'GetPayHistory', 
        label: '查询缴费记录', 
        description: '查询账户缴费历史',
        params: [
          { name: 'account', type: 'string' as const, required: true, description: '账户账号' },
          { name: 'beginTime', type: 'date' as const, required: true, description: '开始时间' },
          { name: 'endTime', type: 'date' as const, required: true, description: '结束时间' }
        ]
      },
      { 
        name: 'GetConsumption', 
        label: '查询消费记录', 
        description: '查询套餐租金、月租等消费',
        params: [
          { name: 'account', type: 'string' as const, required: true, description: '账户账号' },
          { name: 'beginTime', type: 'date' as const, required: true, description: '开始时间' },
          { name: 'endTime', type: 'date' as const, required: true, description: '结束时间' }
        ]
      },
      { 
        name: 'GetCustomerPhoneBook', 
        label: '查询电话簿', 
        description: '查询账户电话簿',
        params: [
          { name: 'account', type: 'string' as const, required: true, description: '账户账号' }
        ]
      },
    ]
  },
  {
    category: '话机管理',
    apis: [
      { 
        name: 'GetPhone', 
        label: '查询话机', 
        description: '查询话机详细信息',
        params: [
          { name: 'e164s', type: 'array' as const, required: true, description: '话机号码列表' }
        ]
      },
      { 
        name: 'GetPhoneOnline', 
        label: '查询在线话机', 
        description: '查询指定话机在线状态',
        params: [
          { name: 'e164s', type: 'array' as const, required: false, description: '话机号码列表（留空查全部）' }
        ]
      },
      { 
        name: 'GetAllPhoneOnline', 
        label: '获取所有在线话机', 
        description: '获取当前所有在线话机',
        params: []
      },
    ]
  },
  {
    category: '网关管理',
    apis: [
      { 
        name: 'GetGatewayMapping', 
        label: '查询对接网关', 
        description: '查询对接网关配置',
        params: [
          { name: 'names', type: 'array' as const, required: false, description: '网关名称列表（留空查全部）' }
        ]
      },
      { 
        name: 'GetGatewayMappingOnline', 
        label: '查询在线对接网关', 
        description: '查询对接网关在线状态',
        params: [
          { name: 'names', type: 'array' as const, required: false, description: '网关名称列表（留空查全部）' }
        ]
      },
      { 
        name: 'GetGatewayRouting', 
        label: '查询落地网关', 
        description: '查询落地网关配置',
        params: [
          { name: 'names', type: 'array' as const, required: false, description: '网关名称列表（留空查全部）' }
        ]
      },
      { 
        name: 'GetGatewayRoutingOnline', 
        label: '查询在线落地网关', 
        description: '查询落地网关在线状态',
        params: [
          { name: 'names', type: 'array' as const, required: false, description: '网关名称列表（留空查全部）' }
        ]
      },
    ]
  },
  {
    category: '通话管理',
    apis: [
      { 
        name: 'GetCurrentCall', 
        label: '查询当前通话', 
        description: '查询正在进行的通话',
        params: [
          { name: 'callerE164s', type: 'array' as const, required: false, description: '主叫号码列表' },
          { name: 'calleeE164s', type: 'array' as const, required: false, description: '被叫号码列表' }
        ]
      },
      { 
        name: 'GetCdr', 
        label: '查询历史话单', 
        description: '查询历史通话记录',
        params: [
          { name: 'accounts', type: 'array' as const, required: true, description: '账户列表' },
          { name: 'beginTime', type: 'date' as const, required: true, description: '开始时间' },
          { name: 'endTime', type: 'date' as const, required: true, description: '结束时间' }
        ]
      },
      { 
        name: 'GetPerformance', 
        label: '查询性能', 
        description: '查询系统并发数和队列长度',
        params: []
      },
    ]
  },
  {
    category: '费率与套餐',
    apis: [
      { 
        name: 'GetFeeRateGroup', 
        label: '查询费率组', 
        description: '查询费率组列表',
        params: [
          { name: 'names', type: 'array' as const, required: false, description: '费率组名称列表（留空查全部）' }
        ]
      },
      { 
        name: 'GetFeeRate', 
        label: '查询费率', 
        description: '查询费率详情',
        params: [
          { name: 'feeRateGroup', type: 'string' as const, required: true, description: '费率组名称' },
          { name: 'areaCodes', type: 'array' as const, required: false, description: '区域代码列表' }
        ]
      },
      { 
        name: 'GetSuite', 
        label: '查询套餐', 
        description: '查询套餐信息',
        params: [
          { name: 'ids', type: 'array' as const, required: false, description: '套餐ID列表（留空查全部）' }
        ]
      },
    ]
  },
  {
    category: '系统管理',
    apis: [
      { 
        name: 'GetSoftSwitch', 
        label: '查询软交换', 
        description: '获取所有软交换信息',
        params: []
      },
      { 
        name: 'GetAlarmCurrent', 
        label: '获取当前告警', 
        description: '获取VOS当前告警列表',
        params: []
      },
    ]
  }
]

export default function VosApiPage() {
  const { currentVOS } = useVOS()
  const [selectedApi, setSelectedApi] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [refresh, setRefresh] = useState(false)
  const [result, setResult] = useState<any>(null)
  const [cacheStats, setCacheStats] = useState<any>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  useEffect(() => {
    if (currentVOS) {
      fetchCacheStats()
    }
  }, [currentVOS])

  const fetchCacheStats = async () => {
    if (!currentVOS) return
    try {
      const res = await api.get(`/vos-api/instances/${currentVOS.id}/cache/stats`)
      setCacheStats(res.data?.stats)
    } catch (e) {
      console.error('获取缓存统计失败:', e)
    }
  }

  const handleApiSelect = (apiConfig: any) => {
    setSelectedApi(apiConfig)
    setResult(null)
    setCurrentPage(1)
  }

  const handleQuery = async (params: any) => {
    if (!currentVOS || !selectedApi) return
    
    setLoading(true)
    setCurrentPage(1)
    try {
      const url = `/vos-api/instances/${currentVOS.id}/${selectedApi.name}${refresh ? '?refresh=true' : ''}`
      const res = await api.post(url, params)
      setResult(res.data)
      
      // 刷新缓存统计
      await fetchCacheStats()
    } catch (e: any) {
      console.error('查询失败:', e)
      setResult({
        success: false,
        error: e.response?.data?.detail || e.message || '查询失败'
      })
    } finally {
      setLoading(false)
    }
  }

  // 获取结果数据数组（用于分页）
  const getResultData = () => {
    if (!result || !result.data) return []
    
    // 查找数据数组
    const data = result.data
    if (Array.isArray(data)) return data
    
    // 尝试常见的数据字段
    for (const key of ['items', 'list', 'records', 'data', 'infos', 'results']) {
      if (data[key] && Array.isArray(data[key])) {
        return data[key]
      }
    }
    
    // 如果找不到数组，返回单个对象作为数组
    return [data]
  }

  const resultData = getResultData()
  const totalPages = Math.ceil(resultData.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedData = resultData.slice(startIndex, endIndex)

  const handleClearCache = async (apiPath?: string) => {
    if (!currentVOS) return
    
    const confirmed = confirm(apiPath ? `确定要清除 ${apiPath} 的缓存吗？` : '确定要清除所有缓存吗？')
    if (!confirmed) return

    try {
      const url = apiPath 
        ? `/vos-api/instances/${currentVOS.id}/cache?api_path=${encodeURIComponent(apiPath)}`
        : `/vos-api/instances/${currentVOS.id}/cache`
      await api.delete(url)
      alert('缓存已清除')
      await fetchCacheStats()
    } catch (e) {
      console.error('清除缓存失败:', e)
      alert('清除缓存失败')
    }
  }

  if (!currentVOS) {
    return (
      <div className='max-w-7xl mx-auto p-6'>
        <div className='bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center'>
          <svg className='mx-auto h-12 w-12 text-yellow-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z' />
          </svg>
          <h3 className='mt-4 text-lg font-medium text-yellow-900'>请先选择 VOS 实例</h3>
          <p className='mt-2 text-sm text-yellow-700'>前往 VOS 节点页面选择一个实例</p>
          <a
            href='/vos'
            className='mt-4 inline-flex items-center px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700'
          >
            前往选择
          </a>
        </div>
      </div>
    )
  }

  return (
    <div className='max-w-7xl mx-auto p-6'>
      {/* 头部 */}
      <div className='mb-6'>
        <div className='flex items-center justify-between mb-2'>
          <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
            VOS API 数据查询
          </h1>
          <div className='flex items-center gap-3'>
            <span className='text-sm text-gray-600'>
              当前实例: <span className='font-semibold text-blue-600'>{currentVOS.name}</span>
            </span>
            <button
              onClick={() => handleClearCache()}
              className='px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition text-sm'
            >
              清除所有缓存
            </button>
          </div>
        </div>
        <p className='text-gray-600'>支持 37 个 VOS 接口的统一查询和缓存管理</p>
      </div>

      {/* 缓存统计 */}
      {cacheStats && (
        <div className='mb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-5 border border-blue-200'>
          <h3 className='text-lg font-semibold mb-3 text-gray-800'>缓存统计</h3>
          <div className='grid grid-cols-2 md:grid-cols-4 gap-4'>
            <div className='bg-white rounded-lg p-3'>
              <p className='text-sm text-gray-600'>总缓存数</p>
              <p className='text-2xl font-bold text-blue-600'>{cacheStats.total}</p>
            </div>
            <div className='bg-white rounded-lg p-3'>
              <p className='text-sm text-gray-600'>有效缓存</p>
              <p className='text-2xl font-bold text-green-600'>{cacheStats.valid}</p>
            </div>
            <div className='bg-white rounded-lg p-3'>
              <p className='text-sm text-gray-600'>已过期</p>
              <p className='text-2xl font-bold text-orange-600'>{cacheStats.expired}</p>
            </div>
            <div className='bg-white rounded-lg p-3'>
              <p className='text-sm text-gray-600'>无效缓存</p>
              <p className='text-2xl font-bold text-red-600'>{cacheStats.invalid}</p>
            </div>
          </div>
        </div>
      )}

      <div className='grid grid-cols-1 lg:grid-cols-3 gap-6'>
        {/* 左侧：API 列表 */}
        <div className='lg:col-span-1'>
          <div className='bg-white rounded-xl shadow-lg p-5 sticky top-6'>
            <h2 className='text-xl font-bold mb-4 text-gray-800'>接口列表</h2>
            <div className='space-y-4 max-h-[calc(100vh-200px)] overflow-y-auto'>
              {VOS_APIS.map((category) => (
                <div key={category.category}>
                  <h3 className='font-semibold text-gray-700 mb-2 text-sm uppercase tracking-wide'>
                    {category.category}
                  </h3>
                  <div className='space-y-1'>
                    {category.apis.map((apiConfig) => (
                      <button
                        key={apiConfig.name}
                        onClick={() => handleApiSelect(apiConfig)}
                        className={`w-full text-left px-3 py-2 rounded-lg transition text-sm ${
                          selectedApi?.name === apiConfig.name
                            ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md'
                            : 'bg-gray-50 hover:bg-gray-100 text-gray-700'
                        }`}
                      >
                        <div className='font-medium'>{apiConfig.label}</div>
                        <div className='text-xs opacity-80 mt-0.5'>{apiConfig.name}</div>
                      </button>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 右侧：查询区域 */}
        <div className='lg:col-span-2 space-y-6'>
          {/* 参数配置 */}
          <div className='bg-white rounded-xl shadow-lg p-6'>
            <h2 className='text-xl font-bold mb-4 text-gray-800'>
              {selectedApi ? selectedApi.label : '请选择接口'}
            </h2>
            
            {selectedApi && (
              <>
                <p className='text-sm text-gray-600 mb-4'>{selectedApi.description}</p>
                
                {/* 强制刷新选项 */}
                <div className='flex items-center gap-4 mb-4 p-3 bg-gray-50 rounded-lg'>
                  <label className='flex items-center gap-2 cursor-pointer'>
                    <input
                      type='checkbox'
                      checked={refresh}
                      onChange={(e) => setRefresh(e.target.checked)}
                      className='w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
                    />
                    <span className='text-sm font-medium text-gray-700'>强制刷新缓存</span>
                  </label>
                  <span className='text-xs text-gray-500'>
                    （勾选后将从 VOS 获取最新数据）
                  </span>
                </div>

                {/* 友好的参数表单 */}
                <VosApiParamForm 
                  apiName={selectedApi.name}
                  paramDefinitions={selectedApi.params}
                  onSubmit={handleQuery}
                  loading={loading}
                />
              </>
            )}
            
            {!selectedApi && (
              <div className='text-center py-12'>
                <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2' />
                </svg>
                <p className='mt-4 text-gray-600'>请从左侧选择一个 API 接口开始查询</p>
              </div>
            )}
          </div>

          {/* 查询结果 */}
          {result && (
            <div className='bg-white rounded-xl shadow-lg p-6'>
              <div className='flex items-center justify-between mb-4'>
                <h2 className='text-xl font-bold text-gray-800'>查询结果</h2>
                <div className='flex items-center gap-2'>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    result.success 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {result.success ? '✓ 成功' : '✗ 失败'}
                  </span>
                  {result.data_source && (
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      result.data_source === 'database' 
                        ? 'bg-blue-100 text-blue-800' 
                        : 'bg-purple-100 text-purple-800'
                    }`}>
                      {result.data_source === 'database' ? '📦 缓存' : '🔄 VOS API'}
                    </span>
                  )}
                </div>
              </div>

              {result.synced_at && (
                <p className='text-sm text-gray-600 mb-3'>
                  同步时间: {new Date(result.synced_at).toLocaleString('zh-CN')}
                </p>
              )}

              {result.error && (
                <div className='mb-4 p-4 bg-red-50 border border-red-200 rounded-lg'>
                  <p className='text-red-800 font-medium'>错误信息</p>
                  <p className='text-red-600 text-sm mt-1'>{result.error}</p>
                </div>
              )}

              {/* 数据统计和分页控制 */}
              {result.success && resultData.length > 0 && (
                <div className='flex items-center justify-between mb-4 p-3 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg'>
                  <div className='flex items-center gap-4'>
                    <p className='text-sm text-gray-700'>
                      共 <span className='font-bold text-blue-600'>{resultData.length}</span> 条记录
                    </p>
                  </div>
                  <select
                    value={pageSize}
                    onChange={(e) => {
                      setPageSize(Number(e.target.value))
                      setCurrentPage(1)
                    }}
                    className='p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white'
                  >
                    <option value={10}>10条/页</option>
                    <option value={20}>20条/页</option>
                    <option value={50}>50条/页</option>
                    <option value={100}>100条/页</option>
                  </select>
                </div>
              )}

              {/* 分页数据展示 */}
              <div className='bg-gray-50 rounded-lg p-4 max-h-[500px] overflow-auto'>
                <pre className='text-xs font-mono text-gray-800'>
                  {resultData.length > 0 
                    ? JSON.stringify(paginatedData, null, 2)
                    : JSON.stringify(result.data || result, null, 2)
                  }
                </pre>
              </div>

              {/* 分页控制 */}
              {resultData.length > pageSize && (
                <div className='mt-4 flex items-center justify-between p-3 bg-gray-50 rounded-lg'>
                  <div className='text-sm text-gray-600'>
                    第 <span className='font-semibold'>{currentPage}</span> / {totalPages} 页
                    （显示 {startIndex + 1} - {Math.min(endIndex, resultData.length)} 条）
                  </div>
                  <div className='flex items-center gap-2'>
                    <button
                      onClick={() => setCurrentPage(1)}
                      disabled={currentPage === 1}
                      className='px-3 py-1 border rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed text-sm'
                    >
                      首页
                    </button>
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className='px-3 py-1 border rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed text-sm'
                    >
                      上一页
                    </button>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className='px-3 py-1 border rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed text-sm'
                    >
                      下一页
                    </button>
                    <button
                      onClick={() => setCurrentPage(totalPages)}
                      disabled={currentPage === totalPages}
                      className='px-3 py-1 border rounded-lg hover:bg-white disabled:opacity-50 disabled:cursor-not-allowed text-sm'
                    >
                      末页
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

