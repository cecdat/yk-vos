'use client'
import React, { useEffect, useState } from 'react'
import api from '../../lib/api'
import { useVOS } from '../../contexts/VOSContext'

interface CDR {
  [key: string]: any
  _instance_name?: string
}

export default function CdrPage() {
  const { currentVOS, allVOS } = useVOS()
  const [cdrs, setCdrs] = useState<CDR[]>([])
  const [loading, setLoading] = useState(false)
  const [instanceResults, setInstanceResults] = useState<any[]>([])
  const [queryMode, setQueryMode] = useState<'current' | 'all'>('current')  // 查询模式：当前VOS 或 所有VOS
  const [forceVOS, setForceVOS] = useState(false)  // 是否强制从VOS查询
  const [dataSource, setDataSource] = useState('')  // 数据来源
  const [queryTime, setQueryTime] = useState(0)  // 查询耗时
  
  // 查询参数
  const [beginTime, setBeginTime] = useState(() => {
    // 默认查询前一天
    const date = new Date()
    date.setDate(date.getDate() - 1)
    return formatDate(date)
  })
  const [endTime, setEndTime] = useState(() => {
    // 默认查询前一天
    const date = new Date()
    date.setDate(date.getDate() - 1)
    return formatDate(date)
  })
  const [accounts, setAccounts] = useState('')
  const [caller, setCaller] = useState('')
  const [callee, setCallee] = useState('')
  const [gateway, setGateway] = useState('')
  
  // 分页
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  // 格式化日期为 yyyyMMdd
  function formatDate(date: Date): string {
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const day = String(date.getDate()).padStart(2, '0')
    return `${year}${month}${day}`
  }

  // 解析日期用于显示
  function parseDate(dateStr: string): string {
    if (!dateStr || dateStr.length !== 8) return dateStr
    return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
  }

  async function handleQuery() {
    setLoading(true)
    try {
      if (queryMode === 'current') {
        // 查询当前 VOS
        if (!currentVOS) {
          alert('请先选择 VOS 节点')
          return
        }

        const payload = {
          begin_time: beginTime,
          end_time: endTime,
          accounts: accounts ? accounts.split(',').map(a => a.trim()) : undefined,
          caller_e164: caller ? caller.trim() : undefined,
          callee_e164: callee ? callee.trim() : undefined,
          callee_gateway: gateway ? gateway.trim() : undefined
        }

        const res = await api.post(
          `/cdr/query-from-vos/${currentVOS.id}?force_vos=${forceVOS}`, 
          payload
        )
        
        if (res.data.success) {
          const cdrsWithInstance = res.data.cdrs.map((cdr: any) => ({
            ...cdr,
            _instance_name: res.data.instance_name
          }))
          setCdrs(cdrsWithInstance || [])
          setDataSource(res.data.data_source)
          setQueryTime(res.data.query_time_ms)
          setInstanceResults([{
            instance_id: currentVOS.id,
            instance_name: currentVOS.name,
            count: res.data.count,
            success: true,
            data_source: res.data.data_source,
            query_time: res.data.query_time_ms
          }])
        } else {
          setCdrs([])
          setInstanceResults([{
            instance_id: currentVOS.id,
            instance_name: currentVOS.name,
            count: 0,
            success: false,
            error: res.data.error
          }])
        }
      } else {
        // 查询所有 VOS
        const params = new URLSearchParams()
        params.append('begin_time', beginTime)
        params.append('end_time', endTime)
        if (accounts) params.append('accounts', accounts)
        if (caller) params.append('caller', caller)
        if (callee) params.append('callee', callee)

        const res = await api.get(`/cdr/query-all-instances?${params.toString()}`)
        setCdrs(res.data.cdrs || [])
        setInstanceResults(res.data.instances || [])
        setDataSource('multiple_vos')
      }
      
      setCurrentPage(1) // 重置到第一页
    } catch (e: any) {
      console.error('查询话单失败:', e)
      alert(e.response?.data?.detail || '查询失败')
    } finally {
      setLoading(false)
    }
  }

  // 分页
  const totalPages = Math.ceil(cdrs.length / pageSize)
  const startIndex = (currentPage - 1) * pageSize
  const endIndex = startIndex + pageSize
  const paginatedCdrs = cdrs.slice(startIndex, endIndex)

  // 格式化时长
  function formatDuration(seconds: number): string {
    if (!seconds) return '0s'
    const h = Math.floor(seconds / 3600)
    const m = Math.floor((seconds % 3600) / 60)
    const s = seconds % 60
    if (h > 0) return `${h}h${m}m${s}s`
    if (m > 0) return `${m}m${s}s`
    return `${s}s`
  }

  // 格式化时间戳为简洁格式（避免换行）
  function formatDateTime(dateTimeStr: string | null | undefined): string {
    if (!dateTimeStr) return '-'
    try {
      // 如果已经是格式化的字符串，直接显示简短格式
      if (dateTimeStr.includes(' ')) {
        // 格式: "2025-10-23 08:30:15" -> "10-23 08:30"
        const parts = dateTimeStr.split(' ')
        const datePart = parts[0].split('-').slice(1).join('-') // 取月-日
        const timePart = parts[1].split(':').slice(0, 2).join(':') // 取时:分
        return `${datePart} ${timePart}`
      }
      return dateTimeStr
    } catch {
      return dateTimeStr || '-'
    }
  }

  // 导出Excel
  async function handleExport() {
    try {
      if (!currentVOS) {
        alert('请先选择 VOS 节点')
        return
      }

      // 使用当前查询条件
      const payload = {
        begin_time: beginTime,
        end_time: endTime,
        accounts: accounts ? accounts.split(',').map(a => a.trim()) : undefined,
        caller_e164: caller ? caller.trim() : undefined,
        callee_e164: callee ? callee.trim() : undefined,
        callee_gateway: gateway ? gateway.trim() : undefined
      }

      const res = await api.post(
        `/cdr/export/${currentVOS.id}`,
        payload,
        { responseType: 'blob' }
      )

      // 创建下载链接
      const url = window.URL.createObjectURL(new Blob([res.data]))
      const link = document.createElement('a')
      link.href = url
      const filename = `话单_${currentVOS.name}_${beginTime}-${endTime}.xlsx`
      link.setAttribute('download', filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)
    } catch (e: any) {
      console.error('导出失败:', e)
      alert(e.response?.data?.detail || '导出失败')
    }
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          历史话单查询
        </h1>
      </div>

      {/* 查询表单 */}
      <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl p-4 shadow-lg border border-white border-opacity-30 mb-4'>
        {/* 当前VOS节点显示 */}
        <div className='mb-3 flex items-center gap-2 text-sm'>
          <span className='text-gray-600'>当前VOS节点:</span>
          <span className='font-semibold text-blue-600'>
            {currentVOS ? currentVOS.name : '未选择'}
          </span>
        </div>

        <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mb-3'>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>开始日期</label>
            <input
              type='date'
              value={beginTime ? parseDate(beginTime) : ''}
              onChange={e => {
                if (e.target.value) {
                  const date = e.target.value.replace(/-/g, '')
                  setBeginTime(date)
                }
              }}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>结束日期</label>
            <input
              type='date'
              value={endTime ? parseDate(endTime) : ''}
              onChange={e => {
                if (e.target.value) {
                  const date = e.target.value.replace(/-/g, '')
                  setEndTime(date)
                }
              }}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>客户账号</label>
            <input
              type='text'
              value={accounts}
              onChange={e => setAccounts(e.target.value)}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='多个账号用逗号分隔'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>主叫号码</label>
            <input
              type='text'
              value={caller}
              onChange={e => setCaller(e.target.value)}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='例如: 86138xxxx'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>被叫号码</label>
            <input
              type='text'
              value={callee}
              onChange={e => setCallee(e.target.value)}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='例如: 86139xxxx'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-xs font-medium mb-1 text-gray-700'>网关</label>
            <input
              type='text'
              value={gateway}
              onChange={e => setGateway(e.target.value)}
              className='w-full p-2 text-sm border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='网关名称'
              disabled={loading}
            />
          </div>
          <div className='flex items-end'>
            <button
              onClick={handleQuery}
              disabled={loading}
              className='w-full py-2 text-sm bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 transition disabled:opacity-50 flex items-center justify-center gap-2'
            >
              {loading && (
                <svg className='animate-spin h-4 w-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                  <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                </svg>
              )}
              {loading ? '查询中...' : '查询'}
            </button>
          </div>
        </div>

        {/* 导出按钮 */}
        {cdrs.length > 0 && (
          <div className='mt-3 flex items-center gap-2'>
            <button
              onClick={handleExport}
              disabled={loading}
              className='px-4 py-2 text-sm bg-gradient-to-r from-green-600 to-teal-600 text-white rounded-lg font-medium hover:from-green-700 hover:to-teal-700 transition disabled:opacity-50 flex items-center gap-2'
            >
              <svg className='w-4 h-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
              </svg>
              导出Excel ({cdrs.length}条)
            </button>
            <span className='text-xs text-gray-500'>当前查询结果</span>
          </div>
        )}
      </div>

      {/* 话单列表 */}
      {loading ? (
        <div className='text-center py-16 bg-white rounded-xl'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>查询中，请稍候...</p>
        </div>
      ) : cdrs.length === 0 ? (
        <div className='text-center py-16 bg-white rounded-xl shadow-sm'>
          <svg className='mx-auto h-12 w-12 text-gray-400' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
          </svg>
          <h3 className='mt-2 text-lg font-medium text-gray-900'>暂无话单数据</h3>
          <p className='mt-1 text-sm text-gray-500'>请选择查询条件并点击"查询"按钮</p>
        </div>
      ) : (
        <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl shadow-lg border border-white border-opacity-30 overflow-hidden'>
          {/* 顶部信息栏 */}
          <div className='px-6 py-4 bg-gradient-to-r from-blue-50 to-purple-50 border-b flex items-center justify-between'>
            <div className='flex items-center gap-4'>
              <p className='text-sm text-gray-700'>
                共查询到 <span className='font-bold text-blue-600'>{cdrs.length}</span> 条话单记录
              </p>
              {dataSource && queryMode === 'current' && (
                <div className='flex items-center gap-2 text-xs'>
                  <span className={`px-2 py-1 rounded-full font-medium ${
                    dataSource === 'local_database' 
                      ? 'bg-green-100 text-green-700'
                      : 'bg-orange-100 text-orange-700'
                  }`}>
                    {dataSource === 'local_database' ? '📦 本地数据库' : '🌐 VOS API'}
                  </span>
                  <span className='text-gray-600'>⚡ {queryTime}ms</span>
                  {dataSource === 'local_database' && (
                    <span className='text-green-600 font-medium'>✓ 极速查询</span>
                  )}
                </div>
              )}
            </div>
            <select
              value={pageSize}
              onChange={e => {
                setPageSize(Number(e.target.value))
                setCurrentPage(1)
              }}
              className='p-2 border rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none bg-white'
            >
              <option value={20}>20条/页</option>
              <option value={50}>50条/页</option>
              <option value={100}>100条/页</option>
            </select>
          </div>

          {/* 表格 */}
          <div className='overflow-x-auto'>
            <table className='min-w-full divide-y divide-gray-200'>
              <thead className='bg-gray-50'>
                <tr>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>话单ID</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>VOS节点</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>账户</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>主叫号码</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>被叫号码</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>网关</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>开始时间</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>结束时间</th>
                  <th className='px-2 py-2 text-right text-xs font-semibold text-gray-700'>通话时长</th>
                  <th className='px-2 py-2 text-right text-xs font-semibold text-gray-700'>计费时长</th>
                  <th className='px-2 py-2 text-right text-xs font-semibold text-gray-700'>费用</th>
                  <th className='px-2 py-2 text-center text-xs font-semibold text-gray-700'>挂断方</th>
                  <th className='px-2 py-2 text-left text-xs font-semibold text-gray-700'>终止原因</th>
                </tr>
              </thead>
              <tbody className='divide-y divide-gray-200'>
                {paginatedCdrs.map((cdr, index) => (
                  <tr key={index} className='hover:bg-gray-50 transition'>
                    <td className='px-2 py-2 text-xs'>
                      <span className='px-1.5 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-mono'>
                        {cdr.flowNo || '-'}
                      </span>
                    </td>
                    <td className='px-2 py-2 text-xs'>
                      <span className='px-1.5 py-0.5 bg-blue-100 text-blue-800 rounded text-xs font-medium'>
                        {cdr._instance_name || '-'}
                      </span>
                    </td>
                    <td className='px-2 py-2 text-xs'>
                      <div>
                        <div className='font-medium text-gray-900'>{cdr.accountName || '-'}</div>
                        <div className='text-xs text-gray-500'>{cdr.account || '-'}</div>
                      </div>
                    </td>
                    <td className='px-2 py-2 text-xs text-gray-600 font-mono'>{cdr.callerE164 || '-'}</td>
                    <td className='px-2 py-2 text-xs text-gray-600 font-mono'>{cdr.calleeAccessE164 || '-'}</td>
                    <td className='px-2 py-2 text-xs text-gray-600 truncate max-w-xs' title={cdr.calleeGateway}>
                      {cdr.calleeGateway || '-'}
                    </td>
                    <td className='px-2 py-2 text-xs text-gray-600 whitespace-nowrap'>{formatDateTime(cdr.start)}</td>
                    <td className='px-2 py-2 text-xs text-gray-600 whitespace-nowrap'>{formatDateTime(cdr.stop)}</td>
                    <td className='px-2 py-2 text-xs text-right text-gray-900'>
                      {formatDuration(cdr.holdTime || 0)}
                    </td>
                    <td className='px-2 py-2 text-xs text-right text-gray-600'>
                      {formatDuration(cdr.feeTime || 0)}
                    </td>
                    <td className='px-2 py-2 text-xs text-right font-semibold text-green-600'>
                      {cdr.fee ? `¥${Number(cdr.fee).toFixed(4)}` : '-'}
                    </td>
                    <td className='px-2 py-2 text-center'>
                      <span className={`px-1.5 py-0.5 rounded-full text-xs font-medium ${
                        cdr.endDirection === 0 ? 'bg-blue-100 text-blue-700' :
                        cdr.endDirection === 1 ? 'bg-purple-100 text-purple-700' :
                        cdr.endDirection === 2 ? 'bg-gray-100 text-gray-700' :
                        'bg-gray-50 text-gray-500'
                      }`}>
                        {cdr.endDirection === 0 ? '主叫' :
                         cdr.endDirection === 1 ? '被叫' :
                         cdr.endDirection === 2 ? '服务器' : '-'}
                      </span>
                    </td>
                    <td className='px-2 py-2 text-xs text-gray-600'>
                      <span className={`px-1.5 py-0.5 rounded text-xs ${
                        cdr.endReason === '200' || cdr.endReason === '0' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {cdr.endReason || '-'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 分页控制 */}
          <div className='px-6 py-4 bg-gray-50 border-t flex items-center justify-between'>
            <div className='flex items-center gap-2 text-sm text-gray-600'>
              <p>第 <span className='font-semibold text-gray-900'>{currentPage}</span> / {totalPages} 页</p>
              <span className='text-gray-400'>|</span>
              <p>显示 {startIndex + 1} - {Math.min(endIndex, cdrs.length)} 条</p>
            </div>

            <div className='flex items-center gap-2'>
              <button
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm'
              >
                首页
              </button>
              <button
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm'
              >
                上一页
              </button>

              {/* 页码 */}
              <div className='flex items-center gap-1'>
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  let pageNum
                  if (totalPages <= 5) {
                    pageNum = i + 1
                  } else if (currentPage <= 3) {
                    pageNum = i + 1
                  } else if (currentPage >= totalPages - 2) {
                    pageNum = totalPages - 4 + i
                  } else {
                    pageNum = currentPage - 2 + i
                  }

                  return (
                    <button
                      key={pageNum}
                      onClick={() => setCurrentPage(pageNum)}
                      className={`px-3 py-2 rounded-lg transition text-sm ${
                        currentPage === pageNum
                          ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white font-semibold'
                          : 'border hover:bg-gray-100'
                      }`}
                    >
                      {pageNum}
                    </button>
                  )
                })}
              </div>

              <button
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm'
              >
                下一页
              </button>
              <button
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
                className='px-3 py-2 border rounded-lg hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed transition text-sm'
              >
                末页
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

