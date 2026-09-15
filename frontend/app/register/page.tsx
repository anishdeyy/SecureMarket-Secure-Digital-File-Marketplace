'use client';
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth';
import { getErrorMessage } from '@/lib/api';
import { Shield, Eye, EyeOff, Loader2, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const { register } = useAuth();
  const router = useRouter();
  const [form, setForm] = useState({ email: '', username: '', password: '', full_name: '' });
  const [selectedRole, setSelectedRole] = useState<'BUYER' | 'SELLER'>('BUYER');
  const [showPass, setShowPass] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (form.password.length < 8) { toast.error('Password must be at least 8 characters'); return; }
    setLoading(true);
    try {
      await register({ ...form, role: selectedRole });
      toast.success(`Account created as ${selectedRole === 'SELLER' ? 'Seller' : 'Buyer'}! Welcome to SecureMarket.`);
      router.push(selectedRole === 'SELLER' ? '/seller/dashboard' : '/marketplace');
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Registration failed'));
    } finally { setLoading(false); }
  };

  const strength = form.password.length >= 12 ? 'Strong' : form.password.length >= 8 ? 'Good' : form.password.length > 0 ? 'Weak' : '';
  const strengthColor = strength === 'Strong' ? 'text-green-600' : strength === 'Good' ? 'text-blue-600' : 'text-red-500';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 px-4">
      <div className="max-w-md w-full mx-auto">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2 mb-6">
            <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <span className="font-bold text-gray-900 text-xl">SecureMarket</span>
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 mt-1">Select your account type to get started</p>
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 shadow-sm">
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Account Role Selector */}
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-gray-700 mb-2">
                Account Type <span className="text-red-500">*</span>
              </label>
              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setSelectedRole('BUYER')}
                  className={`p-3 rounded-xl border-2 text-left transition-all ${
                    selectedRole === 'BUYER'
                      ? 'border-blue-600 bg-blue-50/50 ring-2 ring-blue-500/20'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-bold text-gray-900">Buyer</span>
                    {selectedRole === 'BUYER' && <CheckCircle className="w-4 h-4 text-blue-600" />}
                  </div>
                  <p className="text-[11px] text-gray-500 leading-tight">
                    Browse, purchase, and download digital assets
                  </p>
                </button>

                <button
                  type="button"
                  onClick={() => setSelectedRole('SELLER')}
                  className={`p-3 rounded-xl border-2 text-left transition-all ${
                    selectedRole === 'SELLER'
                      ? 'border-purple-600 bg-purple-50/50 ring-2 ring-purple-500/20'
                      : 'border-gray-200 hover:border-gray-300 bg-white'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-bold text-gray-900">Seller</span>
                    {selectedRole === 'SELLER' && <CheckCircle className="w-4 h-4 text-purple-600" />}
                  </div>
                  <p className="text-[11px] text-gray-500 leading-tight">
                    Publish products, earn payouts, and view sales
                  </p>
                </button>
              </div>
              <p className="text-[11px] text-gray-400 mt-1.5 italic">
                * Note: Roles are strictly separated for security and compliance.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Full Name</label>
              <input value={form.full_name} onChange={e => setForm({ ...form, full_name: e.target.value })}
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="John Doe" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Username <span className="text-red-500">*</span></label>
              <input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="johndoe" minLength={3} maxLength={30} />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Email <span className="text-red-500">*</span></label>
              <input type="email" value={form.email} onChange={e => setForm({ ...form, email: e.target.value })} required
                className="w-full border border-gray-300 rounded-lg px-4 py-2.5 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                placeholder="you@example.com" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Password <span className="text-red-500">*</span></label>
              <div className="relative">
                <input type={showPass ? 'text' : 'password'} value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required
                  className="w-full border border-gray-300 rounded-lg px-4 py-2.5 pr-10 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                  placeholder="Min 8 characters" minLength={8} />
                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-3 text-gray-400 hover:text-gray-600">
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {strength && <p className={`text-xs mt-1 font-medium ${strengthColor}`}>Password strength: {strength}</p>}
            </div>

            <button type="submit" disabled={loading}
              className="w-full bg-blue-600 text-white py-2.5 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50 flex items-center justify-center gap-2 mt-2">
              {loading && <Loader2 className="w-4 h-4 animate-spin" />}
              {loading ? 'Creating account...' : 'Create Account'}
            </button>
          </form>
          <p className="text-center text-sm text-gray-500 mt-6">
            Already have an account?{' '}
            <Link href="/login" className="text-blue-600 font-medium hover:underline">Sign in</Link>
          </p>
          <p className="text-center text-xs text-gray-400 mt-4">
            By creating an account you agree to our{' '}
            <Link href="/terms" className="underline">Terms</Link> and{' '}
            <Link href="/privacy" className="underline">Privacy Policy</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
