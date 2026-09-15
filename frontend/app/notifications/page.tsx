'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import { Bell, CheckCheck, Loader2, Info, CheckCircle, AlertTriangle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';

const TYPE_ICON: Record<string, any> = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
};
const TYPE_COLOR: Record<string, string> = {
  success: 'text-green-600 bg-green-50 border-green-200',
  error: 'text-red-600 bg-red-50 border-red-200',
  warning: 'text-amber-600 bg-amber-50 border-amber-200',
  info: 'text-blue-600 bg-blue-50 border-blue-200',
};

export default function NotificationsPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [notifs, setNotifs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    api.get('/api/notifications')
      .then(r => setNotifs(r.data.notifications || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  const markAllRead = async () => {
    await api.post('/api/notifications/read-all');
    setNotifs(prev => prev.map(n => ({ ...n, is_read: true })));
    toast.success('All marked as read');
  };

  const markRead = async (id: string) => {
    await api.post(`/api/notifications/${id}/read`);
    setNotifs(prev => prev.map(n => n.id === id ? { ...n, is_read: true } : n));
  };

  const unread = notifs.filter(n => !n.is_read).length;

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-blue-600" /></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-2xl mx-auto px-4 py-8 w-full">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <Bell className="w-6 h-6 text-blue-600" /> Notifications
            </h1>
            {unread > 0 && <p className="text-sm text-gray-500 mt-1">{unread} unread</p>}
          </div>
          {unread > 0 && (
            <button onClick={markAllRead}
              className="flex items-center gap-2 text-sm text-blue-600 hover:underline font-medium">
              <CheckCheck className="w-4 h-4" /> Mark all read
            </button>
          )}
        </div>

        {notifs.length === 0 ? (
          <div className="text-center py-20 bg-white border border-gray-200 rounded-2xl">
            <Bell className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-400">No notifications yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {notifs.map(n => {
              const Icon = TYPE_ICON[n.type] || Info;
              const color = TYPE_COLOR[n.type] || TYPE_COLOR.info;
              return (
                <div key={n.id}
                  onClick={() => { if (!n.is_read) markRead(n.id); if (n.action_url) router.push(n.action_url); }}
                  className={`bg-white border rounded-xl p-4 flex gap-4 cursor-pointer hover:shadow-sm transition-all ${!n.is_read ? 'border-blue-200 bg-blue-50/30' : 'border-gray-200'}`}>
                  <div className={`w-9 h-9 rounded-lg border flex items-center justify-center flex-shrink-0 ${color}`}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm font-semibold ${!n.is_read ? 'text-gray-900' : 'text-gray-700'}`}>{n.title}</p>
                      {!n.is_read && <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0 mt-1.5" />}
                    </div>
                    <p className="text-sm text-gray-500 mt-0.5 leading-relaxed">{n.message}</p>
                    <p className="text-xs text-gray-400 mt-1.5">{new Date(n.created_at).toLocaleString('en-IN')}</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
