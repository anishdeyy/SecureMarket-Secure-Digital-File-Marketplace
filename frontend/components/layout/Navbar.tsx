'use client';
import Link from 'next/link';
import { useAuth } from '@/lib/auth';
import { useState, useEffect } from 'react';
import {
  Shield, Bell, User, LogOut, Menu, X, LayoutDashboard,
  Package, ShoppingBag, Search, ChevronDown, PlusCircle, Heart
} from 'lucide-react';
import api from '@/lib/api';
import { useRouter } from 'next/navigation';

export default function Navbar() {
  const { user, logout, isAdmin, isSeller } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [unread, setUnread] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchOpen, setSearchOpen] = useState(false);
  const router = useRouter();

  useEffect(() => {
    if (user) {
      api.get('/api/notifications')
        .then(r => setUnread(r.data.unread_count || 0))
        .catch(() => {});
    }
  }, [user]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/marketplace?search=${encodeURIComponent(searchQuery)}`);
      setSearchOpen(false);
      setMobileOpen(false);
    }
  };

  return (
    <header className="bg-white/95 backdrop-blur-md border-b border-gray-200 sticky top-0 z-50 transition-all">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16 gap-4">
          {/* LEFT: Logo */}
          <Link href="/" className="flex items-center gap-2.5 flex-shrink-0 group">
            <div className="w-9 h-9 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm group-hover:bg-blue-700 transition-colors">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-gray-900 text-lg tracking-tight group-hover:text-blue-600 transition-colors">
              SecureMarket
            </span>
          </Link>

          {/* CENTER: Navigation Links */}
          <nav className="hidden md:flex items-center gap-8 text-sm font-medium text-gray-600">
            <Link href="/marketplace" className="hover:text-gray-900 transition-colors">
              Browse
            </Link>
            <Link href="/marketplace?category=Programming" className="hover:text-gray-900 transition-colors">
              Categories
            </Link>
            {user ? (
              isSeller() ? (
                <>
                  <Link href="/seller/dashboard" className="hover:text-gray-900 transition-colors flex items-center gap-1 text-purple-700 font-semibold">
                    <Package className="w-4 h-4 text-purple-600" /> Seller Dashboard
                  </Link>
                  <Link href="/seller/upload" className="hover:text-gray-900 transition-colors flex items-center gap-1">
                    <PlusCircle className="w-4 h-4 text-blue-600" /> Upload Product
                  </Link>
                </>
              ) : isAdmin() ? (
                <Link href="/admin/dashboard" className="hover:text-gray-900 transition-colors flex items-center gap-1 text-red-700 font-semibold">
                  <LayoutDashboard className="w-4 h-4 text-red-600" /> Admin Console
                </Link>
              ) : (
                <Link href="/purchases" className="hover:text-gray-900 transition-colors flex items-center gap-1">
                  <ShoppingBag className="w-4 h-4 text-gray-500" /> My Purchases
                </Link>
              )
            ) : null}
          </nav>

          {/* RIGHT: Search & User / Auth Actions */}
          <div className="hidden md:flex items-center gap-3">
            {/* Quick Search */}
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search resources..."
                className="w-48 lg:w-64 pl-9 pr-3 py-1.5 text-xs bg-gray-50 border border-gray-200 rounded-lg text-gray-900 placeholder-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              />
              <Search className="w-4 h-4 text-gray-400 absolute left-2.5 top-2 pointer-events-none" />
            </form>

            {user ? (
              <div className="flex items-center gap-2">
                <Link
                  href="/wishlist"
                  className="p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
                  title="Wishlist"
                >
                  <Heart className="w-4 h-4" />
                </Link>

                <Link
                  href="/notifications"
                  className="relative p-2 text-gray-500 hover:text-gray-900 rounded-lg hover:bg-gray-50 transition-colors"
                  title="Notifications"
                >
                  <Bell className="w-4 h-4" />
                  {unread > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full" />
                  )}
                </Link>

                {/* User Dropdown */}
                <div className="relative group">
                  <button className="flex items-center gap-2 text-xs font-semibold text-gray-700 hover:text-gray-900 pl-2 pr-2.5 py-1.5 rounded-lg border border-gray-200 hover:bg-gray-50 transition-all">
                    <div className="w-6 h-6 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs">
                      {user.username.slice(0, 1).toUpperCase()}
                    </div>
                    <span className="max-w-[100px] truncate">{user.username}</span>
                    <ChevronDown className="w-3.5 h-3.5 text-gray-400 group-hover:rotate-180 transition-transform" />
                  </button>

                  <div className="absolute right-0 top-full mt-1.5 w-60 bg-white border border-gray-200 rounded-xl shadow-xl py-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
                    <div className="px-4 py-2.5 border-b border-gray-100">
                      <div className="flex items-center justify-between gap-2">
                        <p className="text-xs font-bold text-gray-900 truncate">{user.username}</p>
                        {isAdmin() && (
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-red-100 text-red-700 rounded-full border border-red-200">
                            Admin
                          </span>
                        )}
                        {isSeller() && (
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full border border-purple-200">
                            Seller
                          </span>
                        )}
                        {!isAdmin() && !isSeller() && (
                          <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full border border-blue-200">
                            Buyer
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-gray-400 truncate mt-0.5">{user.email}</p>
                    </div>

                    <div className="py-1">
                      {isAdmin() && (
                        <Link href="/admin/dashboard" className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-red-700 hover:bg-red-50 transition-colors">
                          <LayoutDashboard className="w-3.5 h-3.5 text-red-600" /> Admin Dashboard
                        </Link>
                      )}

                      {isSeller() && (
                        <>
                          <Link href="/seller/dashboard" className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-purple-700 hover:bg-purple-50 transition-colors">
                            <Package className="w-3.5 h-3.5 text-purple-600" /> Seller Dashboard
                          </Link>
                          <Link href="/seller/upload" className="flex items-center gap-2.5 px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 transition-colors">
                            <PlusCircle className="w-3.5 h-3.5 text-blue-600" /> Upload Product
                          </Link>
                        </>
                      )}

                      {!isAdmin() && !isSeller() && (
                        <>
                          <Link href="/dashboard" className="flex items-center gap-2.5 px-4 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50 transition-colors">
                            <User className="w-3.5 h-3.5 text-blue-600" /> Buyer Dashboard
                          </Link>
                          <Link href="/purchases" className="flex items-center gap-2.5 px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 transition-colors">
                            <ShoppingBag className="w-3.5 h-3.5 text-gray-500" /> My Purchases
                          </Link>
                          <Link href="/wishlist" className="flex items-center gap-2.5 px-4 py-2 text-xs text-gray-700 hover:bg-gray-50 transition-colors">
                            <Heart className="w-3.5 h-3.5 text-pink-500" /> My Wishlist
                          </Link>
                        </>
                      )}
                    </div>

                    <div className="my-1 border-t border-gray-100" />
                    <button
                      onClick={logout}
                      className="flex items-center gap-2.5 px-4 py-2 text-xs text-red-600 hover:bg-red-50 w-full text-left font-medium transition-colors"
                    >
                      <LogOut className="w-3.5 h-3.5" /> Sign Out
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="text-xs font-semibold text-gray-700 hover:text-gray-900 px-3.5 py-2 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-4 py-2 rounded-lg shadow-sm transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile hamburger button */}
          <div className="flex md:hidden items-center gap-2">
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="p-2 text-gray-500 hover:text-gray-900"
              aria-label="Search"
            >
              <Search className="w-5 h-5" />
            </button>
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="p-2 text-gray-600 hover:text-gray-900 rounded-lg hover:bg-gray-100"
              aria-label="Toggle Menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Search Input */}
        {searchOpen && (
          <div className="md:hidden pb-3 pt-1 border-t border-gray-100">
            <form onSubmit={handleSearch} className="relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search templates, code, guides..."
                className="w-full pl-9 pr-3 py-2 text-sm bg-gray-50 border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
              <Search className="w-4 h-4 text-gray-400 absolute left-3 top-3 pointer-events-none" />
            </form>
          </div>
        )}
      </div>

      {/* Mobile Drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-gray-200 bg-white px-4 py-5 space-y-4 shadow-xl">
          <nav className="space-y-1">
            <Link
              href="/marketplace"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg"
            >
              Browse Marketplace
            </Link>
            <Link
              href="/marketplace?category=Programming"
              onClick={() => setMobileOpen(false)}
              className="block px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 rounded-lg"
            >
              Categories
            </Link>
            {user && isSeller() && (
              <Link
                href="/seller/upload"
                onClick={() => setMobileOpen(false)}
                className="block px-3 py-2 text-sm font-medium text-purple-600 hover:bg-purple-50 rounded-lg"
              >
                + Upload New Product
              </Link>
            )}
          </nav>

          <div className="pt-3 border-t border-gray-100">
            {user ? (
              <div className="space-y-1">
                <div className="px-3 py-2 bg-gray-50 rounded-lg mb-2 flex items-center justify-between">
                  <div>
                    <p className="text-xs font-semibold text-gray-900">{user.username}</p>
                    <p className="text-[11px] text-gray-500 truncate">{user.email}</p>
                  </div>
                  {isAdmin() && <span className="text-[10px] font-bold px-2 py-0.5 bg-red-100 text-red-700 rounded-full">Admin</span>}
                  {isSeller() && <span className="text-[10px] font-bold px-2 py-0.5 bg-purple-100 text-purple-700 rounded-full">Seller</span>}
                  {!isAdmin() && !isSeller() && <span className="text-[10px] font-bold px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full">Buyer</span>}
                </div>

                {isAdmin() && (
                  <Link href="/admin/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs font-semibold text-red-700 hover:bg-red-50 rounded-lg">
                    Admin Dashboard
                  </Link>
                )}

                {isSeller() && (
                  <>
                    <Link href="/seller/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs font-semibold text-purple-700 hover:bg-purple-50 rounded-lg">
                      Seller Dashboard
                    </Link>
                    <Link href="/seller/upload" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 rounded-lg">
                      Upload Product
                    </Link>
                  </>
                )}

                {!isAdmin() && !isSeller() && (
                  <>
                    <Link href="/dashboard" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs font-semibold text-blue-700 hover:bg-blue-50 rounded-lg">
                      Buyer Dashboard
                    </Link>
                    <Link href="/purchases" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 rounded-lg">
                      My Purchases
                    </Link>
                    <Link href="/wishlist" onClick={() => setMobileOpen(false)} className="block px-3 py-2 text-xs text-gray-700 hover:bg-gray-50 rounded-lg">
                      My Wishlist
                    </Link>
                  </>
                )}

                <button
                  onClick={() => { logout(); setMobileOpen(false); }}
                  className="block w-full text-left px-3 py-2 text-xs text-red-600 font-medium hover:bg-red-50 rounded-lg"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-2 pt-2">
                <Link
                  href="/login"
                  onClick={() => setMobileOpen(false)}
                  className="text-center py-2.5 text-sm font-medium text-gray-700 border border-gray-200 rounded-xl"
                >
                  Sign In
                </Link>
                <Link
                  href="/register"
                  onClick={() => setMobileOpen(false)}
                  className="text-center py-2.5 text-sm font-medium text-white bg-blue-600 rounded-xl"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
