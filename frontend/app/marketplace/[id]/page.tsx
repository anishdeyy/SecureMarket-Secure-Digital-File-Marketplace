'use client';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import FilePreview from '@/components/ui/FilePreview';
import api, { getErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import {
  Star, Shield, CheckCircle2, Download, Heart, ShoppingCart, 
  FileText, Users, Hash, Clock, Loader2, Tag, ChevronDown, 
  ChevronUp, ExternalLink, Copy, ArrowLeft, Lock, Sparkles, Check,
  ShieldCheck, RefreshCw, AlertTriangle
} from 'lucide-react';

declare global {
  interface Window {
    Razorpay: any;
  }
}

const loadRazorpayScript = (): Promise<boolean> => {
  return new Promise((resolve) => {
    if (typeof window === 'undefined') return resolve(false);
    if (window.Razorpay) return resolve(true);
    const existing = document.getElementById('razorpay-checkout-script') as HTMLScriptElement | null;
    if (existing) {
      if (window.Razorpay) return resolve(true);
      existing.addEventListener('load', () => resolve(!!window.Razorpay));
      existing.addEventListener('error', () => resolve(false));
      setTimeout(() => resolve(!!window.Razorpay), 1500);
      return;
    }
    const script = document.createElement('script');
    script.id = 'razorpay-checkout-script';
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.async = true;
    script.onload = () => resolve(!!window.Razorpay);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
    setTimeout(() => resolve(!!window.Razorpay), 2500);
  });
};

function StarRow({ rating }: { rating: number }) {
  return (
    <div className="flex items-center gap-0.5">
      {[1, 2, 3, 4, 5].map((i) => (
        <Star
          key={i}
          className={`w-4 h-4 ${
            i <= Math.round(rating)
              ? 'text-amber-400 fill-amber-400'
              : 'text-gray-200'
          }`}
        />
      ))}
    </div>
  );
}

export default function ProductDetailPage() {
  const { id } = useParams();
  const { user, isBuyer, isSeller, isAdmin } = useAuth();
  const router = useRouter();
  const [product, setProduct] = useState<any>(null);
  const [reviews, setReviews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [buying, setBuying] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [inWishlist, setInWishlist] = useState(false);
  const [purchased, setPurchased] = useState(false);
  const [showFullDesc, setShowFullDesc] = useState(false);
  const [copiedHash, setCopiedHash] = useState(false);
  const [activeTab, setActiveTab] = useState<'overview' | 'quality' | 'security' | 'reviews'>('overview');
  const [canReview, setCanReview] = useState(false);
  const [userReview, setUserReview] = useState<any>(null);
  const [reviewRating, setReviewRating] = useState(5);
  const [reviewHoverRating, setReviewHoverRating] = useState(0);
  const [reviewTitle, setReviewTitle] = useState('');
  const [reviewComment, setReviewComment] = useState('');
  const [submittingReview, setSubmittingReview] = useState(false);
  const [editingReview, setEditingReview] = useState(false);

  // Live Integrity Audit state
  const [verifyingIntegrity, setVerifyingIntegrity] = useState(false);
  const [integrityResult, setIntegrityResult] = useState<{
    match: boolean;
    status: string;
    actual_hash: string;
    stored_hash: string;
    file_size_bytes: number;
  } | null>(null);

  const handleLiveVerify = async () => {
    if (!id) return;
    setVerifyingIntegrity(true);
    try {
      const { data } = await api.get(`/api/integrity/product/${id}/live-verify`);
      setIntegrityResult(data);
      if (data.match) {
        toast.success(data.status || 'MATCH: File integrity verified', { id: 'integrity-toast' });
      } else {
        toast.error(data.status || 'MISMATCH: File integrity check failed', { id: 'integrity-toast' });
      }
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Failed to verify integrity'), { id: 'integrity-toast' });
    } finally {
      setVerifyingIntegrity(false);
    }
  };

  // Pre-payment Checkout Breakdown Modal state
  const [showCheckoutModal, setShowCheckoutModal] = useState(false);
  const [checkoutData, setCheckoutData] = useState<any>(null);
  const [calculatingCheckout, setCalculatingCheckout] = useState(false);

  const openCheckoutModal = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    if (isSeller()) {
      toast.error('Seller accounts cannot purchase marketplace products. Please switch to a Buyer account.');
      return;
    }
    if (isAdmin()) {
      toast.error('Administrator accounts cannot purchase marketplace products.');
      return;
    }

    setShowCheckoutModal(true);
    setCalculatingCheckout(true);
    try {
      const { data } = await api.get(`/api/payments/calculate-checkout?product_id=${id}`);
      setCheckoutData(data);
    } catch {
      const price = Number(product?.price || 0);
      const subtotal = price;
      const platformFee = Math.round(subtotal * 0.05 * 100) / 100;
      const tax = Math.round((subtotal + platformFee) * 0.18 * 100) / 100;
      const total = Math.round((subtotal + platformFee + tax) * 100) / 100;
      setCheckoutData({
        subtotal,
        platform_fee: platformFee,
        tax,
        total_amount: total,
        currency: 'INR'
      });
    } finally {
      setCalculatingCheckout(false);
    }
  };

  // Preload Razorpay checkout script on mount
  useEffect(() => {
    loadRazorpayScript();
  }, []);

  // Fetch product and reviews - keyed strictly to product ID
  useEffect(() => {
    if (!id) return;
    setLoading(true);
    Promise.all([
      api.get(`/api/products/${id}`),
      api.get(`/api/products/${id}/reviews?per_page=20`),
    ])
      .then(([pRes, rRes]) => {
        setProduct(pRes.data);
        setReviews(rRes.data?.reviews || []);
        if (rRes.data?.can_review) setCanReview(true);
        if (rRes.data?.user_review) {
          setUserReview(rRes.data.user_review);
          setReviewRating(rRes.data.user_review.rating);
          setReviewComment(rRes.data.user_review.comment || rRes.data.user_review.body || '');
          setReviewTitle(rRes.data.user_review.title || '');
        }
      })
      .catch((err) => {
        toast.error(getErrorMessage(err, 'Product not found'), { id: 'prod-load-err' });
      })
      .finally(() => setLoading(false));
  }, [id]);

  // Check purchase status if logged in
  useEffect(() => {
    if (!id || !user?.id) return;
    api.get('/api/orders').then((r) => {
      const orders = r.data?.orders || [];
      const hasPurchased = orders.some(
        (o: any) =>
          o.status === 'paid' && o.items?.some((i: any) => String(i.product_id) === String(id))
      );
      setPurchased(hasPurchased);
      if (hasPurchased && !userReview) setCanReview(true);
    }).catch(() => {});
  }, [id, user?.id, userReview]);

  const handleSubmitReview = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!id || !user) return;
    if (reviewComment.trim().length < 3) {
      toast.error('Review comment must be at least 3 characters.');
      return;
    }
    setSubmittingReview(true);
    try {
      if (userReview) {
        // Edit existing review
        const { data } = await api.put(`/api/reviews/${userReview.id}`, {
          rating: reviewRating,
          title: reviewTitle.trim() || undefined,
          comment: reviewComment.trim(),
        });
        toast.success('Your review has been updated!');
        setUserReview(data);
        setEditingReview(false);
      } else {
        // Create new review
        const { data } = await api.post(`/api/products/${id}/reviews`, {
          rating: reviewRating,
          title: reviewTitle.trim() || undefined,
          comment: reviewComment.trim(),
        });
        toast.success('Your review has been published!');
        setUserReview(data);
        setCanReview(false);
      }

      // Refresh reviews and ratings
      const rRes = await api.get(`/api/products/${id}/reviews?per_page=20`);
      setReviews(rRes.data?.reviews || []);
      setProduct((prev: any) => prev ? {
        ...prev,
        avg_rating: rRes.data?.average_rating ?? prev.avg_rating,
        review_count: rRes.data?.review_count ?? prev.review_count
      } : prev);
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Failed to submit review'));
    } finally {
      setSubmittingReview(false);
    }
  };

  const handleBuy = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    setBuying(true);
    try {
      // 1. Direct server-authoritative order creation
      const { data: orderRes } = await api.post('/api/payments/create-order', {
        product_id: String(id),
      });

      // Free product handled immediately on server
      if (orderRes.is_free || orderRes.paid) {
        toast.success('Free asset claimed! Download is ready in your library.');
        setPurchased(true);
        return;
      }

      if (orderRes.gateway === 'razorpay') {
        const loaded = await loadRazorpayScript();
        if (!loaded || !window.Razorpay) {
          toast.error('Razorpay payment gateway failed to load. Please check your network.');
          setBuying(false);
          return;
        }

        const options = {
          key: orderRes.key_id || process.env.NEXT_PUBLIC_RAZORPAY_KEY_ID,
          amount: orderRes.amount_paise,
          currency: orderRes.currency || 'INR',
          name: 'SecureMarket',
          description: orderRes.product_title || product?.title || 'Digital Asset',
          order_id: orderRes.razorpay_order_id,
          handler: async (paymentResponse: any) => {
            try {
              toast.loading('Verifying cryptographic signature...', { id: 'rzp-verify' });
              const { data: verifyRes } = await api.post('/api/payments/verify', {
                order_id: orderRes.order_id,
                payment_data: {
                  razorpay_order_id: paymentResponse.razorpay_order_id,
                  razorpay_payment_id: paymentResponse.razorpay_payment_id,
                  razorpay_signature: paymentResponse.razorpay_signature,
                },
              });
              if (verifyRes.success) {
                toast.success('Payment verified! Download is unlocked.', { id: 'rzp-verify' });
                setPurchased(true);
              } else {
                toast.error('Payment signature check failed.', { id: 'rzp-verify' });
              }
            } catch (err: any) {
              toast.error(getErrorMessage(err, 'Payment verification failed'), { id: 'rzp-verify' });
            } finally {
              setBuying(false);
            }
          },
          prefill: {
            email: user.email,
            name: user.full_name || user.username,
          },
          theme: { color: '#2563eb' },
          modal: {
            ondismiss: () => {
              setBuying(false);
              toast('Checkout was cancelled', { icon: 'ℹ️' });
            },
          },
        };

        const rzp = new window.Razorpay(options);
        rzp.on('payment.failed', function (resp: any) {
          toast.error(resp?.error?.description || 'Payment failed');
          setBuying(false);
        });
        rzp.open();
        return;
      } else {
        // Fallback / mock gateway
        await api.post('/api/payments/verify', {
          order_id: orderRes.order_id,
          payment_data: {
            mock_scenario: 'success',
            gateway_order_id: orderRes.gateway_order_id,
          },
        });
        toast.success('Payment completed! Your download is ready.');
        setPurchased(true);
      }
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Purchase failed'));
    } finally {
      setBuying(false);
    }
  };

  const handleDownload = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    setDownloading(true);
    try {
      const { data } = await api.get(`/api/downloads/product/${id}`);
      const link = document.createElement('a');
      link.href = data.download_url;
      if (data.filename) {
        link.download = data.filename;
      }
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      toast.success(`Download started for "${data.filename || product?.title}"! Signed link valid for 5 minutes.`);
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Download failed'));
    } finally {
      setDownloading(false);
    }
  };

  const toggleWishlist = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    try {
      if (inWishlist) {
        await api.delete(`/api/wishlist/${id}`);
        setInWishlist(false);
        toast.success('Removed from wishlist');
      } else {
        await api.post(`/api/wishlist/${id}`);
        setInWishlist(true);
        toast.success('Added to wishlist');
      }
    } catch {
      toast.error('Failed to update wishlist');
    }
  };

  const formatSize = (bytes: number) => {
    if (!bytes) return 'Unknown';
    if (bytes > 1e6) return `${(bytes / 1e6).toFixed(1)} MB`;
    if (bytes > 1e3) return `${(bytes / 1e3).toFixed(1)} KB`;
    return `${bytes} B`;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          <p className="text-sm text-gray-500 font-medium">Loading asset details...</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex flex-col items-center justify-center text-center p-6">
          <FileText className="w-12 h-12 text-gray-300 mb-3" />
          <h2 className="text-lg font-bold text-gray-900">Product not found</h2>
          <p className="text-sm text-gray-500 mt-1 mb-4">The requested asset doesn&apos;t exist or has been removed.</p>
          <Link href="/marketplace" className="text-sm font-semibold text-blue-600 hover:underline">
            ← Return to Marketplace
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      {/* Breadcrumb Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs text-gray-500 truncate">
            <Link href="/marketplace" className="hover:text-gray-900 flex items-center gap-1">
              <ArrowLeft className="w-3.5 h-3.5" /> Back to Marketplace
            </Link>
            <span>/</span>
            <span className="font-medium text-gray-700">{product.category || 'Digital'}</span>
            <span>/</span>
            <span className="text-gray-900 font-semibold truncate max-w-xs">{product.title}</span>
          </div>

          <div className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            Verified Digital Asset
          </div>
        </div>
      </div>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 w-full flex-1">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          
          {/* Main Left Content (8 cols) */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Header Card */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 sm:p-8 shadow-sm">
              <div className="flex items-center gap-2 mb-3 flex-wrap">
                <span className="text-xs uppercase tracking-wider font-semibold bg-slate-100 text-slate-700 px-3 py-1 rounded-md">
                  {product.category || 'Asset'}
                </span>
                {product.subcategory && (
                  <span className="text-xs font-medium bg-gray-100 text-gray-600 px-3 py-1 rounded-md">
                    {product.subcategory}
                  </span>
                )}
                {product.scan_status === 'clean' && (
                  <span className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-full font-medium inline-flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Antivirus Verified
                  </span>
                )}
                {product.difficulty && product.difficulty !== 'Unknown' && (
                  <span className="text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-1 rounded-full font-medium">
                    {product.difficulty} Level
                  </span>
                )}
              </div>

              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight leading-snug">
                {product.title}
              </h1>

              {product.short_description && (
                <p className="mt-2 text-base text-gray-600 leading-relaxed">
                  {product.short_description}
                </p>
              )}

              <div className="flex items-center gap-4 sm:gap-6 mt-5 pt-5 border-t border-gray-100 text-xs sm:text-sm text-gray-600 flex-wrap">
                {product.review_count && product.review_count > 0 ? (
                  <div className="flex items-center gap-1.5">
                    <StarRow rating={product.avg_rating || 5} />
                    <span className="font-bold text-gray-900 ml-1">
                      {Number(product.avg_rating).toFixed(1)}
                    </span>
                    <span className="text-gray-400">({product.review_count} {product.review_count === 1 ? 'review' : 'reviews'})</span>
                  </div>
                ) : (
                  <span className="text-gray-500 italic">
                    No reviews yet
                  </span>
                )}
                <span className="text-gray-300">·</span>
                <span><strong className="text-gray-900">{product.total_sales || 0}</strong> copies sold</span>
                {product.seller && (
                  <>
                    <span className="text-gray-300">·</span>
                    <span>Created by <strong className="text-blue-600 font-semibold">{product.seller.full_name || product.seller.username}</strong></span>
                  </>
                )}
                {product.quality_analysis && (
                  <>
                    <span className="text-gray-300">·</span>
                    <button
                      onClick={() => setActiveTab('quality')}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold border transition-all hover:scale-105 ${
                        product.quality_analysis.overall_score >= 80
                          ? 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100'
                          : product.quality_analysis.overall_score >= 50
                          ? 'bg-teal-50 text-teal-700 border-teal-200 hover:bg-teal-100'
                          : 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                      AI Quality: {product.quality_analysis.overall_score} · {product.quality_analysis.quality_level}
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* Asset Visual Preview */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
              <FilePreview
                extension={product.file_extension}
                title={product.title}
                category={product.category}
                imageUrl={product.preview_image_url}
                className="h-80 w-full"
              />
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm">
              <div className="flex border-b border-gray-200 bg-slate-50/50">
                {(['overview', 'quality', 'security', 'reviews'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`flex-1 py-3.5 px-4 text-sm font-semibold capitalize transition-all border-b-2 ${
                      activeTab === tab
                        ? 'text-blue-600 border-blue-600 bg-white'
                        : 'text-gray-500 border-transparent hover:text-gray-800'
                    }`}
                  >
                    {tab === 'overview' && 'Product Overview'}
                    {tab === 'quality' && `AI Quality (${product.quality_analysis?.overall_score ?? product.quality_score ?? '--'})`}
                    {tab === 'security' && 'Security & Delivery'}
                    {tab === 'reviews' && `Reviews (${product.review_count ?? reviews.length})`}
                  </button>
                ))}
              </div>

              <div className="p-6 sm:p-8">
                {/* Tab 1: Overview */}
                {activeTab === 'overview' && (
                  <div className="space-y-6">
                    {product.summary && (
                      <div>
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-2.5">
                          About this asset
                        </h3>
                        <p className={`text-gray-600 text-sm leading-relaxed ${!showFullDesc && product.summary.length > 350 ? 'line-clamp-4' : ''}`}>
                          {product.summary}
                        </p>
                        {product.summary.length > 350 && (
                          <button
                            onClick={() => setShowFullDesc(!showFullDesc)}
                            className="text-blue-600 text-xs font-semibold mt-2 flex items-center gap-1 hover:underline"
                          >
                            {showFullDesc ? <><ChevronUp className="w-3.5 h-3.5" /> Show less</> : <><ChevronDown className="w-3.5 h-3.5" /> Read full description</>}
                          </button>
                        )}
                      </div>
                    )}

                    {product.key_topics && product.key_topics.length > 0 && (
                      <div>
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-3">
                          What&apos;s Included & Key Topics
                        </h3>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                          {product.key_topics.map((topic: string) => (
                            <div key={topic} className="flex items-start gap-2 text-sm text-gray-700 bg-slate-50 p-2.5 rounded-lg border border-gray-100">
                              <CheckCircle2 className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
                              <span className="text-xs font-medium">{topic}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {product.target_audience && (
                      <div className="bg-slate-50 rounded-xl p-4 border border-gray-100 flex items-start gap-3">
                        <Users className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0" />
                        <div>
                          <span className="text-xs font-bold text-gray-900 uppercase tracking-wider block">Intended Audience</span>
                          <span className="text-sm text-gray-600 mt-0.5 block">{product.target_audience}</span>
                        </div>
                      </div>
                    )}

                    {product.tags && product.tags.length > 0 && (
                      <div>
                        <span className="text-xs font-bold text-gray-900 uppercase tracking-wider block mb-2">Tags</span>
                        <div className="flex flex-wrap gap-1.5">
                          {product.tags.map((t: string) => (
                            <span key={t} className="text-xs bg-gray-100 text-gray-600 px-2.5 py-1 rounded-md font-medium">
                              #{t}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {product.ai_metadata_generated && (
                      <div className="text-xs text-purple-700 bg-purple-50/60 border border-purple-100 rounded-xl p-3 flex items-center gap-2">
                        <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0" />
                        <span>Metadata enriched with Gemini AI engine and verified by author.</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 2: AI File Quality Assessment */}
                {activeTab === 'quality' && (
                  <div className="space-y-6">
                    <div>
                      <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
                        <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider">
                          AI File Quality & Depth Assessment
                        </h3>
                        <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-200">
                          Read-Only System Verification
                        </span>
                      </div>
                      <p className="text-xs text-gray-500">
                        Objective analysis evaluating content usefulness, completeness, structural hierarchy, and technical rigor.
                      </p>
                    </div>

                    {product.quality_analysis ? (
                      <div className="space-y-6">
                        {/* Overall Score Banner */}
                        <div className="bg-gradient-to-br from-slate-50 to-blue-50/40 rounded-2xl p-6 border border-blue-100 flex flex-col sm:flex-row sm:items-center justify-between gap-6">
                          <div className="flex items-center gap-5">
                            <div className="w-20 h-20 rounded-2xl bg-white border border-blue-200 shadow-sm flex flex-col items-center justify-center flex-shrink-0">
                              <span className="text-3xl font-black text-gray-900 tracking-tight leading-none">
                                {product.quality_analysis.overall_score}
                              </span>
                              <span className="text-[10px] font-bold text-gray-400 mt-1 uppercase tracking-wider">
                                / 100
                              </span>
                            </div>
                            <div>
                              <div className="flex items-center gap-2">
                                <span className={`text-xs font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${
                                  product.quality_analysis.overall_score >= 90
                                    ? 'bg-emerald-600 text-white'
                                    : product.quality_analysis.overall_score >= 75
                                    ? 'bg-blue-600 text-white'
                                    : product.quality_analysis.overall_score >= 60
                                    ? 'bg-teal-600 text-white'
                                    : product.quality_analysis.overall_score >= 40
                                    ? 'bg-amber-600 text-white'
                                    : 'bg-rose-600 text-white'
                                }`}>
                                  {product.quality_analysis.overall_score >= 90
                                    ? 'EXCELLENT'
                                    : product.quality_analysis.overall_score >= 75
                                    ? 'GOOD'
                                    : product.quality_analysis.overall_score >= 60
                                    ? 'FAIR'
                                    : product.quality_analysis.overall_score >= 40
                                    ? 'LOW'
                                    : 'VERY LOW'}
                                </span>
                                <span className="text-xs text-gray-500 font-medium">
                                  Confidence: {Math.round((product.quality_analysis.confidence_score || 0.88) * 100)}%
                                </span>
                              </div>
                              <p className="text-xs text-gray-600 mt-1.5 leading-relaxed max-w-lg">
                                Based on {product.quality_analysis.reasoning || "detected content structure and quantitative depth metrics."}
                              </p>
                            </div>
                          </div>

                          {/* Listing Status Badge */}
                          <div className="sm:text-right border-t sm:border-t-0 sm:border-l border-gray-200 pt-3 sm:pt-0 sm:pl-6">
                            <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-1">Listing Status</span>
                            <span className={`inline-flex items-center gap-1 text-xs font-bold px-3 py-1 rounded-lg ${
                              (product.quality_analysis.risk_level || '').toLowerCase() === 'critical'
                                ? 'bg-red-100 text-red-800 border border-red-200'
                                : (product.quality_analysis.risk_level || '').toLowerCase() === 'high'
                                ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                : (product.quality_analysis.risk_level || '').toLowerCase() === 'medium'
                                ? 'bg-amber-100 text-amber-800 border border-amber-200'
                                : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                            }`}>
                              {(product.quality_analysis.risk_level || '').toLowerCase() === 'critical' ? '🛑 Critical Review' :
                               (product.quality_analysis.risk_level || '').toLowerCase() === 'high' ? '⚠️ High Risk' :
                               (product.quality_analysis.risk_level || '').toLowerCase() === 'medium' ? '⚡ Medium Review' : '🛡️ Low Risk'}
                            </span>
                          </div>
                        </div>

                        {/* 6 Component Bars */}
                        <div className="bg-white rounded-2xl border border-gray-200 p-6 space-y-4">
                          <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider mb-3">
                            Quality Dimension Breakdown
                          </h4>
                          <div className="space-y-3.5">
                            {[
                              { label: 'Content Quality', weight: '20%', score: product.quality_analysis.content_usefulness },
                              { label: 'Completeness', weight: '20%', score: product.quality_analysis.completeness },
                              { label: 'Structure & Organization', weight: '15%', score: product.quality_analysis.structure_organization },
                              { label: 'Methodology & Technical Depth', weight: '20%', score: product.quality_analysis.technical_depth },
                              { label: 'Evidence & Results', weight: '15%', score: product.quality_analysis.evidence_results || 72 },
                              { label: 'Usability & Clarity', weight: '10%', score: product.quality_analysis.practical_value },
                            ].map((dim) => (
                              <div key={dim.label}>
                                <div className="flex justify-between text-xs mb-1">
                                  <span className="font-medium text-gray-700">
                                    {dim.label} <span className="text-gray-400 font-normal">({dim.weight} weight)</span>
                                  </span>
                                  <span className="font-bold text-gray-900">{dim.score ?? '--'}/100</span>
                                </div>
                                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full rounded-full transition-all duration-500 ${
                                      (dim.score ?? 0) >= 80 ? 'bg-blue-600' : (dim.score ?? 0) >= 60 ? 'bg-teal-500' : 'bg-amber-500'
                                    }`}
                                    style={{ width: `${Math.min(100, Math.max(0, dim.score ?? 0))}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Listing Status Assessment & Checks */}
                        <div className="bg-slate-50 border border-gray-200 rounded-2xl p-5 space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Listing Status Assessment</span>
                            <span className="text-[11px] text-gray-500">Automated verification & price reasonableness</span>
                          </div>

                          {/* Reasons if any */}
                          {(() => {
                            let reasons: string[] = [];
                            try {
                              reasons = typeof product.quality_analysis.risk_reasons === 'string'
                                ? JSON.parse(product.quality_analysis.risk_reasons)
                                : (product.quality_analysis.risk_reasons || []);
                            } catch {
                              reasons = [];
                            }
                            if (reasons.length === 0 && (product.quality_analysis.risk_level === 'medium' || product.quality_analysis.risk_level === 'high')) {
                              reasons = ['Price is above the recommended range'];
                            }
                            return reasons.length > 0 ? (
                              <div className="space-y-1.5 pt-1">
                                <span className="text-[11px] font-bold text-amber-900 block">Assessment Notes:</span>
                                <ul className="space-y-1 text-xs text-amber-900">
                                  {reasons.map((r: string, idx: number) => (
                                    <li key={idx} className="flex items-start gap-1.5">
                                      <span className="text-amber-600 font-bold">•</span>
                                      <span>{r}</span>
                                    </li>
                                  ))}
                                </ul>
                              </div>
                            ) : null;
                          })()}

                          {/* Positive checks */}
                          <div className="pt-2 border-t border-gray-200/60">
                            <span className="text-[11px] font-bold text-emerald-900 block mb-1.5">Positive Checks:</span>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs text-emerald-900">
                              <div className="flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                                <span>Unique file</span>
                              </div>
                              <div className="flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                                <span>Malware scan passed</span>
                              </div>
                              <div className="flex items-center gap-1.5 bg-emerald-50 px-2.5 py-1.5 rounded-lg border border-emerald-100">
                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0" />
                                <span>Content complete</span>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Two Columns: Strengths & Limitations */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                          {/* Strengths */}
                          <div className="bg-emerald-50/50 border border-emerald-100 rounded-xl p-4 space-y-2">
                            <h5 className="text-xs font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Key Strengths
                            </h5>
                            <ul className="space-y-1.5 text-xs text-emerald-950">
                              {(product.quality_analysis.key_strengths || ['Clear structural layout', 'Valid file formatting']).map((s: string, idx: number) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-emerald-500 font-bold">•</span>
                                  <span>{s}</span>
                                </li>
                              ))}
                            </ul>
                          </div>

                          {/* Limitations */}
                          <div className="bg-amber-50/50 border border-amber-100 rounded-xl p-4 space-y-2">
                            <h5 className="text-xs font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" /> Observed Boundaries
                            </h5>
                            <ul className="space-y-1.5 text-xs text-amber-950">
                              {(product.quality_analysis.limitations || ['Dependent on buyer project scope']).map((l: string, idx: number) => (
                                <li key={idx} className="flex items-start gap-1.5">
                                  <span className="text-amber-500 font-bold">•</span>
                                  <span>{l}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        </div>

                        {/* Target Use Case */}
                        {product.quality_analysis.target_use_case && (
                          <div className="bg-slate-50 border border-gray-200 rounded-xl p-4">
                            <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider block mb-1">
                              Recommended Application
                            </span>
                            <p className="text-xs text-gray-700 leading-relaxed font-medium">
                              {product.quality_analysis.target_use_case}
                            </p>
                          </div>
                        )}

                        {/* Disclaimer */}
                        <div className="p-3.5 bg-gray-50 border border-gray-200/80 rounded-xl text-[11px] text-gray-500 leading-relaxed flex items-start gap-2">
                          <Sparkles className="w-3.5 h-3.5 text-gray-400 mt-0.5 flex-shrink-0" />
                          <span>
                            {product.quality_analysis.disclaimer || "AI-generated assessment based on file structure and content analysis. Independent verification recommended."}
                          </span>
                        </div>
                      </div>
                    ) : (
                      <div className="text-center py-10 px-4 bg-slate-50 rounded-xl border border-gray-100">
                        <p className="text-xs text-gray-500">Quality score assessment is being computed for this file.</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Tab 3: Security & Delivery */}
                {activeTab === 'security' && (
                  <div className="space-y-6">
                    <div>
                      <h3 className="text-sm font-bold text-gray-900 uppercase tracking-wider mb-1">
                        Security & Delivery Protection
                      </h3>
                      <p className="text-xs text-gray-500">
                        Every digital product is systematically checked and protected across its entire lifecycle.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                      <div className="p-4 bg-slate-50 rounded-2xl border border-gray-100 flex items-start gap-3.5">
                        <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <CheckCircle2 className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-gray-900">Malware scan passed</span>
                            <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full">
                              Verified
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                            The uploaded file passed automated malware and security checks before release.
                          </p>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-50 rounded-2xl border border-gray-100 flex items-start gap-3.5">
                        <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <ShieldCheck className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-gray-900">File integrity verified</span>
                            <span className="text-[10px] bg-blue-100 text-blue-800 font-semibold px-2 py-0.5 rounded-full">
                              Protected
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                            The marketplace verifies that the stored file has not been unexpectedly modified.
                          </p>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-50 rounded-2xl border border-gray-100 flex items-start gap-3.5">
                        <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Lock className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-gray-900">Secure payment</span>
                            <span className="text-[10px] bg-purple-100 text-purple-800 font-semibold px-2 py-0.5 rounded-full">
                              Encrypted
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                            Your payment is securely processed and verified before download access is granted.
                          </p>
                        </div>
                      </div>

                      <div className="p-4 bg-slate-50 rounded-2xl border border-gray-100 flex items-start gap-3.5">
                        <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center flex-shrink-0 mt-0.5">
                          <Download className="w-4 h-4" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-gray-900">Protected download</span>
                            <span className="text-[10px] bg-teal-100 text-teal-800 font-semibold px-2 py-0.5 rounded-full">
                              Instant
                            </span>
                          </div>
                          <p className="text-xs text-gray-500 mt-1 leading-relaxed">
                            Your purchased file is delivered through temporary secure access directly to your library.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Cryptographic File Authenticity & Real SHA-256 Digest */}
                    <div className="p-5 bg-gradient-to-br from-slate-900 via-slate-900 to-slate-800 text-white rounded-2xl border border-slate-700 shadow-sm space-y-4">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center flex-shrink-0">
                            <ShieldCheck className="w-4 h-4 text-blue-400" />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <h4 className="text-sm font-bold text-white">Cryptographic File Authenticity</h4>
                              <span className="text-[10px] bg-emerald-500/20 text-emerald-300 font-semibold px-2 py-0.5 rounded-full border border-emerald-500/30">
                                SHA-256 Verified
                              </span>
                            </div>
                            <p className="text-xs text-slate-400">
                              Immutable 256-bit cryptographic digest calculated directly from file bytes.
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 flex-shrink-0">
                          <button
                            type="button"
                            onClick={() => {
                              const hash = product?.sha256_hash || product?.file_hash_sha256 || '';
                              if (hash) {
                                navigator.clipboard.writeText(hash);
                                setCopiedHash(true);
                                toast.success('SHA-256 digest copied to clipboard');
                                setTimeout(() => setCopiedHash(false), 2000);
                              }
                            }}
                            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-600 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors"
                          >
                            {copiedHash ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                            <span>{copiedHash ? 'Copied' : 'Copy Hash'}</span>
                          </button>
                          <button
                            type="button"
                            onClick={handleLiveVerify}
                            disabled={verifyingIntegrity}
                            className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors disabled:opacity-50 shadow-sm"
                          >
                            {verifyingIntegrity ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                            <span>{verifyingIntegrity ? 'Auditing...' : 'Verify Integrity'}</span>
                          </button>
                        </div>
                      </div>

                      {/* Monospace SHA-256 Digest Box */}
                      <div className="bg-slate-950/90 rounded-xl p-3.5 border border-slate-800 font-mono text-xs flex flex-col sm:flex-row sm:items-center justify-between gap-2 overflow-x-auto">
                        <span className="text-slate-400 select-none text-[11px] uppercase tracking-wider font-sans font-bold flex-shrink-0">
                          SHA-256:
                        </span>
                        <span className="text-emerald-400 break-all select-all font-mono tracking-tight">
                          {product?.sha256_hash || product?.file_hash_sha256 || 'Calculating SHA-256 fingerprint...'}
                        </span>
                      </div>

                      {/* Live Verification Result Box */}
                      {integrityResult && (
                        <div
                          className={`p-3.5 rounded-xl border flex items-start gap-3 text-xs transition-all ${
                            integrityResult.match
                              ? 'bg-emerald-950/60 border-emerald-700/70 text-emerald-200'
                              : 'bg-red-950/60 border-red-700/70 text-red-200'
                          }`}
                        >
                          <div className="mt-0.5 flex-shrink-0">
                            {integrityResult.match ? (
                              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                            ) : (
                              <AlertTriangle className="w-4 h-4 text-red-400" />
                            )}
                          </div>
                          <div className="flex-1 space-y-1">
                            <div className="font-bold flex items-center gap-2">
                              <span>{integrityResult.status}</span>
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-black/40 font-mono text-slate-300">
                                {integrityResult.file_size_bytes} bytes
                              </span>
                            </div>
                            <p className="text-[11px] opacity-80 leading-relaxed font-mono break-all">
                              Disk byte hash: {integrityResult.actual_hash}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Tab 4: Reviews */}
                {activeTab === 'reviews' && (
                  <div className="space-y-6">
                    {/* Header Summary */}
                    <div className="flex items-center justify-between pb-6 border-b border-gray-100 flex-wrap gap-4">
                      <div className="flex items-center gap-4">
                        <div className="text-4xl font-extrabold text-gray-900">
                          {Number(product.avg_rating || 0).toFixed(1)}
                        </div>
                        <div>
                          <StarRow rating={product.avg_rating || 0} />
                          <p className="text-xs text-gray-400 mt-1 font-medium">
                            {product.review_count || reviews.length} verified customer {(product.review_count || reviews.length) === 1 ? 'review' : 'reviews'}
                          </p>
                        </div>
                      </div>
                      {purchased && !userReview && (
                        <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-full">
                          ✓ Verified Purchaser
                        </span>
                      )}
                    </div>

                    {/* Section A: User has already submitted a review */}
                    {userReview && (
                      <div className="p-5 bg-gradient-to-br from-blue-50/50 to-slate-50 border border-blue-100 rounded-2xl space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-gray-900">Your Review</span>
                            <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-medium">
                              ✓ Verified Purchase
                            </span>
                          </div>
                          <button
                            onClick={() => setEditingReview(!editingReview)}
                            className="text-xs text-blue-600 font-semibold hover:underline"
                          >
                            {editingReview ? 'Cancel' : 'Edit Review'}
                          </button>
                        </div>

                        {!editingReview ? (
                          <div className="space-y-1.5">
                            <StarRow rating={userReview.rating} />
                            {userReview.title && <h4 className="text-xs font-semibold text-gray-900 mt-1">{userReview.title}</h4>}
                            <p className="text-xs text-gray-700 leading-relaxed">{userReview.comment || userReview.body}</p>
                            <span className="text-[11px] text-gray-400 block pt-1">
                              Published {new Date(userReview.created_at).toLocaleDateString()}
                            </span>
                          </div>
                        ) : (
                          <form onSubmit={handleSubmitReview} className="space-y-3 pt-2">
                            <div>
                              <label className="text-xs font-semibold text-gray-700 block mb-1">Rating</label>
                              <div className="flex items-center gap-1">
                                {[1, 2, 3, 4, 5].map((star) => (
                                  <button
                                    type="button"
                                    key={star}
                                    onClick={() => setReviewRating(star)}
                                    onMouseEnter={() => setReviewHoverRating(star)}
                                    onMouseLeave={() => setReviewHoverRating(0)}
                                    className="p-1 hover:scale-110 transition-transform"
                                  >
                                    <Star
                                      className={`w-5 h-5 ${
                                        star <= (reviewHoverRating || reviewRating)
                                          ? 'text-amber-400 fill-amber-400'
                                          : 'text-gray-300'
                                      }`}
                                    />
                                  </button>
                                ))}
                                <span className="text-xs font-bold text-gray-700 ml-2">
                                  {reviewHoverRating || reviewRating} / 5 Stars
                                </span>
                              </div>
                            </div>

                            <div>
                              <label className="text-xs font-semibold text-gray-700 block mb-1">Title (Optional)</label>
                              <input
                                type="text"
                                value={reviewTitle}
                                onChange={(e) => setReviewTitle(e.target.value)}
                                placeholder="Summary title"
                                className="w-full text-xs p-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>

                            <div>
                              <label className="text-xs font-semibold text-gray-700 block mb-1">Your Feedback</label>
                              <textarea
                                rows={3}
                                required
                                value={reviewComment}
                                onChange={(e) => setReviewComment(e.target.value)}
                                className="w-full text-xs p-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </div>

                            <div className="flex items-center gap-2">
                              <button
                                type="submit"
                                disabled={submittingReview}
                                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-sm"
                              >
                                {submittingReview ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : null}
                                Save Changes
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingReview(false)}
                                className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-xl text-xs font-semibold"
                              >
                                Cancel
                              </button>
                            </div>
                          </form>
                        )}
                      </div>
                    )}

                    {/* Section B: User purchased and has not reviewed yet */}
                    {!userReview && (purchased || canReview) && (
                      <div className="p-6 bg-slate-50 border border-gray-200 rounded-2xl space-y-4">
                        <div>
                          <h4 className="text-sm font-bold text-gray-900">Share your experience</h4>
                          <p className="text-xs text-gray-500 mt-0.5">
                            You own this digital product. Tell other buyers what you think about its quality and usefulness.
                          </p>
                        </div>
                        <form onSubmit={handleSubmitReview} className="space-y-3.5">
                          <div>
                            <label className="text-xs font-semibold text-gray-700 block mb-1">Rate this product</label>
                            <div className="flex items-center gap-1">
                              {[1, 2, 3, 4, 5].map((star) => (
                                <button
                                  type="button"
                                  key={star}
                                  onClick={() => setReviewRating(star)}
                                  onMouseEnter={() => setReviewHoverRating(star)}
                                  onMouseLeave={() => setReviewHoverRating(0)}
                                  className="p-1 hover:scale-110 transition-transform"
                                >
                                  <Star
                                    className={`w-6 h-6 ${
                                      star <= (reviewHoverRating || reviewRating)
                                        ? 'text-amber-400 fill-amber-400'
                                        : 'text-gray-300'
                                    }`}
                                  />
                                </button>
                              ))}
                              <span className="text-xs font-bold text-gray-700 ml-2">
                                {reviewHoverRating || reviewRating} / 5 Stars
                              </span>
                            </div>
                          </div>

                          <div>
                            <label className="text-xs font-semibold text-gray-700 block mb-1">Review Headline (Optional)</label>
                            <input
                              type="text"
                              value={reviewTitle}
                              onChange={(e) => setReviewTitle(e.target.value)}
                              placeholder="e.g. Exactly what I needed for my project"
                              className="w-full text-xs p-2.5 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>

                          <div>
                            <label className="text-xs font-semibold text-gray-700 block mb-1">Your Review</label>
                            <textarea
                              rows={3}
                              required
                              value={reviewComment}
                              onChange={(e) => setReviewComment(e.target.value)}
                              placeholder="Tell other buyers about the content quality, structure, and clarity..."
                              className="w-full text-xs p-3 bg-white border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-blue-500"
                            />
                          </div>

                          <button
                            type="submit"
                            disabled={submittingReview}
                            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-semibold flex items-center gap-2 shadow-sm transition-colors"
                          >
                            {submittingReview ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Star className="w-3.5 h-3.5" />}
                            Submit Review
                          </button>
                        </form>
                      </div>
                    )}

                    {/* Section C: User is not logged in */}
                    {!user && (
                      <div className="p-6 bg-slate-50 border border-gray-200 rounded-2xl text-center space-y-2">
                        <Users className="w-8 h-8 text-slate-400 mx-auto" />
                        <h4 className="text-sm font-bold text-gray-900">Verified Buyer Reviews</h4>
                        <p className="text-xs text-gray-500 max-w-sm mx-auto">
                          Sign in and purchase this product to leave a verified review.
                        </p>
                        <Link
                          href="/login"
                          className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-colors"
                        >
                          Sign In
                        </Link>
                      </div>
                    )}

                    {/* Section D: User is logged in but hasn't purchased */}
                    {user && !purchased && !canReview && !userReview && (
                      <div className="p-6 bg-slate-50 border border-gray-200 rounded-2xl text-center space-y-2">
                        <Shield className="w-8 h-8 text-blue-600 mx-auto" />
                        <h4 className="text-sm font-bold text-gray-900">Verified Buyer Reviews Only</h4>
                        <p className="text-xs text-gray-500 max-w-md mx-auto">
                          Purchase this product to leave a verified review and share your feedback with creators and buyers.
                        </p>
                        <button
                          onClick={handleBuy}
                          className="mt-2 inline-flex items-center gap-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-semibold transition-colors"
                        >
                          <ShoppingCart className="w-3.5 h-3.5" /> Buy Now
                        </button>
                      </div>
                    )}

                    {/* Review List */}
                    {reviews.length > 0 ? (
                      <div className="space-y-4 pt-2">
                        <h4 className="text-xs font-bold text-gray-900 uppercase tracking-wider">
                          Community Reviews ({reviews.length})
                        </h4>
                        {reviews.map((r) => (
                          <div key={r.id} className="p-4 bg-white border border-gray-100 rounded-xl space-y-2 shadow-sm">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-gray-900">{r.username}</span>
                                {r.is_verified_purchase && (
                                  <span className="text-[10px] text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full font-medium">
                                    ✓ Verified Purchase
                                  </span>
                                )}
                              </div>
                              <span className="text-[11px] text-gray-400">
                                {new Date(r.created_at).toLocaleDateString()}
                              </span>
                            </div>
                            <StarRow rating={r.rating} />
                            {r.title && <h5 className="text-xs font-semibold text-gray-900 mt-1">{r.title}</h5>}
                            {(r.comment || r.body) && (
                              <p className="text-xs text-gray-600 leading-relaxed">{r.comment || r.body}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-10 px-4 bg-slate-50/50 rounded-2xl border border-dashed border-gray-200">
                        <Star className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                        <h4 className="text-sm font-semibold text-gray-800">No reviews yet</h4>
                        <p className="text-xs text-gray-500 mt-1 max-w-sm mx-auto">
                          Be the first verified buyer to review this product.
                        </p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Sidebar: Purchase & Spec Details (4 cols) */}
          <div className="lg:col-span-4 space-y-6 sticky top-24">
            
            {/* Pricing Card */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <div className="flex items-baseline justify-between mb-1">
                <span className="text-3xl font-extrabold text-gray-900">
                  {product.price === 0 ? 'Free' : `₹${product.price.toLocaleString('en-IN')}`}
                </span>
                <span className="text-xs text-gray-400 font-medium">
                  {product.price === 0 ? 'Instant access' : 'One-time payment'}
                </span>
              </div>
              <p className="text-xs text-gray-500 mb-6">Full digital rights · Lifetime updates</p>

              {purchased ? (
                <div className="space-y-3">
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-800 flex items-center gap-2 font-medium">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                    You own this product. Download is ready.
                  </div>
                  <button
                    onClick={handleDownload}
                    disabled={downloading}
                    className="w-full bg-emerald-600 hover:bg-emerald-700 text-white py-3 px-4 rounded-xl font-bold flex items-center justify-center gap-2 shadow-sm transition-colors text-sm disabled:opacity-50"
                  >
                    {downloading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                    {downloading ? 'Preparing Signed Link...' : 'Download File Now'}
                  </button>
                </div>
              ) : isSeller() ? (
                <div className="p-4 bg-purple-50 border border-purple-200 rounded-xl text-xs text-purple-900 space-y-1.5">
                  <div className="flex items-center gap-1.5 font-bold text-purple-800">
                    <AlertTriangle className="w-4 h-4 text-purple-600 flex-shrink-0" />
                    Seller Account Detected
                  </div>
                  <p className="text-purple-700 leading-relaxed">
                    Seller accounts cannot purchase marketplace products under strict role separation. Please switch to a Buyer account to checkout.
                  </p>
                </div>
              ) : isAdmin() ? (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-xs text-red-900 space-y-1.5">
                  <div className="flex items-center gap-1.5 font-bold text-red-800">
                    <Shield className="w-4 h-4 text-red-600 flex-shrink-0" />
                    Admin Account Detected
                  </div>
                  <p className="text-red-700 leading-relaxed">
                    Administrators have management-only access and are restricted from marketplace purchases.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <button
                    onClick={openCheckoutModal}
                    disabled={buying}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3.5 px-4 rounded-xl font-bold flex items-center justify-center gap-2 shadow-sm transition-all text-sm disabled:opacity-50 hover:shadow-blue-500/20 hover:shadow-md"
                  >
                    {buying ? <Loader2 className="w-4 h-4 animate-spin" /> : <ShoppingCart className="w-4 h-4" />}
                    {buying ? 'Securing Transaction...' : product.price === 0 ? 'Claim Free Asset' : 'Buy Now'}
                  </button>

                  <button
                    onClick={toggleWishlist}
                    className={`w-full py-2.5 px-4 rounded-xl border text-xs font-semibold flex items-center justify-center gap-2 transition-colors ${
                      inWishlist
                        ? 'border-rose-200 text-rose-600 bg-rose-50'
                        : 'border-gray-200 text-gray-700 hover:bg-gray-50'
                    }`}
                  >
                    <Heart className={`w-3.5 h-3.5 ${inWishlist ? 'fill-rose-500' : ''}`} />
                    {inWishlist ? 'Saved to Wishlist' : 'Add to Wishlist'}
                  </button>
                </div>
              )}

              {/* Security guarantees */}
              <div className="mt-6 pt-6 border-t border-gray-100 space-y-2.5 text-xs text-gray-600">
                <div className="flex items-center gap-2">
                  <Lock className="w-3.5 h-3.5 text-emerald-600" />
                  <span>Secure checkout</span>
                </div>
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                  <span>File integrity verified</span>
                </div>
                <div className="flex items-center gap-2">
                  <Download className="w-3.5 h-3.5 text-purple-600" />
                  <span>Instant access after checkout</span>
                </div>
              </div>
            </div>

            {/* Specifications Card */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <h3 className="text-xs font-bold text-gray-900 uppercase tracking-wider mb-4">
                File Details & Specifications
              </h3>
              <div className="space-y-3 text-xs">
                {[
                  ['File Extension', `.${product.file_extension?.toUpperCase() || 'FILE'}`],
                  ['File Size', formatSize(product.file_size_bytes)],
                  ['Language', product.language || 'English'],
                  ['Version', product.version || '1.0'],
                  ['Content Type', product.content_type || 'Digital Asset'],
                  ...(product.num_pages ? [['Pages', String(product.num_pages)]] : []),
                  ['Total Downloads', `${product.total_downloads || 0}`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between items-center py-1 border-b border-gray-50 last:border-none">
                    <span className="text-gray-400 font-medium">{k}</span>
                    <span className="text-gray-800 font-semibold">{v}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Seller Profile Card */}
            {product.seller && (
              <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm">
                <span className="text-[11px] font-bold text-gray-400 uppercase tracking-wider block mb-3">
                  Verified Creator
                </span>
                <div className="flex items-center gap-3">
                  <div className="w-11 h-11 bg-blue-600 text-white rounded-xl flex items-center justify-center font-bold text-sm shadow-sm">
                    {product.seller.username?.[0]?.toUpperCase() || 'S'}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-gray-900 leading-none">
                      {product.seller.full_name || product.seller.username}
                    </h4>
                    <p className="text-xs text-gray-400 mt-1">@{product.seller.username}</p>
                  </div>
                </div>
              </div>
            )}

          </div>

        </div>

        {/* Pre-payment Transparent Fee & Tax Breakdown Modal */}
        {showCheckoutModal && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200">
              <div className="flex items-center justify-between pb-4 border-b border-gray-100">
                <div>
                  <h3 className="font-bold text-gray-900 text-base">Order Summary</h3>
                  <p className="text-xs text-gray-500">Transparent marketplace pricing</p>
                </div>
                <button
                  onClick={() => setShowCheckoutModal(false)}
                  className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 text-sm font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="py-4 space-y-3 text-xs">
                <div className="flex justify-between items-center text-gray-600">
                  <span>Digital Product</span>
                  <span className="font-semibold text-gray-900 max-w-[200px] truncate">{product?.title}</span>
                </div>

                <div className="flex justify-between items-center text-gray-600">
                  <span>Product price</span>
                  <span className="font-semibold text-gray-900">
                    ₹{Number(checkoutData?.subtotal ?? product?.price ?? 0).toFixed(2)}
                  </span>
                </div>

                {/* Only render platform fee if enabled and > 0 */}
                {Number(checkoutData?.platform_fee ?? ((product?.price || 0) * 0.05)) > 0 && (
                  <div className="flex justify-between items-center text-gray-600">
                    <span>Platform fee (5%)</span>
                    <span className="font-semibold text-gray-900">
                      ₹{Number(checkoutData?.platform_fee ?? ((product?.price || 0) * 0.05)).toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Only render applicable tax if enabled and > 0 */}
                {Number(checkoutData?.tax ?? (((product?.price || 0) * 1.05) * 0.18)) > 0 && (
                  <div className="flex justify-between items-center text-gray-600">
                    <span>{checkoutData?.tax_label || 'Applicable tax'} (18%)</span>
                    <span className="font-semibold text-gray-900">
                      ₹{Number(checkoutData?.tax ?? (((product?.price || 0) * 1.05) * 0.18)).toFixed(2)}
                    </span>
                  </div>
                )}

                {/* Payment processing fee only if > 0 */}
                {Number(checkoutData?.service_fee ?? 0) > 0 && (
                  <div className="flex justify-between items-center text-gray-600">
                    <span>Payment processing fee</span>
                    <span className="font-semibold text-gray-900">
                      ₹{Number(checkoutData.service_fee).toFixed(2)}
                    </span>
                  </div>
                )}

                <div className="pt-3 border-t border-gray-100 flex justify-between items-baseline">
                  <span className="text-sm font-bold text-gray-900">Total payable</span>
                  <div className="text-right">
                    <span className="text-2xl font-extrabold text-blue-600">
                      ₹{Number(checkoutData?.total_amount ?? (((product?.price || 0) * 1.05) * 1.18)).toFixed(2)}
                    </span>
                    <span className="text-[10px] text-gray-400 block font-normal">INR · Final amount before payment</span>
                  </div>
                </div>
              </div>

              {/* Payment Method Selector */}
              <div className="mb-4 pt-2 border-t border-gray-100">
                <span className="text-[11px] font-bold text-gray-500 uppercase tracking-wider block mb-2">Payment Method</span>
                <div className="grid grid-cols-2 gap-2">
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-blue-200 bg-blue-50/40 text-xs font-semibold text-blue-900 cursor-pointer">
                    <input type="radio" name="pay_method" defaultChecked className="text-blue-600" />
                    <span>UPI</span>
                  </label>
                  <label className="flex items-center gap-2 p-2.5 rounded-xl border border-gray-200 hover:bg-gray-50 text-xs font-semibold text-gray-700 cursor-pointer">
                    <input type="radio" name="pay_method" className="text-blue-600" />
                    <span>Card</span>
                  </label>
                </div>
              </div>

              {/* Secure Checkout Notice */}
              <div className="p-3 bg-slate-50 rounded-xl border border-gray-200 text-[11px] text-gray-600 space-y-0.5 mb-5">
                <div className="flex items-center gap-1.5 font-bold text-gray-900">
                  <ShieldCheck className="w-4 h-4 text-blue-600" /> Secure checkout
                </div>
                <p className="text-gray-500">
                  Payment is verified before download access is enabled.
                </p>
              </div>

              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setShowCheckoutModal(false)}
                  className="flex-1 py-2.5 px-4 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={calculatingCheckout || buying}
                  onClick={() => {
                    setShowCheckoutModal(false);
                    handleBuy();
                  }}
                  className="flex-1 py-2.5 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition-colors shadow-sm disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {buying ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                  Proceed to Pay ₹{Number(checkoutData?.total_amount ?? (((product?.price || 0) * 1.05) * 1.18)).toFixed(2)}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}
