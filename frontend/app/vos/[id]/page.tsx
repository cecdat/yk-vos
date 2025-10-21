'use client'
import React, {useEffect, useState} from 'react'
import api from '../../../lib/api'
import Card from '../../../components/ui/Card'
import Table from '../../../components/ui/Table'
import SimpleLine from '../../../components/charts/LineChart'
export default function VosDetail({ params }: any){
  const id = params?.id
  const [online,setOnline]=useState<any[]>([])
  const [cdrs,setCdrs]=useState<any[]>([])
  const [chartData,setChartData]=useState<any[]>([])
  useEffect(()=>{ if(id) {fetchOnline();fetchCdrs();genChart()} },[id])
  async function fetchOnline(){try{const res=await api.get(`/vos/instances/${id}/phones/online`);const data=res.data||{};const list=data.infoPhoneOnlines||data||[];setOnline(list)}catch(e){console.error(e)}}
  async function fetchCdrs(){try{const res=await api.get(`/cdr/history?vos_id=${id}&limit=50`);setCdrs(res.data||[])}catch(e){console.error(e)}}
  function genChart(){ const d = []; for(let i=6;i>=0;i--){ d.push({ name: `${i}d`, value: Math.floor(Math.random()*200) }) } setChartData(d) }
  return (<div>
    <h1 className='text-2xl mb-4'>VOS 节点 {id}</h1>
    <div className='grid grid-cols-2 gap-4'>
      <Card><h3 className='text-sm'>在线话机</h3><p className='text-2xl'>{online.length}</p></Card>
      <Card><h3 className='text-sm'>最近话单</h3><p className='text-2xl'>{cdrs.length}</p></Card>
    </div>
    <div className='mt-6 grid grid-cols-2 gap-4'>
      <div>
        <h2 className='text-lg mb-2'>在线话机</h2>
        <Table columns={['详情']} rows={online} />
      </div>
      <div>
        <h2 className='text-lg mb-2'>通话趋势（近7天）</h2>
        <SimpleLine data={chartData} />
      </div>
    </div>
    <div className='mt-6'>
      <h2 className='text-lg mb-2'>历史话单（最近50）</h2>
      <Table columns={['开始时间','呼叫方','被叫方','时长(s)','cost']} rows={cdrs} />
    </div>
  </div>)
}
