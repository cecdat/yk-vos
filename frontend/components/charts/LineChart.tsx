'use client'
import React from 'react'
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts'
export default function SimpleLine({data}:{data:any[]}){
  return (
    <div className='p-4 bg-white rounded-2xl border'>
      <ResponsiveContainer width='100%' height={200}>
        <LineChart data={data}><XAxis dataKey='name' /><YAxis /><Tooltip /><Line type='monotone' dataKey='value' stroke='#3b82f6' strokeWidth={2} /></LineChart>
      </ResponsiveContainer>
    </div>
  )
}
