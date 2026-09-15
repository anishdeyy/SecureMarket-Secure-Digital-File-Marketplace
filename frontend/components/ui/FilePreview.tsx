import React from 'react';
import { FileText, Code2, Archive, Table, Image as ImageIcon, BookOpen, Music, Video, ShieldCheck } from 'lucide-react';

interface FilePreviewProps {
  extension?: string;
  title?: string;
  category?: string;
  imageUrl?: string;
  className?: string;
}

export default function FilePreview({
  extension = '',
  title = '',
  category = '',
  imageUrl,
  className = 'h-48',
}: FilePreviewProps) {
  if (imageUrl) {
    return (
      <div className={`relative w-full overflow-hidden bg-gray-50 flex items-center justify-center ${className}`}>
        <img src={imageUrl} alt={title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
      </div>
    );
  }

  const ext = (extension || '').toLowerCase().replace('.', '');

  // Code files
  if (['py', 'js', 'ts', 'jsx', 'tsx', 'html', 'css', 'json', 'sql', 'cpp', 'java'].includes(ext)) {
    return (
      <div className={`relative w-full bg-slate-900 p-4 font-mono text-xs overflow-hidden flex flex-col justify-between border-b border-gray-100 ${className}`}>
        {/* Editor tab bar */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-2.5 mb-2">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
            <span className="w-2.5 h-2.5 rounded-full bg-green-500/80" />
          </div>
          <span className="text-[11px] text-slate-400 font-sans tracking-wide uppercase px-2 py-0.5 rounded bg-slate-800">
            .{ext}
          </span>
        </div>
        {/* Code mockup */}
        <div className="space-y-1.5 text-[11px] opacity-85 leading-relaxed text-slate-300">
          <div className="flex gap-2">
            <span className="text-slate-600 select-none">1</span>
            <span className="text-blue-400">export default</span> <span className="text-purple-300">function</span> <span className="text-amber-300">module</span>() &#123;
          </div>
          <div className="flex gap-2 pl-3">
            <span className="text-slate-600 select-none">2</span>
            <span className="text-emerald-400">// {title.slice(0, 26)}</span>
          </div>
          <div className="flex gap-2 pl-3">
            <span className="text-slate-600 select-none">3</span>
            <span className="text-blue-400">const</span> config = &#123; verified: <span className="text-emerald-300">true</span> &#125;;
          </div>
          <div className="flex gap-2">
            <span className="text-slate-600 select-none">4</span>
            &#125;
          </div>
        </div>
        <div className="flex items-center justify-between text-[11px] text-slate-400 pt-2 border-t border-slate-800/80">
          <span className="flex items-center gap-1 text-emerald-400 font-sans text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5" /> Clean Code
          </span>
          <span className="text-slate-500 font-sans">{category || 'Source Code'}</span>
        </div>
      </div>
    );
  }

  // Documents & PDFs
  if (['pdf', 'docx', 'doc', 'txt', 'epub'].includes(ext)) {
    return (
      <div className={`relative w-full bg-gradient-to-b from-blue-50/60 via-slate-50 to-white p-5 flex flex-col justify-between border-b border-gray-100 ${className}`}>
        <div className="flex justify-between items-start">
          <div className="w-9 h-9 rounded-xl bg-blue-600/10 text-blue-700 flex items-center justify-center border border-blue-200/60">
            {ext === 'pdf' ? <BookOpen className="w-5 h-5" /> : <FileText className="w-5 h-5" />}
          </div>
          <span className="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-blue-100/70 text-blue-800">
            {ext.toUpperCase()}
          </span>
        </div>

        {/* Document lines simulation */}
        <div className="space-y-2 my-auto px-1">
          <div className="h-3 w-4/5 bg-gray-300/80 rounded" />
          <div className="h-2 w-full bg-gray-200/90 rounded" />
          <div className="h-2 w-3/4 bg-gray-200/70 rounded" />
          <div className="h-2 w-5/6 bg-gray-200/50 rounded" />
        </div>

        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
          <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Verified Document
          </span>
          <span className="text-gray-400 text-[11px]">{category || 'Document'}</span>
        </div>
      </div>
    );
  }

  // Archives & ZIPs
  if (['zip', 'rar', '7z', 'tar', 'gz'].includes(ext)) {
    return (
      <div className={`relative w-full bg-gradient-to-b from-amber-50/50 via-slate-50 to-white p-5 flex flex-col justify-between border-b border-gray-100 ${className}`}>
        <div className="flex justify-between items-start">
          <div className="w-9 h-9 rounded-xl bg-amber-600/10 text-amber-700 flex items-center justify-center border border-amber-200/60">
            <Archive className="w-5 h-5" />
          </div>
          <span className="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-amber-100/70 text-amber-800">
            ZIP BUNDLE
          </span>
        </div>
        <div className="my-auto text-center px-4">
          <p className="text-xs font-semibold text-gray-700 truncate">{title || 'Resource Package'}</p>
          <p className="text-[11px] text-gray-400 mt-1">Multi-file digital package</p>
        </div>
        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
          <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Scanned
          </span>
          <span className="text-gray-400 text-[11px]">{category || 'Package'}</span>
        </div>
      </div>
    );
  }

  // Spreadsheets
  if (['xlsx', 'xls', 'csv'].includes(ext)) {
    return (
      <div className={`relative w-full bg-gradient-to-b from-emerald-50/50 via-slate-50 to-white p-5 flex flex-col justify-between border-b border-gray-100 ${className}`}>
        <div className="flex justify-between items-start">
          <div className="w-9 h-9 rounded-xl bg-emerald-600/10 text-emerald-700 flex items-center justify-center border border-emerald-200/60">
            <Table className="w-5 h-5" />
          </div>
          <span className="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-emerald-100/70 text-emerald-800">
            DATA / SHEET
          </span>
        </div>
        {/* Table grid simulation */}
        <div className="grid grid-cols-3 gap-1.5 my-auto px-1 opacity-70">
          <div className="h-3 bg-emerald-200/70 rounded" />
          <div className="h-3 bg-emerald-200/70 rounded" />
          <div className="h-3 bg-emerald-200/70 rounded" />
          <div className="h-2.5 bg-gray-200 rounded" />
          <div className="h-2.5 bg-gray-200 rounded" />
          <div className="h-2.5 bg-gray-200 rounded" />
        </div>
        <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
          <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Formatted
          </span>
          <span className="text-gray-400 text-[11px]">{category || 'Spreadsheet'}</span>
        </div>
      </div>
    );
  }

  // Default Digital File preview
  return (
    <div className={`relative w-full bg-gradient-to-b from-slate-100 to-white p-5 flex flex-col justify-between border-b border-gray-100 ${className}`}>
      <div className="flex justify-between items-start">
        <div className="w-9 h-9 rounded-xl bg-blue-600/10 text-blue-700 flex items-center justify-center border border-blue-200/60">
          <FileText className="w-5 h-5" />
        </div>
        <span className="text-[11px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full bg-gray-100 text-gray-700">
          DIGITAL FILE
        </span>
      </div>
      <div className="my-auto text-center px-4">
        <p className="text-xs font-semibold text-gray-800 truncate">{title || 'Digital Asset'}</p>
        <p className="text-[11px] text-gray-400 mt-1">Verified digital product</p>
      </div>
      <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
        <span className="flex items-center gap-1 text-emerald-700 font-medium text-[11px]">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Protected
        </span>
        <span className="text-gray-400 text-[11px]">{category || 'Asset'}</span>
      </div>
    </div>
  );
}
