'use client'
import React, { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useVOS } from '../../contexts/VOSContext'

export default function Navbar(){
  const router = useRouter()
  const [username, setUsername] = useState('')
  const { currentVOS, allVOS, setCurrentVOS, loading } = useVOS()
  const [showVOSDropdown, setShowVOSDropdown] = useState(false)

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

  const handleVOSSelect = (vos: any) => {
    setCurrentVOS(vos)
    setShowVOSDropdown(false)
  }

  return (
    <div className='flex items-center justify-between mb-6 bg-white bg-opacity-90 backdrop-filter backdrop-blur-lg px-6 py-3 rounded-xl shadow-lg border border-white border-opacity-30'>
      <div className='text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>VOS 控制台</div>
      <div className='flex items-center gap-4'>
        {/* VOS 切换选择器 - 自定义下拉菜单 */}
        {allVOS.length > 0 && (
          <div className='relative'>
            <div 
              onClick={() => !loading && setShowVOSDropdown(!showVOSDropdown)}
              className={`flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-md hover:shadow-lg transition-all ${loading ? 'cursor-not-allowed opacity-75' : 'cursor-pointer'}`}
            >
              <div className='flex items-center gap-2 flex-1'>
                <div className='w-8 h-8 bg-white bg-opacity-20 rounded-md flex items-center justify-center'>
                  <svg className='w-5 h-5 text-white' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
            </svg>
                </div>
                <div className='flex flex-col min-w-[120px]'>
                  <span className='text-xs text-white text-opacity-75'>当前节点</span>
                  <span className='text-sm font-semibold text-white truncate'>
                    {currentVOS?.name || '请选择节点'}
                  </span>
                </div>
              </div>
              <svg 
                className={`w-4 h-4 text-white text-opacity-75 transition-transform ${showVOSDropdown ? 'rotate-180' : ''}`} 
                fill='none' 
                viewBox='0 0 24 24' 
                stroke='currentColor'
              >
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M19 9l-7 7-7-7' />
              </svg>
            </div>
            
            {/* 自定义下拉菜单 */}
            {showVOSDropdown && (
              <>
                {/* 背景遮罩 */}
                <div 
                  className='fixed inset-0 z-10' 
                  onClick={() => setShowVOSDropdown(false)}
                />
                {/* 下拉列表 */}
                <div className='absolute top-full mt-2 right-0 w-64 bg-white rounded-lg shadow-xl border border-gray-200 py-2 z-20 max-h-80 overflow-y-auto'>
                  {allVOS.map(vos => (
                    <div
                      key={vos.id}
                      onClick={() => handleVOSSelect(vos)}
                      className={`px-4 py-2.5 cursor-pointer transition-colors ${
                        currentVOS?.id === vos.id 
                          ? 'bg-gradient-to-r from-blue-50 to-purple-50 border-l-4 border-blue-500' 
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className='flex items-center justify-between'>
                        <div className='flex items-center gap-3'>
                          <div className={`w-2 h-2 rounded-full ${vos.enabled ? 'bg-green-500' : 'bg-gray-400'}`} />
                          <div>
                            <div className='text-sm font-medium text-gray-900'>{vos.name}</div>
                            {!vos.enabled && (
                              <div className='text-xs text-orange-600'>已禁用</div>
                            )}
                          </div>
                        </div>
                        {currentVOS?.id === vos.id && (
                          <svg className='w-5 h-5 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                            <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 13l4 4L19 7' />
                          </svg>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
            
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
