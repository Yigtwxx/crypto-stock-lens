import type { Config } from 'tailwindcss';

const config: Config = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                'oracle': {
                    'dark': '#0a0a0f',
                    'darker': '#050508',
                    'card': '#12121a',
                    'card-hover': '#1a1a25',
                    'border': '#2a2a3a',
                    'accent': '#8b5cf6',        // Vibrant purple
                    'accent-glow': 'rgba(139, 92, 246, 0.3)',
                    'bullish': '#22c55e',       // Bright green
                    'bearish': '#ef4444',       // Red
                    'neutral': '#f59e0b',       // Amber/Orange
                },
                // Extended palette
                'crypto': '#f7931a',            // Bitcoin orange
                'stock': '#3b82f6',             // Blue for stocks
                'cyan': '#06b6d4',              // Cyan for highlights
                'pink': '#ec4899',              // Pink accent
                'lime': '#84cc16',              // Lime green
                'amber': '#f59e0b',             // Amber
                'rose': '#f43f5e',              // Rose red
                'violet': '#8b5cf6',            // Violet
                'indigo': '#6366f1',            // Indigo
                'teal': '#14b8a6',              // Teal
            },
            backgroundImage: {
                'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
                'glow-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
            },
            animation: {
                'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
                'glow': 'glow 2s ease-in-out infinite alternate',
                'slide-in': 'slideIn 0.3s ease-out',
            },
            keyframes: {
                glow: {
                    '0%': { boxShadow: '0 0 5px rgba(99, 102, 241, 0.5)' },
                    '100%': { boxShadow: '0 0 20px rgba(99, 102, 241, 0.8)' },
                },
                slideIn: {
                    '0%': { opacity: '0', transform: 'translateX(-10px)' },
                    '100%': { opacity: '1', transform: 'translateX(0)' },
                },
            },
        },
    },
    plugins: [],
};

export default config;
