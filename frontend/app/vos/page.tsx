'use client'
import React, {useEffect, useState} from 'react'
import api from '../../lib/api'
import Card from '../../components/ui/Card'
export default function VosList(){
  const [instances,setInstances]=useState<any[]>([])
  useEffect(()=>{fetchInstances()},[])
  async function fetchInstances(){try{const res=await api.get('/vos/instances');setInstances(res.data||[])}catch(e){console.error(e)}}
  return (<div><h1 className='text-2xl mb-4'>VOS 节点</h1><div className='grid grid-cols-2 gap-4'>{instances.map(it=>(<Card key={it.id}><a href={`/vos/${it.id}`} className='font-semibold'>{it.name}</a><div className='text-sm text-gray-600'>{it.base_url}</div></Card>))}</div></div>)
}
