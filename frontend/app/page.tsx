'use client'
import React, {useEffect, useState} from 'react'
import api from '../lib/api'
import StatCard from '../components/ui/StatCard'
import Card from '../components/ui/Card'
export default function Page(){
  const [instances,setInstances]=useState<any[]>([])
  const [onlineCount,setOnlineCount]=useState(0)
  const [cdrCount,setCdrCount]=useState(0)
  useEffect(()=>{fetchInstances();fetchCdrCount()},[])
  async function fetchInstances(){
    try{const res=await api.get('/vos/instances');setInstances(res.data||[])}catch(e){console.error(e)}
  }
  async function fetchCdrCount(){
    try{const res=await api.get('/cdr/history?limit=1'); setCdrCount(res.data? res.data.length : 0)}catch(e){console.error(e)}
  }
  return (
    <div>
      <h1 className='text-2xl font-semibold mb-4'>仪表盘</h1>
      <div className='grid grid-cols-3 gap-4'>
        <StatCard title='VOS 实例数' value={instances.length} />
        <StatCard title='在线话机数' value={onlineCount} />
        <StatCard title='历史话单数（示例）' value={cdrCount} />
      </div>
      <section className='mt-6'>
        <h2 className='text-lg font-medium mb-3'>已注册实例</h2>
        <div className='grid grid-cols-2 gap-4'>
          {instances.map((it:any)=>(
            <Card key={it.id}><a href={`/vos/${it.id}`} className='text-lg font-semibold'>{it.name}</a><div className='text-sm text-gray-600'>{it.base_url}</div></Card>
          ))}
        </div>
      </section>
    </div>
  )
}
