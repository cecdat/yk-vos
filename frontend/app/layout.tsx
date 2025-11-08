'use client'
import './globals.css'
import { usePathname } from 'next/navigation'
import AuthGuard from '../components/AuthGuard'
import Navbar from '../components/ui/Navbar'
import { VOSProvider } from '../contexts/VOSContext'

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const isLoginPage = pathname === '/login'

  return (
    <html lang='zh-CN'>
      <head>
        <title>云客信息-VOS管理平台</title>
        <meta name="description" content="云客信息VOS3000管理平台" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </head>
      <body>
        <VOSProvider>
          <AuthGuard>
          {isLoginPage ? (
            // 登录页面：透明背景，显示渐变
            <div className='login-page'>
              {children}
            </div>
          ) : (
            // 其他页面：显示完整布局
            <div className='flex min-h-screen'>
              <aside className='w-64 p-6 bg-white bg-opacity-95 backdrop-filter backdrop-blur-lg border-r border-white border-opacity-30 shadow-lg hidden md:block fixed left-0 top-0 bottom-0 overflow-y-auto'>
                <div className='flex items-center gap-2 mb-8'>
                  <div className='w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center flex-shrink-0'>
                    <svg className='w-6 h-6 text-white' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
                    </svg>
                  </div>
                  <h2 className='text-base font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent whitespace-nowrap leading-tight'>云客信息-VOS管理平台</h2>
                </div>
                <nav className='space-y-1'>
                  <a href='/' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                    <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' />
                    </svg>
                    <span className='font-medium'>仪表盘</span>
                  </a>
                  <a href='/customers' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                    <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z' />
                    </svg>
                    <span className='font-medium'>客户管理</span>
                  </a>
                  <a href='/gateway' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                    <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z' />
                    </svg>
                    <span className='font-medium'>网关管理</span>
                  </a>
                  <a href='/cdr' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                    <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                      <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
                    </svg>
                    <span className='font-medium'>话单历史</span>
                  </a>
                  <div className='pt-4 mt-4 border-t border-gray-200'>
                    <p className='px-3 text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2'>数据管理</p>
                    <a href='/statistics' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z' />
                      </svg>
                      <span className='font-medium'>数据统计</span>
                    </a>
                    <a href='/account-detail-reports' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z' />
                      </svg>
                      <span className='font-medium'>账户明细报表</span>
                    </a>
                    <a href='/sync-management' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
                      </svg>
                      <span className='font-medium'>同步管理</span>
                    </a>
                    <a href='/vos-api' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z' />
                      </svg>
                      <span className='font-medium'>VOS API</span>
                    </a>
                    <a href='/cache' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4' />
                      </svg>
                      <span className='font-medium'>缓存管理</span>
                    </a>
                  </div>
                  <div className='pt-4 mt-4 border-t border-gray-200'>
                    <a href='/settings' className='flex items-center gap-3 text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-purple-50 p-3 rounded-lg transition group'>
                      <svg className='w-5 h-5 text-gray-500 group-hover:text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z' />
                        <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M15 12a3 3 0 11-6 0 3 3 0 016 0z' />
                      </svg>
                      <span className='font-medium'>系统设置</span>
                    </a>
                  </div>
            </nav>
          </aside>
              <div className='flex-1 p-6 main-content ml-64'>
            <Navbar />
            {children}
          </div>
        </div>
          )}
          </AuthGuard>
        </VOSProvider>
      </body>
    </html>
  )
}
