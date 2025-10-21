'use client'
import React from 'react'
export default function Navbar(){
  return (
    <div className='flex items-center justify-between mb-6'>
      <div className='flex items-center gap-4'>
        <div className='text-2xl font-bold'>VOS 控制台</div>
        <nav className='space-x-3 text-sm text-gray-600 hidden md:inline'>
          <a href='/' className='hover:underline'>仪表盘</a>
          <a href='/vos' className='hover:underline'>VOS 节点</a>
          <a href='/cdr' className='hover:underline'>话单历史</a>
        </nav>
      </div>
      <div className='flex items-center gap-3'>
        <a href='/login' className='text-sm text-gray-700'>登录</a>
      </div>
    </div>
  )
}
