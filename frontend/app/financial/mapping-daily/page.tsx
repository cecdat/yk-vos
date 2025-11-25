'use client'
import React, { useState, useEffect } from 'react'
import api from '../../../lib/api'
import { useVOS } from '../../../contexts/VOSContext'

interface GatewayRecord {
    date: string
    gateway_name: string
    total_fee: number
    total_duration: number
    total_calls: number
    connected_calls: number
    connection_rate: number
}

export default function MappingDailyPage() {
    const { currentVOS } = useVOS()
    const [data, setData] = useState<GatewayRecord[]>([])
    const [loading, setLoading] = useState(false)
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [searchName, setSearchName] = useState('')

    useEffect(() => {
        const end = new Date()
        const start = new Date()
        start.setDate(end.getDate() - 7) // 默认最近7天
        setStartDate(start.toISOString().split('T')[0])
        setEndDate(end.toISOString().split('T')[0])
    }, [])

    useEffect(() => {
        if (startDate && endDate) {
            fetchData()
        }
    }, [startDate, endDate, currentVOS])

    async function fetchData() {
        setLoading(true)
        try {
            const params: any = {
                start_date: startDate,
                end_date: endDate
            }
            if (currentVOS) {
                params.vos_id = currentVOS.id
            }
            if (searchName) {
                params.gateway_name = searchName
            }

            const res = await api.get('/financial/mapping-daily', { params })
            setData(res.data.data)
        } catch (e) {
            console.error('获取对接账户报表失败:', e)
        } finally {
            setLoading(false)
        }
    }

    function formatMoney(amount: number) {
        return new Intl.NumberFormat('zh-CN', {
            style: 'currency',
            currency: 'CNY'
        }).format(amount)
    }

    function formatDuration(seconds: number) {
        const h = Math.floor(seconds / 3600)
        const m = Math.floor((seconds % 3600) / 60)
        const s = seconds % 60
        return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
    }

    return (
        <div className='max-w-7xl mx-auto'>
            <div className='flex flex-col md:flex-row md:items-center justify-between mb-6 gap-4'>
                <h1 className='text-2xl font-bold text-gray-800'>对接账户日明细</h1>
                <div className='flex flex-wrap gap-3'>
                    <input
                        type='text'
                        placeholder='搜索网关名称...'
                        value={searchName}
                        onChange={(e) => setSearchName(e.target.value)}
                        className='border rounded-lg px-3 py-2 w-40'
                    />
                    <input
                        type='date'
                        value={startDate}
                        onChange={(e) => setStartDate(e.target.value)}
                        className='border rounded-lg px-3 py-2'
                    />
                    <span className='self-center text-gray-500'>至</span>
                    <input
                        type='date'
                        value={endDate}
                        onChange={(e) => setEndDate(e.target.value)}
                        className='border rounded-lg px-3 py-2'
                    />
                    <button
                        onClick={fetchData}
                        disabled={loading}
                        className='bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50'
                    >
                        {loading ? '加载中...' : '查询'}
                    </button>
                </div>
            </div>

            <div className='bg-white rounded-xl shadow-sm overflow-hidden border border-gray-100'>
                <div className='overflow-x-auto'>
                    <table className='w-full text-left'>
                        <thead className='bg-gray-50 border-b border-gray-100'>
                            <tr>
                                <th className='px-6 py-4 font-semibold text-gray-700'>日期</th>
                                <th className='px-6 py-4 font-semibold text-gray-700'>对接网关</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>费用 (元)</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>通话时长</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>呼叫总数</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>接通数</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>接通率</th>
                            </tr>
                        </thead>
                        <tbody className='divide-y divide-gray-50'>
                            {data.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className='px-6 py-8 text-center text-gray-500'>
                                        暂无数据
                                    </td>
                                </tr>
                            ) : (
                                data.map((row, index) => (
                                    <tr key={index} className='hover:bg-gray-50 transition'>
                                        <td className='px-6 py-4 text-gray-800 whitespace-nowrap'>{row.date}</td>
                                        <td className='px-6 py-4 text-gray-800 font-medium'>{row.gateway_name}</td>
                                        <td className='px-6 py-4 text-right font-medium text-blue-600'>
                                            {formatMoney(row.total_fee)}
                                        </td>
                                        <td className='px-6 py-4 text-right text-gray-600 whitespace-nowrap'>
                                            {formatDuration(row.total_duration)}
                                        </td>
                                        <td className='px-6 py-4 text-right text-gray-600'>
                                            {row.total_calls.toLocaleString()}
                                        </td>
                                        <td className='px-6 py-4 text-right text-gray-600'>
                                            {row.connected_calls.toLocaleString()}
                                        </td>
                                        <td className='px-6 py-4 text-right'>
                                            <span className={`px-2 py-1 rounded text-xs font-semibold ${row.connection_rate > 50 ? 'bg-green-100 text-green-800' :
                                                    row.connection_rate > 20 ? 'bg-yellow-100 text-yellow-800' :
                                                        'bg-red-100 text-red-800'
                                                }`}>
                                                {row.connection_rate}%
                                            </span>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}
