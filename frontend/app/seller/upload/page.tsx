'use client';
import { useState, useRef, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api, { getErrorMessage } from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import {
  UploadCloud, CheckCircle2, AlertCircle, Loader2, FileText, 
  Sparkles, ShieldCheck, Hash, X, Eye, ArrowRight, Lock, 
  ChevronRight, RefreshCw, FileCode, Check
} from 'lucide-react';

const STEPS = ['Upload File', 'Security Scan', 'AI Metadata', 'Review & Publish'];

export default function SellerUploadPage() {
  const { user, isSeller } = useAuth();
  const router = useRouter();
  const fileRef = useRef<HTMLInputElement>(null);
  const [step, setStep] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [price, setPrice] = useState('');
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [meta, setMeta] = useState<any>({});
  const [publishing, setPublishing] = useState(false);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f) setFile(f);
  }, []);

  const handleUpload = async () => {
    if (!file || !price) {
      toast.error('Please select a file and set a price');
      return;
    }
    if (!user) {
      router.push('/login');
      return;
    }
    if (!isSeller()) {
      await api.post('/api/auth/become-seller');
    }
    setUploading(true);
    setStep(1);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('price', price);

    try {
      const { data } = await api.post('/api/uploads/product', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(data);
      setMeta({
        title: data.ai_metadata?.title || data.product?.title || file.name,
        short_description: data.ai_metadata?.short_description || '',
        summary: data.ai_metadata?.summary || '',
        category: data.ai_metadata?.category || 'Documents',
        subcategory: data.ai_metadata?.subcategory || '',
        tags: (data.ai_metadata?.tags || []).join(', '),
        keywords: (data.ai_metadata?.keywords || []).join(', '),
        language: data.ai_metadata?.language || 'English',
        difficulty: data.ai_metadata?.difficulty || 'Unknown',
        content_type: data.ai_metadata?.content_type || 'Document',
        target_audience: data.ai_metadata?.target_audience || '',
        price: data.product?.price !== undefined ? String(data.product.price) : price,
      });
      setStep(2);
      if (data.ai_error) {
        toast('AI metadata unavailable — please verify manually', { icon: '⚠️' });
      } else {
        toast.success('✨ File verified and AI metadata generated!');
      }
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Upload failed'));
      setStep(0);
      setUploading(false);
    } finally {
      setUploading(false);
    }
  };

  const handlePublish = async () => {
    if (!result?.product_id) return;
    setPublishing(true);
    try {
      await api.put(`/api/products/${result.product_id}`, {
        title: meta.title,
        short_description: meta.short_description,
        summary: meta.summary,
        category: meta.category,
        subcategory: meta.subcategory,
        tags: meta.tags ? meta.tags.split(',').map((t: string) => t.trim()).filter(Boolean) : [],
        keywords: meta.keywords ? meta.keywords.split(',').map((k: string) => k.trim()).filter(Boolean) : [],
        language: meta.language,
        difficulty: meta.difficulty,
        price: parseFloat(meta.price) || 0,
        content_type: meta.content_type,
        target_audience: meta.target_audience,
      });

      await api.post(`/api/products/${result.product_id}/publish`);
      setStep(3);
      toast.success('Product successfully published to marketplace!');
    } catch (err: any) {
      toast.error(getErrorMessage(err, 'Publish failed'));
    } finally {
      setPublishing(false);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center p-4">
          <div className="bg-white border border-gray-200 rounded-3xl p-8 max-w-md text-center shadow-sm">
            <Lock className="w-12 h-12 text-blue-600 mx-auto mb-4" />
            <h2 className="text-xl font-bold text-gray-900 mb-2">Sign in to Upload</h2>
            <p className="text-sm text-gray-500 mb-6">You must be logged into a creator account to upload digital assets.</p>
            <button
              onClick={() => router.push('/login')}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-xl shadow-sm transition-colors text-sm"
            >
              Sign In to Continue
            </button>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        
        {/* Page Header */}
        <div className="mb-8">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2 border border-blue-100">
            <ShieldCheck className="w-3.5 h-3.5" />
            Secure Publishing Pipeline
          </div>
          <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Upload & List Digital Asset</h1>
          <p className="text-gray-500 text-sm mt-1">
            Automated virus scanning, file integrity verification, and Gemini AI metadata generation.
          </p>
        </div>

        {/* Stepper Wizard Indicator */}
        <div className="bg-white border border-gray-200 rounded-2xl p-4 sm:p-5 mb-8 shadow-sm">
          <div className="flex items-center justify-between">
            {STEPS.map((s, i) => {
              const isDone = i < step;
              const isCurrent = i === step;
              return (
                <div key={s} className="flex items-center flex-1 last:flex-none">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-9 h-9 rounded-xl flex items-center justify-center text-xs font-bold transition-all ${
                        isDone
                          ? 'bg-emerald-600 text-white shadow-sm shadow-emerald-500/20'
                          : isCurrent
                          ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20 ring-4 ring-blue-50'
                          : 'bg-slate-100 text-gray-400'
                      }`}
                    >
                      {isDone ? <Check className="w-4 h-4" /> : i + 1}
                    </div>
                    <span
                      className={`text-xs font-semibold hidden md:block ${
                        isCurrent ? 'text-blue-600 font-bold' : isDone ? 'text-gray-700' : 'text-gray-400'
                      }`}
                    >
                      {s}
                    </span>
                  </div>
                  {i < STEPS.length - 1 && (
                    <div
                      className={`flex-1 h-0.5 mx-4 transition-colors ${
                        i < step ? 'bg-emerald-500' : 'bg-gray-100'
                      }`}
                    />
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Step 0: Upload Form */}
        {step === 0 && (
          <div className="bg-white border border-gray-200 rounded-3xl p-6 sm:p-10 space-y-8 shadow-sm">
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-2">Select Digital File</label>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
                  dragOver
                    ? 'border-blue-500 bg-blue-50/60 ring-4 ring-blue-50'
                    : file
                    ? 'border-emerald-400 bg-emerald-50/40'
                    : 'border-gray-200 hover:border-blue-400 hover:bg-slate-50'
                }`}
              >
                <input
                  ref={fileRef}
                  type="file"
                  className="hidden"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  accept=".pdf,.docx,.doc,.txt,.zip,.rar,.xlsx,.xls,.csv,.pptx,.ppt,.png,.jpg,.jpeg,.gif,.svg,.py,.js,.ts,.html,.css,.json,.md,.epub,.mp3,.mp4"
                />

                {file ? (
                  <div className="space-y-2">
                    <div className="w-14 h-14 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto">
                      <FileText className="w-8 h-8" />
                    </div>
                    <p className="font-bold text-gray-900 text-base">{file.name}</p>
                    <p className="text-xs text-gray-500">{(file.size / (1024 * 1024)).toFixed(2)} MB · Ready for scanning</p>
                    <button
                      type="button"
                      onClick={(e) => { e.stopPropagation(); setFile(null); }}
                      className="inline-flex items-center gap-1 text-xs text-rose-600 hover:underline pt-2 font-medium"
                    >
                      <X className="w-3.5 h-3.5" /> Choose different file
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="w-14 h-14 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto">
                      <UploadCloud className="w-7 h-7" />
                    </div>
                    <div>
                      <p className="text-base font-bold text-gray-800">Drag & drop your file here</p>
                      <p className="text-xs text-gray-400 mt-0.5">or browse from your computer · Up to 100MB</p>
                    </div>
                    <div className="flex flex-wrap justify-center gap-1.5 pt-2 max-w-md mx-auto">
                      {['PDF', 'ZIP', 'PY', 'TS/JS', 'DOCX', 'XLSX', 'EPUB', 'PNG/SVG'].map((ext) => (
                        <span key={ext} className="text-[10px] font-mono bg-slate-100 text-slate-600 px-2 py-0.5 rounded-md font-semibold">
                          .{ext}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Price Setting */}
            <div>
              <label className="block text-sm font-bold text-gray-900 mb-2">
                Listing Price (INR ₹) <span className="text-blue-600">*</span>
              </label>
              <div className="relative max-w-xs">
                <span className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400 font-bold text-base">₹</span>
                <input
                  type="number"
                  value={price}
                  onChange={(e) => setPrice(e.target.value)}
                  min="0"
                  step="1"
                  placeholder="0 (Free) or e.g. 499"
                  className="w-full pl-9 pr-4 py-3 bg-slate-50 border border-gray-200 rounded-xl text-gray-900 font-bold focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all text-base"
                />
              </div>
              <p className="text-xs text-gray-400 mt-2">Enter 0 to distribute your digital asset for free.</p>
            </div>

            {/* Submit button */}
            <button
              onClick={handleUpload}
              disabled={!file || !price}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-3.5 px-6 rounded-xl shadow-sm transition-all disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2 text-sm"
            >
              <ShieldCheck className="w-4 h-4" /> Scan File & Generate AI Metadata
            </button>
          </div>
        )}

        {/* Step 1: Scanning Progress */}
        {step === 1 && (
          <div className="bg-white border border-gray-200 rounded-3xl p-8 sm:p-12 text-center shadow-sm">
            <div className="w-16 h-16 bg-blue-50 text-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <Loader2 className="w-8 h-8 animate-spin" />
            </div>
            <h2 className="text-xl font-extrabold text-gray-900 mb-2">Verifying & Analyzing Asset...</h2>
            <p className="text-sm text-gray-500 max-w-md mx-auto mb-8">
              Verifying file integrity, scanning for malware, and generating Gemini AI marketplace metadata.
            </p>

            <div className="max-w-md mx-auto space-y-3 text-left">
              {[
                { label: 'File received & validated', status: 'done' },
                { label: 'File integrity verified', status: uploading ? 'active' : 'done' },
                { label: 'Malware inspection pipeline', status: uploading ? 'active' : 'done' },
                { label: 'Dynamic price evaluation', status: uploading ? 'active' : 'done' },
                { label: 'AI metadata generation (Gemini)', status: uploading ? 'active' : 'done' },
              ].map((item) => (
                <div key={item.label} className="flex items-center gap-3 p-3 rounded-xl bg-slate-50 border border-gray-100">
                  {item.status === 'done' ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  ) : (
                    <Loader2 className="w-4 h-4 text-blue-600 animate-spin flex-shrink-0" />
                  )}
                  <span className="text-xs font-semibold text-gray-700">{item.label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Review AI Metadata */}
        {step === 2 && result && (
          <div className="space-y-6">
            
            {/* Security Confirmation Banner */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <ShieldCheck className="w-5 h-5 text-emerald-600" />
                  <h3 className="font-bold text-gray-900 text-sm">Security & Integrity Pass</h3>
                </div>
                <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-full">
                  All Checks Passed
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-2">
                <div className="p-3 bg-emerald-50/60 rounded-xl border border-emerald-100 flex items-center gap-2.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <div>
                    <span className="text-[11px] font-bold text-emerald-900 block">Malware Scan Passed</span>
                    <span className="text-[10px] text-emerald-700">Zero threats detected</span>
                  </div>
                </div>
                <div className="p-3 bg-blue-50/60 rounded-xl border border-blue-100 flex items-center gap-2.5">
                  <ShieldCheck className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <div>
                    <span className="text-[11px] font-bold text-blue-900 block">File Integrity Verified</span>
                    <span className="text-[10px] text-blue-700">Tamper-proof protection</span>
                  </div>
                </div>
                <div className="p-3 bg-purple-50/60 rounded-xl border border-purple-100 flex items-center gap-2.5">
                  <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0" />
                  <div>
                    <span className="text-[11px] font-bold text-purple-900 block">Protected Delivery</span>
                    <span className="text-[10px] text-purple-700">Secure buyer downloads</span>
                  </div>
                </div>
              </div>

              {/* Duplicate Detection Alert */}
              {result.duplicate_status === 'DUPLICATE_DETECTED' && (
                <div className="mt-4 bg-rose-50 border border-rose-200 rounded-2xl p-4 text-rose-900 flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-rose-600 flex-shrink-0 mt-0.5" />
                  <div className="space-y-1">
                    <h4 className="text-sm font-bold text-rose-900">Duplicate Content Detected</h4>
                    <p className="text-xs text-rose-700 leading-relaxed">
                      This file matches an existing asset in the marketplace ({result.duplicate_check?.match_level || 'Duplicate Detected'}).
                      SecureMarket policies require all published assets to be original. Publishing is disabled for this file.
                    </p>
                  </div>
                </div>
              )}

              {/* Quality Score Indicator */}
              {result.quality_score !== undefined && result.quality_score !== null && (
                <div className="mt-4 bg-blue-50/60 border border-blue-200 rounded-2xl p-4 flex items-center justify-between flex-wrap gap-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-blue-600 text-white flex items-center justify-center font-bold text-sm">
                      {result.quality_score}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-blue-950 uppercase tracking-wider">AI Quality Score: {result.quality_level}</h4>
                      <p className="text-xs text-blue-700">Calculated across content usefulness, structure, and depth.</p>
                    </div>
                  </div>
                  <span className="text-[11px] font-semibold text-slate-500 bg-white px-2.5 py-1 rounded-lg border border-gray-200">
                    System Read-Only
                  </span>
                </div>
              )}
            </div>

            {/* AI Metadata Form */}
            <div className="bg-white border border-gray-200 rounded-3xl p-6 sm:p-8 shadow-sm space-y-6">
              <div className="flex items-center gap-2 pb-4 border-b border-gray-100">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <div>
                  <h3 className="font-bold text-gray-900 text-base">Review AI-Generated Metadata</h3>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {result.ai_metadata?._ai_provider === 'gemini'
                      ? '✨ Enriched by Gemini 3.6 Flash · Adjust anything before final publishing'
                      : '✨ Generated by local Ollama engine · Adjust anything before final publishing'}
                  </p>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">
                    Product Title <span className="text-blue-600">*</span>
                  </label>
                  <input
                    type="text"
                    value={meta.title || ''}
                    onChange={(e) => setMeta({ ...meta, title: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">
                    Short Description
                  </label>
                  <input
                    type="text"
                    value={meta.short_description || ''}
                    onChange={(e) => setMeta({ ...meta, short_description: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">
                    Detailed Summary
                  </label>
                  <textarea
                    rows={4}
                    value={meta.summary || ''}
                    onChange={(e) => setMeta({ ...meta, summary: e.target.value })}
                    className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all resize-none leading-relaxed"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Category</label>
                    <select
                      value={meta.category || 'Programming'}
                      onChange={(e) => setMeta({ ...meta, category: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                    >
                      {['Programming', 'Design', 'Education', 'Business', 'Finance', 'Templates', 'Marketing', 'Documents', 'Graphics', 'Ebooks', 'Other'].map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Skill / Difficulty</label>
                    <select
                      value={meta.difficulty || 'Intermediate'}
                      onChange={(e) => setMeta({ ...meta, difficulty: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                    >
                      {['Beginner', 'Intermediate', 'Advanced', 'All Levels', 'Unknown'].map((d) => (
                        <option key={d} value={d}>{d}</option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Price (₹)</label>
                    <input
                      type="number"
                      value={meta.price || 0}
                      onChange={(e) => setMeta({ ...meta, price: e.target.value })}
                      className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">Target Audience</label>
                    <input
                      type="text"
                      value={meta.target_audience || ''}
                      onChange={(e) => setMeta({ ...meta, target_audience: e.target.value })}
                      placeholder="e.g., Python Developers, UI Designers"
                      className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                    />
                  </div>
                </div>

                {/* Seller Pricing Guidance & Ceiling Card */}
                {result?.pricing && (
                  <div className="p-4 bg-slate-50 rounded-2xl border border-gray-200 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-gray-700 uppercase tracking-wider flex items-center gap-1.5">
                        <Sparkles className="w-3.5 h-3.5 text-blue-600" /> Marketplace Pricing Guidance
                      </span>
                      {result.pricing.tier && (
                        <span className="text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-800 px-2 py-0.5 rounded-md">
                          {result.pricing.tier} Tier
                        </span>
                      )}
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center">
                      <div className="p-2.5 bg-white rounded-xl border border-gray-100">
                        <span className="text-[10px] text-gray-500 font-medium block">Recommended</span>
                        <span className="text-sm font-bold text-blue-600">₹{result.pricing.suggested_price ?? '—'}</span>
                      </div>
                      <div className="p-2.5 bg-white rounded-xl border border-gray-100">
                        <span className="text-[10px] text-gray-500 font-medium block">Suggested Range</span>
                        <span className="text-xs font-semibold text-gray-800">
                          {result.pricing.suggested_price_min !== undefined
                            ? `₹${result.pricing.suggested_price_min} – ₹${result.pricing.suggested_price_max}`
                            : '—'}
                        </span>
                      </div>
                      <div className="p-2.5 bg-white rounded-xl border border-gray-100">
                        <span className="text-[10px] text-gray-500 font-medium block">Maximum Allowed</span>
                        <span className="text-sm font-bold text-gray-900">₹{result.pricing.maximum_allowed_price ?? '—'}</span>
                      </div>
                    </div>

                    {result.pricing.suggested_price !== undefined && Number(meta.price) !== result.pricing.suggested_price && (
                      <button
                        type="button"
                        onClick={() => setMeta({ ...meta, price: String(result.pricing.suggested_price) })}
                        className="text-xs text-blue-600 hover:text-blue-800 font-medium hover:underline flex items-center gap-1"
                      >
                        Apply Recommended Price (₹{result.pricing.suggested_price})
                      </button>
                    )}

                    {/* Dynamic Price Status Indicators */}
                    {result.pricing.maximum_allowed_price && Number(meta.price) > result.pricing.maximum_allowed_price ? (
                      <div className="bg-rose-50 border border-rose-200 rounded-xl p-3 flex items-start gap-2.5 text-rose-900 text-xs">
                        <AlertCircle className="w-4 h-4 text-rose-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold text-rose-900">
                            ✕ Price exceeds marketplace limit for this product (Max: ₹{result.pricing.maximum_allowed_price})
                          </p>
                          <p className="text-rose-700 text-[11px] mt-0.5 leading-relaxed">
                            To ensure fair pricing and protect buyer confidence, listings for this content type are capped at ₹{result.pricing.maximum_allowed_price}. Please adjust your price to publish.
                          </p>
                        </div>
                      </div>
                    ) : Number(meta.price) > (result.pricing.suggested_price_max || (result.pricing.suggested_price * 1.5)) ? (
                      <div className="bg-amber-50 border border-amber-200 rounded-xl p-3 flex items-start gap-2.5 text-amber-900 text-xs">
                        <AlertCircle className="w-4 h-4 text-amber-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="font-bold text-amber-900">
                            ⚠ Price is above the recommended range (Suggested: ₹{result.pricing.suggested_price_min} – ₹{result.pricing.suggested_price_max})
                          </p>
                          <p className="text-amber-700 text-[11px] mt-0.5 leading-relaxed">
                            Your asset price is above algorithmic guidance. High-value listings receive an informational review indicator on the marketplace.
                          </p>
                        </div>
                      </div>
                    ) : (
                      <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-2.5 flex items-center gap-2 text-emerald-900 text-xs">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                        <span className="font-semibold text-emerald-900">✓ Price is within marketplace limits</span>
                      </div>
                    )}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-bold text-gray-700 uppercase tracking-wider mb-1.5">
                    Tags <span className="text-gray-400 font-normal">(comma-separated)</span>
                  </label>
                  <input
                    type="text"
                    value={meta.tags || ''}
                    onChange={(e) => setMeta({ ...meta, tags: e.target.value })}
                    placeholder="react, tailwind, dashboard, api"
                    className="w-full px-4 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm font-medium text-gray-900 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 transition-all"
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-gray-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setStep(0)}
                  className="px-5 py-2.5 rounded-xl border border-gray-200 text-sm font-semibold text-gray-600 hover:bg-slate-50 transition-colors"
                >
                  Back to File
                </button>
                <button
                  type="button"
                  onClick={handlePublish}
                  disabled={
                    publishing ||
                    !meta.title ||
                    result?.duplicate_status === 'DUPLICATE_DETECTED' ||
                    Boolean(result?.pricing?.maximum_allowed_price && Number(meta.price) > result.pricing.maximum_allowed_price)
                  }
                  className={`font-bold text-sm px-6 py-2.5 rounded-xl shadow-sm transition-all flex items-center gap-2 ${
                    result?.duplicate_status === 'DUPLICATE_DETECTED' ||
                    Boolean(result?.pricing?.maximum_allowed_price && Number(meta.price) > result.pricing.maximum_allowed_price)
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-blue-600 hover:bg-blue-700 text-white disabled:opacity-50'
                  }`}
                >
                  {publishing ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4" />
                  )}
                  {result?.duplicate_status === 'DUPLICATE_DETECTED'
                    ? 'Publishing Blocked (Duplicate)'
                    : Boolean(result?.pricing?.maximum_allowed_price && Number(meta.price) > result.pricing.maximum_allowed_price)
                    ? 'Price Exceeds Platform Limit'
                    : publishing
                    ? 'Publishing Asset...'
                    : 'Confirm & Publish'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Success Published */}
        {step === 3 && (
          <div className="bg-white border border-gray-200 rounded-3xl p-8 sm:p-12 text-center shadow-sm max-w-2xl mx-auto">
            <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-2xl flex items-center justify-center mx-auto mb-6">
              <CheckCircle2 className="w-9 h-9" />
            </div>
            <h2 className="text-2xl font-extrabold text-gray-900 mb-2">Product Published Successfully!</h2>
            <p className="text-sm text-gray-500 mb-8">
              Your digital asset is now live in the marketplace with security checks passed and file protection active.
            </p>

            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <button
                onClick={() => router.push(`/marketplace/${result?.product_id}`)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-bold text-sm px-6 py-3 rounded-xl shadow-sm transition-colors flex items-center justify-center gap-2"
              >
                <Eye className="w-4 h-4" /> View Public Listing
              </button>
              <button
                onClick={() => router.push('/seller/dashboard')}
                className="border border-gray-200 hover:bg-slate-50 text-gray-700 font-semibold text-sm px-6 py-3 rounded-xl transition-colors"
              >
                Go to Seller Dashboard
              </button>
            </div>
          </div>
        )}

      </main>

      <Footer />
    </div>
  );
}
