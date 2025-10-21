'use client'
import React from 'react'
export default function Card({children, className='' }:{children:React.ReactNode, className?:string}){
  return <div className={`p-4 bg-white rounded-2xl shadow-sm border ${className}`}>{children}</div>
}
