'use client'
import React from 'react'
export default function Table({columns, rows}:{columns:string[], rows:any[]}){
  return (
    <div className='overflow-x-auto bg-white rounded border'>
      <table className='min-w-full'>
        <thead className='bg-gray-50'><tr>{columns.map((c,i)=>(<th key={i} className='text-left px-4 py-2 text-sm text-gray-600'>{c}</th>))}</tr></thead>
        <tbody>{rows.map((r,ri)=>(<tr key={ri} className='border-t'><td className='px-4 py-2' colSpan={columns.length}><pre className='text-xs'>{JSON.stringify(r,null,2)}</pre></td></tr>))}</tbody>
      </table>
    </div>
  )
}
