'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import { useAuth } from '@/lib/auth';
import api, { getErrorMessage } from '@/lib/api';
import toast from 'react-hot-toast';
import { Package, Shield, DollarSign, Zap, CheckCircle, Loader2 } from 'lucide-react';
import Link from 'next/link';

export default function BecomeSeller() {
  const { user, refreshUser, isSeller } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  if (isSeller()) {
    router.push('/seller/dashboard');
    return null;
  }

  const handleBecomeSeller = async () => {
    if (!user) { router.push('/login'); return; }
    setLoading(true);
    try {
      await api.post('/api/auth/become-seller');
      await refreshUser();
      toast.success('Seller account activated!');
      router.push('/seller/upload');
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Failed to activate seller account'));
    } finally { setLoading(false); }
  };

  const PERKS = [
    { icon: Package, title: 'Upload Any Digital File', desc: 'PDFs, ZIPs, DOCX, XLSX, source code, images, and more.' },
    { icon: Zap, title: 'AI-Powered Metadata', desc: 'Gemini AI generates titles, descriptions, tags automatically.' },
    { icon: Shield, title: 'Built-in Security', desc: 'SHA-256 hashing, malware scanning, and private cloud storage.' },
    { icon: DollarSign, title: 'Instant Payouts via Razorpay', desc: 'Secure UPI and card payments with real-time verification.' },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-16 w-full">
        <div className="text-center mb-12">
          <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <Package className="w-9 h-9 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-3">Start Selling on SecureMarket</h1>
          <p className="text-gray-500 text-lg max-w-xl mx-auto">
            Reach buyers worldwide. Upload digital files, set your price, and get paid securely.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5 mb-10">
          {PERKS.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-white border border-gray-200 rounded-xl p-5 flex gap-4">
              <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                <Icon className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 text-sm">{title}</p>
                <p className="text-sm text-gray-500 mt-0.5">{desc}</p>
              </div>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center">
          {user ? (
            <>
              <p className="text-gray-600 mb-6">Ready to activate seller mode for <strong>{user.email}</strong>?</p>
              <button onClick={handleBecomeSeller} disabled={loading}
                className="bg-blue-600 text-white px-10 py-3.5 rounded-xl font-bold text-base hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center gap-2 mx-auto">
                {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle className="w-5 h-5" />}
                {loading ? 'Activating…' : 'Activate Seller Account — Free'}
              </button>
            </>
          ) : (
            <>
              <p className="text-gray-600 mb-6">Create a free account to start selling.</p>
              <Link href="/register?seller=true"
                className="bg-blue-600 text-white px-10 py-3.5 rounded-xl font-bold text-base hover:bg-blue-700 transition-colors inline-block">
                Create Free Account
              </Link>
            </>
          )}
          <p className="text-xs text-gray-400 mt-4">No listing fees. No monthly charges. Secure payments via Razorpay.</p>
        </div>
      </div>
    </div>
  );
}
