import './globals.css'
import Navbar from '../components/ui/Navbar'
export const metadata = { title: 'VOS Dashboard' }
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang='zh-CN'>
      <body>
        <div className='flex min-h-screen bg-gray-50'>
          <aside className='w-64 p-6 bg-white border-r hidden md:block'>
            <h2 className='text-xl font-bold'>VOS 仪表盘</h2>
            <nav className='mt-6 space-y-2 text-sm'>
              <a href='/' className='block text-gray-700'>仪表盘</a>
              <a href='/vos' className='block text-gray-700'>VOS 节点</a>
              <a href='/cdr' className='block text-gray-700'>话单历史</a>
            </nav>
          </aside>
          <div className='flex-1 p-6'>
            <Navbar />
            {children}
          </div>
        </div>
      </body>
    </html>
  )
}
