import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
    title: 'Oracle-X | Financial Intelligence Terminal',
    description: 'AI-powered financial analysis with blockchain verification. Real-time insights for stocks and crypto.',
    keywords: ['finance', 'AI', 'trading', 'stocks', 'crypto', 'blockchain', 'analysis'],
};

export default function RootLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en">
            <body className={inter.className}>
                {children}
            </body>
        </html>
    );
}
