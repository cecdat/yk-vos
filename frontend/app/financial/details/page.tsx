'use client'
import React, { useState, useEffect } from 'react'
import api from '../../../lib/api'
import { useVOS } from '../../../contexts/VOSContext'

interface FinancialRecord {
    date: string
    income: number
    expense: number
    profit: number
    duration: number
    calls: number
}

export default function FinancialDetailsPage() {
    const { currentVOS } = useVOS()
    const [data, setData] = useState<FinancialRecord[]>([])
    const [loading, setLoading] = useState(false)
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')

    useEffect(() => {
        // 默认最近30天
        const end = new Date()
        const start = new Date()
        start.setDate(end.getDate() - 30)
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

            const res = await api.get('/financial/income-expense', { params })
            setData(res.data.data)
        } catch (e) {
            console.error('获取财务报表失败:', e)
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
        return `${h}时${m}分${s}秒`
    }

    return (
        <div className='max-w-7xl mx-auto'>
            <div className='flex items-center justify-between mb-6'>
                <h1 className='text-2xl font-bold text-gray-800'>财务明细收支</h1>
                <div className='flex gap-4'>
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
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>收入 (元)</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>支出 (元)</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>利润 (元)</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>通话时长</th>
                                <th className='px-6 py-4 font-semibold text-gray-700 text-right'>通话次数</th>
                            </tr>
                        </thead>
                        <tbody className='divide-y divide-gray-50'>
                            {data.length === 0 ? (
                                <tr>
                                    <td colSpan={6} className='px-6 py-8 text-center text-gray-500'>
                                        暂无数据
                                    </td>
                                </tr>
                            ) : (
                                data.map((row, index) => (
                                    <tr key={index} className='hover:bg-gray-50 transition'>
                                        <td className='px-6 py-4 text-gray-800'>{row.date}</td>
                                        <td className='px-6 py-4 text-right font-medium text-green-600'>
                                            {formatMoney(row.income)}
                                        </td>
                                        <td className='px-6 py-4 text-right font-medium text-red-600'>
                                            {formatMoney(row.expense)}
                                        </td>
                                        <td className='px-6 py-4 text-right font-bold text-blue-600'>
                                            {formatMoney(row.profit)}
                                        </td>
                                        <td className='px-6 py-4 text-right text-gray-600'>
                                            {formatDuration(row.duration)}
                                        </td>
                                        <td className='px-6 py-4 text-right text-gray-600'>
                                            {row.calls.toLocaleString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                        {data.length > 0 && (
                            <tfoot className='bg-gray-50 font-bold'>
                                <tr>
                                    <td className='px-6 py-4'>合计</td>
                                    <td className='px-6 py-4 text-right text-green-700'>
                                        {formatMoney(data.reduce((sum, row) => sum + row.income, 0))}
                                    </td>
                                    <td className='px-6 py-4 text-right text-red-700'>
                                        {formatMoney(data.reduce((sum, row) => sum + row.expense, 0))}
                                    </td>
                                    <td className='px-6 py-4 text-right text-blue-700'>
                                        {formatMoney(data.reduce((sum, row) => sum + row.profit, 0))}
                                    </td>
                                    <td className='px-6 py-4 text-right'>
                                        {formatDuration(data.reduce((sum, row) => sum + row.duration, 0))}
                                    </td>
                                    <td className='px-6 py-4 text-right'>
                                        {data.reduce((sum, row) => sum + row.calls, 0).toLocaleString()}
                                    </td>
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>
            </div>
        </div>
    )
}
