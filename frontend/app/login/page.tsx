'use client'
import React, {useState} from 'react'
import api from '../../lib/api'
export default function Login(){
  const [u,setU]=useState('admin')
  const [p,setP]=useState('Ykxx@2025')
  const [msg,setMsg]=useState('')
  async function doLogin(){
    try{const res=await api.post('/auth/login',{username:u,password:p});localStorage.setItem('token',res.data.access_token);setMsg('登录成功');window.location.href='/';}catch(e){setMsg('登录失败')}
  }
  return (
    <div className='max-w-md mx-auto'>
      <h1 className='text-2xl mb-4'>登录</h1>
      <input value={u} onChange={e=>setU(e.target.value)} className='w-full p-2 mb-2 border rounded' />
      <input value={p} onChange={e=>setP(e.target.value)} className='w-full p-2 mb-2 border rounded' />
      <button onClick={doLogin} className='px-4 py-2 bg-blue-600 text-white rounded'>登录</button>
      <div className='mt-2 text-sm'>{msg}</div>
    </div>
  )
}
