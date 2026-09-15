'use client';
import Link from 'next/link';
import { Shield, ShieldCheck, Lock, Sparkles } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 lg:gap-12">
          {/* Brand & Mission (2 cols on desktop) */}
          <div className="col-span-2">
            <Link href="/" className="flex items-center gap-2.5 mb-4 group">
              <div className="w-8 h-8 bg-blue-600 rounded-xl flex items-center justify-center shadow-sm">
                <Shield className="w-4 h-4 text-white" />
              </div>
              <span className="font-bold text-gray-900 text-lg tracking-tight">
                SecureMarket
              </span>
            </Link>
            <p className="text-sm text-gray-500 max-w-sm leading-relaxed mb-5">
              The secure Web2 digital marketplace. Buy and sell digital guides, source code, templates, and designs with automated AI metadata, malware scanning, and SHA-256 cryptographic verification.
            </p>
            <div className="flex flex-wrap gap-2">
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200/80">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> SHA-256 Sealed
              </span>
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-blue-800 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200/80">
                <Lock className="w-3.5 h-3.5 text-blue-600" /> Razorpay Verified
              </span>
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-800 bg-purple-50 px-2.5 py-1 rounded-full border border-purple-200/80">
                <Sparkles className="w-3.5 h-3.5 text-purple-600" /> Gemini AI Engine
              </span>
            </div>
          </div>

          {/* Marketplace */}
          <div>
            <h4 className="font-semibold text-gray-900 text-xs uppercase tracking-wider mb-4">
              Marketplace
            </h4>
            <ul className="space-y-2.5">
              {[
                ['Browse Files', '/marketplace'],
                ['Programming', '/marketplace?category=Programming'],
                ['Design Assets', '/marketplace?category=Design'],
                ['Templates', '/marketplace?category=Templates'],
                ['Start Selling', '/seller/become'],
              ].map(([label, href]) => (
                <li key={label}>
                  <Link href={href} className="text-xs text-gray-600 hover:text-gray-900 transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Security & Proof */}
          <div>
            <h4 className="font-semibold text-gray-900 text-xs uppercase tracking-wider mb-4">
              Security
            </h4>
            <ul className="space-y-2.5">
              {[
                ['Verify Integrity ID', '/integrity/FI-C577A9B4'],
                ['Malware Protection', '/about'],
                ['HMAC Tamper Proof', '/about'],
                ['Temporary Downloads', '/terms'],
                ['API Security Docs', 'http://localhost:8001/docs'],
              ].map(([label, href]) => (
                <li key={label}>
                  <Link href={href} className="text-xs text-gray-600 hover:text-gray-900 transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Company & Legal */}
          <div>
            <h4 className="font-semibold text-gray-900 text-xs uppercase tracking-wider mb-4">
              Company
            </h4>
            <ul className="space-y-2.5">
              {[
                ['About SecureMarket', '/about'],
                ['Contact Us', '/contact'],
                ['Terms of Service', '/terms'],
                ['Privacy Policy', '/privacy'],
              ].map(([label, href]) => (
                <li key={label}>
                  <Link href={href} className="text-xs text-gray-600 hover:text-gray-900 transition-colors">
                    {label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-gray-200 mt-12 pt-6 flex flex-col sm:flex-row justify-between items-center gap-4 text-xs text-gray-500">
          <p>© 2026 SecureMarket. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5 text-gray-500">
              <span className="w-2 h-2 rounded-full bg-emerald-500" /> Localhost Active (Port 3000 & 8001)
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
