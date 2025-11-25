'use client'
import React, { useState, useEffect } from 'react'
import api from '../../../lib/api'
import { useVOS } from '../../../contexts/VOSContext'

interface FinancialRecord {
    date: string
    account: string
    account_name: string
    income: number
    expense: number
    profit: number
    income_cdr_count: number
    expense_cdr_count: number
    total_cdr_count: number
    caller_gateways: string
    callee_gateways: string
}

interface ApiResponse {
    data: FinancialRecord[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

export default function FinancialDetailsPage() {
    const { currentVOS } = useVOS()
    const [data, setData] = useState<FinancialRecord[]>([])
    const [loading, setLoading] = useState(false)
    const [startDate, setStartDate] = useState('')
    const [endDate, setEndDate] = useState('')
    const [periodType, setPeriodType] = useState('day')
    const [page, setPage] = useState(1)
    const [pageSize] = useState(25)
    const [total, setTotal] = useState(0)
    const [totalPages, setTotalPages] = useState(0)

    useEffect(() => {
        // 默认最近7天
        const end = new Date()
        const start = new Date()
        start.setDate(end.getDate() - 7)
        setStartDate(start.toISOString().split('T')[0])
        setEndDate(end.toISOString().split('T')[0])
    }, [])

    useEffect(() => {
        if (startDate && endDate) {
            setPage(1) // 重置页码
            fetchData()
        }
    }, [startDate, endDate, currentVOS, periodType])

    useEffect(() => {
        if (startDate && endDate) {
            fetchData()
        }
    }, [page])

    async function fetchData() {
        setLoading(true)
        try {
            const params: any = {
                start_date: startDate,
                end_date: endDate,
                period_type: periodType,
                page,
                page_size: pageSize
            }
            if (currentVOS) {
                params.vos_id = currentVOS.id
            }

            const res = await api.get<ApiResponse>('/financial/income-expense', { params })
            setData(res.data.data)
            setTotal(res.data.total)
            setTotalPages(res.data.total_pages)
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
        <div className='max-w-full mx-auto px-4'>
            <div className='flex items-center justify-between mb-6 flex-wrap gap-4'>
                <h1 className='text-2xl font-bold text-gray-800'>财务明细收支</h1>
                <div className='flex gap-4 flex-wrap'>
                    <select
                        value={periodType}
                        onChange={(e) => setPeriodType(e.target.value)}
                        className='border rounded-lg px-3 py-2'
                    >
                        <option value='day'>按日统计</option>
                        <option value='month'>按月统计</option>
                        <option value='quarter'>按季度统计</option>
                        <option value='year'>按年统计</option>
                    </select>
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
                    <table className='w-full text-left text-sm'>
                        <thead className='bg-gray-50 border-b border-gray-100'>
                            <tr>
                                <th className='px-4 py-3 font-semibold text-gray-700'>日期</th>
                                <th className='px-4 py-3 font-semibold text-gray-700'>账户号码</th>
                                <th className='px-4 py-3 font-semibold text-gray-700'>账户名称</th>
                                <th className='px-4 py-3 font-semibold text-gray-700'>对接账户</th>
                                <th className='px-4 py-3 font-semibold text-gray-700'>落地账户</th>
                                <th className='px-4 py-3 font-semibold text-gray-700 text-right'>话单数量</th>
                                <th className='px-4 py-3 font-semibold text-gray-700 text-right'>收入 (元)</th>
                                <th className='px-4 py-3 font-semibold text-gray-700 text-right'>支出 (元)</th>
                                <th className='px-4 py-3 font-semibold text-gray-700 text-right'>利润 (元)</th>
                            </tr>
                        </thead>
                        <tbody className='divide-y divide-gray-50'>
                            {data.length === 0 ? (
                                <tr>
                                    <td colSpan={9} className='px-6 py-8 text-center text-gray-500'>
                                        暂无数据
                                    </td>
                                </tr>
                            ) : (
                                data.map((row, index) => (
                                    <tr key={index} className='hover:bg-gray-50 transition'>
                                        <td className='px-4 py-3 text-gray-800'>{row.date}</td>
                                        <td className='px-4 py-3 text-gray-600'>{row.account || '-'}</td>
                                        <td className='px-4 py-3 text-gray-600'>{row.account_name || '-'}</td>
                                        <td className='px-4 py-3 text-gray-600 text-xs max-w-xs truncate' title={row.caller_gateways}>
                                            {row.caller_gateways || '-'}
                                        </td>
                                        <td className='px-4 py-3 text-gray-600 text-xs max-w-xs truncate' title={row.callee_gateways}>
                                            {row.callee_gateways || '-'}
                                        </td>
                                        <td className='px-4 py-3 text-right text-gray-600'>
                                            {row.total_cdr_count.toLocaleString()}
                                        </td>
                                        <td className='px-4 py-3 text-right font-medium text-green-600'>
                                            {formatMoney(row.income)}
                                        </td>
                                        <td className='px-4 py-3 text-right font-medium text-red-600'>
                                            {formatMoney(row.expense)}
                                        </td>
                                        <td className='px-4 py-3 text-right font-bold text-blue-600'>
                                            {formatMoney(row.profit)}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>

                {/* 分页 */}
                {totalPages > 1 && (
                    <div className='flex items-center justify-between px-6 py-4 border-t border-gray-100'>
                        <div className='text-sm text-gray-600'>
                            共 {total} 条记录，第 {page} / {totalPages} 页
                        </div>
                        <div className='flex gap-2'>
                            <button
                                onClick={() => setPage(Math.max(1, page - 1))}
                                disabled={page === 1}
                                className='px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
                            >
                                上一页
                            </button>
                            <button
                                onClick={() => setPage(Math.min(totalPages, page + 1))}
                                disabled={page === totalPages}
                                className='px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed'
                            >
                                下一页
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    )
}
