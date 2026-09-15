import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import { Shield, Zap, Hash, Lock, Users, Star } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-16 w-full">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">About SecureMarket</h1>
          <p className="text-xl text-gray-500 max-w-2xl mx-auto">
            SecureMarket is a Web2 digital file marketplace that combines AI-powered metadata generation,
            cryptographic file integrity, and secure payments in one platform.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
          {[
            { icon: Shield, title: 'Security First', desc: 'Every file is malware-scanned, SHA-256 hashed, and stored in private cloud storage. Downloads are protected by temporary signed URLs.' },
            { icon: Zap, title: 'AI-Powered', desc: 'Gemini AI generates metadata for every uploaded product — titles, descriptions, categories, tags, and keywords automatically.' },
            { icon: Lock, title: 'Tamper-Evident', desc: 'Each file gets a unique Integrity ID (e.g. FI-A3B4C5D6) sealed with HMAC-SHA256. Any tampering with the record is detectable.' },
          ].map(({ icon: Icon, title, desc }) => (
            <div key={title} className="border border-gray-200 rounded-2xl p-6 text-center">
              <div className="w-12 h-12 bg-blue-50 rounded-xl flex items-center justify-center mx-auto mb-4">
                <Icon className="w-6 h-6 text-blue-600" />
              </div>
              <h3 className="font-bold text-gray-900 mb-2">{title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>

        <div className="bg-gray-50 border border-gray-200 rounded-2xl p-8 mb-10">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Technology Stack</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
            {[['Frontend', 'Next.js 14, TypeScript, Tailwind CSS'], ['Backend', 'FastAPI, Python, SQLAlchemy'], ['Database', 'PostgreSQL / SQLite (dev)'], ['Storage', 'AWS S3 / Local (dev)'], ['AI', 'Google Gemini 1.5 Flash'], ['Payments', 'Razorpay (UPI + Cards)'], ['Security', 'SHA-256 + HMAC-SHA256'], ['Scanning', 'ClamAV / Mock (dev)']].map(([k, v]) => (
              <div key={k} className="bg-white border border-gray-200 rounded-lg p-3">
                <p className="font-semibold text-gray-700 text-xs uppercase tracking-wide mb-1">{k}</p>
                <p className="text-xs text-gray-500">{v}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <Footer />
    </div>
  );
}
