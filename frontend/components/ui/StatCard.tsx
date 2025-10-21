'use client'
import React from 'react'
export default function StatCard({title,value}:{title:string,value:React.ReactNode}){
  return (
    <div className='p-4 bg-white rounded-2xl shadow-sm border'>
      <div className='text-sm text-gray-500'>{title}</div>
      <div className='text-2xl font-semibold'>{value}</div>
    </div>
  )
}
