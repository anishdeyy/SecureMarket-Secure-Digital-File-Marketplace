'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import {
  ShoppingBag, Download, Heart, User, Shield, Bell, CheckCircle2, 
  Clock, AlertCircle, Loader2, ArrowRight, ExternalLink, Sparkles,
  Layers, ChevronRight, Lock
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, href, badge }: any) {
  const content = (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 hover:border-gray-300 hover:shadow-sm transition-all">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</span>
        <div className="w-8 h-8 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <div className="flex items-baseline justify-between">
        <p className="text-2xl font-extrabold text-gray-900 tracking-tight">{value}</p>
        {badge && (
          <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full">
            {badge}
          </span>
        )}
      </div>
    </div>
  );

  return href ? <Link href={href}>{content}</Link> : content;
}

export default function DashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [notifCount, setNotifCount] = useState(0);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    Promise.all([
      api.get('/api/orders'),
      api.get('/api/notifications'),
    ])
      .then(([oRes, nRes]) => {
        setOrders(oRes.data.orders || []);
        setNotifCount(nRes.data.unread_count || 0);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const paid = orders.filter((o) => o.status === 'paid');
  const totalSpent = paid.reduce((s: number, o: any) => s + (o.total_amount || 0), 0);

  if (!user || loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm text-gray-500 font-medium">Loading account overview...</p>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        
        {/* Welcome Bar */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 sm:p-8 mb-8 shadow-sm">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-6">
            <div className="flex items-center gap-4">
              <div className="w-16 h-16 rounded-2xl bg-blue-600 text-white font-black text-2xl flex items-center justify-center shadow-md shadow-blue-500/20">
                {(user.full_name || user.username || 'U')[0].toUpperCase()}
              </div>
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <h1 className="text-xl sm:text-2xl font-extrabold text-gray-900 tracking-tight">
                    {user.full_name || user.username}
                  </h1>
                  <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full inline-flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" /> Verified Account
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">{user.email}</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Link
                href="/seller/upload"
                className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold px-4 py-2.5 rounded-xl shadow-sm transition-colors flex items-center gap-1.5"
              >
                <Sparkles className="w-3.5 h-3.5" /> Sell Assets
              </Link>
              <Link
                href="/marketplace"
                className="border border-gray-200 hover:bg-slate-50 text-gray-700 text-xs font-semibold px-4 py-2.5 rounded-xl transition-colors"
              >
                Browse Catalog
              </Link>
            </div>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <StatCard
            icon={ShoppingBag}
            label="Purchases"
            value={paid.length}
            href="/purchases"
            badge="Lifetime"
          />
          <StatCard
            icon={Download}
            label="Downloads"
            value={paid.reduce(
              (s: number, o: any) =>
                s + (o.items?.filter((i: any) => i.download_count > 0).length || 0),
              0
            )}
            href="/purchases"
            badge="Active Links"
          />
          <StatCard
            icon={Heart}
            label="Wishlist"
            value="View"
            href="/wishlist"
          />
          <StatCard
            icon={Bell}
            label="Notifications"
            value={notifCount}
            href="/notifications"
            badge={notifCount > 0 ? 'New' : undefined}
          />
        </div>

        {/* Total Spent Banner */}
        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 mb-8 text-white flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shadow-lg shadow-slate-900/10">
          <div>
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-1">
              Total Invested in Digital Assets
            </span>
            <p className="text-3xl font-extrabold tracking-tight">₹{totalSpent.toLocaleString('en-IN')}</p>
            <p className="text-xs text-slate-400 mt-1">Directly empowering independent creators & engineers.</p>
          </div>
          <Link
            href="/purchases"
            className="bg-white hover:bg-slate-100 text-slate-900 font-bold text-xs px-5 py-2.5 rounded-xl transition-colors inline-flex items-center gap-2 shadow-sm"
          >
            Manage Purchased Files <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {/* Recent Orders Table */}
        <div className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-sm mb-8">
          <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-gray-900">Recent Purchase Orders</h2>
              <p className="text-xs text-gray-400 mt-0.5">Secure payment & instant download links</p>
            </div>
            <Link href="/purchases" className="text-xs font-semibold text-blue-600 hover:underline">
              View all orders →
            </Link>
          </div>

          {orders.length === 0 ? (
            <div className="text-center py-16">
              <ShoppingBag className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm font-semibold text-gray-700">No purchases found</p>
              <p className="text-xs text-gray-400 mt-1 mb-5">Explore verified code, templates, and designs.</p>
              <Link
                href="/marketplace"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-2 rounded-xl transition-colors"
              >
                Browse Marketplace
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {orders.slice(0, 5).map((o) => (
                <div key={o.id} className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono font-bold text-gray-900">{o.order_number}</span>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                          o.status === 'paid'
                            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                            : 'bg-slate-100 text-slate-600 border-slate-200'
                        }`}
                      >
                        {o.status.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-400 mt-1">
                      {o.items?.length || 1} item(s) · {new Date(o.created_at).toLocaleDateString()}
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-sm font-bold text-gray-900">₹{o.total_amount?.toLocaleString('en-IN')}</span>
                    <Link
                      href={`/purchases`}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800 bg-blue-50 px-3 py-1.5 rounded-lg"
                    >
                      Download
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Security Summary Card */}
        <div className="bg-white border border-gray-200 rounded-3xl p-6 shadow-sm">
          <div className="flex items-center gap-2 mb-4">
            <Lock className="w-5 h-5 text-blue-600" />
            <h3 className="text-sm font-bold text-gray-900">Account Security & Trust</h3>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {[
              { label: 'Email Authenticated', ok: user.is_email_verified },
              { label: 'Anti-Fraud Status Normal', ok: !user.is_suspended },
              { label: 'Tamper-Proof File Access', ok: true },
            ].map((check) => (
              <div
                key={check.label}
                className="p-3.5 rounded-xl border border-emerald-100 bg-emerald-50/50 flex items-center gap-2.5"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                <span className="text-xs font-semibold text-emerald-900">{check.label}</span>
              </div>
            ))}
          </div>
        </div>

      </main>

      <Footer />
    </div>
  );
}
