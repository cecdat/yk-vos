'use client'
import React from 'react'
import { useVOS } from '../../contexts/VOSContext'
import CacheManagement from '../../components/CacheManagement'

export default function CachePage() {
  const { currentVOS } = useVOS()

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
      <div className='mb-6'>
        <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-2'>
          缓存管理
        </h1>
        <p className='text-gray-600'>
          查看和管理 VOS API 数据缓存，优化系统性能
        </p>
      </div>

      <CacheManagement 
        instanceId={currentVOS.id} 
        instanceName={currentVOS.name} 
      />

      {/* 使用说明 */}
      <div className='mt-6 bg-blue-50 border border-blue-200 rounded-xl p-6'>
        <h3 className='text-lg font-semibold text-blue-900 mb-3'>💡 缓存说明</h3>
        <div className='space-y-2 text-sm text-blue-800'>
          <p>• <strong>缓存机制</strong>: 系统会自动缓存 VOS API 的响应数据到数据库中</p>
          <p>• <strong>缓存时间</strong>: 不同类型的数据有不同的缓存时间（30秒到24小时）</p>
          <p>• <strong>自动同步</strong>: 后台任务会定期检查并更新过期的缓存</p>
          <p>• <strong>手动清除</strong>: 可以手动清除特定API或所有缓存</p>
          <p>• <strong>性能提升</strong>: 缓存可以减少90%以上的VOS API调用，大幅提升响应速度</p>
        </div>
      </div>

      {/* 缓存策略 */}
      <div className='mt-6 bg-white rounded-xl shadow-lg p-6'>
        <h3 className='text-lg font-semibold text-gray-800 mb-4'>缓存策略</h3>
        <div className='grid grid-cols-1 md:grid-cols-2 gap-4'>
          <div className='border border-gray-200 rounded-lg p-4'>
            <div className='flex items-center gap-2 mb-2'>
              <span className='w-3 h-3 bg-red-500 rounded-full'></span>
              <h4 className='font-semibold text-gray-800'>实时数据 (30秒)</h4>
            </div>
            <p className='text-sm text-gray-600 mb-2'>适合频繁变化的数据</p>
            <ul className='text-xs text-gray-500 space-y-1'>
              <li>• 在线话机状态</li>
              <li>• 当前通话</li>
              <li>• 系统性能指标</li>
              <li>• 网关在线状态</li>
            </ul>
          </div>

          <div className='border border-gray-200 rounded-lg p-4'>
            <div className='flex items-center gap-2 mb-2'>
              <span className='w-3 h-3 bg-orange-500 rounded-full'></span>
              <h4 className='font-semibold text-gray-800'>准实时数据 (5分钟)</h4>
            </div>
            <p className='text-sm text-gray-600 mb-2'>平衡实时性和性能</p>
            <ul className='text-xs text-gray-500 space-y-1'>
              <li>• 客户列表</li>
              <li>• 话机信息</li>
              <li>• 账户信息</li>
            </ul>
          </div>

          <div className='border border-gray-200 rounded-lg p-4'>
            <div className='flex items-center gap-2 mb-2'>
              <span className='w-3 h-3 bg-blue-500 rounded-full'></span>
              <h4 className='font-semibold text-gray-800'>历史数据 (1小时)</h4>
            </div>
            <p className='text-sm text-gray-600 mb-2'>减少VOS API压力</p>
            <ul className='text-xs text-gray-500 space-y-1'>
              <li>• 话单记录(CDR)</li>
              <li>• 缴费历史</li>
              <li>• 消费记录</li>
            </ul>
          </div>

          <div className='border border-gray-200 rounded-lg p-4'>
            <div className='flex items-center gap-2 mb-2'>
              <span className='w-3 h-3 bg-green-500 rounded-full'></span>
              <h4 className='font-semibold text-gray-800'>配置数据 (24小时)</h4>
            </div>
            <p className='text-sm text-gray-600 mb-2'>几乎不变的配置</p>
            <ul className='text-xs text-gray-500 space-y-1'>
              <li>• 费率组配置</li>
              <li>• 网关配置</li>
              <li>• 套餐信息</li>
              <li>• 软交换信息</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

