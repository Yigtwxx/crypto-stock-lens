'use client';

import React, { useState } from 'react';
import { User, Mail, Lock, Twitter, MessageCircle, CreditCard, Shield, Check, Github, Globe } from 'lucide-react';

export default function ProfilePage() {
    const [isLogin, setIsLogin] = useState(true);

    return (
        <div className="h-full overflow-y-auto custom-scrollbar p-6 space-y-8 bg-[#0b0b15]">
            {/* Header Section */}
            <div className="flex items-center gap-6 p-6 bg-gradient-to-r from-oracle-dark/50 to-teal/5 rounded-2xl border border-oracle-border/50">
                <div className="w-20 h-20 rounded-full bg-gradient-to-br from-purple-500 to-cyan flex items-center justify-center shadow-lg shadow-cyan/20">
                    <User className="w-10 h-10 text-white" />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-white">Guest User</h1>
                    <p className="text-gray-400">Join Oracle-X to sync your data across devices.</p>
                    <div className="mt-2 inline-flex px-3 py-1 rounded-full bg-gray-800 border border-gray-700 text-xs font-medium text-gray-300">
                        Free Plan
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Account Access Section */}
                <div className="bg-oracle-card rounded-2xl border border-oracle-border p-6">
                    <div className="flex items-center justify-between mb-6">
                        <h2 className="text-lg font-semibold text-white flex items-center gap-2">
                            <Shield className="w-5 h-5 text-teal" />
                            Account Access
                        </h2>
                        <div className="flex bg-black/30 rounded-lg p-1">
                            <button
                                onClick={() => setIsLogin(true)}
                                className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${isLogin ? 'bg-teal text-black' : 'text-gray-400 hover:text-white'}`}
                            >
                                Login
                            </button>
                            <button
                                onClick={() => setIsLogin(false)}
                                className={`px-4 py-1.5 text-xs font-medium rounded-md transition-all ${!isLogin ? 'bg-teal text-black' : 'text-gray-400 hover:text-white'}`}
                            >
                                Sign Up
                            </button>
                        </div>
                    </div>

                    <form className="space-y-4">
                        {!isLogin && (
                            <div className="space-y-1">
                                <label className="text-xs font-medium text-gray-400">Full Name</label>
                                <div className="relative">
                                    <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                                    <input
                                        type="text"
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
                                    placeholder="you@example.com"
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
                                    placeholder="••••••••"
                                    className="w-full bg-black/20 border border-oracle-border rounded-lg pl-10 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-teal/50 transition-colors"
                                />
                            </div>
                        </div>
                        <button className="w-full bg-teal hover:bg-teal/90 text-black font-semibold py-2.5 rounded-lg transition-colors mt-4">
                            {isLogin ? 'Sign In' : 'Create Account'}
                        </button>
                    </form>
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
                                    <p className="text-xs text-gray-500">Connect to sync watchlist</p>
                                </div>
                            </div>
                            <button className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all">
                                Connect
                            </button>
                        </div>

                        {/* Discord */}
                        <div className="flex items-center justify-between p-4 bg-black/20 border border-oracle-border/50 rounded-xl hover:border-purple-500/30 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-[#5865F2]/10 rounded-lg group-hover:bg-[#5865F2]/20 transition-colors">
                                    <MessageCircle className="w-5 h-5 text-[#5865F2]" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">Discord</h3>
                                    <p className="text-xs text-gray-500">Join the community</p>
                                </div>
                            </div>
                            <button className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all">
                                Connect
                            </button>
                        </div>

                        {/* Telegram */}
                        <div className="flex items-center justify-between p-4 bg-black/20 border border-oracle-border/50 rounded-xl hover:border-purple-500/30 transition-colors group">
                            <div className="flex items-center gap-4">
                                <div className="p-2 bg-[#0088cc]/10 rounded-lg group-hover:bg-[#0088cc]/20 transition-colors">
                                    <User className="w-5 h-5 text-[#0088cc]" />
                                </div>
                                <div>
                                    <h3 className="font-medium text-white">Telegram</h3>
                                    <p className="text-xs text-gray-500">Get instant alerts</p>
                                </div>
                            </div>
                            <button className="px-3 py-1.5 text-xs font-medium border border-gray-600 rounded-lg text-gray-300 hover:text-white hover:border-white transition-all">
                                Connect
                            </button>
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
                    <div className="p-6 rounded-xl border border-oracle-border bg-black/20 flex flex-col">
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
                        <button className="w-full py-2 rounded-lg border border-gray-600 text-gray-300 font-medium hover:border-white hover:text-white transition-all cursor-default">
                            Current Plan
                        </button>
                    </div>

                    {/* Pro Tier (Popular) */}
                    <div className="p-6 rounded-xl border border-teal/50 bg-teal/5 relative flex flex-col transform scale-105 shadow-xl shadow-teal/10">
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
                        <button className="w-full py-2.5 rounded-lg bg-teal hover:bg-teal/90 text-black font-bold transition-all shadow-lg shadow-teal/20">
                            Upgrade Now
                        </button>
                    </div>

                    {/* Whale Tier */}
                    <div className="p-6 rounded-xl border border-purple-500/30 bg-purple-500/5 flex flex-col">
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
                        <button className="w-full py-2 rounded-lg border border-purple-500/50 text-purple-200 font-medium hover:bg-purple-500/20 transition-all">
                            Contact Sales
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
