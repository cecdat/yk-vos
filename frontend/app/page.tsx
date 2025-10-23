'use client'
import React, {useEffect, useState} from 'react'
import api from '../lib/api'
import StatCard from '../components/ui/StatCard'
import Card from '../components/ui/Card'
import { useVOS } from '../contexts/VOSContext'

interface CustomerSummary {
  total_customers: number
  instances: Array<{
    instance_id: number
    instance_name: string
    customer_count: number
    error?: string
  }>
  instance_count: number
}

interface TaskStatus {
  workers: {
    count: number
    status: string
  }
  tasks: {
    active: number
    scheduled: number
    reserved: number
    active_list: Array<{
      name: string
      worker: string
      id: string
    }>
  }
  sync_tasks: {
    registered_count: number
    task_types: string[]
  }
  status: string
}

export default function Page(){
  const { currentVOS } = useVOS()
  const [instances, setInstances] = useState<any[]>([])
  const [onlineCount, setOnlineCount] = useState(0)
  const [cdrCount, setCdrCount] = useState(0)
  const [customerSummary, setCustomerSummary] = useState<CustomerSummary | null>(null)
  const [taskStatus, setTaskStatus] = useState<TaskStatus | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  async function fetchData() {
    setLoading(true)
    await Promise.all([
      fetchInstances(),
      fetchCdrCount(),
      fetchCustomerSummary(),
      fetchTaskStatus()
    ])
    setLoading(false)
  }

  async function fetchInstances() {
    try {
      const res = await api.get('/vos/instances')
      setInstances(res.data || [])
    } catch (e) {
      console.error('获取实例失败:', e)
    }
  }

  async function fetchCdrCount() {
    try {
      const res = await api.get('/cdr/history?limit=1')
      setCdrCount(res.data ? res.data.length : 0)
    } catch (e) {
      console.error('获取话单数失败:', e)
    }
  }

  async function fetchCustomerSummary() {
    try {
      const res = await api.get('/vos/customers/summary')
      setCustomerSummary(res.data)
    } catch (e) {
      console.error('获取客户统计失败:', e)
      setCustomerSummary({ total_customers: 0, instances: [], instance_count: 0 })
    }
  }

  async function fetchTaskStatus() {
    try {
      const res = await api.get('/tasks/status')
      setTaskStatus(res.data)
    } catch (e) {
      console.error('获取任务状态失败:', e)
      setTaskStatus({
        workers: { count: 0, status: 'unknown' },
        tasks: { active: 0, scheduled: 0, reserved: 0, active_list: [] },
        sync_tasks: { registered_count: 0, task_types: [] },
        status: 'error'
      })
    }
  }

  return (
    <div className='max-w-7xl'>
      <div className='flex items-center justify-between mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>
          系统概览
        </h1>
        <button
          onClick={fetchData}
          disabled={loading}
          className='px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition flex items-center gap-2 disabled:opacity-50'
        >
          <svg className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
          </svg>
          刷新数据
        </button>
      </div>

      {/* 统计卡片 */}
      <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8'>
        <div className='bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-blue-100 text-sm mb-1'>VOS 实例</p>
              <p className='text-3xl font-bold'>{instances.length}</p>
            </div>
            <div className='w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-6 h-6' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-green-500 to-green-600 rounded-xl p-6 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-green-100 text-sm mb-1'>客户总数</p>
              <p className='text-3xl font-bold'>{customerSummary?.total_customers || 0}</p>
            </div>
            <div className='w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-6 h-6' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-purple-100 text-sm mb-1'>在线话机</p>
              <p className='text-3xl font-bold'>{onlineCount}</p>
            </div>
            <div className='w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-6 h-6' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z' />
              </svg>
            </div>
          </div>
        </div>

        <div className='bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white shadow-lg'>
          <div className='flex items-center justify-between'>
            <div>
              <p className='text-orange-100 text-sm mb-1'>话单记录</p>
              <p className='text-3xl font-bold'>{cdrCount}</p>
            </div>
            <div className='w-12 h-12 bg-white bg-opacity-20 rounded-lg flex items-center justify-center'>
              <svg className='w-6 h-6' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
              </svg>
            </div>
          </div>
        </div>
      </div>

      {/* 任务同步状态卡片 */}
      {taskStatus && (
        <div className='mb-8'>
          <h2 className='text-xl font-bold mb-4 text-gray-800 flex items-center gap-2'>
            <svg className='w-6 h-6 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01' />
            </svg>
            任务同步状态
            <span className={`px-3 py-1 rounded-full text-sm ${
              taskStatus.status === 'healthy' ? 'bg-green-100 text-green-700' :
              taskStatus.status === 'warning' ? 'bg-yellow-100 text-yellow-700' :
              'bg-red-100 text-red-700'
            }`}>
              {taskStatus.status === 'healthy' ? '✓ 正常' :
               taskStatus.status === 'warning' ? '⚠ 警告' :
               '✗ 异常'}
            </span>
          </h2>
          
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4'>
            {/* Worker状态 */}
            <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl p-5 shadow-lg border border-white border-opacity-30'>
              <div className='flex items-center gap-3 mb-3'>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  taskStatus.workers.status === 'running' ? 'bg-green-100' :
                  taskStatus.workers.status === 'stopped' ? 'bg-red-100' : 'bg-gray-100'
                }`}>
                  <svg className={`w-5 h-5 ${
                    taskStatus.workers.status === 'running' ? 'text-green-600' :
                    taskStatus.workers.status === 'stopped' ? 'text-red-600' : 'text-gray-600'
                  }`} fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z' />
                  </svg>
                </div>
                <div>
                  <p className='text-sm text-gray-600'>Worker数量</p>
                  <p className='text-2xl font-bold text-gray-900'>{taskStatus.workers.count}</p>
                </div>
              </div>
              <div className='text-xs text-gray-500'>
                状态: <span className={`font-semibold ${
                  taskStatus.workers.status === 'running' ? 'text-green-600' :
                  taskStatus.workers.status === 'stopped' ? 'text-red-600' : 'text-gray-600'
                }`}>{taskStatus.workers.status}</span>
              </div>
            </div>

            {/* 活跃任务 */}
            <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl p-5 shadow-lg border border-white border-opacity-30'>
              <div className='flex items-center gap-3 mb-3'>
                <div className='w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center'>
                  <svg className='w-5 h-5 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 10V3L4 14h7v7l9-11h-7z' />
                  </svg>
                </div>
                <div>
                  <p className='text-sm text-gray-600'>活跃任务</p>
                  <p className='text-2xl font-bold text-gray-900'>{taskStatus.tasks.active}</p>
                </div>
              </div>
              {taskStatus.tasks.active_list && taskStatus.tasks.active_list.length > 0 && (
                <div className='text-xs text-gray-500 mt-2'>
                  <p className='font-semibold mb-1'>当前执行:</p>
                  {taskStatus.tasks.active_list.slice(0, 2).map((task, idx) => (
                    <p key={idx} className='truncate'>• {task.name}</p>
                  ))}
                </div>
              )}
            </div>

            {/* 计划任务 */}
            <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl p-5 shadow-lg border border-white border-opacity-30'>
              <div className='flex items-center gap-3 mb-3'>
                <div className='w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center'>
                  <svg className='w-5 h-5 text-purple-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' />
                  </svg>
                </div>
                <div>
                  <p className='text-sm text-gray-600'>计划任务</p>
                  <p className='text-2xl font-bold text-gray-900'>{taskStatus.tasks.scheduled}</p>
                </div>
              </div>
              <div className='text-xs text-gray-500'>
                队列中: {taskStatus.tasks.reserved} 个
              </div>
            </div>

            {/* 注册的同步任务类型 */}
            <div className='bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg rounded-xl p-5 shadow-lg border border-white border-opacity-30'>
              <div className='flex items-center gap-3 mb-3'>
                <div className='w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center'>
                  <svg className='w-5 h-5 text-orange-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                  </svg>
                </div>
                <div>
                  <p className='text-sm text-gray-600'>同步任务</p>
                  <p className='text-2xl font-bold text-gray-900'>{taskStatus.sync_tasks.registered_count}</p>
                </div>
              </div>
              {taskStatus.sync_tasks.task_types && taskStatus.sync_tasks.task_types.length > 0 && (
                <div className='text-xs text-gray-500 mt-2'>
                  <p className='font-semibold mb-1'>任务类型:</p>
                  {taskStatus.sync_tasks.task_types.slice(0, 2).map((type, idx) => (
                    <p key={idx} className='truncate'>• {type}</p>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* 各实例客户分布 */}
      {customerSummary && customerSummary.instances.length > 0 && (
        <section className='mb-8'>
          <h2 className='text-xl font-bold mb-4 text-gray-800 flex items-center gap-2'>
            各实例客户分布
            <span className='text-sm font-normal text-gray-500'>(当前选中的实例会高亮显示)</span>
          </h2>
          <div className='grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'>
            {customerSummary.instances.map((inst) => {
              const isCurrentVOS = currentVOS?.id === inst.instance_id
              return (
                <div 
                  key={inst.instance_id} 
                  className={`p-5 rounded-xl shadow-lg border transition-all ${
                    isCurrentVOS 
                      ? 'bg-gradient-to-br from-blue-50 to-purple-50 border-blue-300 border-2 ring-2 ring-blue-300' 
                      : 'bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg border-white border-opacity-30'
                  }`}
                >
                  <div className='flex items-center justify-between mb-3'>
                    <div className='flex items-center gap-2'>
                      <h3 className='font-semibold text-gray-800'>{inst.instance_name}</h3>
                      {isCurrentVOS && (
                        <span className='px-2 py-0.5 bg-blue-500 text-white text-xs rounded-full'>
                          当前
                        </span>
                      )}
                    </div>
                    <span className='px-3 py-1 bg-gradient-to-r from-green-100 to-green-200 text-green-800 rounded-full text-sm font-medium'>
                      {inst.customer_count} 户
                    </span>
                  </div>
                  {inst.error && (
                    <p className='text-xs text-red-600 mt-2'>⚠️ {inst.error}</p>
                  )}
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* 已注册实例 */}
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
                  {inst.description && (
                    <p className='text-sm text-gray-500 mt-2'>{inst.description}</p>
                  )}
                  <div className='mt-3 pt-3 border-t flex items-center justify-between'>
                    <span className={`text-xs px-2 py-1 rounded-full ${inst.enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'}`}>
                      {inst.enabled ? '✓ 启用中' : '○ 已禁用'}
                    </span>
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
