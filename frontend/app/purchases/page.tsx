'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api, { getErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import Link from 'next/link';
import { Download, CheckCircle, Clock, XCircle, Loader2, Shield, FileText, Copy, Check } from 'lucide-react';

export default function PurchasesPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [orders, setOrders] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [copiedHashId, setCopiedHashId] = useState<string | null>(null);

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    api.get('/api/orders').then(r => setOrders(r.data.orders || [])).catch(() => {}).finally(() => setLoading(false));
  }, [user]);

  const handleDownload = async (productId: string, productTitle: string) => {
    setDownloading(productId);
    try {
      const { data } = await api.get(`/api/downloads/product/${productId}`);
      const link = document.createElement('a');
      link.href = data.download_url;
      if (data.filename) {
        link.download = data.filename;
      }
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success(`Download started for "${data.filename || productTitle}"\nLink expires in 5 minutes.`);
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Download failed'));
    } finally { setDownloading(null); }
  };

  const statusIcon = (s: string) => {
    if (s === 'paid') return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (s === 'failed') return <XCircle className="w-4 h-4 text-red-600" />;
    return <Clock className="w-4 h-4 text-amber-500" />;
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-blue-600"/></div>
    </div>
  );

  const paid = orders.filter(o => o.status === 'paid');
  const other = orders.filter(o => o.status !== 'paid');

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8 w-full">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">My Purchases</h1>
        <p className="text-gray-500 text-sm mb-8">{paid.length} paid order(s) · {orders.length} total</p>

        {orders.length === 0 ? (
          <div className="text-center py-20">
            <FileText className="w-12 h-12 text-gray-300 mx-auto mb-4"/>
            <p className="text-gray-500">No purchases yet.</p>
            <Link href="/marketplace" className="mt-4 inline-block text-blue-600 font-medium hover:underline">Browse marketplace →</Link>
          </div>
        ) : (
          <div className="space-y-4">
            {orders.map(order => (
              <div key={order.id} className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
                {/* Order header */}
                <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                  <div className="flex items-center gap-3">
                    {statusIcon(order.status)}
                    <div>
                      <span className="font-bold text-gray-900 text-sm">{order.order_number}</span>
                      <span className="text-gray-400 text-xs ml-3">{new Date(order.created_at).toLocaleDateString('en-IN', { year:'numeric', month:'short', day:'numeric' })}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-xs px-2.5 py-1 rounded-full border font-semibold ${
                      order.status === 'paid' ? 'bg-green-50 text-green-700 border-green-200' :
                      order.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                      'bg-gray-100 text-gray-600 border-gray-200'}`}>
                      {order.status.replace('_', ' ').toUpperCase()}
                    </span>
                    <span className="font-bold text-gray-900">₹{order.total_amount}</span>
                  </div>
                </div>

                {/* Order items */}
                {order.items?.map((item: any) => (
                  <div key={item.id} className="px-6 py-4 border-b border-gray-50 last:border-0">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 flex-1">
                        <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                          <FileText className="w-5 h-5 text-blue-600"/>
                        </div>
                        <div>
                          <p className="font-medium text-gray-900 text-sm">{item.product?.title || 'Product'}</p>
                          <p className="text-xs text-gray-400 mt-0.5 uppercase">.{item.product?.file_extension}</p>
                          <p className="text-xs text-gray-400 mt-1">₹{item.price_at_purchase}</p>

                          {/* Security & Verification info */}
                          {order.status === 'paid' && (
                            <div className="mt-2.5 bg-emerald-50/70 border border-emerald-200 rounded-xl p-3 text-xs space-y-2">
                              <div className="flex items-center gap-1.5 text-emerald-800 font-semibold">
                                <Shield className="w-3.5 h-3.5 text-emerald-600" />
                                <span>Verified & Protected Digital Asset</span>
                              </div>
                              <p className="text-emerald-700 text-[11px]">
                                Malware scan passed · File integrity verified · Secure download ready
                              </p>
                              {item.product?.sha256_hash && (
                                <div className="mt-1 pt-2 border-t border-emerald-200/60 flex items-center justify-between gap-2">
                                  <div className="flex items-center gap-1.5 overflow-hidden">
                                    <span className="text-[10px] font-bold text-emerald-900 uppercase tracking-wider font-sans">
                                      SHA-256:
                                    </span>
                                    <span className="font-mono text-[11px] text-emerald-800 truncate max-w-[260px] sm:max-w-[340px]">
                                      {item.product.sha256_hash}
                                    </span>
                                  </div>
                                  <button
                                    onClick={() => {
                                      navigator.clipboard.writeText(item.product.sha256_hash);
                                      setCopiedHashId(item.id);
                                      toast.success('SHA-256 hash copied to clipboard');
                                      setTimeout(() => setCopiedHashId(null), 2000);
                                    }}
                                    className="px-2 py-1 bg-white hover:bg-emerald-100 text-emerald-800 border border-emerald-300 rounded text-[10px] font-semibold flex items-center gap-1 transition-colors flex-shrink-0"
                                    title="Copy full SHA-256 hash"
                                  >
                                    {copiedHashId === item.id ? (
                                      <>
                                        <Check className="w-3 h-3 text-emerald-600" /> Copied
                                      </>
                                    ) : (
                                      <>
                                        <Copy className="w-3 h-3" /> Copy
                                      </>
                                    )}
                                  </button>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </div>

                      {order.status === 'paid' && item.download_enabled && (
                        <div className="flex flex-col items-end gap-2 flex-shrink-0">
                          <button onClick={() => handleDownload(item.product_id, item.product?.title || '')}
                            disabled={downloading === item.product_id}
                            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50">
                            {downloading === item.product_id ? <Loader2 className="w-4 h-4 animate-spin"/> : <Download className="w-4 h-4"/>}
                            Download
                          </button>
                          <p className="text-xs text-gray-400">{item.download_count}/{item.download_limit} downloads used</p>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
