'use client'
import React, {useState, useEffect} from 'react'
import api from '../../lib/api'
export default function Login(){
  const [u,setU]=useState('admin')
  const [p,setP]=useState('admin123')
  const [msg,setMsg]=useState('')
  const [loading,setLoading]=useState(false)
  
  // 检查是否是会话超时跳转
  useEffect(() => {
    const params = new URLSearchParams(window.location.search)
    if (params.get('timeout') === '1') {
      setMsg('会话已超时，请重新登录')
    }
  }, [])
  
  async function doLogin(){
    if(loading) return
    setLoading(true)
    setMsg('')
    try{
      const res=await api.post('/auth/login',{username:u,password:p})
      localStorage.setItem('token',res.data.access_token)
      setMsg('登录成功，正在跳转...')
      setTimeout(()=>window.location.href='/',500)
    }catch(e:any){
      console.error('Login error:', e)
      setMsg(e.response?.data?.detail || '登录失败，请检查用户名和密码')
    }finally{
      setLoading(false)
    }
  }
  
  return (
    <div className='min-h-screen flex items-center justify-center'>
      <div className='max-w-md w-full bg-white bg-opacity-95 backdrop-filter backdrop-blur-lg p-8 rounded-2xl shadow-2xl'>
        <div className='text-center mb-8'>
          <div className='w-16 h-16 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-4'>
            <svg className='w-10 h-10 text-white' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01' />
            </svg>
          </div>
          <h1 className='text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent'>云客信息-VOS管理平台</h1>
          <p className='text-gray-500 mt-2'>欢迎回来，请登录您的账户</p>
        </div>
        <div className='space-y-4'>
          <div>
            <label className='block text-sm font-medium mb-1'>用户名</label>
            <input 
              value={u} 
              onChange={e=>setU(e.target.value)} 
              className='w-full p-3 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='请输入用户名'
              disabled={loading}
            />
          </div>
          <div>
            <label className='block text-sm font-medium mb-1'>密码</label>
            <input 
              type='password'
              value={p} 
              onChange={e=>setP(e.target.value)} 
              className='w-full p-3 border rounded focus:ring-2 focus:ring-blue-500 outline-none'
              placeholder='请输入密码'
              disabled={loading}
              onKeyPress={e=>e.key==='Enter'&&doLogin()}
            />
          </div>
          <button 
            onClick={doLogin} 
            disabled={loading}
            className='w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg font-medium hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 transition-all shadow-lg hover:shadow-xl'
          >
            {loading ? '登录中...' : '登录'}
          </button>
          {msg && (
            <div className={`mt-3 p-3 rounded text-sm ${
              msg.includes('成功') ? 'bg-green-50 text-green-800' : 
              msg.includes('超时') ? 'bg-yellow-50 text-yellow-800' : 
              'bg-red-50 text-red-800'
            }`}>
              {msg}
            </div>
          )}
          <div className='mt-4 p-4 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg text-sm border border-blue-200'>
            <p className='font-semibold text-gray-700 mb-2 flex items-center gap-2'>
              <svg className='w-4 h-4 text-blue-600' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
                <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z' />
              </svg>
              默认账号
            </p>
            <p className='text-gray-600'>用户名: <span className='font-medium text-gray-800'>admin</span></p>
            <p className='text-gray-600'>密码: <span className='font-medium text-gray-800'>admin123</span></p>
          </div>
        </div>
      </div>
    </div>
  )
}
