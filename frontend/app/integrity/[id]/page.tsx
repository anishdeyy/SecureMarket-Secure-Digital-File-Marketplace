'use client';
import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import api from '@/lib/api';
import Navbar from '@/components/layout/Navbar';
import { Shield, CheckCircle, AlertTriangle, Hash, FileText, Clock, Loader2, ExternalLink, Copy } from 'lucide-react';
import toast from 'react-hot-toast';

export default function IntegrityVerifyPage() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!id) return;
    api.get(`/api/integrity/${id}`)
      .then(r => setData(r.data))
      .catch(err => setError(err?.response?.data?.detail || 'Integrity record not found'))
      .finally(() => setLoading(false));
  }, [id]);

  const copy = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    toast.success(`${label} copied`);
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600"/></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-12 w-full">
        {/* Title */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-blue-50 border border-blue-200 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Shield className="w-9 h-9 text-blue-600"/>
          </div>
          <h1 className="text-2xl font-bold text-gray-900">File Integrity Verification</h1>
          <p className="text-gray-500 text-sm mt-2">Secure verification of asset authenticity and platform integrity</p>
        </div>

        {error ? (
          <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center">
            <AlertTriangle className="w-10 h-10 text-red-500 mx-auto mb-3"/>
            <p className="font-semibold text-red-800 mb-1">Record Not Found</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        ) : data && (
          <>
            {/* Overall status banner */}
            <div className={`rounded-2xl p-5 mb-6 border ${data.overall_ok ? 'bg-green-50 border-green-300' : 'bg-red-50 border-red-300'}`}>
              <div className="flex items-center gap-3">
                {data.overall_ok
                  ? <CheckCircle className="w-8 h-8 text-green-600 flex-shrink-0"/>
                  : <AlertTriangle className="w-8 h-8 text-red-600 flex-shrink-0"/>}
                <div>
                  <p className={`text-lg font-bold ${data.overall_ok ? 'text-green-800' : 'text-red-800'}`}>
                    {data.overall_ok ? '✅ Integrity Verified' : '⚠️ Integrity Check Failed'}
                  </p>
                  <p className={`text-sm ${data.overall_ok ? 'text-green-700' : 'text-red-700'}`}>
                    {data.overall_ok
                      ? 'Authenticity check is valid and file has not been modified'
                      : 'One or more checks failed — this file may have been modified'}
                  </p>
                </div>
              </div>
            </div>

            {/* Details card */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden mb-6">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                <h2 className="font-bold text-gray-900 flex items-center gap-2"><Shield className="w-4 h-4 text-blue-600"/>Integrity Record Details</h2>
              </div>
              <div className="divide-y divide-gray-100">
                {[
                  { label: 'Verification Status', value: data.overall_ok ? 'Active & Authentic' : 'Check Pending', mono: false },
                  { label: 'File Name', value: data.original_filename, mono: false },
                  { label: 'File Size', value: `${Number(data.file_size).toLocaleString()} bytes`, mono: false },
                  { label: 'MIME Type', value: data.mime_type, mono: true },
                  ...(data.sha256_hash ? [{ label: 'Cryptographic Hash (Admin)', value: data.sha256_hash, mono: true, copyable: true, truncate: true }] : [{ label: 'Integrity Seal', value: 'Verified Platform Fingerprint', mono: false }]),
                  { label: 'Verified At', value: data.verified_at ? new Date(data.verified_at).toLocaleString('en-IN') : '—', mono: false },
                  { label: 'Last Checked', value: data.last_checked_at ? new Date(data.last_checked_at).toLocaleString('en-IN') : 'Not re-checked', mono: false },
                ].map(({ label, value, mono, copyable, truncate }: any) => (
                  <div key={label} className="px-6 py-3.5 flex items-start justify-between gap-4">
                    <span className="text-sm text-gray-500 flex-shrink-0 w-32">{label}</span>
                    <div className="flex items-center gap-2 min-w-0 flex-1 justify-end">
                      <span className={`text-sm text-right ${mono ? 'font-mono text-gray-700' : 'text-gray-900 font-medium'} ${truncate ? 'truncate max-w-xs' : ''}`}
                        title={value}>{value}</span>
                      {copyable && (
                        <button onClick={() => copy(value, label)} className="flex-shrink-0 text-gray-400 hover:text-blue-600 transition-colors">
                          <Copy className="w-3.5 h-3.5"/>
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Checks */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden mb-6">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
                <h2 className="font-bold text-gray-900 flex items-center gap-2"><CheckCircle className="w-4 h-4"/>Verification Checks</h2>
              </div>
              <div className="divide-y divide-gray-100">
                {[
                  { label: 'HMAC-SHA256 Seal', ok: data.seal_valid, msg: data.seal_message },
                  { label: 'Cross-Check (product ↔ record)', ok: data.cross_check_ok, msg: data.cross_check_msg },
                  { label: 'Tamper Flag', ok: !data.tampered_detected, msg: data.tampered_detected ? '⚠ Tamper detected flag is set' : 'No tamper detected' },
                ].map(({ label, ok, msg }) => (
                  <div key={label} className={`px-6 py-4 flex items-start gap-3 ${ok ? '' : 'bg-red-50'}`}>
                    {ok ? <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5"/> : <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5"/>}
                    <div>
                      <p className="text-sm font-semibold text-gray-900">{label}</p>
                      <p className={`text-xs mt-0.5 ${ok ? 'text-gray-500' : 'text-red-600'}`}>{msg}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* How to verify */}
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2"><FileText className="w-4 h-4"/>How to verify independently</h3>
              <p className="text-sm text-blue-800 mb-3">After downloading the file, run this command to compute its SHA-256 hash and compare with the value above:</p>
              <div className="bg-white border border-blue-200 rounded-lg p-3 font-mono text-xs text-gray-700 space-y-1">
                <p># Linux / macOS</p>
                <p className="text-blue-700">sha256sum your-downloaded-file</p>
                <p className="mt-2"># Windows (PowerShell)</p>
                <p className="text-blue-700">Get-FileHash your-downloaded-file -Algorithm SHA256</p>
              </div>
              <p className="text-xs text-blue-700 mt-3">The output must exactly match: <code className="font-mono bg-white px-1 py-0.5 rounded border border-blue-200">{data.sha256_hash?.slice(0,32)}…</code></p>
            </div>

            {/* View product */}
            {data.product_id && (
              <div className="text-center mt-6">
                <Link href={`/marketplace/${data.product_id}`}
                  className="inline-flex items-center gap-2 text-sm text-blue-600 font-medium hover:underline">
                  <ExternalLink className="w-4 h-4"/>View Product Listing
                </Link>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
