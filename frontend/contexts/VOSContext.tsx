'use client'
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import api from '../lib/api'

interface VOSInstance {
  id: number
  name: string
  base_url: string
  description?: string
  enabled: boolean
}

interface VOSContextType {
  currentVOS: VOSInstance | null
  allVOS: VOSInstance[]
  setCurrentVOS: (vos: VOSInstance | null) => void
  refreshVOSList: () => Promise<void>
  loading: boolean
}

const VOSContext = createContext<VOSContextType | undefined>(undefined)

export function VOSProvider({ children }: { children: ReactNode }) {
  const [currentVOS, setCurrentVOSState] = useState<VOSInstance | null>(null)
  const [allVOS, setAllVOS] = useState<VOSInstance[]>([])
  const [loading, setLoading] = useState(true)

  // 从 localStorage 恢复上次选择的 VOS
  useEffect(() => {
    const savedVOSId = localStorage.getItem('selectedVOSId')
    if (savedVOSId && allVOS.length > 0) {
      const vos = allVOS.find(v => v.id === parseInt(savedVOSId))
      if (vos) {
        setCurrentVOSState(vos)
      } else if (allVOS.length > 0) {
        // 如果保存的 VOS 不存在，选择第一个启用的
        const firstEnabled = allVOS.find(v => v.enabled) || allVOS[0]
        setCurrentVOSState(firstEnabled)
      }
    } else if (allVOS.length > 0 && !currentVOS) {
      // 首次加载，选择第一个启用的 VOS
      const firstEnabled = allVOS.find(v => v.enabled) || allVOS[0]
      setCurrentVOSState(firstEnabled)
    }
  }, [allVOS])

  // 获取 VOS 列表
  async function refreshVOSList() {
    setLoading(true)
    try {
      const res = await api.get('/vos/instances')
      const instances = res.data || []
      setAllVOS(instances)
    } catch (e) {
      console.error('获取 VOS 列表失败:', e)
      setAllVOS([])
    } finally {
      setLoading(false)
    }
  }

  // 设置当前 VOS（同时保存到 localStorage）
  function setCurrentVOS(vos: VOSInstance | null) {
    setCurrentVOSState(vos)
    if (vos) {
      localStorage.setItem('selectedVOSId', vos.id.toString())
    } else {
      localStorage.removeItem('selectedVOSId')
    }
  }

  // 初始化时获取 VOS 列表
  useEffect(() => {
    refreshVOSList()
  }, [])

  return (
    <VOSContext.Provider
      value={{
        currentVOS,
        allVOS,
        setCurrentVOS,
        refreshVOSList,
        loading
      }}
    >
      {children}
    </VOSContext.Provider>
  )
}

// Hook for using VOS context
export function useVOS() {
  const context = useContext(VOSContext)
  if (context === undefined) {
    throw new Error('useVOS must be used within a VOSProvider')
  }
  return context
}

// Hook for getting current VOS ID (with fallback)
export function useCurrentVOSId(): number | null {
  const { currentVOS } = useVOS()
  return currentVOS?.id || null
}

