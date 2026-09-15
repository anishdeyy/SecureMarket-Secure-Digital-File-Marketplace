'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import {
  Users, Package, ShoppingBag, DollarSign, AlertTriangle, Shield,
  CheckCircle, XCircle, Hash, Clock, Loader2, FileText, Search,
  RefreshCw, Eye, Ban, Activity, Lock
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, sub, color }: any) {
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5">
      <div className="flex justify-between items-start mb-3">
        <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color}`}><Icon className="w-5 h-5"/></div>
      </div>
      <p className="text-2xl font-bold text-gray-900">{value ?? '—'}</p>
      <p className="text-sm text-gray-500 mt-0.5">{label}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

const TABS = ['Overview', 'Integrity Records', 'Database View', 'Fraud Alerts', 'Audit Logs', 'Users', 'Products'];

export default function AdminDashboardPage() {
  const { user, isAdmin } = useAuth();
  const router = useRouter();
  const [tab, setTab] = useState('Overview');
  const [stats, setStats] = useState<any>(null);
  const [integrityRecords, setIntegrityRecords] = useState<any[]>([]);
  const [fraudAlerts, setFraudAlerts] = useState<any[]>([]);
  const [auditLogs, setAuditLogs] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [dbView, setDbView] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState<string | null>(null);
  const [searchUser, setSearchUser] = useState('');
  const [productToDelete, setProductToDelete] = useState<any>(null);
  const [deleteReason, setDeleteReason] = useState('Marketplace policy and security compliance standard');
  const [deleting, setDeleting] = useState(false);

  const handleDeleteProduct = async () => {
    if (!productToDelete) return;
    setDeleting(true);
    try {
      const { data } = await api.delete(`/api/admin/products/${productToDelete.id}?reason=${encodeURIComponent(deleteReason)}`);
      toast.success(data.message || 'Product removed from marketplace');
      setProducts(prev => prev.map(p => p.id === productToDelete.id ? { ...p, status: 'removed_by_admin' } : p));
      setProductToDelete(null);
    } catch (err: any) {
      toast.error('Failed to remove product: ' + (err?.response?.data?.detail || err.message));
    } finally {
      setDeleting(false);
    }
  };

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    if (!isAdmin()) { router.push('/dashboard'); return; }
    loadAll();
  }, [user]);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [sRes, iRes, fRes, aRes, uRes, pRes, dRes] = await Promise.all([
        api.get('/api/admin/stats'),
        api.get('/api/integrity/admin/all?per_page=50'),
        api.get('/api/admin/fraud?per_page=20'),
        api.get('/api/admin/audit-logs?per_page=30'),
        api.get('/api/admin/users?per_page=20'),
        api.get('/api/admin/products?per_page=20'),
        api.get('/api/admin/database-view').catch(() => ({ data: null })),
      ]);
      setStats(sRes.data);
      setIntegrityRecords(iRes.data.items || []);
      setFraudAlerts(fRes.data.items || []);
      setAuditLogs(aRes.data.items || []);
      setUsers(uRes.data.items || []);
      setProducts(pRes.data.items || []);
      setDbView(dRes?.data || null);
    } catch { toast.error('Failed to load admin data'); }
    finally { setLoading(false); }
  };

  const runIntegrityCheck = async (integrityId: string) => {
    setVerifying(integrityId);
    try {
      const { data } = await api.post(`/api/integrity/admin/${integrityId}/verify`);
      toast[data.overall_ok ? 'success' : 'error'](
        data.overall_ok ? `✅ ${integrityId}: Integrity confirmed` : `⚠️ ${integrityId}: ${data.seal_message}`
      );
      // Refresh
      const iRes = await api.get('/api/integrity/admin/all?per_page=50');
      setIntegrityRecords(iRes.data.items || []);
    } catch { toast.error('Verification failed'); }
    finally { setVerifying(null); }
  };

  const resolveAlert = async (id: string, action: string) => {
    try {
      await api.post(`/api/admin/fraud/${id}/resolve?action=${action}`);
      toast.success(`Alert ${action}`);
      setFraudAlerts(prev => prev.map(a => a.id === id ? { ...a, status: action } : a));
    } catch { toast.error('Action failed'); }
  };

  const suspendUser = async (id: string, username: string) => {
    try {
      await api.post(`/api/admin/users/${id}/suspend`);
      toast.success(`${username} suspended`);
      setUsers(prev => prev.map(u => u.id === id ? { ...u, is_suspended: true } : u));
    } catch { toast.error('Failed'); }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-8 h-8 animate-spin text-blue-600"/></div>
    </div>
  );

  const riskColor = (l: string) => ({ low: 'bg-green-50 text-green-700 border-green-200', medium: 'bg-amber-50 text-amber-700 border-amber-200', high: 'bg-orange-50 text-orange-700 border-orange-200', critical: 'bg-red-50 text-red-700 border-red-200' })[l] || 'bg-gray-50 text-gray-600 border-gray-200';

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 py-8 w-full">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2"><Lock className="w-6 h-6 text-blue-600"/>Admin Dashboard</h1>
            <p className="text-gray-500 text-sm mt-1">Full platform management · Logged in as {user?.username}</p>
          </div>
          <button onClick={loadAll} className="flex items-center gap-2 text-sm border border-gray-300 bg-white px-3 py-2 rounded-lg hover:bg-gray-50 text-gray-600">
            <RefreshCw className="w-4 h-4"/>Refresh
          </button>
        </div>

        {/* Stats row */}
        {stats && (
          <div className="space-y-4 mb-8">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-3">
              <StatCard icon={Users} label="Total Users" value={stats.total_users} color="bg-blue-50 text-blue-600"/>
              <StatCard icon={Users} label="Buyers" value={stats.buyers} color="bg-cyan-50 text-cyan-600"/>
              <StatCard icon={Users} label="Sellers" value={stats.sellers} color="bg-purple-50 text-purple-600"/>
              <StatCard icon={Package} label="Products" value={stats.total_products} color="bg-indigo-50 text-indigo-600"/>
              <StatCard icon={Package} label="Published" value={stats.published_products} color="bg-green-50 text-green-600"/>
              <StatCard icon={ShoppingBag} label="Orders" value={stats.total_orders} color="bg-amber-50 text-amber-600"/>
              <StatCard icon={AlertTriangle} label="Fraud Alerts" value={stats.open_fraud_alerts} color="bg-red-50 text-red-600"/>
              <StatCard icon={Shield} label="Malware Hits" value={stats.malware_alerts} color="bg-rose-50 text-rose-600"/>
            </div>

            {/* Financial Ledger Architecture Summary */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 p-4 bg-gradient-to-r from-slate-900 to-slate-800 text-white rounded-2xl shadow-sm">
              <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                <span className="text-xs text-slate-400 font-semibold block uppercase">Gross Marketplace GMV</span>
                <span className="text-xl font-bold text-white">₹{(stats.total_revenue||0).toLocaleString()}</span>
                <span className="text-[11px] text-slate-400 block mt-0.5">Authoritative server total</span>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                <span className="text-xs text-purple-300 font-semibold block uppercase">Platform Fees Earned (5%)</span>
                <span className="text-xl font-bold text-purple-400">₹{(stats.total_platform_fees||0).toLocaleString()}</span>
                <span className="text-[11px] text-purple-200/70 block mt-0.5">Marketplace commission</span>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                <span className="text-xs text-emerald-300 font-semibold block uppercase">Seller Net Royalties (95%)</span>
                <span className="text-xl font-bold text-emerald-400">₹{(stats.total_seller_payouts||0).toLocaleString()}</span>
                <span className="text-[11px] text-emerald-200/70 block mt-0.5">Creator payouts balance</span>
              </div>
              <div className="p-3 bg-white/5 rounded-xl border border-white/10">
                <span className="text-xs text-amber-300 font-semibold block uppercase">GST / Statutory Taxes (18%)</span>
                <span className="text-xl font-bold text-amber-400">₹{(stats.total_taxes||0).toLocaleString()}</span>
                <span className="text-[11px] text-amber-200/70 block mt-0.5">Govt tax obligations</span>
              </div>
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="flex gap-1 mb-6 bg-gray-100 p-1 rounded-xl w-full overflow-x-auto">
          {TABS.map(t => (
            <button key={t} onClick={() => setTab(t)}
              className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-all ${tab === t ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab: Overview */}
        {tab === 'Overview' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2"><Activity className="w-4 h-4"/>Recent Audit Events</h3>
              <div className="space-y-2">
                {auditLogs.slice(0,8).map(l => (
                  <div key={l.id} className="flex items-start gap-2 text-xs py-1 border-b border-gray-50 last:border-0">
                    <span className="font-mono bg-blue-50 text-blue-700 px-2 py-0.5 rounded text-xs flex-shrink-0">{l.event}</span>
                    <span className="text-gray-500 truncate">{l.description || l.actor_email || l.resource_id}</span>
                    <span className="text-gray-300 flex-shrink-0">{new Date(l.created_at).toLocaleTimeString()}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2"><AlertTriangle className="w-4 h-4 text-red-500"/>Open Fraud Alerts</h3>
              {fraudAlerts.filter(a => a.status === 'open').length === 0 ? (
                <p className="text-gray-400 text-sm text-center py-4">No open alerts</p>
              ) : fraudAlerts.filter(a => a.status === 'open').slice(0,5).map(a => (
                <div key={a.id} className="py-2 border-b border-gray-50 last:border-0">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium text-gray-800">{a.user_id?.slice(0,8)}…</span>
                    <span className={`text-xs px-2 py-0.5 rounded-full border font-bold ${riskColor(a.risk_level)}`}>{a.risk_score} · {a.risk_level.toUpperCase()}</span>
                  </div>
                  <p className="text-xs text-gray-400 mt-0.5">{(JSON.parse(a.reasons || '[]')).join(' · ')}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab: Integrity Records */}
        {tab === 'Integrity Records' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between bg-gray-50">
              <h2 className="font-bold text-gray-900 flex items-center gap-2"><Hash className="w-5 h-5 text-blue-600"/>SHA-256 Integrity Records ({integrityRecords.length})</h2>
              <span className="text-xs text-gray-400">HMAC-SHA256 sealed · Tamper-evident</span>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="text-left border-b border-gray-100 bg-gray-50">
                    {['Integrity ID', 'Product', 'File', 'SHA-256 (partial)', 'Size', 'Seal', 'Cross-Check', 'Verified At', 'Actions'].map(h => (
                      <th key={h} className="px-4 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide whitespace-nowrap">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {integrityRecords.map(r => (
                    <tr key={r.integrity_id} className={`hover:bg-gray-50 ${!r.overall_ok ? 'bg-red-50' : ''}`}>
                      <td className="px-4 py-3">
                        <Link href={`/integrity/${r.integrity_id}`} className="font-mono text-xs font-bold text-blue-600 hover:underline">{r.integrity_id}</Link>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-700 max-w-[160px] truncate" title={r.product_title}>{r.product_title || r.product_id?.slice(0,8)}</td>
                      <td className="px-4 py-3 text-xs text-gray-500 max-w-[140px] truncate" title={r.original_filename}>{r.original_filename}</td>
                      <td className="px-4 py-3 font-mono text-xs text-gray-500">{r.sha256_hash?.slice(0,20)}…</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{r.file_size ? `${(Number(r.file_size)/1024).toFixed(0)} KB` : '—'}</td>
                      <td className="px-4 py-3">
                        {r.seal_valid
                          ? <span className="text-xs bg-green-50 text-green-700 border border-green-200 px-2 py-0.5 rounded-full flex items-center gap-1 w-fit"><CheckCircle className="w-3 h-3"/>Valid</span>
                          : <span className="text-xs bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded-full flex items-center gap-1 w-fit"><AlertTriangle className="w-3 h-3"/>FAIL</span>}
                      </td>
                      <td className="px-4 py-3">
                        {r.cross_check_ok
                          ? <span className="text-xs text-green-600">✅ Match</span>
                          : <span className="text-xs text-red-600 font-bold">❌ MISMATCH</span>}
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{r.verified_at ? new Date(r.verified_at).toLocaleDateString() : '—'}</td>
                      <td className="px-4 py-3">
                        <button onClick={() => runIntegrityCheck(r.integrity_id)} disabled={verifying === r.integrity_id}
                          className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg hover:bg-blue-100 flex items-center gap-1 disabled:opacity-40">
                          {verifying === r.integrity_id ? <Loader2 className="w-3 h-3 animate-spin"/> : <RefreshCw className="w-3 h-3"/>}
                          Verify
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab: Database View */}
        {tab === 'Database View' && (
          <div className="space-y-6">
            <div className="bg-white border border-gray-200 rounded-2xl p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h2 className="font-bold text-gray-900 flex items-center gap-2">
                    <Activity className="w-5 h-5 text-blue-600"/> Localhost Database & Storage Inspector
                  </h2>
                  <p className="text-sm text-gray-500 mt-0.5">
                    Live inspection of SQLite database records and file changes on localhost (backend: <a href="http://localhost:8001/docs" target="_blank" rel="noreferrer" className="text-blue-600 underline">API Docs</a>)
                  </p>
                </div>
                <div className="flex gap-2">
                  <a href="http://localhost:8001/api/admin/database-view" target="_blank" rel="noreferrer"
                    className="text-xs bg-gray-50 text-gray-700 border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-100 flex items-center gap-1 font-medium">
                    <Eye className="w-3.5 h-3.5"/> Raw JSON
                  </a>
                </div>
              </div>

              {dbView?.counts && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
                  {Object.entries(dbView.counts).map(([tbl, count]: [string, any]) => (
                    <div key={tbl} className="bg-gray-50 border border-gray-200 rounded-xl p-3 text-center">
                      <p className="text-xl font-bold text-gray-900">{count}</p>
                      <p className="text-xs text-gray-500 font-mono capitalize">{tbl.replace(/_/g, ' ')}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent File Integrity Records in DB */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-bold text-gray-900 flex items-center gap-2 text-sm">
                  <Hash className="w-4 h-4 text-purple-600"/> Registered Files in Database (File Integrity Records)
                </h3>
                <span className="text-xs text-gray-500">Immutable SHA-256 + Unique ID</span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-gray-50 border-b border-gray-100 text-gray-500 font-semibold uppercase tracking-wider">
                    <tr>
                      <th className="px-5 py-3">Integrity ID</th>
                      <th className="px-5 py-3">Filename</th>
                      <th className="px-5 py-3">SHA-256 Hash</th>
                      <th className="px-5 py-3">Tamper Status</th>
                      <th className="px-5 py-3">Created</th>
                      <th className="px-5 py-3">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 text-gray-700">
                    {(dbView?.recent_file_integrity_records || integrityRecords).slice(0, 10).map((r: any) => (
                      <tr key={r.integrity_id} className="hover:bg-gray-50">
                        <td className="px-5 py-3 font-mono font-bold text-blue-700">{r.integrity_id}</td>
                        <td className="px-5 py-3 max-w-xs truncate" title={r.original_filename}>{r.original_filename}</td>
                        <td className="px-5 py-3 font-mono text-gray-500 truncate max-w-xs" title={r.sha256_hash}>
                          {r.sha256_hash?.slice(0, 16)}…
                        </td>
                        <td className="px-5 py-3">
                          <span className={`px-2 py-0.5 rounded-full border text-[11px] font-semibold ${
                            r.tampered_detected
                              ? 'bg-red-50 text-red-700 border-red-200'
                              : 'bg-green-50 text-green-700 border-green-200'
                          }`}>
                            {r.tampered_detected ? 'Tampered' : 'Verified OK'}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-gray-400">
                          {r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}
                        </td>
                        <td className="px-5 py-3">
                          <a href={`/integrity/${r.integrity_id}`} target="_blank" rel="noreferrer"
                            className="text-blue-600 hover:underline inline-flex items-center gap-1 font-medium">
                            <Eye className="w-3 h-3"/> Verify
                          </a>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Audit Log / File Changes Trail */}
            <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex justify-between items-center">
                <h3 className="font-bold text-gray-900 flex items-center gap-2 text-sm">
                  <Activity className="w-4 h-4 text-green-600"/> Database Audit Trail (File & Record Changes)
                </h3>
                <span className="text-xs text-gray-500">Live event logs</span>
              </div>
              <div className="divide-y divide-gray-100 text-xs">
                {(dbView?.recent_audit_changes || auditLogs).slice(0, 10).map((l: any) => (
                  <div key={l.id} className="px-6 py-3 flex items-center justify-between gap-4 hover:bg-gray-50">
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-200 rounded font-mono text-[10px] uppercase font-bold flex-shrink-0">
                        {l.event}
                      </span>
                      <span className="text-gray-900 font-medium truncate max-w-md">{l.description || '—'}</span>
                    </div>
                    <div className="flex items-center gap-3 text-gray-400 flex-shrink-0">
                      <span>{l.actor_email || 'System'}</span>
                      <span>{l.created_at ? new Date(l.created_at).toLocaleTimeString() : '—'}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Tab: Fraud Alerts */}
        {tab === 'Fraud Alerts' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="font-bold text-gray-900 flex items-center gap-2"><AlertTriangle className="w-5 h-5 text-red-500"/>Fraud Alerts ({fraudAlerts.length})</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {fraudAlerts.length === 0 ? (
                <div className="text-center py-12 text-gray-400"><AlertTriangle className="w-10 h-10 mx-auto mb-3 opacity-40"/><p>No fraud alerts</p></div>
              ) : fraudAlerts.map(a => {
                const reasons = (() => { try { return JSON.parse(a.reasons || '[]'); } catch { return []; } })();
                return (
                  <div key={a.id} className="px-6 py-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1 flex-wrap">
                          <span className="font-mono text-xs text-gray-500">User: {a.user_id?.slice(0,12)}…</span>
                          <span className={`text-xs px-2.5 py-0.5 rounded-full border font-bold ${riskColor(a.risk_level)}`}>
                            Score: {a.risk_score} · {a.risk_level.toUpperCase()}
                          </span>
                          <span className={`text-xs px-2 py-0.5 rounded-full border ${a.status === 'open' ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-gray-50 text-gray-500 border-gray-200'}`}>{a.status}</span>
                        </div>
                        <div className="flex flex-wrap gap-2 mt-1">
                          {reasons.map((r: string, i: number) => (
                            <span key={i} className="text-xs bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded-full">{r}</span>
                          ))}
                        </div>
                        <p className="text-xs text-gray-400 mt-1">IP: {a.ip_address || '—'} · {new Date(a.created_at).toLocaleString()}</p>
                      </div>
                      {a.status === 'open' && (
                        <div className="flex gap-2 flex-shrink-0">
                          <button onClick={() => resolveAlert(a.id, 'reviewed')} className="text-xs bg-blue-50 text-blue-700 border border-blue-200 px-3 py-1.5 rounded-lg hover:bg-blue-100 font-medium">Review</button>
                          <button onClick={() => resolveAlert(a.id, 'resolved')} className="text-xs bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-lg hover:bg-green-100 font-medium">Resolve</button>
                          <button onClick={() => resolveAlert(a.id, 'dismissed')} className="text-xs bg-gray-50 text-gray-600 border border-gray-200 px-3 py-1.5 rounded-lg hover:bg-gray-100 font-medium">Dismiss</button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Tab: Audit Logs */}
        {tab === 'Audit Logs' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50">
              <h2 className="font-bold text-gray-900 flex items-center gap-2"><Activity className="w-5 h-5"/>Audit Logs ({auditLogs.length} recent)</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead><tr className="border-b border-gray-100 bg-gray-50">
                  {['Event', 'Actor', 'Resource', 'Description', 'IP', 'Time'].map(h => (
                    <th key={h} className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wide">{h}</th>
                  ))}
                </tr></thead>
                <tbody className="divide-y divide-gray-100">
                  {auditLogs.map(l => (
                    <tr key={l.id} className="hover:bg-gray-50">
                      <td className="px-4 py-3"><span className="font-mono text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{l.event}</span></td>
                      <td className="px-4 py-3 text-xs text-gray-600">{l.actor_email || '—'}</td>
                      <td className="px-4 py-3 text-xs text-gray-500">{l.resource_type ? `${l.resource_type}:${(l.resource_id||'').slice(0,8)}` : '—'}</td>
                      <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{l.description || '—'}</td>
                      <td className="px-4 py-3 text-xs font-mono text-gray-400">{l.ip_address || '—'}</td>
                      <td className="px-4 py-3 text-xs text-gray-400 whitespace-nowrap">{new Date(l.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Tab: Users */}
        {tab === 'Users' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
              <h2 className="font-bold text-gray-900 flex items-center gap-2"><Users className="w-5 h-5"/>Users ({users.length})</h2>
            </div>
            <div className="divide-y divide-gray-100">
              {users.map(u => (
                <div key={u.id} className="px-6 py-3.5 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-2">
                      <p className="font-medium text-sm text-gray-900">{u.username}</p>
                      <p className="text-xs text-gray-400">{u.email}</p>
                      {u.is_suspended && <span className="text-xs bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded-full">Suspended</span>}
                    </div>
                    <div className="flex gap-1.5 mt-1 flex-wrap">
                      {u.roles?.split(',').filter(Boolean).map((r: string) => (
                        <span key={r} className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full border border-blue-200 capitalize">{r}</span>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{new Date(u.created_at).toLocaleDateString()}</span>
                    {!u.is_suspended && !u.roles?.includes('admin') && (
                      <button onClick={() => suspendUser(u.id, u.username)}
                        className="text-xs bg-red-50 text-red-700 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-100 flex items-center gap-1">
                        <Ban className="w-3 h-3"/>Suspend
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab: Products */}
        {tab === 'Products' && (
          <div className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 bg-gray-50 flex items-center justify-between">
              <h2 className="font-bold text-gray-900 flex items-center gap-2">
                <Package className="w-5 h-5 text-blue-600"/>Marketplace Products ({products.length})
              </h2>
              <span className="text-xs text-gray-500 font-normal">
                Full administrative supervision & policy enforcement
              </span>
            </div>
            <div className="divide-y divide-gray-100">
              {products.map(p => (
                <div key={p.id} className="px-6 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <p className="font-bold text-sm text-gray-900 truncate">{p.title}</p>
                      {p.status === 'removed_by_admin' ? (
                        <span className="text-xs px-2.5 py-0.5 rounded-full border font-bold bg-red-100 text-red-800 border-red-300">
                          Removed by Admin
                        </span>
                      ) : p.status === 'removed' ? (
                        <span className="text-xs px-2.5 py-0.5 rounded-full border font-medium bg-slate-100 text-slate-700 border-slate-300">
                          Removed by Seller
                        </span>
                      ) : (
                        <span className={`text-xs px-2 py-0.5 rounded-full border font-medium ${p.status === 'published' ? 'bg-green-50 text-green-700 border-green-200' : p.status === 'rejected' ? 'bg-red-50 text-red-700 border-red-200' : 'bg-gray-50 text-gray-600 border-gray-200'}`}>
                          {p.status}
                        </span>
                      )}
                      <span className={`text-xs px-2 py-0.5 rounded-full border ${p.scan_status === 'clean' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-red-50 text-red-700 border-red-200'}`}>
                        {p.scan_status}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-gray-500 mt-1 flex-wrap">
                      <span>Category: <strong className="text-gray-700">{p.category}</strong></span>
                      <span>·</span>
                      <span>Price: <strong className="text-gray-900">₹{p.price}</strong></span>
                      <span>·</span>
                      <span>Orders: <strong className="text-gray-900">{p.orders_count ?? p.total_sales ?? 0}</strong></span>
                      {p.seller_name && (
                        <>
                          <span>·</span>
                          <span>Seller: <strong className="text-purple-700">{p.seller_name}</strong></span>
                        </>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0 flex-wrap">
                    {p.status === 'published' && (
                      <Link href={`/marketplace/${p.id}`} className="text-xs border border-gray-300 text-gray-600 px-3 py-1.5 rounded-lg hover:bg-gray-50 flex items-center gap-1 font-medium">
                        <Eye className="w-3 h-3"/>View
                      </Link>
                    )}
                    {p.status !== 'published' && p.status !== 'rejected' && p.status !== 'removed_by_admin' && (
                      <button onClick={async () => { await api.post(`/api/admin/products/${p.id}/approve`); loadAll(); toast.success('Approved'); }}
                        className="text-xs bg-green-50 text-green-700 border border-green-200 px-3 py-1.5 rounded-lg hover:bg-green-100 font-medium">Approve</button>
                    )}
                    {p.status !== 'suspended' && p.status !== 'removed_by_admin' && (
                      <button onClick={async () => { await api.post(`/api/products/${p.id}/suspend`); loadAll(); toast.success('Suspended'); }}
                        className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-3 py-1.5 rounded-lg hover:bg-amber-100 font-medium">Suspend</button>
                    )}
                    {p.status !== 'removed_by_admin' && (
                      <button
                        onClick={() => {
                          setProductToDelete(p);
                          setDeleteReason('Marketplace compliance and security standards enforcement');
                        }}
                        className="text-xs bg-red-50 text-red-700 border border-red-200 px-3 py-1.5 rounded-lg hover:bg-red-100 font-medium flex items-center gap-1"
                      >
                        <Ban className="w-3 h-3" /> Delete
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Product Delete Confirmation Modal */}
        {productToDelete && (
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-gray-100 animate-in fade-in zoom-in duration-200 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-gray-100">
                <div className="flex items-center gap-2 text-red-600 font-bold text-base">
                  <AlertTriangle className="w-5 h-5 text-red-600" />
                  Confirm Marketplace Product Removal
                </div>
                <button
                  onClick={() => setProductToDelete(null)}
                  className="w-7 h-7 flex items-center justify-center text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 font-bold"
                >
                  ✕
                </button>
              </div>

              <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 text-xs space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Product Title:</span>
                  <strong className="text-gray-900 font-semibold">{productToDelete.title}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Product ID:</span>
                  <span className="font-mono text-gray-700">{productToDelete.id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Creator / Seller:</span>
                  <span className="font-medium text-purple-700">{productToDelete.seller_name || productToDelete.seller_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Price:</span>
                  <span className="font-bold text-gray-900">₹{productToDelete.price}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Historical Orders:</span>
                  <span className="font-bold text-blue-600">{productToDelete.orders_count ?? productToDelete.total_sales ?? 0}</span>
                </div>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-gray-700 block">Reason for Removal</label>
                <input
                  type="text"
                  value={deleteReason}
                  onChange={e => setDeleteReason(e.target.value)}
                  placeholder="e.g. Copyright infringement, malware, quality breach"
                  className="w-full text-xs p-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-red-500 outline-none"
                />
              </div>

              <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 space-y-1">
                <strong className="font-bold flex items-center gap-1 text-amber-950">
                  <Shield className="w-3.5 h-3.5 text-amber-600" /> Soft-Deletion Policy
                </strong>
                <p className="text-amber-800 leading-relaxed text-[11px]">
                  This product will be immediately delisted from the marketplace search and catalog. New purchases will be blocked. Existing buyers will retain access to historical downloads to maintain entitlement integrity.
                </p>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setProductToDelete(null)}
                  className="flex-1 py-2.5 px-4 border border-gray-200 rounded-xl text-xs font-semibold text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  disabled={deleting}
                  onClick={handleDeleteProduct}
                  className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold shadow-sm disabled:opacity-50 flex items-center justify-center gap-1.5"
                >
                  {deleting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Ban className="w-3.5 h-3.5" />}
                  Confirm Permanent Removal
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
