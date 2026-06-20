/** @type {import('next').NextConfig} */
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
    reactStrictMode: true,
    eslint: {
        // Linting is a dedicated CI step (`npm run lint`); don't fail production
        // builds on lint issues.
        ignoreDuringBuilds: true,
    },
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: `${API_URL}/api/:path*`,
            },
        ];
    },
};

module.exports = nextConfig;
