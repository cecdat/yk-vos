'use client'
import React, {useEffect, useState} from 'react'
import api from '../../lib/api'
import Table from '../../components/ui/Table'
export default function CdrPage(){
  const [cdrs,setCdrs]=useState<any[]>([])
  useEffect(()=>{fetchCdrs()},[])
  async function fetchCdrs(){try{const res=await api.get('/cdr/history?limit=100');setCdrs(res.data||[])}catch(e){console.error(e)}}
  return (<div><h1 className='text-2xl mb-4'>历史话单</h1><Table columns={['开始时间','呼叫方','被叫方','时长(s)','cost']} rows={cdrs} /></div>)
}
