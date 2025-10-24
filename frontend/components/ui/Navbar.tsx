'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useVOS } from '../../contexts/VOSContext'

export default function Navbar(){
  const router = useRouter()
  const [username, setUsername] = useState('')
  const { currentVOS, allVOS, setCurrentVOS, loading } = useVOS()

  useEffect(() => {
    // 这里可以调用 API 获取用户信息，暂时显示默认值
    setUsername('admin')
  }, [])

  const handleLogout = () => {
    if (confirm('确定要退出登录吗？')) {
      localStorage.removeItem('token')
      router.push('/login')
    }
  }

  const handleVOSChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const vosId = parseInt(e.target.value)
    const selectedVOS = allVOS.find(v => v.id === vosId)
    if (selectedVOS) {
      setCurrentVOS(selectedVOS)
    }
  }

  return (
    <div className='flex items-center justify-between mb-6 bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg p-4 rounded-xl shadow-lg border border-white border-opacity-30'>
      <div className='text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>VOS 控制台</div>
      <div className='flex items-center gap-4'>
        {/* VOS 切换选择器 - 美化版 */}
        {allVOS.length > 0 && (
          <div className='relative group'>
            <div className='flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-md hover:shadow-lg transition-all cursor-pointer'>
              <div className='flex items-center gap-2 flex-1'>
                <div className='w-8 h-8 bg-white bg-opacity-20 rounded-md flex items-center justify-center'>
                  <svg className='w-5 h-5 text-white' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                    <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
                  </svg>
                </div>
                <div className='flex flex-col'>
                  <span className='text-xs text-white text-opacity-75'>当前节点</span>
                  <select
                    value={currentVOS?.id || ''}
                    onChange={handleVOSChange}
                    disabled={loading}
                    className='bg-transparent text-sm font-semibold text-white outline-none cursor-pointer disabled:cursor-not-allowed appearance-none pr-6'
                    style={{
                      background: 'transparent',
                      WebkitAppearance: 'none',
                      MozAppearance: 'none'
                    }}
                  >
                    {allVOS.length === 0 && (
                      <option value=''>暂无 VOS 节点</option>
                    )}
                    {allVOS.map(vos => (
                      <option key={vos.id} value={vos.id} className='text-gray-900 bg-white'>
                        {vos.name}
                        {!vos.enabled && ' (禁用)'}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <svg className='w-4 h-4 text-white text-opacity-75' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
            {currentVOS?.enabled === false && (
              <div className='absolute -bottom-1 -right-1 px-2 py-0.5 bg-orange-500 text-white text-xs rounded-full shadow-md'>
                已禁用
              </div>
            )}
          </div>
        )}
        
        {/* 用户信息 */}
        <div className='flex items-center gap-2 px-3 py-2 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg'>
          <svg className='w-5 h-5 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' />
          </svg>
          <span className='text-sm text-gray-700'>
            <span className='font-medium'>{username}</span>
          </span>
        </div>
        <button 
          onClick={handleLogout}
          className='flex items-center gap-2 text-sm px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition border border-red-200 hover:border-red-300'
        >
          <svg className='w-4 h-4' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1' />
          </svg>
          退出登录
        </button>
      </div>
    </div>
  )
}
