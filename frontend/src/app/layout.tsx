import '../styles/globals.css'

import type { Metadata } from 'next'
import { Fraunces, Sora } from 'next/font/google'
import { Toaster } from 'react-hot-toast'

const fraunces = Fraunces({
  variable: '--font-fraunces',
  subsets: ['latin'],
  weight: ['500', '600', '700'],
})

const sora = Sora({
  variable: '--font-sora',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
})

export const metadata: Metadata = {
  title: 'Lumina — HIPAA Privacy Desk',
  description:
    'Health-system privacy desk: grounded HIPAA policy Q&A, breach clocks, patient access guides, and BAA vendor screens.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${fraunces.variable} ${sora.variable}`}>
      <body>
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              borderRadius: '12px',
              background: '#14181f',
              color: '#fffdf9',
              fontSize: '13px',
              fontFamily: 'var(--font-sora)',
            },
          }}
        />
        {children}
      </body>
    </html>
  )
}
