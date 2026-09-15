'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api, { getErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import {
  Package, TrendingUp, ShoppingBag, IndianRupee, Plus, Eye,
  CheckCircle2, AlertCircle, Clock, Loader2, BarChart3, Star,
  Shield, Hash, ExternalLink, ArrowRight, Sparkles
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, color }: any) {
  return (
    <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wider">{label}</span>
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${color}`}>
          <Icon className="w-4 h-4" />
        </div>
      </div>
      <p className="text-2xl font-extrabold text-gray-900 tracking-tight">{value}</p>
    </div>
  );
}

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  published: { color: 'bg-emerald-50 text-emerald-700 border-emerald-200', label: 'Published' },
  ready: { color: 'bg-blue-50 text-blue-700 border-blue-200', label: 'Ready to Publish' },
  draft: { color: 'bg-slate-100 text-slate-700 border-slate-200', label: 'Draft' },
  scanning: { color: 'bg-amber-50 text-amber-700 border-amber-200', label: 'Scanning' },
  rejected: { color: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Rejected' },
  suspended: { color: 'bg-rose-50 text-rose-700 border-rose-200', label: 'Suspended' },
};

export default function SellerDashboardPage() {
  const { user, isSeller } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<any>(null);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState<string | null>(null);

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    if (!isSeller()) {
      setLoading(false);
      return;
    }
    Promise.all([
      api.get('/api/seller/stats'),
      api.get('/api/products/seller/my-products?per_page=20'),
    ])
      .then(([sRes, pRes]) => {
        setStats(sRes.data);
        setProducts(pRes.data.items || []);
      })
      .catch(() => toast.error('Failed to load creator metrics'))
      .finally(() => setLoading(false));
  }, [user]);

  const handlePublish = async (productId: string) => {
    setPublishing(productId);
    try {
      await api.post(`/api/products/${productId}/publish`);
      toast.success('Product successfully published!');
      setProducts((prev) =>
        prev.map((p) => (p.id === productId ? { ...p, status: 'published' } : p))
      );
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Publish failed'));
    } finally {
      setPublishing(null);
    }
  };

  const handleDelist = async (productId: string, title: string) => {
    if (!confirm(`Are you sure you want to delist "${title}"? Existing buyers will retain download access, but it will be hidden from the marketplace.`)) return;
    try {
      await api.delete(`/api/products/${productId}`);
      toast.success('Product delisted from marketplace');
      setProducts((prev) =>
        prev.map((p) => (p.id === productId ? { ...p, status: 'removed' } : p))
      );
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Failed to delist product'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm text-gray-500 font-medium">Loading creator workspace...</p>
        </div>
        <Footer />
      </div>
    );
  }

  if (!isSeller()) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center max-w-md mx-auto p-6 text-center">
          <div className="w-12 h-12 rounded-2xl bg-purple-100 text-purple-600 flex items-center justify-center mb-4">
            <Package className="w-6 h-6" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">Seller Access Restricted</h2>
          <p className="text-sm text-gray-500 mb-6">
            You are currently signed in as a <strong>Buyer</strong> ({user?.username}). SecureMarket enforces strict role separation. To sell digital products, please register a dedicated Seller account.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/dashboard" className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700">
              Buyer Dashboard
            </Link>
            <Link href="/register" className="px-4 py-2 border border-gray-200 bg-white text-gray-700 rounded-xl text-xs font-semibold hover:bg-gray-50">
              Register Seller
            </Link>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  const grossSales = stats?.total_revenue || 0;
  const platformFee = Math.round(grossSales * 0.05 * 100) / 100;
  const netEarnings = stats?.net_revenue ?? (Math.round(grossSales * 0.95 * 100) / 100);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
          <div>
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-purple-50 text-purple-700 text-xs font-semibold mb-2 border border-purple-100">
              <BarChart3 className="w-3.5 h-3.5" /> Seller Portal
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">Seller Dashboard</h1>
            <p className="text-xs sm:text-sm text-gray-500 mt-0.5">
              Manage your published software, templates, transparent payouts, and catalog.
            </p>
          </div>

          <Link
            href="/seller/upload"
            className="bg-purple-600 hover:bg-purple-700 text-white font-bold text-xs sm:text-sm px-5 py-2.5 rounded-xl shadow-sm transition-colors inline-flex items-center gap-2 self-start sm:self-center"
          >
            <Plus className="w-4 h-4" /> Upload New Product
          </Link>
        </div>

        {/* Stats Grid with Transparent Fee Breakdown */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard
              icon={Package}
              label="Active Catalog"
              value={stats.published_products}
              color="bg-blue-50 text-blue-600"
            />
            <StatCard
              icon={ShoppingBag}
              label="Total Orders"
              value={stats.total_orders}
              color="bg-indigo-50 text-indigo-600"
            />
            <StatCard
              icon={TrendingUp}
              label="Gross Sales"
              value={`₹${grossSales.toLocaleString('en-IN')}`}
              color="bg-slate-100 text-slate-700"
            />
            <StatCard
              icon={IndianRupee}
              label="Net Payout (95%)"
              value={`₹${netEarnings.toLocaleString('en-IN')}`}
              color="bg-emerald-50 text-emerald-600"
            />
          </div>
        )}

        {/* Transparent Fee Banner */}
        <div className="p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-2xl border border-purple-100 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="text-xs text-purple-900 space-y-0.5">
            <p className="font-bold flex items-center gap-1.5 text-purple-950">
              <Shield className="w-4 h-4 text-purple-600" /> Marketplace Fee Architecture
            </p>
            <p className="text-purple-700">
              Platform Fee: <strong>5%</strong> · Seller Net Earnings: <strong>95%</strong> · Applicable Tax is paid by the buyer and strictly separated from seller revenue.
            </p>
          </div>
          <div className="text-xs text-right bg-white px-3 py-1.5 rounded-xl border border-purple-100 shadow-xs">
            <span className="text-gray-400">Platform Fee Deducted:</span>{' '}
            <strong className="text-purple-700 font-bold">₹{platformFee.toFixed(2)}</strong>
          </div>
        </div>

        {/* Products Listing */}
        <div className="bg-white border border-gray-200 rounded-3xl overflow-hidden shadow-sm mb-8">
          <div className="px-6 py-5 border-b border-gray-100 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Package className="w-5 h-5 text-gray-400" />
              <h2 className="text-base font-bold text-gray-900">Your Catalog ({products.length})</h2>
            </div>
            <Link href="/seller/upload" className="text-xs font-semibold text-blue-600 hover:underline">
              + Add new asset
            </Link>
          </div>

          {products.length === 0 ? (
            <div className="text-center py-16">
              <Package className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-sm font-semibold text-gray-800">No products uploaded yet</p>
              <p className="text-xs text-gray-400 mt-1 mb-5">
                Upload your code, templates, or ebooks to start earning.
              </p>
              <Link
                href="/seller/upload"
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs px-4 py-2.5 rounded-xl shadow-sm transition-colors inline-flex items-center gap-1.5"
              >
                <Plus className="w-3.5 h-3.5" /> Upload First Asset
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-gray-100">
              {products.map((p) => {
                const sc = STATUS_CONFIG[p.status] || STATUS_CONFIG.draft;
                return (
                  <div key={p.id} className="p-6 hover:bg-slate-50/60 transition-colors">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5 flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <h3 className="font-bold text-gray-900 text-sm truncate max-w-md">{p.title}</h3>
                          <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${sc.color}`}>
                            {sc.label}
                          </span>
                          {p.scan_status === 'clean' && (
                            <span className="text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full">
                              ✓ Antivirus Passed
                            </span>
                          )}
                          {p.ai_metadata_generated && (
                            <span className="text-[10px] font-semibold text-purple-700 bg-purple-50 border border-purple-200 px-2 py-0.5 rounded-full flex items-center gap-0.5">
                              <Sparkles className="w-2.5 h-2.5" /> AI Enriched
                            </span>
                          )}
                        </div>

                        <div className="flex items-center gap-3 text-xs text-gray-400 flex-wrap">
                          <span className="font-medium text-gray-600">{p.category}</span>
                          <span>·</span>
                          <span className="uppercase font-mono font-semibold">.{p.file_extension}</span>
                          {p.file_size_bytes && (
                            <>
                              <span>·</span>
                              <span>{(p.file_size_bytes / (1024 * 1024)).toFixed(1)} MB</span>
                            </>
                          )}
                          <span>·</span>
                          <span>{p.total_sales || 0} sales</span>
                          {p.integrity_id && (
                            <>
                              <span>·</span>
                              <span className="font-mono text-blue-600 font-semibold">{p.integrity_id}</span>
                            </>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center gap-4 self-end sm:self-center">
                        <div className="text-right">
                          <span className="text-base font-extrabold text-gray-900">
                            {p.price === 0 ? 'Free' : `₹${p.price.toLocaleString('en-IN')}`}
                          </span>
                        </div>

                        <div className="flex items-center gap-2">
                          {p.status === 'published' && (
                            <Link
                              href={`/marketplace/${p.id}`}
                              className="text-xs font-semibold text-gray-700 hover:text-blue-600 border border-gray-200 hover:border-blue-200 px-3 py-1.5 rounded-lg flex items-center gap-1 bg-white"
                            >
                              <Eye className="w-3.5 h-3.5" /> View
                            </Link>
                          )}

                          {(p.status === 'ready' || p.status === 'draft') && (
                            <button
                              onClick={() => handlePublish(p.id)}
                              disabled={publishing === p.id}
                              className="text-xs font-bold bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-lg flex items-center gap-1 disabled:opacity-50"
                            >
                              {publishing === p.id ? (
                                <Loader2 className="w-3 h-3 animate-spin" />
                              ) : (
                                <CheckCircle2 className="w-3 h-3" />
                              )}
                              Publish Live
                            </button>
                          )}

                          {p.status !== 'removed' && (
                            <button
                              onClick={() => handleDelist(p.id, p.title)}
                              className="text-xs text-rose-600 hover:text-rose-700 hover:bg-rose-50 border border-transparent hover:border-rose-200 px-2.5 py-1.5 rounded-lg transition-colors font-medium"
                              title="Delist from marketplace"
                            >
                              Delist
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </main>

      <Footer />
    </div>
  );
}
