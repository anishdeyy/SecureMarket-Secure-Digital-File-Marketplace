import React from 'react';
import Link from 'next/link';
import { Star, ShieldCheck, ArrowRight, User } from 'lucide-react';
import FilePreview from '@/components/ui/FilePreview';

export interface Product {
  id: string;
  title: string;
  short_description?: string;
  price: number;
  category?: string;
  file_extension?: string;
  preview_image_url?: string;
  scan_status?: string;
  avg_rating?: number;
  review_count?: number;
  quality?: {
    score?: number;
    level?: string;
  };
  quality_score?: number;
  seller?: {
    username?: string;
  };
  seller_id?: string;
  integrity_id?: string;
}

export default function ProductCard({ product }: { product: Product }) {
  const formatPrice = (p: number) => {
    if (p === 0) return 'Free';
    return `₹${p.toLocaleString('en-IN')}`;
  };

  const qualityScore = product.quality?.score ?? product.quality_score;
  const qualityLevel = product.quality?.level ?? (qualityScore ? (qualityScore >= 90 ? 'Excellent' : qualityScore >= 75 ? 'Good' : qualityScore >= 60 ? 'Fair' : qualityScore >= 40 ? 'Low' : 'Very Low') : null);
  const hasReviews = (product.review_count ?? 0) > 0 && (product.avg_rating ?? 0) > 0;

  return (
    <Link
      href={`/marketplace/${product.id}`}
      className="flex flex-col h-full bg-white border border-gray-200 rounded-2xl overflow-hidden hover:border-gray-300 hover:shadow-lg hover:-translate-y-1 transition-all duration-200 group"
    >
      {/* Visual Preview */}
      <div className="relative w-full overflow-hidden bg-gray-50 border-b border-gray-100">
        <FilePreview
          extension={product.file_extension}
          title={product.title}
          category={product.category}
          imageUrl={product.preview_image_url}
          className="h-44"
        />
        {product.integrity_id && (
          <span className="absolute top-3 right-3 px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-white/95 text-blue-900 shadow-sm border border-blue-100 backdrop-blur-sm">
            {product.integrity_id}
          </span>
        )}
      </div>

      {/* Content */}
      <div className="p-5 flex flex-col flex-1">
        {/* Category & Badges */}
        <div className="flex items-center justify-between gap-2 mb-2.5 flex-wrap">
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-semibold tracking-wide uppercase px-2.5 py-0.5 rounded-md bg-slate-100 text-slate-700">
              {product.category || 'Digital'}
            </span>
            {qualityScore !== undefined && qualityScore !== null && (
              <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border ${
                qualityScore >= 80
                  ? 'bg-blue-50 text-blue-700 border-blue-200'
                  : qualityScore >= 50
                  ? 'bg-teal-50 text-teal-700 border-teal-200'
                  : 'bg-amber-50 text-amber-700 border-amber-200'
              }`}>
                AI Quality: {qualityScore} · {qualityLevel}
              </span>
            )}
          </div>
          <span className="flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 border border-emerald-200/60 px-2 py-0.5 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Verified
          </span>
        </div>

        {/* Title */}
        <h3 className="font-semibold text-gray-900 text-base leading-snug line-clamp-2 group-hover:text-blue-600 transition-colors mb-1.5">
          {product.title}
        </h3>

        {/* Description */}
        {product.short_description && (
          <p className="text-xs text-gray-500 line-clamp-2 mb-4 leading-relaxed">
            {product.short_description}
          </p>
        )}

        {/* Bottom meta pushed to bottom */}
        <div className="mt-auto pt-4 border-t border-gray-100 space-y-3">
          {/* Rating & Seller */}
          <div className="flex items-center justify-between text-xs text-gray-500">
            {hasReviews ? (
              <div className="flex items-center gap-1">
                <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                <span className="font-semibold text-gray-800">{Number(product.avg_rating).toFixed(1)}</span>
                <span className="text-gray-400">({product.review_count})</span>
              </div>
            ) : (
              <span className="text-[11px] text-gray-400 italic">No reviews yet</span>
            )}
            <div className="flex items-center gap-1 text-gray-500 truncate max-w-[130px]">
              <User className="w-3 h-3 text-gray-400 flex-shrink-0" />
              <span className="truncate">{product.seller?.username || 'Verified Seller'}</span>
            </div>
          </div>

          {/* Price & Action */}
          <div className="flex items-center justify-between">
            <div>
              <span className="text-lg font-bold text-gray-900">
                {formatPrice(product.price)}
              </span>
              {product.price > 0 && (
                <span className="text-[11px] text-gray-400 block -mt-1 font-normal">One-time purchase</span>
              )}
            </div>
            <span className="inline-flex items-center gap-1 text-xs font-semibold text-blue-600 group-hover:translate-x-0.5 transition-transform bg-blue-50 hover:bg-blue-100 px-3 py-1.5 rounded-lg">
              View <ArrowRight className="w-3.5 h-3.5" />
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
