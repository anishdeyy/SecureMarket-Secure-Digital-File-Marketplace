import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import { AuthProvider } from '@/lib/auth';
import { Toaster } from 'react-hot-toast';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'SecureMarket — Buy & Sell Digital Files Securely',
  description: 'Secure digital marketplace with AI metadata, SHA-256 integrity, malware scanning, and protected downloads.',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <script src="https://checkout.razorpay.com/v1/checkout.js" async></script>
      </head>
      <body className={`${inter.className} min-h-screen bg-white text-gray-900 antialiased selection:bg-blue-100 selection:text-blue-900`}>
        <AuthProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#ffffff',
                color: '#111827',
                border: '1px solid #e5e7eb',
                borderRadius: '12px',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
                fontSize: '14px',
                padding: '12px 16px',
                fontWeight: 500,
              },
              success: { iconTheme: { primary: '#2563eb', secondary: '#ffffff' } },
              error: { iconTheme: { primary: '#dc2626', secondary: '#ffffff' } },
            }}
          />
        </AuthProvider>
      </body>
    </html>
  );
}
