import '../styles/globals.css'

import type { Metadata } from 'next'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'Lumina — HIPAA Privacy Desk',
  description:
    'Health-system privacy desk: grounded HIPAA policy Q&A, breach clocks, patient access guides, and BAA vendor screens.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              borderRadius: '14px',
              background: '#1d1d1f',
              color: '#f5f5f7',
              fontSize: '13px',
              fontWeight: 500,
              fontFamily: 'var(--font-body)',
              padding: '12px 16px',
              boxShadow: '0 8px 28px rgba(0,0,0,0.18)',
            },
          }}
        />
        {children}
      </body>
    </html>
  )
}
