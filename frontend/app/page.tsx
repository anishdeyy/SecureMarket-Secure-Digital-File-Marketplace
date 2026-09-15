'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';
import ProductCard from '@/components/ui/ProductCard';
import api from '@/lib/api';
import {
  Search, Shield, ShieldCheck, ArrowRight, Code2, Palette, FileText,
  BookOpen, Briefcase, BarChart3, Megaphone, Layers, Sparkles,
  CreditCard, DownloadCloud, CheckCircle2, Lock, Zap, Check, Star
} from 'lucide-react';
import { useRouter } from 'next/navigation';

const CATEGORIES = [
  {
    name: 'Programming',
    desc: 'Code, scripts and developer resources',
    icon: Code2,
    badge: 'Python, React, SQL',
  },
  {
    name: 'Design',
    desc: 'UI kits, templates and creative assets',
    icon: Palette,
    badge: 'Figma, Tailwind, UI',
  },
  {
    name: 'Documents',
    desc: 'Guides, whitepapers and resumes',
    icon: FileText,
    badge: 'PDF, DOCX, Guides',
  },
  {
    name: 'Education',
    desc: 'Courses, workbooks and tutorials',
    icon: BookOpen,
    badge: 'Ebooks, Learning',
  },
  {
    name: 'Business',
    desc: 'Pitch decks, contracts and strategies',
    icon: Briefcase,
    badge: 'Proposals, Plans',
  },
  {
    name: 'Finance',
    desc: 'Financial models, sheets and ROI tools',
    icon: BarChart3,
    badge: 'Spreadsheets, XLSX',
  },
  {
    name: 'Marketing',
    desc: 'SEO playbooks, copy and swipe files',
    icon: Megaphone,
    badge: 'Campaigns, Content',
  },
  {
    name: 'Graphics',
    desc: 'Icon sets, vectors and illustration packs',
    icon: Layers,
    badge: 'SVG, PNG Packs',
  },
];

const HOW_IT_WORKS = [
  {
    step: '01',
    title: 'Discover & Inspect',
    desc: 'Browse curated digital assets with transparent AI quality breakdowns, file previews, and verified creator profiles before purchasing.',
    icon: Search,
  },
  {
    step: '02',
    title: 'Secure Instant Checkout',
    desc: 'Pay safely with modern payment methods including UPI, cards, and net banking with end-to-end transaction security.',
    icon: CreditCard,
  },
  {
    step: '03',
    title: 'Instant Download & Verified Delivery',
    desc: 'Access your purchased assets immediately with cryptographic integrity seals ensuring byte-for-byte authenticity.',
    icon: DownloadCloud,
  },
];

const TRUST_FEATURES = [
  {
    icon: ShieldCheck,
    title: 'Curated Quality & AI Scoring',
    desc: 'Every file is assessed on usefulness, structure, and completeness with objective scores.',
  },
  {
    icon: CreditCard,
    title: 'Protected Web2 Payments',
    desc: 'UPI, credit/debit cards, and net banking via trusted Razorpay payment rails.',
  },
  {
    icon: Shield,
    title: 'Pre-Screened Security',
    desc: 'Automated malware inspection screens all uploads before they are listed on the marketplace.',
  },
  {
    icon: Lock,
    title: 'Cryptographic Authenticity',
    desc: 'SHA-256 digital fingerprinting ensures downloaded files are never modified or tampered with.',
  },
  {
    icon: DownloadCloud,
    title: 'Direct Signed Delivery',
    desc: 'Expiring signed authorization links deliver files securely straight to your local device.',
  },
  {
    icon: Sparkles,
    title: 'AI Metadata & Search',
    desc: 'Gemini AI indexes topics, difficulty levels, and summaries for effortless resource discovery.',
  },
];

const TRENDING_TAGS = ['Python', 'Financial Models', 'Resume Templates', 'React', 'Startup Pitch Decks'];

