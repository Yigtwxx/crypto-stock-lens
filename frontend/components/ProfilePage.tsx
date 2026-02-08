'use client';

import React, { useState, useEffect } from 'react';
import { User, Mail, Lock, Twitter, MessageCircle, CreditCard, Shield, Check, Globe, LogOut, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';

interface Profile {
    id: string;
    email: string;
    full_name?: string;
    avatar_url?: string;
    subscription_plan: 'free' | 'pro' | 'whale';
    ai_queries_today: number;
    ai_query_limit: number;
    ai_queries_remaining: number;
}

interface ConnectedAccount {
    provider: string;
    provider_username: string;
    connected_at: string;
}

export default function ProfilePage() {
    const { user, loading: authLoading, signIn, signUp, signOut } = useAuth();
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [fullName, setFullName] = useState('');
    const [error, setError] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [profile, setProfile] = useState<Profile | null>(null);
    const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([]);
    const [loadingProfile, setLoadingProfile] = useState(false);

    // Load profile when user logs in
    useEffect(() => {
        if (user) {
            loadProfile();
            loadConnectedAccounts();
        } else {
            setProfile(null);
            setConnectedAccounts([]);
        }
    }, [user]);

    const loadProfile = async () => {
        if (!user) return;
        setLoadingProfile(true);
        try {
            const res = await fetch(`http://localhost:8000/api/profile/${user.id}`);
            if (res.ok) {
                const data = await res.json();
                setProfile(data);
            }
        } catch (err) {
            console.error('Error loading profile:', err);
        } finally {
            setLoadingProfile(false);
        }
    };

    const loadConnectedAccounts = async () => {
        if (!user) return;
        try {
            const res = await fetch(`http://localhost:8000/api/profile/${user.id}/accounts`);
            if (res.ok) {
                const data = await res.json();
                setConnectedAccounts(data.accounts || []);
            }
        } catch (err) {
            console.error('Error loading connected accounts:', err);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsSubmitting(true);

        try {
            if (isLogin) {
                const { error } = await signIn(email, password);
                if (error) setError(error.message);
            } else {
                const { error } = await signUp(email, password);
                if (error) setError(error.message);
                else setError('Check your email to confirm your account!');
            }
        } catch (err: any) {
            setError(err.message || 'An error occurred');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleSignOut = async () => {
        await signOut();
    };

    const isConnected = (provider: string) => {
        return connectedAccounts.some(a => a.provider === provider);
    };

    const getConnectedUsername = (provider: string) => {
        const account = connectedAccounts.find(a => a.provider === provider);
        return account?.provider_username || '';
    };

    const handleConnectAccount = async (provider: string) => {
        // In production, this would redirect to OAuth flow
        // For now, just show a placeholder
        alert(`OAuth flow for ${provider} would start here. This requires setting up OAuth apps with Twitter/Discord/Telegram.`);
    };

    const handleDisconnectAccount = async (provider: string) => {
        if (!user) return;
        try {
            const res = await fetch(`http://localhost:8000/api/profile/${user.id}/accounts/${provider}`, {
                method: 'DELETE'
            });
            if (res.ok) {
                setConnectedAccounts(prev => prev.filter(a => a.provider !== provider));
            }
        } catch (err) {
            console.error('Error disconnecting account:', err);
        }
    };

    const currentPlan = profile?.subscription_plan || 'free';

    if (authLoading) {
        return (
            <div className="h-full flex items-center justify-center bg-[#0b0b15]">
                <Loader2 className="w-8 h-8 text-teal animate-spin" />
            </div>
        );
    }

    return (
        <div className="h-full overflow-y-auto custom-scrollbar p-6 space-y-8 bg-[#0b0b15]">
            {/* Header Section */}
            <div className="flex items-center justify-between gap-6 p-6 bg-gradient-to-r from-oracle-dark/50 to-teal/5 rounded-2xl border border-oracle-border/50">
                <div className="flex items-center gap-6">
                    <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-cyan flex items-center justify-center shadow-lg shadow-cyan/20">
                        {user?.user_metadata?.avatar_url ? (
                            <img src={user.user_metadata.avatar_url} alt="Avatar" className="w-full h-full rounded-full object-cover" />
                        ) : (
                            <User className="w-10 h-10 text-white" />
                        )}
                    </div>
                    <div>
                        <h1 className="text-2xl font-bold text-white">
                            {user ? (profile?.full_name || user.email?.split('@')[0] || 'User') : 'Guest User'}
                        </h1>
                        <p className="text-gray-400">
                            {user ? user.email : 'Join Oracle-X to sync your data across devices.'}
                        </p>
                        <div className="mt-2 inline-flex px-3 py-1 rounded-full bg-gray-800 border border-gray-700 text-xs font-medium text-gray-300">
                            {currentPlan === 'whale' ? '🐋 Whale Plan' : currentPlan === 'pro' ? '⚡ Pro Plan' : 'Free Plan'}
                        </div>
                        {profile && currentPlan === 'free' && (
                            <span className="ml-2 text-xs text-gray-500">
                                AI Queries: {profile.ai_queries_today}/{profile.ai_query_limit} today
                            </span>
                        )}
                    </div>
                </div>
                {user && (
                    <button
                        onClick={handleSignOut}
                        className="flex items-center gap-2 px-4 py-2 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 rounded-lg transition-all"
                    >
                        <LogOut className="w-4 h-4" />
                        Sign Out
                    </button>
                )}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Account Access Section */}
                <div className="bg-oracle-card rounded-2xl border border-oracle-border p-6">
                    {user ? (
                        // Logged in - Show profile info
                        <div className="space-y-6">
                            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                <Shield className="w-5 h-5 text-teal" />
                                Account Details
                            </h2>
                            <div className="space-y-4">
                                <div className="p-4 bg-black/20 rounded-xl border border-oracle-border/50">
                                    <div className="text-xs text-gray-500 mb-1">Email</div>
                                    <div className="text-white">{user.email}</div>
                                </div>
                                <div className="p-4 bg-black/20 rounded-xl border border-oracle-border/50">
                                    <div className="text-xs text-gray-500 mb-1">User ID</div>
                                    <div className="text-white text-sm font-mono truncate">{user.id}</div>
                                </div>
                                <div className="p-4 bg-black/20 rounded-xl border border-oracle-border/50">
                                    <div className="text-xs text-gray-500 mb-1">Member Since</div>
                                    <div className="text-white">
                                        {new Date(user.created_at).toLocaleDateString('en-US', {
                                            year: 'numeric',
                                            month: 'long',
                                            day: 'numeric'
                                        })}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ) : (
                        // Not logged in - Show login/signup form
                        <>
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-teal" />
                                    Account Access
                                </h2>
                                <div className="flex bg-black/30 rounded-lg p-1">
                                    <button
                                        onClick={() => { setIsLogin(true); setError(''); }}
                                        className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${isLogin ? 'bg-teal text-black' : 'text-gray-400 hover:text-white'}`}
                                    >
                                        Login
                                    </button>
                                    <button
                                        onClick={() => { setIsLogin(false); setError(''); }}
                                        className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${!isLogin ? 'bg-teal text-black' : 'text-gray-400 hover:text-white'}`}
                                    >
                                        Sign Up
                                    </button>
                                </div>
                            </div>

                            <form className="space-y-4" onSubmit={handleSubmit}>
                                {!isLogin && (
                                    <div className="space-y-1">
                                        <label className="text-xs font-medium text-gray-400">Full Name</label>
                                        <div className="relative">
                                            <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                            <input
                                                type="text"
                                                value={fullName}
                                                onChange={(e) => setFullName(e.target.value)}
                                                placeholder="John Doe"
                                                className="w-full bg-black/20 border border-oracle-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal/50 transition-colors"
                                            />
                                        </div>
                                    </div>
                                )}
                                <div className="space-y-1">
                                    <label className="text-xs font-medium text-gray-400">Email Address</label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            type="email"
                                            value={email}
                                            onChange={(e) => setEmail(e.target.value)}
                                            placeholder="you@example.com"
                                            required
                                            className="w-full bg-black/20 border border-oracle-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal/50 transition-colors"
                                        />
                                    </div>
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs font-medium text-gray-400">Password</label>
                                    <div className="relative">
                                        <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="••••••••"
                                            required
                                            minLength={6}
                                            className="w-full bg-black/20 border border-oracle-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal/50 transition-colors"
                                        />
                                    </div>
                                </div>
                                {error && (
                                    <div className={`text-sm p-3 rounded-lg ${error.includes('Check your email') ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'}`}>
                                        {error}
                                    </div>
                                )}
                                <button
                                    type="submit"
                                    disabled={isSubmitting}
                                    className="w-full bg-teal hover:bg-teal/90 text-black font-semibold py-2.5 rounded-lg transition-colors mt-4 disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                    {isLogin ? 'Sign In' : 'Create Account'}
                                </button>
                            </form>
                        </>
                    )}
                </div>

                {/* Social Connections */}
                <div className="bg-oracle-card rounded-2xl border border-oracle-border p-6 space-y-6">
                    <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                        <Globe className="w-5 h-5 text-purple-400" />
                        Connected Accounts
                    </h2>

                    <div className="space-y-3">
                        {/* Twitter */}
                        <div className="flex items-center justify-between p-4 bg-black/20 border border-oracle-border/50 rounded-xl hover:border-purple-500/30 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-[#1DA1F2]/10 rounded-lg group-hover:bg-[#1DA1F2]/20 transition-colors">
                                    <Twitter className="w-5 h-5 text-[#1DA1F2]" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">Twitter / X</h3>
                                    <p className="text-xs text-gray-500">
                                        {isConnected('twitter') ? `@${getConnectedUsername('twitter')}` : 'Connect to sync watchlist'}
                                    </p>
                                </div>
                            </div>
                            {isConnected('twitter') ? (
                                <button
                                    onClick={() => handleDisconnectAccount('twitter')}
                                    className="px-3 py-1.5 text-xs font-medium border border-red-500/50 rounded-lg text-red-400 hover:bg-red-500/20 transition-all"
                                >
                                    Disconnect
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleConnectAccount('twitter')}
                                    disabled={!user}
                                    className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all disabled:opacity-50"
                                >
                                    Connect
                                </button>
                            )}
                        </div>

                        {/* Discord */}
                        <div className="flex items-center justify-between p-4 bg-black/20 border border-oracle-border/50 rounded-xl hover:border-purple-500/30 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-[#5865F2]/10 rounded-lg group-hover:bg-[#5865F2]/20 transition-colors">
                                    <MessageCircle className="w-5 h-5 text-[#5865F2]" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">Discord</h3>
                                    <p className="text-xs text-gray-500">
                                        {isConnected('discord') ? getConnectedUsername('discord') : 'Join the community'}
                                    </p>
                                </div>
                            </div>
                            {isConnected('discord') ? (
                                <button
                                    onClick={() => handleDisconnectAccount('discord')}
                                    className="px-3 py-1.5 text-xs font-medium border border-red-500/50 rounded-lg text-red-400 hover:bg-red-500/20 transition-all"
                                >
                                    Disconnect
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleConnectAccount('discord')}
                                    disabled={!user}
                                    className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all disabled:opacity-50"
                                >
                                    Connect
                                </button>
                            )}
                        </div>

                        {/* Telegram */}
                        <div className="flex items-center justify-between p-4 bg-black/20 border border-oracle-border/50 rounded-xl hover:border-purple-500/30 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-[#0088cc]/10 rounded-lg group-hover:bg-[#0088cc]/20 transition-colors">
                                    <User className="w-5 h-5 text-[#0088cc]" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">Telegram</h3>
                                    <p className="text-xs text-gray-500">
                                        {isConnected('telegram') ? getConnectedUsername('telegram') : 'Get instant alerts'}
                                    </p>
                                </div>
                            </div>
                            {isConnected('telegram') ? (
                                <button
                                    onClick={() => handleDisconnectAccount('telegram')}
                                    className="px-3 py-1.5 text-xs font-medium border border-red-500/50 rounded-lg text-red-400 hover:bg-red-500/20 transition-all"
                                >
                                    Disconnect
                                </button>
                            ) : (
                                <button
                                    onClick={() => handleConnectAccount('telegram')}
                                    disabled={!user}
                                    className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all disabled:opacity-50"
                                >
                                    Connect
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Subscription Section */}
            <div className="bg-oracle-card rounded-2xl border border-oracle-border p-6">
                <div className="text-center mb-8">
                    <h2 className="text-2xl font-bold text-white mb-2">Upgrade Your Intelligence</h2>
                    <p className="text-gray-400 text-sm max-w-lg mx-auto">
                        Unlock advanced liquidation data, faster news feeds, and unlimited AI analysis.
                    </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Free Tier */}
                    <div className={`p-6 rounded-xl border ${currentPlan === 'free' ? 'border-teal/50 bg-teal/5' : 'border-oracle-border bg-black/20'} flex flex-col`}>
                        <h3 className="text-xl font-bold text-white">Free</h3>
                        <div className="mt-2 mb-6">
                            <span className="text-3xl font-bold text-white">$0</span>
                            <span className="text-gray-500">/mo</span>
                        </div>
                        <ul className="space-y-3 mb-8 flex-1">
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-teal" /> 15 min News Delay
                            </li>
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-teal" /> Basic Charts
                            </li>
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-teal" /> 5 AI Queries/day
                            </li>
                        </ul>
                        <button
                            className={`w-full py-2 rounded-lg ${currentPlan === 'free' ? 'bg-teal/20 text-teal border border-teal/50' : 'border border-gray-600 text-gray-300'} font-medium`}
                            disabled={currentPlan === 'free'}
                        >
                            {currentPlan === 'free' ? 'Current Plan' : 'Downgrade'}
                        </button>
                    </div>

                    {/* Pro Tier (Popular) */}
                    <div className={`p-6 rounded-xl border ${currentPlan === 'pro' ? 'border-teal bg-teal/10' : 'border-teal/50 bg-teal/5'} relative flex flex-col transform ${currentPlan !== 'pro' ? 'scale-105' : ''} shadow-xl shadow-teal/10`}>
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-0.5 bg-teal text-black text-[10px] font-bold uppercase rounded-full">
                            Most Popular
                        </div>
                        <h3 className="text-xl font-bold text-white">Pro</h3>
                        <div className="mt-2 mb-6">
                            <span className="text-3xl font-bold text-white">$29</span>
                            <span className="text-gray-500">/mo</span>
                        </div>
                        <ul className="space-y-3 mb-8 flex-1">
                            <li className="flex items-center gap-2 text-sm text-white">
                                <Check className="w-4 h-4 text-teal" /> Real-time News Feed
                            </li>
                            <li className="flex items-center gap-2 text-sm text-white">
                                <Check className="w-4 h-4 text-teal" /> Live Liquidation Heatmaps
                            </li>
                            <li className="flex items-center gap-2 text-sm text-white">
                                <Check className="w-4 h-4 text-teal" /> Unlimited AI Analysis
                            </li>
                            <li className="flex items-center gap-2 text-sm text-white">
                                <Check className="w-4 h-4 text-teal" /> Advanced Technical Alerts
                            </li>
                        </ul>
                        <button
                            className={`w-full py-2.5 rounded-lg ${currentPlan === 'pro' ? 'bg-teal/20 text-teal border border-teal' : 'bg-teal hover:bg-teal/90 text-black'} font-bold transition-all shadow-lg shadow-teal/20`}
                            disabled={currentPlan === 'pro' || !user}
                        >
                            {currentPlan === 'pro' ? 'Current Plan' : 'Upgrade Now'}
                        </button>
                    </div>

                    {/* Whale Tier */}
                    <div className={`p-6 rounded-xl border ${currentPlan === 'whale' ? 'border-purple-500 bg-purple-500/10' : 'border-purple-500/30 bg-purple-500/5'} flex flex-col`}>
                        <h3 className="text-xl font-bold text-white">Whale</h3>
                        <div className="mt-2 mb-6">
                            <span className="text-3xl font-bold text-white">$99</span>
                            <span className="text-gray-500">/mo</span>
                        </div>
                        <ul className="space-y-3 mb-8 flex-1">
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-purple-400" /> All Pro Features
                            </li>
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-purple-400" /> On-Chain Whale Alerts
                            </li>
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-purple-400" /> API Access
                            </li>
                            <li className="flex items-center gap-2 text-sm text-gray-300">
                                <Check className="w-4 h-4 text-purple-400" /> Priority Support
                            </li>
                        </ul>
                        <button
                            className={`w-full py-2 rounded-lg ${currentPlan === 'whale' ? 'bg-purple-500/20 text-purple-300 border border-purple-500' : 'border border-purple-500/50 text-purple-200 hover:bg-purple-500/20'} font-medium transition-all`}
                            disabled={currentPlan === 'whale' || !user}
                        >
                            {currentPlan === 'whale' ? 'Current Plan' : 'Contact Sales'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
