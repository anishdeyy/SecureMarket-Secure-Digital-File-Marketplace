import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-16 w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Terms of Service</h1>
        <p className="text-gray-400 text-sm mb-10">Last updated: January 2024</p>
        <div className="prose prose-gray max-w-none space-y-6 text-gray-600 text-sm leading-relaxed">
          {[
            ['1. Acceptance', 'By accessing SecureMarket, you agree to these terms. If you disagree, please do not use the platform.'],
            ['2. Seller Responsibilities', 'Sellers must only upload content they own or have rights to distribute. Uploading malware, illegal content, or infringing materials is strictly prohibited and will result in immediate account suspension.'],
            ['3. Buyer Rights', 'Buyers receive a personal, non-transferable licence to use purchased digital files. Redistribution, resale, or sharing of purchased files is prohibited.'],
            ['4. Payments', 'All payments are processed by Razorpay. SecureMarket does not store payment card information. Prices are shown inclusive of applicable taxes.'],
            ['5. Security', 'All files are scanned for malware before listing. SHA-256 hashes are computed for every file. Integrity records are sealed with HMAC-SHA256 to detect tampering.'],
            ['6. Refunds', 'Due to the digital nature of products, refunds are not provided once a file has been downloaded. Contact support if you experience technical issues.'],
            ['7. Prohibited Content', 'Executable malware, adult content, pirated material, personally identifiable data without consent, or any content that violates applicable law.'],
            ['8. Changes', 'We may update these terms at any time. Continued use of the platform after changes constitutes acceptance of the new terms.'],
          ].map(([title, text]) => (
            <div key={title as string}>
              <h2 className="text-base font-bold text-gray-900 mb-1">{title}</h2>
              <p>{text}</p>
            </div>
          ))}
        </div>
      </div>
      <Footer />
    </div>
  );
}
