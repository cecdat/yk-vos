'use client'
import { useEffect, useState } from 'react'
import { usePathname, useRouter } from 'next/navigation'

export default function AuthGuard({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // 登录页面不需要验证
    if (pathname === '/login') {
      setIsAuthenticated(true)
      setIsLoading(false)
      return
    }

    // 检查是否有 token
    const token = localStorage.getItem('token')
    
    if (!token) {
      // 没有 token，跳转到登录页
      router.push('/login')
      setIsLoading(false)
      return
    }

    // 有 token，验证通过
    setIsAuthenticated(true)
    setIsLoading(false)
  }, [pathname, router])

  // 加载中显示加载状态
  if (isLoading) {
    return (
      <div className='min-h-screen flex items-center justify-center'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4'></div>
          <p className='text-gray-600'>加载中...</p>
        </div>
      </div>
    )
  }

  // 未认证且不在登录页，不显示内容（会跳转）
  if (!isAuthenticated && pathname !== '/login') {
    return null
  }

  return <>{children}</>
}

