'use client'
import React, { useState, useEffect } from 'react'

interface ParamDefinition {
  name: string
  type: 'string' | 'array' | 'integer' | 'date' | 'boolean'
  required?: boolean
  description?: string
  default?: any
}

interface VosApiParamFormProps {
  apiName: string
  paramDefinitions: ParamDefinition[]
  onSubmit: (params: any) => void
  loading?: boolean
}

// 格式化日期为 yyyyMMdd
function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}${month}${day}`
}

// 获取最近N天的日期
function getRecentDate(daysAgo: number): string {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  return formatDate(date)
}

// 格式化显示日期 yyyyMMdd -> yyyy-MM-dd
function parseDate(dateStr: string): string {
  if (!dateStr || dateStr.length !== 8) return ''
  return `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
}

export default function VosApiParamForm({ apiName, paramDefinitions, onSubmit, loading = false }: VosApiParamFormProps) {
  const [formData, setFormData] = useState<Record<string, any>>({})

  // 初始化表单数据
  useEffect(() => {
    const initialData: Record<string, any> = {}
    
    paramDefinitions.forEach(param => {
      // 为时间参数设置默认值（最近3天）
      if (param.name === 'beginTime') {
        initialData[param.name] = getRecentDate(3)
      } else if (param.name === 'endTime') {
        initialData[param.name] = getRecentDate(0) // 今天
      } else if (param.default !== undefined) {
        initialData[param.name] = param.default
      } else {
        // 根据类型设置默认值
        if (param.type === 'array') {
          initialData[param.name] = []
        } else if (param.type === 'integer') {
          initialData[param.name] = 0
        } else if (param.type === 'boolean') {
          initialData[param.name] = false
        } else {
          initialData[param.name] = ''
        }
      }
    })
    
    setFormData(initialData)
  }, [apiName, paramDefinitions])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    
    // 构建提交数据，过滤空值（数组除外）
    const submitData: Record<string, any> = {}
    
    paramDefinitions.forEach(param => {
      const value = formData[param.name]
      
      if (param.type === 'array') {
        // 数组类型：始终提交，即使为空
        submitData[param.name] = value || []
      } else if (param.required || (value !== '' && value !== null && value !== undefined)) {
        // 必填或有值的字段
        if (param.type === 'integer') {
          submitData[param.name] = parseInt(value) || 0
        } else {
          submitData[param.name] = value
        }
      }
    })
    
    onSubmit(submitData)
  }

  const renderInput = (param: ParamDefinition) => {
    const value = formData[param.name] || ''

    switch (param.type) {
      case 'date':
      case 'string':
        if (param.name.toLowerCase().includes('time')) {
          // 时间字段使用日期选择器
          return (
            <input
              type='date'
              value={parseDate(value)}
              onChange={(e) => {
                const date = e.target.value.replace(/-/g, '')
                setFormData({ ...formData, [param.name]: date })
              }}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              required={param.required}
            />
          )
        } else {
          // 普通字符串输入
          return (
            <input
              type='text'
              value={value}
              onChange={(e) => setFormData({ ...formData, [param.name]: e.target.value })}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              placeholder={`请输入${param.description || param.name}`}
              required={param.required}
            />
          )
        }

      case 'array':
        // 数组类型：用文本框输入，逗号分隔
        const arrayValue = Array.isArray(value) ? value.join(', ') : ''
        return (
          <div className='space-y-2'>
            <input
              type='text'
              value={arrayValue}
              onChange={(e) => {
                const inputValue = e.target.value
                const arrayData = inputValue
                  ? inputValue.split(',').map(item => item.trim()).filter(item => item)
                  : []
                setFormData({ ...formData, [param.name]: arrayData })
              }}
              className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
              placeholder='多个值用逗号分隔，留空表示查询全部'
            />
            <p className='text-xs text-gray-500'>
              {Array.isArray(value) && value.length > 0 
                ? `当前: [${value.map(v => `"${v}"`).join(', ')}]` 
                : '留空将查询全部数据'}
            </p>
          </div>
        )

      case 'integer':
        return (
          <input
            type='number'
            value={value}
            onChange={(e) => setFormData({ ...formData, [param.name]: e.target.value })}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            placeholder={`请输入${param.description || param.name}`}
            required={param.required}
          />
        )

      case 'boolean':
        return (
          <label className='flex items-center gap-2 cursor-pointer'>
            <input
              type='checkbox'
              checked={value}
              onChange={(e) => setFormData({ ...formData, [param.name]: e.target.checked })}
              className='w-4 h-4 text-blue-600 rounded focus:ring-2 focus:ring-blue-500'
            />
            <span className='text-sm text-gray-700'>是</span>
          </label>
        )

      default:
        return (
          <input
            type='text'
            value={value}
            onChange={(e) => setFormData({ ...formData, [param.name]: e.target.value })}
            className='w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            required={param.required}
          />
        )
    }
  }

  return (
    <form onSubmit={handleSubmit} className='space-y-4'>
      {paramDefinitions.map((param) => (
        <div key={param.name}>
          <label className='block text-sm font-medium text-gray-700 mb-1'>
            {param.description || param.name}
            {param.required && <span className='text-red-500 ml-1'>*</span>}
            {param.name.toLowerCase().includes('time') && (
              <span className='ml-2 text-xs text-gray-500'>(默认最近3天)</span>
            )}
          </label>
          {renderInput(param)}
        </div>
      ))}

      <button
        type='submit'
        disabled={loading}
        className='w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg hover:from-blue-700 hover:to-purple-700 transition font-medium disabled:opacity-50 flex items-center justify-center gap-2'
      >
        {loading ? (
          <>
            <svg className='animate-spin h-5 w-5' fill='none' viewBox='0 0 24 24' stroke='currentColor'>
              <path strokeLinecap='round' strokeLinejoin='round' strokeWidth={2} d='M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15' />
            </svg>
            查询中...
          </>
        ) : (
          '执行查询'
        )}
      </button>

      {/* JSON 预览 */}
      <details className='mt-4'>
        <summary className='cursor-pointer text-sm text-gray-600 hover:text-gray-800'>
          查看 JSON 参数（高级用户）
        </summary>
        <div className='mt-2 bg-gray-50 rounded-lg p-3'>
          <pre className='text-xs font-mono text-gray-800 overflow-x-auto'>
            {JSON.stringify(formData, null, 2)}
          </pre>
        </div>
      </details>
    </form>
  )
}

