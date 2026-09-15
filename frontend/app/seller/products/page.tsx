'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import api, { getErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import { Plus, Package, Eye, CheckCircle, AlertCircle, Clock, Loader2, Sparkles, Shield } from 'lucide-react';

const STATUS_STYLE: Record<string, string> = {
  published: 'bg-green-50 text-green-700 border-green-200',
  ready:     'bg-blue-50 text-blue-700 border-blue-200',
  draft:     'bg-gray-50 text-gray-600 border-gray-200',
  scanning:  'bg-amber-50 text-amber-700 border-amber-200',
  rejected:  'bg-red-50 text-red-700 border-red-200',
  suspended: 'bg-red-50 text-red-700 border-red-200',
};

export default function SellerProductsPage() {
  const { user, isSeller } = useAuth();
  const router = useRouter();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    if (!isSeller()) { router.push('/seller/become'); return; }
    fetchProducts();
  }, [user, page]);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const { data } = await api.get(`/api/products/seller/my-products?page=${page}&per_page=15`);
      setProducts(data.items || []);
      setTotal(data.total || 0);
    } catch { toast.error('Failed to load products'); }
    finally { setLoading(false); }
  };

  const publish = async (id: string) => {
    setPublishing(id);
    try {
      await api.post(`/api/products/${id}/publish`);
      toast.success('Product published!');
      fetchProducts();
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Publish failed'));
    } finally { setPublishing(null); }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return '';
    if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  if (loading && products.length === 0) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-blue-600" /></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-6xl mx-auto px-4 py-8 w-full">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">My Products</h1>
            <p className="text-sm text-gray-500 mt-1">{total} product{total !== 1 ? 's' : ''} total</p>
          </div>
          <Link href="/seller/upload"
            className="bg-blue-600 text-white px-4 py-2.5 rounded-xl font-semibold hover:bg-blue-700 flex items-center gap-2 text-sm">
            <Plus className="w-4 h-4" /> Upload New
          </Link>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-24 bg-white border border-gray-200 rounded-2xl">
            <Package className="w-14 h-14 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-6 text-lg">No products yet</p>
            <Link href="/seller/upload"
              className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 inline-flex items-center gap-2">
              <Plus className="w-4 h-4" /> Upload Your First Product
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {products.map(p => (
              <div key={p.id} className="bg-white border border-gray-200 rounded-xl p-5 hover:shadow-sm transition-shadow">
                <div className="flex items-start gap-5">
                  {/* File type icon */}
                  <div className="w-12 h-12 bg-gray-100 rounded-xl flex items-center justify-center flex-shrink-0">
                    <span className="text-xs font-bold text-gray-500 uppercase">{p.file_extension || 'FILE'}</span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3 flex-wrap">
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-gray-900 truncate">{p.title}</h3>
                        {p.short_description && (
                          <p className="text-sm text-gray-500 truncate mt-0.5">{p.short_description}</p>
                        )}
                      </div>
                      <span className="font-bold text-gray-900 flex-shrink-0 text-lg">₹{p.price}</span>
                    </div>

                    {/* Badges row */}
                    <div className="flex items-center gap-2 mt-2.5 flex-wrap">
                      <span className={`text-xs px-2.5 py-0.5 rounded-full border font-medium ${STATUS_STYLE[p.status] || STATUS_STYLE.draft}`}>
                        {p.status}
                      </span>
                      <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full flex items-center gap-1 font-medium">
                        <Shield className="w-3 h-3 text-emerald-600" /> Integrity Verified
                      </span>
                      {p.duplicate_status === 'DUPLICATE_DETECTED' && (
                        <span className="text-xs bg-rose-50 text-rose-700 border border-rose-200 px-2.5 py-0.5 rounded-full flex items-center gap-1 font-semibold">
                          <AlertCircle className="w-3 h-3 text-rose-600" /> Duplicate Detected
                        </span>
                      )}
                      {p.quality && (
                        <span className={`text-xs px-2.5 py-0.5 rounded-full border font-semibold flex items-center gap-1 ${
                          p.quality.overall_score >= 80 ? 'bg-blue-50 text-blue-700 border-blue-200' : p.quality.overall_score >= 50 ? 'bg-teal-50 text-teal-700 border-teal-200' : 'bg-amber-50 text-amber-700 border-amber-200'
                        }`}>
                          <Sparkles className="w-3 h-3" /> Quality: {p.quality.overall_score}/100
                        </span>
                      )}
                      {p.ai_metadata_generated && (
                        <span className="text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                          <Sparkles className="w-3 h-3" /> AI Metadata
                        </span>
                      )}
                      {p.category && (
                        <span className="text-xs bg-gray-100 text-gray-600 px-2.5 py-0.5 rounded-full">{p.category}</span>
                      )}
                      {p.difficulty && (
                        <span className="text-xs bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-0.5 rounded-full">{p.difficulty}</span>
                      )}
                    </div>

                    {/* Stats row */}
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-400 flex-wrap">
                      {p.file_size_bytes && <span>{formatSize(p.file_size_bytes)}</span>}
                      {p.original_filename && <span className="truncate max-w-xs">{p.original_filename}</span>}
                      <span>{p.total_sales} sales</span>
                      <span>{p.total_downloads} downloads</span>
                      {p.avg_rating > 0 && <span>★ {p.avg_rating.toFixed(1)} ({p.review_count})</span>}
                      <span>{p.published_at ? `Published ${new Date(p.published_at).toLocaleDateString()}` : `Created ${new Date(p.created_at).toLocaleDateString()}`}</span>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex flex-col gap-2 flex-shrink-0">
                    {p.status === 'published' && (
                      <Link href={`/marketplace/${p.id}`}
                        className="flex items-center gap-1.5 text-xs border border-gray-300 text-gray-600 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors">
                        <Eye className="w-3.5 h-3.5" /> View Live
                      </Link>
                    )}
                    {(p.status === 'ready' || p.status === 'draft') && p.duplicate_status !== 'DUPLICATE_DETECTED' && (
                      <button onClick={() => publish(p.id)} disabled={publishing === p.id}
                        className="flex items-center gap-1.5 text-xs bg-blue-600 text-white px-3 py-1.5 rounded-lg hover:bg-blue-700 disabled:opacity-40 transition-colors">
                        {publishing === p.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                        Publish
                      </button>
                    )}
                    {p.duplicate_status === 'DUPLICATE_DETECTED' && (
                      <span className="flex items-center gap-1.5 text-xs text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1.5 rounded-lg font-semibold" title="Duplicate content cannot be published">
                        <AlertCircle className="w-3.5 h-3.5 text-rose-600" /> Blocked (Duplicate)
                      </span>
                    )}
                    {p.status === 'rejected' && p.duplicate_status !== 'DUPLICATE_DETECTED' && (
                      <span className="flex items-center gap-1.5 text-xs text-red-600 bg-red-50 border border-red-200 px-3 py-1.5 rounded-lg">
                        <AlertCircle className="w-3.5 h-3.5" /> Rejected
                      </span>
                    )}
                    {p.status === 'scanning' && (
                      <span className="flex items-center gap-1.5 text-xs text-amber-600 bg-amber-50 border border-amber-200 px-3 py-1.5 rounded-lg">
                        <Clock className="w-3.5 h-3.5" /> Scanning…
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}

            {/* Pagination */}
            {total > 15 && (
              <div className="flex justify-center gap-2 mt-6">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40">← Prev</button>
                <span className="px-4 py-2 text-sm text-gray-600">Page {page}</span>
                <button onClick={() => setPage(p => p + 1)} disabled={products.length < 15}
                  className="px-4 py-2 border border-gray-300 rounded-lg text-sm hover:bg-gray-50 disabled:opacity-40">Next →</button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
