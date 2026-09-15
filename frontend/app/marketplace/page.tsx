'use client';
import { useState, useEffect, useCallback, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import api from '@/lib/api';
import ProductCard from '@/components/ui/ProductCard';
import { 
  Search, SlidersHorizontal, ChevronLeft, ChevronRight, X, 
  Layers, Sparkles, Code2, BookOpen, Briefcase, FileSpreadsheet, 
  Palette, FileText, CheckCircle2, RotateCcw
} from 'lucide-react';

const CATEGORIES = [
  { name: 'All', icon: Layers },
  { name: 'Programming', icon: Code2 },
  { name: 'Design', icon: Palette },
  { name: 'Education', icon: BookOpen },
  { name: 'Business', icon: Briefcase },
  { name: 'Templates', icon: FileSpreadsheet },
  { name: 'Finance', icon: FileSpreadsheet },
  { name: 'Documents', icon: FileText },
  { name: 'Graphics', icon: Palette },
  { name: 'Ebooks', icon: BookOpen },
];

const SORTS = [
  { value: 'newest', label: 'Newest Arrivals' },
  { value: 'popular', label: 'Most Popular' },
  { value: 'price_low', label: 'Price: Low to High' },
  { value: 'price_high', label: 'Price: High to Low' },
  { value: 'rating', label: 'Highest Rated' },
];

function MarketplaceContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [category, setCategory] = useState(searchParams.get('category') || 'All');
  const [sort, setSort] = useState('newest');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page: String(page), per_page: '12', sort });
      if (search) params.set('search', search);
      if (category && category !== 'All') params.set('category', category);
      if (minPrice) params.set('min_price', minPrice);
      if (maxPrice) params.set('max_price', maxPrice);
      const { data } = await api.get(`/api/products?${params}`);
      setProducts(data.items || []);
      setTotal(data.total || 0);
      setPages(data.pages || 1);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  }, [page, search, category, sort, minPrice, maxPrice]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchProducts();
  };

  const clearAllFilters = () => {
    setSearch('');
    setCategory('All');
    setMinPrice('');
    setMaxPrice('');
    setSort('newest');
    setPage(1);
  };

  const hasActiveFilters = Boolean(search || (category && category !== 'All') || minPrice || maxPrice || sort !== 'newest');

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      <Navbar />

      {/* Hero / Page Header */}
      <div className="bg-white border-b border-gray-200 py-10 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50 text-blue-700 text-xs font-semibold mb-2.5 border border-blue-100">
                <Sparkles className="w-3.5 h-3.5" />
                Verified Digital Assets
              </div>
              <h1 className="text-3xl font-extrabold text-gray-900 tracking-tight">Marketplace Catalog</h1>
              <p className="text-gray-500 text-sm mt-1 max-w-xl">
                Explore tamper-proof source code, templates, design systems, and guides scanned with SHA-256 integrity assurance.
              </p>
            </div>
            <div className="text-sm text-gray-500 font-medium">
              Showing <span className="text-gray-900 font-bold">{total}</span> available products
            </div>
          </div>

          {/* Search & Sort Controls Bar */}
          <div className="mt-8 flex flex-col sm:flex-row gap-3">
            <form onSubmit={handleSearch} className="flex-1 flex gap-2">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search by title, technology, file type (e.g., python, react, pdf)..."
                  className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-gray-200 rounded-xl text-sm text-gray-900 placeholder-gray-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all"
                />
                {search && (
                  <button
                    type="button"
                    onClick={() => { setSearch(''); setPage(1); }}
                    className="absolute right-3.5 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 p-0.5 rounded-full hover:bg-gray-100"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>
              <button
                type="submit"
                className="bg-blue-600 hover:bg-blue-700 text-white font-medium text-sm px-5 py-2.5 rounded-xl transition-colors shadow-sm flex items-center gap-1.5"
              >
                Search
              </button>
            </form>

            <div className="flex items-center gap-2">
              <select
                value={sort}
                onChange={(e) => { setSort(e.target.value); setPage(1); }}
                className="bg-slate-50 border border-gray-200 text-gray-700 text-sm font-medium rounded-xl px-4 py-2.5 outline-none focus:ring-2 focus:ring-blue-600 focus:bg-white transition-all cursor-pointer"
              >
                {SORTS.map((s) => (
                  <option key={s.value} value={s.value}>
                    {s.label}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={() => setShowFilters(!showFilters)}
                className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border transition-colors ${
                  showFilters || minPrice || maxPrice
                    ? 'bg-blue-50 border-blue-200 text-blue-700'
                    : 'bg-slate-50 border-gray-200 text-gray-700 hover:bg-gray-100'
                }`}
              >
                <SlidersHorizontal className="w-4 h-4" />
                <span>Filters</span>
                {(minPrice || maxPrice) && (
                  <span className="w-2 h-2 rounded-full bg-blue-600"></span>
                )}
              </button>
            </div>
          </div>

          {/* Filter Drawer */}
          {showFilters && (
            <div className="mt-4 p-5 bg-slate-50 border border-gray-200 rounded-2xl animate-in fade-in slide-in-from-top-2 duration-150">
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3 w-full sm:w-auto">
                  <span className="text-xs font-semibold text-gray-700 uppercase tracking-wider">Price Range (₹):</span>
                  <div className="flex items-center gap-2">
                    <input
                      type="number"
                      placeholder="Min ₹"
                      value={minPrice}
                      onChange={(e) => setMinPrice(e.target.value)}
                      className="w-28 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                    <span className="text-gray-400 text-sm">to</span>
                    <input
                      type="number"
                      placeholder="Max ₹"
                      value={maxPrice}
                      onChange={(e) => setMaxPrice(e.target.value)}
                      className="w-28 px-3 py-1.5 bg-white border border-gray-200 rounded-lg text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-600"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto justify-end">
                  <button
                    onClick={() => { setMinPrice(''); setMaxPrice(''); setPage(1); }}
                    className="text-xs font-semibold text-gray-500 hover:text-gray-800 px-3 py-1.5 rounded-lg hover:bg-gray-200/60 transition-colors"
                  >
                    Clear Price
                  </button>
                  <button
                    onClick={() => { setPage(1); fetchProducts(); }}
                    className="text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white px-4 py-1.5 rounded-lg transition-colors"
                  >
                    Apply Filter
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Category Tabs */}
          <div className="mt-6 flex gap-2 overflow-x-auto pb-2 scrollbar-none">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              const isSelected = category === cat.name;
              return (
                <button
                  key={cat.name}
                  onClick={() => { setCategory(cat.name); setPage(1); }}
                  className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold tracking-wide whitespace-nowrap transition-all border ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-500/20'
                      : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${isSelected ? 'text-white' : 'text-gray-500'}`} />
                  {cat.name}
                </button>
              );
            })}
          </div>

          {/* Active Filter Chips */}
          {hasActiveFilters && (
            <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2 flex-wrap text-xs">
              <span className="text-gray-400 font-medium">Active filters:</span>
              {category !== 'All' && (
                <span className="inline-flex items-center gap-1 bg-blue-50 border border-blue-100 text-blue-700 px-2.5 py-1 rounded-md font-medium">
                  Category: {category}
                  <X className="w-3 h-3 cursor-pointer hover:text-blue-900" onClick={() => setCategory('All')} />
                </span>
              )}
              {search && (
                <span className="inline-flex items-center gap-1 bg-blue-50 border border-blue-100 text-blue-700 px-2.5 py-1 rounded-md font-medium">
                  Search: &quot;{search}&quot;
                  <X className="w-3 h-3 cursor-pointer hover:text-blue-900" onClick={() => setSearch('')} />
                </span>
              )}
              {(minPrice || maxPrice) && (
                <span className="inline-flex items-center gap-1 bg-blue-50 border border-blue-100 text-blue-700 px-2.5 py-1 rounded-md font-medium">
                  Price: ₹{minPrice || '0'} - ₹{maxPrice || '∞'}
                  <X className="w-3 h-3 cursor-pointer hover:text-blue-900" onClick={() => { setMinPrice(''); setMaxPrice(''); }} />
                </span>
              )}
              <button
                onClick={clearAllFilters}
                className="inline-flex items-center gap-1 text-gray-500 hover:text-gray-800 ml-1 font-medium hover:underline"
              >
                <RotateCcw className="w-3 h-3" /> Reset all
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Main Grid Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 w-full flex-1">
        {loading ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="bg-white border border-gray-200 rounded-2xl p-4 animate-pulse space-y-4">
                <div className="h-44 bg-slate-100 rounded-xl" />
                <div className="space-y-2">
                  <div className="h-4 bg-slate-100 rounded w-1/3" />
                  <div className="h-5 bg-slate-100 rounded w-4/5" />
                  <div className="h-4 bg-slate-100 rounded w-full" />
                </div>
                <div className="pt-4 border-t border-slate-100 flex justify-between">
                  <div className="h-5 bg-slate-100 rounded w-1/4" />
                  <div className="h-5 bg-slate-100 rounded w-1/4" />
                </div>
              </div>
            ))}
          </div>
        ) : products.length > 0 ? (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>

            {/* Pagination */}
            {pages > 1 && (
              <div className="flex justify-center items-center gap-3 mt-12 pt-8 border-t border-gray-200">
                <button
                  onClick={() => { setPage((p) => Math.max(1, p - 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                  disabled={page === 1}
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-gray-200 bg-white rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition-all"
                >
                  <ChevronLeft className="w-4 h-4" /> Previous
                </button>
                <span className="text-sm font-medium text-gray-600 px-3">
                  Page <span className="font-bold text-gray-900">{page}</span> of <span className="font-bold text-gray-900">{pages}</span>
                </span>
                <button
                  onClick={() => { setPage((p) => Math.min(pages, p + 1)); window.scrollTo({ top: 0, behavior: 'smooth' }); }}
                  disabled={page === pages}
                  className="inline-flex items-center gap-1.5 px-4 py-2 border border-gray-200 bg-white rounded-xl text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed shadow-sm transition-all"
                >
                  Next <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </>
        ) : (
          <div className="max-w-md mx-auto text-center py-20 bg-white border border-gray-200 rounded-3xl p-10 shadow-sm">
            <div className="w-16 h-16 bg-blue-50 border border-blue-100 rounded-2xl flex items-center justify-center mx-auto mb-5">
              <FileText className="w-8 h-8 text-blue-500" />
            </div>
            <h3 className="text-lg font-bold text-gray-900 mb-2">No matching products found</h3>
            <p className="text-gray-500 text-sm leading-relaxed mb-6">
              We couldn&apos;t find any digital assets matching your criteria. Try adjusting your search keywords or resetting category filters.
            </p>
            <button
              onClick={clearAllFilters}
              className="inline-flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-5 py-2.5 rounded-xl shadow-sm transition-colors"
            >
              <RotateCcw className="w-4 h-4" /> Reset all filters
            </button>
          </div>
        )}
      </main>

      <Footer />
    </div>
  );
}

export default function MarketplacePage() {
  return (
    <Suspense>
      <MarketplaceContent />
    </Suspense>
  );
}