export default function HomePage() {
  const [search, setSearch] = useState('');
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.get('/api/products?per_page=8&sort=popular')
      .then(r => setProducts(r.data.items || []))
      .catch(() => setProducts([]))
      .finally(() => setLoading(false));
  }, []);

  const handleSearch = (e?: React.FormEvent, term?: string) => {
    if (e) e.preventDefault();
    const query = term !== undefined ? term : search;
    if (query.trim()) {
      router.push(`/marketplace?search=${encodeURIComponent(query.trim())}`);
    }
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />

      {/* HERO SECTION */}
      <section className="relative overflow-hidden pt-12 pb-20 md:pt-20 md:pb-28 border-b border-gray-100 bg-gradient-to-b from-slate-50/70 via-white to-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Hero Column */}
            <div className="lg:col-span-7 text-left space-y-6">
              {/* Category badge / pre-header */}
              <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200/80 shadow-xs">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Curated digital resources • AI-assisted discovery • Secure checkout</span>
              </div>

              {/* Primary Headline */}
              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-gray-950 tracking-tight leading-[1.12]">
                Discover digital resources,<br />
                <span className="text-blue-600">made for your next project.</span>
              </h1>

              {/* Supporting Description */}
              <p className="text-base sm:text-lg text-gray-600 max-w-xl leading-relaxed">
                Browse verified developer guides, spreadsheets, UI templates, design systems, and business documents. Instant access, transparent quality scores, and secure payments.
              </p>

              {/* Search Bar */}
              <form onSubmit={(e) => handleSearch(e)} className="max-w-xl pt-2">
                <div className="flex items-center gap-2 p-1.5 bg-white border border-gray-300 rounded-2xl shadow-sm focus-within:ring-2 focus-within:ring-blue-500/30 focus-within:border-blue-600 transition-all">
                  <Search className="w-5 h-5 text-gray-400 ml-3 flex-shrink-0" />
                  <input
                    type="text"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    placeholder="Search guides, templates, code, spreadsheets..."
                    className="flex-1 outline-none text-sm text-gray-900 placeholder-gray-400 bg-transparent py-2 px-1"
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-5 py-3 rounded-xl shadow-xs transition-colors flex-shrink-0"
                  >
                    Search
                  </button>
                </div>
              </form>

              {/* Trending Filter Chips */}
              <div className="flex items-center gap-2 flex-wrap pt-1">
                <span className="text-xs font-medium text-gray-400">Popular:</span>
                {TRENDING_TAGS.map((tag) => (
                  <button
                    key={tag}
                    onClick={() => handleSearch(undefined, tag)}
                    className="text-xs font-medium text-gray-600 bg-gray-100 hover:bg-blue-50 hover:text-blue-600 px-3 py-1 rounded-lg transition-colors"
                  >
                    {tag}
                  </button>
                ))}
              </div>

              {/* Primary Action Buttons */}
              <div className="flex flex-wrap items-center gap-3 pt-2">
                <Link
                  href="/marketplace"
                  className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-6 py-3.5 rounded-xl shadow-sm hover:shadow transition-all inline-flex items-center gap-2"
                >
                  Explore Marketplace <ArrowRight className="w-4 h-4" />
                </Link>
                <Link
                  href="/seller/become"
                  className="bg-white hover:bg-gray-50 text-gray-800 border border-gray-200 text-sm font-semibold px-6 py-3.5 rounded-xl transition-all shadow-xs"
                >
                  Start Selling
                </Link>
              </div>

              {/* Benefit Chips Row */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-4 border-t border-gray-100 text-xs text-gray-600">
                <div className="flex items-center gap-1.5 font-medium">
                  <Zap className="w-4 h-4 text-blue-600 flex-shrink-0" />
                  <span>Instant digital access</span>
                </div>
                <div className="flex items-center gap-1.5 font-medium">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
                  <span>Curated resources</span>
                </div>
                <div className="flex items-center gap-1.5 font-medium">
                  <Sparkles className="w-4 h-4 text-purple-600 flex-shrink-0" />
                  <span>AI-assisted info</span>
                </div>
                <div className="flex items-center gap-1.5 font-medium">
                  <ShieldCheck className="w-4 h-4 text-teal-600 flex-shrink-0" />
                  <span>Secure checkout</span>
                </div>
              </div>
            </div>

            {/* Right Hero Column: Featured Product Showcase Card */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md w-full">
                {/* Background ambient glow */}
                <div className="absolute -top-6 -right-6 w-64 h-64 bg-blue-100/70 rounded-full blur-3xl pointer-events-none" />
                <div className="absolute -bottom-6 -left-6 w-64 h-64 bg-indigo-100/70 rounded-full blur-3xl pointer-events-none" />

                {/* Floating badge */}
                <div className="absolute -top-3.5 right-6 z-10">
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold bg-blue-600 text-white shadow-md border border-blue-400/40 animate-pulse">
                    <Sparkles className="w-3.5 h-3.5" /> Featured Asset
                  </span>
                </div>

                {/* Main Featured Showcase Card */}
                <div className="relative bg-white border border-gray-200 rounded-3xl shadow-xl p-6 sm:p-7 space-y-5">
                  {/* Category & Badge */}
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[11px] font-bold uppercase tracking-wider px-2.5 py-1 rounded-md bg-blue-50 text-blue-700 border border-blue-100">
                      Programming / Data Science
                    </span>
                    <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full flex items-center gap-1">
                      <Check className="w-3 h-3 text-emerald-600" /> Verified
                    </span>
                  </div>

                  {/* Title & Creator */}
                  <div>
                    <h3 className="text-xl font-bold text-gray-950 leading-snug">
                      Complete Python Data Analysis Guide
                    </h3>
                    <p className="text-xs text-gray-500 mt-1">
                      PDF Guide + Real-World Exercises • Created by Verified Author
                    </p>
                  </div>

                  {/* Visual Preview / Feature Card */}
                  <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-4 text-white space-y-3 shadow-inner">
                    <div className="flex items-center justify-between text-xs text-slate-400 border-b border-slate-700/60 pb-2">
                      <span className="flex items-center gap-1.5 font-mono">
                        <Code2 className="w-3.5 h-3.5 text-blue-400" /> python-analysis.pdf
                      </span>
                      <span className="text-[11px] bg-slate-800 text-slate-300 px-2 py-0.5 rounded">2.5 MB</span>
                    </div>
                    <div className="space-y-1.5 text-xs text-slate-300 font-mono">
                      <p className="text-emerald-400">✓ Pandas DataFrame Pipelines</p>
                      <p className="text-blue-300">✓ NumPy Vectorized Computations</p>
                      <p className="text-indigo-300">✓ Matplotlib & Seaborn Visuals</p>
                    </div>
                  </div>

                  {/* AI Quality & Price Row */}
                  <div className="flex items-center justify-between pt-2 border-t border-gray-100">
                    <div>
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs font-bold text-blue-700 bg-blue-50 border border-blue-200 px-2.5 py-0.5 rounded-md">
                          AI Quality: 92 · High Quality
                        </span>
                      </div>
                      <span className="text-[11px] text-gray-400 block mt-1">
                        Verified structure & depth
                      </span>
                    </div>

                    <div className="text-right">
                      <span className="text-2xl font-black text-gray-950">₹499</span>
                      <span className="text-[11px] text-gray-400 block -mt-1">One-time purchase</span>
                    </div>
                  </div>

                  {/* CTA Action */}
                  <Link
                    href="/marketplace/prod0001-0000-0000-0000-000000000001"
                    className="w-full py-3 px-4 bg-gray-900 hover:bg-blue-600 text-white rounded-xl text-xs font-bold transition-colors flex items-center justify-center gap-2 shadow-sm"
                  >
                    View Product Details <ArrowRight className="w-4 h-4" />
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CATEGORIES SECTION */}
      <section className="py-16 sm:py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">Explore Marketplace</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">Browse by Category</h2>
              <p className="text-sm text-gray-500 mt-1">Carefully organized digital assets across engineering, design, and business.</p>
            </div>
            <Link
              href="/marketplace"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1 group"
            >
              View all products <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
            {CATEGORIES.map(({ name, desc, icon: Icon, badge }) => (
              <Link
                key={name}
                href={`/marketplace?category=${encodeURIComponent(name)}`}
                className="group p-5 bg-white border border-gray-200 rounded-2xl hover:border-blue-200 hover:shadow-md hover:-translate-y-0.5 transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="w-10 h-10 rounded-xl bg-slate-50 border border-gray-200 group-hover:bg-blue-50 group-hover:border-blue-200 text-gray-700 group-hover:text-blue-600 flex items-center justify-center transition-colors mb-3.5">
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-gray-900 text-base mb-1 group-hover:text-blue-600 transition-colors">
                    {name}
                  </h3>
                  <p className="text-xs text-gray-500 leading-relaxed">
                    {desc}
                  </p>
                </div>
                <div className="pt-4 mt-2 border-t border-gray-100 flex items-center justify-between text-[11px] text-gray-400">
                  <span>{badge}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-gray-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* TRENDING PRODUCTS SECTION */}
      <section className="py-16 sm:py-20 bg-slate-50/60 border-t border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-blue-600 mb-1">Curated Resources</p>
              <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">Trending This Week</h2>
              <p className="text-sm text-gray-500 mt-1">High-quality guides, templates, and packages with verified authenticity.</p>
            </div>
            <Link
              href="/marketplace"
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 inline-flex items-center gap-1 group"
            >
              Explore all {products.length} products <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>

          {loading ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map(i => (
                <div key={i} className="bg-white border border-gray-200 rounded-2xl h-80 animate-pulse p-4 space-y-4">
                  <div className="h-40 bg-gray-100 rounded-xl" />
                  <div className="h-4 bg-gray-100 rounded w-3/4" />
                  <div className="h-3 bg-gray-100 rounded w-1/2" />
                </div>
              ))}
            </div>
          ) : products.length === 0 ? (
            <div className="bg-white border border-gray-200 rounded-2xl p-12 text-center max-w-md mx-auto">
              <Shield className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-base font-semibold text-gray-800 mb-1">No products found</p>
              <p className="text-xs text-gray-500 mb-4">Be the first to list a verified digital asset.</p>
              <Link href="/seller/upload" className="inline-block bg-blue-600 text-white text-xs font-semibold px-4 py-2.5 rounded-xl">
                Upload Product
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
              {products.map(p => (
                <ProductCard key={p.id} product={p} />
              ))}
            </div>
          )}
        </div>
      </section>

      {/* HOW SECUREMARKET WORKS (3 Steps) */}
      <section className="py-16 sm:py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto text-center mb-16 space-y-3">
            <p className="text-xs font-bold uppercase tracking-wider text-blue-600">Simple & Transparent</p>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-950 tracking-tight">
              How SecureMarket Works
            </h2>
            <p className="text-sm sm:text-base text-gray-500 leading-relaxed">
              From discovering top-tier resources to verified byte-for-byte downloads in seconds.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {HOW_IT_WORKS.map(({ step, title, desc, icon: Icon }) => (
              <div
                key={step}
                className="relative p-7 bg-white border border-gray-200 rounded-3xl hover:border-blue-200 hover:shadow-md transition-all space-y-4"
              >
                <div className="flex items-center justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                    <Icon className="w-6 h-6" />
                  </div>
                  <span className="text-3xl font-black text-slate-200 font-mono">
                    {step}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-gray-950">{title}</h3>
                <p className="text-xs sm:text-sm text-gray-600 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* SELLER CALL TO ACTION BANNER */}
      <section className="py-16 bg-gradient-to-r from-blue-600 to-indigo-700 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6">
          <span className="inline-block px-3 py-1 bg-white/15 rounded-full text-xs font-semibold text-blue-100 backdrop-blur-sm">
            Have Something Worth Sharing?
          </span>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight">
            Monetize your code, guides, and templates
          </h2>
          <p className="text-base text-blue-100 max-w-xl mx-auto leading-relaxed">
            Upload your files, let Gemini AI generate titles and summaries, and get paid directly via secure Web2 payments.
          </p>
          <div className="pt-2">
            <Link
              href="/seller/become"
              className="bg-white text-blue-700 hover:bg-blue-50 text-sm font-bold px-8 py-3.5 rounded-xl shadow-lg hover:shadow-xl transition-all inline-flex items-center gap-2"
            >
              Start Selling Today <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </section>

      {/* EVERYTHING YOU NEED TO BUY WITH CONFIDENCE (Trust Section) */}
      <section className="py-16 sm:py-24 bg-slate-50/50 border-t border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="max-w-2xl mx-auto text-center mb-16 space-y-3">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Buyer Protection & Authenticity
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold text-gray-950 tracking-tight">
              Everything you need to buy with confidence
            </h2>
            <p className="text-sm sm:text-base text-gray-500 leading-relaxed">
              We combine transparent AI quality assessments with enterprise-grade cryptographic guarantees so you always get exactly what you paid for.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {TRUST_FEATURES.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="p-6 bg-white border border-gray-200 rounded-2xl hover:border-gray-300 hover:shadow-sm transition-all space-y-3"
              >
                <div className="w-10 h-10 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-gray-900 text-base">{title}</h3>
                <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
}
