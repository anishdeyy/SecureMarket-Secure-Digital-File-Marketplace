'use client';
import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api from '@/lib/api';
import { useAuth } from '@/lib/auth';
import toast from 'react-hot-toast';
import { Heart, Trash2, Loader2, FileText, ShoppingCart } from 'lucide-react';

export default function WishlistPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [items, setItems] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [removing, setRemoving] = useState<string | null>(null);

  useEffect(() => {
    if (!user) { router.push('/login'); return; }
    api.get('/api/wishlist').then(r => setItems(r.data.items || [])).catch(() => {}).finally(() => setLoading(false));
  }, [user]);

  const remove = async (productId: string) => {
    setRemoving(productId);
    try {
      await api.delete(`/api/wishlist/${productId}`);
      setItems(prev => prev.filter(i => i.product_id !== productId));
      toast.success('Removed from wishlist');
    } catch { toast.error('Failed'); }
    finally { setRemoving(null); }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex flex-col"><Navbar />
      <div className="flex-1 flex items-center justify-center"><Loader2 className="w-7 h-7 animate-spin text-blue-600" /></div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-8 w-full">
        <h1 className="text-2xl font-bold text-gray-900 mb-2 flex items-center gap-2">
          <Heart className="w-6 h-6 text-red-500" /> My Wishlist
        </h1>
        <p className="text-gray-500 text-sm mb-8">{items.length} saved item{items.length !== 1 ? 's' : ''}</p>

        {items.length === 0 ? (
          <div className="text-center py-20 bg-white border border-gray-200 rounded-2xl">
            <Heart className="w-12 h-12 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-500 mb-4">Your wishlist is empty</p>
            <Link href="/marketplace" className="bg-blue-600 text-white px-6 py-2.5 rounded-xl font-semibold hover:bg-blue-700 inline-block">Browse Marketplace</Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {items.map(item => (
              <div key={item.id} className="bg-white border border-gray-200 rounded-xl overflow-hidden hover:shadow-sm transition-shadow">
                <div className="h-36 bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center">
                  {item.preview_image_url ? (
                    <img src={item.preview_image_url} alt={item.title} className="w-full h-full object-cover" />
                  ) : (
                    <FileText className="w-10 h-10 text-gray-300" />
                  )}
                </div>
                <div className="p-4">
                  <div className="flex justify-between items-start gap-2">
                    <div className="flex-1 min-w-0">
                      <span className="text-xs text-gray-400 uppercase">{item.category}</span>
                      <Link href={`/marketplace/${item.product_id}`}>
                        <h3 className="font-semibold text-gray-900 text-sm mt-0.5 line-clamp-2 hover:text-blue-600 transition-colors">{item.title}</h3>
                      </Link>
                    </div>
                    <p className="font-bold text-gray-900 flex-shrink-0">{item.price === 0 ? 'Free' : `₹${item.price}`}</p>
                  </div>
                  <div className="flex items-center justify-between mt-3 gap-2">
                    <Link href={`/marketplace/${item.product_id}`}
                      className="flex-1 bg-blue-600 text-white text-sm py-2 rounded-lg font-semibold hover:bg-blue-700 transition-colors text-center flex items-center justify-center gap-1.5">
                      <ShoppingCart className="w-4 h-4" /> Buy Now
                    </Link>
                    <button onClick={() => remove(item.product_id)} disabled={removing === item.product_id}
                      className="p-2 text-gray-400 hover:text-red-500 border border-gray-200 rounded-lg hover:border-red-200 hover:bg-red-50 transition-colors">
                      {removing === item.product_id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Added {new Date(item.added_at).toLocaleDateString()}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
}
