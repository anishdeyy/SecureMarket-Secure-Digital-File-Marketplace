import Navbar from '@/components/layout/Navbar';
import Footer from '@/components/layout/Footer';

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <div className="max-w-3xl mx-auto px-4 py-16 w-full">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Privacy Policy</h1>
        <p className="text-gray-400 text-sm mb-10">Last updated: January 2024</p>
        <div className="space-y-6 text-sm text-gray-600 leading-relaxed">
          {[
            ['What We Collect', 'Email address, username, and password (hashed). Uploaded file metadata (not the files themselves for buyers). Purchase and download history. IP addresses and user agents for security audit logs.'],
            ['What We Do NOT Collect', 'Payment card numbers (handled by Razorpay). Plaintext passwords. Precise location data. Third-party tracking cookies.'],
            ['How We Use Data', 'To provide marketplace services. To scan files for malware. To verify payment integrity. To detect fraud and abuse. To generate AI metadata via Gemini (file content is sent to Google\'s API for processing).'],
            ['Data Security', 'Passwords are hashed using PBKDF2-SHA256. File integrity is sealed with HMAC-SHA256. All files are stored in private cloud storage. Download links expire within 5 minutes.'],
            ['Data Retention', 'Account data is retained while your account is active. Audit logs are retained for 12 months. You may request deletion of your account and associated data at any time.'],
            ['Third Parties', 'Razorpay (payment processing), Google Gemini (AI metadata generation), AWS (file storage). We do not sell or share your personal data with advertisers.'],
            ['Your Rights', 'You may request access to, correction of, or deletion of your personal data by contacting support.'],
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
