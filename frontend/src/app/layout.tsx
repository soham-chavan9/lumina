import '../styles/globals.css'

import type { Metadata } from 'next'
import { Manrope } from 'next/font/google'
import { Toaster } from 'react-hot-toast'

const manrope = Manrope({
  variable: '--font-manrope',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
})

export const metadata: Metadata = {
  title: 'Lumina — Compliance Intelligence',
  description:
    'Apple-inspired compliance assistant: upload policies, ask grounded questions, scan risks.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={manrope.variable}>
      <body>
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              borderRadius: '14px',
              background: '#1d1d1f',
              color: '#fff',
              fontSize: '14px',
            },
          }}
        />
        {children}
      </body>
    </html>
  )
}
