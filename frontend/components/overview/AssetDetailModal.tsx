'use client';

import { useState, useEffect } from 'react';
import {
    X, ExternalLink, Globe, Github, Twitter,
    TrendingUp, TrendingDown, BarChart3, Coins, Users,
    Calendar, Hash, Layers, Building2, MapPin, Loader2,
    ArrowUp, ArrowDown, Link2
} from 'lucide-react';
import { fetchAssetDetail, AssetDetail } from '@/lib/api';
import { formatVolume, formatPrice } from './overview-utils';

interface AssetDetailModalProps {
    symbol: string;
    marketType: 'crypto' | 'nasdaq';
    onClose: () => void;
}

function formatSupply(n: number | null | undefined): string {
    if (!n) return '--';
    if (n >= 1e12) return `${(n / 1e12).toFixed(2)}T`;
    if (n >= 1e9) return `${(n / 1e9).toFixed(2)}B`;
    if (n >= 1e6) return `${(n / 1e6).toFixed(2)}M`;
    return n.toLocaleString();
}

function formatDate(dateStr: string | undefined): string {
    if (!dateStr) return '--';
    try {
        return new Date(dateStr).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    } catch {
        return '--';
    }
}

function ChangeIndicator({ value, size = 'sm' }: { value: number | undefined; size?: 'sm' | 'lg' }) {
    if (value === undefined || value === null) return <span className="text-gray-500">--</span>;
    const isPositive = value >= 0;
    const textSize = size === 'lg' ? 'text-lg font-bold' : 'text-sm font-medium';
    return (
        <span className={`flex items-center gap-1 ${textSize} ${isPositive ? 'text-green-400' : 'text-red-400'}`}>
            {isPositive ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {isPositive ? '+' : ''}{value.toFixed(2)}%
        </span>
    );
}

function StatBox({ label, value, sub }: { label: string; value: string; sub?: React.ReactNode }) {
    return (
        <div className="p-3 bg-black/20 rounded-xl border border-oracle-border/30">
            <div className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</div>
            <div className="text-white font-semibold text-sm">{value}</div>
            {sub && <div className="mt-0.5">{sub}</div>}
        </div>
    );
}

function LinkButton({ href, icon: Icon, label }: { href: string; icon: React.ElementType; label: string }) {
    return (
        <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-3 py-2 bg-black/20 rounded-lg border border-oracle-border/30 hover:border-purple-500/40 hover:bg-purple-500/5 transition-all text-sm text-gray-300 hover:text-white group"
        >
            <Icon className="w-4 h-4 text-gray-500 group-hover:text-purple-400 transition-colors" />
            <span>{label}</span>
            <ExternalLink className="w-3 h-3 ml-auto text-gray-600" />
        </a>
    );
}

export default function AssetDetailModal({ symbol, marketType, onClose }: AssetDetailModalProps) {
    const [data, setData] = useState<AssetDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        const load = async () => {
            setLoading(true);
            setError(null);
            try {
                const type = marketType === 'nasdaq' ? 'stock' : 'crypto';
                const result = await fetchAssetDetail(symbol, type);
                if (!cancelled) setData(result);
            } catch (err: any) {
                if (!cancelled) setError(err.message || 'Failed to load data');
            } finally {
                if (!cancelled) setLoading(false);
            }
        };
        load();
        return () => { cancelled = true; };
    }, [symbol, marketType]);

    // Close on Escape key
    useEffect(() => {
        const handleKey = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleKey);
        return () => window.removeEventListener('keydown', handleKey);
    }, [onClose]);

    return (
        <div>
            {/* Backdrop */}
            <div
                className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 animate-in fade-in duration-200"
                onClick={onClose}
            />

            {/* Centered Modal */}
            <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
                <div className="w-full max-w-[720px] max-h-[85vh] bg-[#0b0b15] border border-oracle-border rounded-2xl overflow-y-auto custom-scrollbar shadow-2xl shadow-black/50 animate-in zoom-in-95 fade-in duration-200">
                    {/* Header */}
                    <div className="sticky top-0 z-10 bg-[#0b0b15]/95 backdrop-blur-md border-b border-oracle-border/50 px-6 py-4 rounded-t-2xl">
                        <div className="flex items-center justify-between">
                            {data && !loading ? (
                                <div className="flex items-center gap-3">
                                    <img
                                        src={data.logo}
                                        alt={data.symbol}
                                        className="w-10 h-10 rounded-full bg-oracle-border object-cover"
                                        onError={(e) => {
                                            e.currentTarget.src = `https://ui-avatars.com/api/?name=${data.symbol}&background=4f46e5&color=fff&size=64&bold=true`;
                                        }}
                                    />
                                    <div>
                                        <h2 className="text-lg font-bold text-white">{data.name}</h2>
                                        <div className="flex items-center gap-2">
                                            <span className="text-xs text-gray-400 font-mono">{data.symbol}</span>
                                            {data.market_cap_rank && (
                                                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-300 font-medium">
                                                    #{data.market_cap_rank}
                                                </span>
                                            )}
                                            {data.type === 'stock' && data.sector && (
                                                <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-cyan/10 text-cyan font-medium">
                                                    {data.sector}
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="flex items-center gap-3">
                                    <div className="w-10 h-10 rounded-full bg-oracle-border animate-pulse" />
                                    <div className="space-y-2">
                                        <div className="w-24 h-5 bg-oracle-border rounded animate-pulse" />
                                        <div className="w-16 h-3 bg-oracle-border rounded animate-pulse" />
                                    </div>
                                </div>
                            )}
                            <button
                                onClick={onClose}
                                className="p-2 hover:bg-white/5 rounded-lg transition-colors text-gray-400 hover:text-white"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>
                    </div>

                    {/* Content */}
                    <div className="px-6 py-5 space-y-6">
                        {loading ? (
                            <div className="flex flex-col items-center justify-center py-20">
                                <Loader2 className="w-8 h-8 text-purple-500 animate-spin mb-3" />
                                <p className="text-gray-400 text-sm">Loading asset details...</p>
                            </div>
                        ) : error ? (
                            <div className="flex flex-col items-center justify-center py-20">
                                <p className="text-red-400 mb-2">Error: {error}</p>
                                <button onClick={onClose} className="text-sm text-gray-400 hover:text-white">Close</button>
                            </div>
                        ) : data ? (
                            <>
                                {/* === PRICE SECTION === */}
                                <div>
                                    <div className="flex items-end gap-3 mb-3">
                                        <span className="text-3xl font-bold text-white">{formatPrice(data.price)}</span>
                                        <ChangeIndicator value={data.change_24h} size="lg" />
                                    </div>
                                    <div className="flex gap-4 text-xs text-gray-400">
                                        <span className="flex items-center gap-1">
                                            <TrendingUp className="w-3 h-3 text-green-500" />
                                            H: {formatPrice(data.high_24h)}
                                        </span>
                                        <span className="flex items-center gap-1">
                                            <TrendingDown className="w-3 h-3 text-red-500" />
                                            L: {formatPrice(data.low_24h)}
                                        </span>
                                    </div>
                                </div>

                                {/* === CHANGE PERIODS === */}
                                {(data.change_7d !== undefined || data.change_30d !== undefined) && (
                                    <div className="grid grid-cols-4 gap-2">
                                        <div className="p-2 bg-black/20 rounded-lg border border-oracle-border/30 text-center">
                                            <div className="text-[10px] text-gray-500 mb-1">24h</div>
                                            <ChangeIndicator value={data.change_24h} />
                                        </div>
                                        <div className="p-2 bg-black/20 rounded-lg border border-oracle-border/30 text-center">
                                            <div className="text-[10px] text-gray-500 mb-1">7d</div>
                                            <ChangeIndicator value={data.change_7d} />
                                        </div>
                                        <div className="p-2 bg-black/20 rounded-lg border border-oracle-border/30 text-center">
                                            <div className="text-[10px] text-gray-500 mb-1">30d</div>
                                            <ChangeIndicator value={data.change_30d} />
                                        </div>
                                        <div className="p-2 bg-black/20 rounded-lg border border-oracle-border/30 text-center">
                                            <div className="text-[10px] text-gray-500 mb-1">1y</div>
                                            <ChangeIndicator value={data.change_1y} />
                                        </div>
                                    </div>
                                )}

                                {/* === MARKET DATA === */}
                                <div>
                                    <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                        <BarChart3 className="w-4 h-4 text-purple-400" />
                                        Market Data
                                    </h3>
                                    <div className="grid grid-cols-2 gap-2">
                                        <StatBox label="Market Cap" value={formatVolume(data.market_cap)} />
                                        <StatBox label="Volume (24h)" value={formatVolume(data.total_volume)} />
                                        {data.type === 'crypto' && (
                                            <StatBox label="Fully Diluted Val." value={data.fully_diluted_valuation ? formatVolume(data.fully_diluted_valuation) : '--'} />
                                        )}
                                        {data.type === 'stock' && data.pe_ratio ? (
                                            <StatBox label="P/E Ratio" value={data.pe_ratio.toFixed(2)} />
                                        ) : null}
                                        {data.type === 'stock' && data.dividend_yield ? (
                                            <StatBox label="Dividend Yield" value={`${data.dividend_yield}%`} />
                                        ) : null}
                                    </div>
                                </div>

                                {/* === ATH / ATL (Crypto) or 52-Week (Stock) === */}
                                {data.type === 'crypto' ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <TrendingUp className="w-4 h-4 text-green-400" />
                                            All-Time High / Low
                                        </h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            <StatBox
                                                label="ATH"
                                                value={data.ath ? formatPrice(data.ath) : '--'}
                                                sub={
                                                    <div>
                                                        <ChangeIndicator value={data.ath_change_percentage} />
                                                        <div className="text-[10px] text-gray-500 mt-0.5">{formatDate(data.ath_date)}</div>
                                                    </div>
                                                }
                                            />
                                            <StatBox
                                                label="ATL"
                                                value={data.atl ? formatPrice(data.atl) : '--'}
                                                sub={
                                                    <div>
                                                        <ChangeIndicator value={data.atl_change_percentage} />
                                                        <div className="text-[10px] text-gray-500 mt-0.5">{formatDate(data.atl_date)}</div>
                                                    </div>
                                                }
                                            />
                                        </div>
                                    </div>
                                ) : (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <TrendingUp className="w-4 h-4 text-green-400" />
                                            52-Week Range
                                        </h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            <StatBox label="52-Week High" value={data.fifty_two_week_high ? formatPrice(data.fifty_two_week_high) : '--'} />
                                            <StatBox label="52-Week Low" value={data.fifty_two_week_low ? formatPrice(data.fifty_two_week_low) : '--'} />
                                        </div>
                                        {/* Range Bar */}
                                        {data.fifty_two_week_low && data.fifty_two_week_high && data.price > 0 && (
                                            <div className="mt-3">
                                                <div className="h-2 bg-oracle-border rounded-full overflow-hidden relative">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 rounded-full"
                                                        style={{
                                                            width: `${Math.min(100, Math.max(0, ((data.price - data.fifty_two_week_low) / (data.fifty_two_week_high - data.fifty_two_week_low)) * 100))}%`
                                                        }}
                                                    />
                                                </div>
                                                <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                                                    <span>{formatPrice(data.fifty_two_week_low)}</span>
                                                    <span className="text-white font-medium">{formatPrice(data.price)}</span>
                                                    <span>{formatPrice(data.fifty_two_week_high)}</span>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* === SUPPLY INFO (Crypto) === */}
                                {data.type === 'crypto' && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Coins className="w-4 h-4 text-yellow-400" />
                                            Supply
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2">
                                            <StatBox label="Circulating" value={formatSupply(data.circulating_supply)} />
                                            <StatBox label="Total" value={formatSupply(data.total_supply)} />
                                            <StatBox label="Max" value={data.max_supply ? formatSupply(data.max_supply) : '∞'} />
                                        </div>
                                        {data.circulating_supply && data.max_supply && data.max_supply > 0 && (
                                            <div className="mt-2">
                                                <div className="h-1.5 bg-oracle-border rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-purple-500 to-cyan rounded-full"
                                                        style={{ width: `${Math.min(100, (data.circulating_supply / data.max_supply) * 100)}%` }}
                                                    />
                                                </div>
                                                <div className="text-[10px] text-gray-500 mt-1 text-right">
                                                    {((data.circulating_supply / data.max_supply) * 100).toFixed(1)}% in circulation
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* === COMPANY INFO (Stock) === */}
                                {data.type === 'stock' && (data.industry || data.country || data.employees) && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Building2 className="w-4 h-4 text-blue-400" />
                                            Company Info
                                        </h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            {data.industry && <StatBox label="Industry" value={data.industry} />}
                                            {data.country && <StatBox label="Country" value={data.country} />}
                                            {data.employees ? <StatBox label="Employees" value={data.employees.toLocaleString()} /> : null}
                                        </div>
                                    </div>
                                )}

                                {/* === ABOUT === */}
                                {data.description && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Layers className="w-4 h-4 text-indigo-400" />
                                            About {data.name}
                                        </h3>
                                        <p className="text-sm text-gray-300 leading-relaxed">
                                            {data.description}
                                        </p>
                                        {data.categories && data.categories.length > 0 && (
                                            <div className="flex flex-wrap gap-1.5 mt-3">
                                                {data.categories.filter(Boolean).map((cat) => (
                                                    <span
                                                        key={cat}
                                                        className="text-[10px] px-2 py-1 rounded-full bg-purple-500/10 text-purple-300 border border-purple-500/20"
                                                    >
                                                        {cat}
                                                    </span>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* === EXTRA INFO === */}
                                {data.type === 'crypto' && (data.genesis_date || data.hashing_algorithm) && (
                                    <div className="grid grid-cols-2 gap-2">
                                        {data.genesis_date && (
                                            <div className="flex items-center gap-2 text-xs text-gray-400 p-2 bg-black/10 rounded-lg">
                                                <Calendar className="w-3.5 h-3.5 text-gray-500" />
                                                Genesis: {formatDate(data.genesis_date)}
                                            </div>
                                        )}
                                        {data.hashing_algorithm && (
                                            <div className="flex items-center gap-2 text-xs text-gray-400 p-2 bg-black/10 rounded-lg">
                                                <Hash className="w-3.5 h-3.5 text-gray-500" />
                                                {data.hashing_algorithm}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* === COMMUNITY (Crypto) === */}
                                {data.type === 'crypto' && (data.twitter_followers || data.reddit_subscribers || data.telegram_channel_user_count) ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Users className="w-4 h-4 text-blue-400" />
                                            Community
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2">
                                            {data.twitter_followers ? <StatBox label="Twitter Followers" value={formatSupply(data.twitter_followers)} /> : null}
                                            {data.reddit_subscribers ? <StatBox label="Reddit Subscribers" value={formatSupply(data.reddit_subscribers)} /> : null}
                                            {data.telegram_channel_user_count ? <StatBox label="Telegram Members" value={formatSupply(data.telegram_channel_user_count)} /> : null}
                                        </div>
                                    </div>
                                ) : null}

                                {/* === DEVELOPER ACTIVITY (Crypto) === */}
                                {data.type === 'crypto' && (data.github_stars || data.commit_count_4_weeks || data.github_forks) ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Github className="w-4 h-4 text-gray-300" />
                                            Developer Activity
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2">
                                            {data.github_stars ? <StatBox label="GitHub Stars" value={formatSupply(data.github_stars)} /> : null}
                                            {data.github_forks ? <StatBox label="Forks" value={formatSupply(data.github_forks)} /> : null}
                                            {data.commit_count_4_weeks ? <StatBox label="Commits (4w)" value={data.commit_count_4_weeks.toLocaleString()} /> : null}
                                            {data.github_pull_requests_merged ? <StatBox label="PRs Merged" value={formatSupply(data.github_pull_requests_merged)} /> : null}
                                            {data.github_total_issues ? (
                                                <StatBox
                                                    label="Issues"
                                                    value={`${formatSupply(data.github_closed_issues || 0)} / ${formatSupply(data.github_total_issues)}`}
                                                    sub={<span className="text-[10px] text-gray-500">closed / total</span>}
                                                />
                                            ) : null}
                                            {data.github_subscribers ? <StatBox label="Watchers" value={formatSupply(data.github_subscribers)} /> : null}
                                        </div>
                                    </div>
                                ) : null}

                                {/* === SENTIMENT (Crypto) === */}
                                {data.type === 'crypto' && (data.sentiment_votes_up_percentage || data.watchlist_portfolio_users) ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <BarChart3 className="w-4 h-4 text-amber-400" />
                                            Sentiment
                                        </h3>
                                        {(data.sentiment_votes_up_percentage ?? 0) > 0 && (
                                            <div className="mb-3">
                                                <div className="flex justify-between text-xs text-gray-400 mb-1">
                                                    <span>👍 {data.sentiment_votes_up_percentage?.toFixed(0)}%</span>
                                                    <span>👎 {data.sentiment_votes_down_percentage?.toFixed(0)}%</span>
                                                </div>
                                                <div className="h-2 bg-red-500/30 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-green-500 rounded-full transition-all"
                                                        style={{ width: `${data.sentiment_votes_up_percentage}%` }}
                                                    />
                                                </div>
                                            </div>
                                        )}
                                        {data.watchlist_portfolio_users ? (
                                            <div className="text-xs text-gray-400">
                                                📊 {formatSupply(data.watchlist_portfolio_users)} users have this in their watchlist
                                            </div>
                                        ) : null}
                                    </div>
                                ) : null}

                                {/* === STOCK FINANCIALS === */}
                                {data.type === 'stock' && (data.revenue || data.earnings_per_share || data.profit_margin) ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Coins className="w-4 h-4 text-emerald-400" />
                                            Financials
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2">
                                            {data.revenue ? <StatBox label="Revenue" value={formatVolume(data.revenue)} /> : null}
                                            {data.net_income ? <StatBox label="Net Income" value={formatVolume(data.net_income)} /> : null}
                                            {data.free_cash_flow ? <StatBox label="Free Cash Flow" value={formatVolume(data.free_cash_flow)} /> : null}
                                            {data.earnings_per_share ? <StatBox label="EPS (TTM)" value={`$${data.earnings_per_share}`} /> : null}
                                            {data.forward_eps ? <StatBox label="EPS (Forward)" value={`$${data.forward_eps}`} /> : null}
                                            {data.forward_pe ? <StatBox label="Forward P/E" value={data.forward_pe.toFixed(2)} /> : null}
                                            {data.profit_margin ? <StatBox label="Profit Margin" value={`${data.profit_margin}%`} /> : null}
                                            {data.operating_margin ? <StatBox label="Op. Margin" value={`${data.operating_margin}%`} /> : null}
                                            {data.return_on_equity ? <StatBox label="ROE" value={`${data.return_on_equity}%`} /> : null}
                                            {data.beta ? <StatBox label="Beta" value={data.beta.toFixed(2)} /> : null}
                                            {data.book_value ? <StatBox label="Book Value" value={`$${data.book_value}`} /> : null}
                                            {data.price_to_book ? <StatBox label="P/B Ratio" value={data.price_to_book.toFixed(2)} /> : null}
                                            {data.debt_to_equity ? <StatBox label="Debt/Equity" value={data.debt_to_equity.toFixed(2)} /> : null}
                                        </div>
                                    </div>
                                ) : null}

                                {/* === ANALYST TARGETS (Stock) === */}
                                {data.type === 'stock' && data.target_mean_price ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <TrendingUp className="w-4 h-4 text-cyan" />
                                            Analyst Price Targets
                                        </h3>
                                        <div className="grid grid-cols-3 gap-2 mb-3">
                                            <StatBox label="Target Low" value={formatPrice(data.target_low_price || 0)} />
                                            <StatBox label="Target Mean" value={formatPrice(data.target_mean_price)} />
                                            <StatBox label="Target High" value={formatPrice(data.target_high_price || 0)} />
                                        </div>
                                        {data.target_low_price && data.target_high_price && (
                                            <div>
                                                <div className="h-2 bg-oracle-border rounded-full overflow-hidden relative">
                                                    <div
                                                        className="h-full bg-gradient-to-r from-red-500 via-cyan to-green-500 rounded-full"
                                                        style={{
                                                            width: `${Math.min(100, Math.max(0, ((data.price - data.target_low_price) / (data.target_high_price - data.target_low_price)) * 100))}%`
                                                        }}
                                                    />
                                                </div>
                                                <div className="flex justify-between mt-1 text-[10px] text-gray-500">
                                                    <span>{formatPrice(data.target_low_price)}</span>
                                                    <span className="text-white font-medium">Current: {formatPrice(data.price)}</span>
                                                    <span>{formatPrice(data.target_high_price)}</span>
                                                </div>
                                            </div>
                                        )}
                                        {data.recommendation && (
                                            <div className="mt-3 flex items-center gap-2">
                                                <span className="text-xs text-gray-400">Recommendation:</span>
                                                <span className={`text-xs px-2 py-1 rounded-full font-semibold uppercase ${data.recommendation.includes('buy') ? 'bg-green-500/20 text-green-400' :
                                                    data.recommendation.includes('sell') ? 'bg-red-500/20 text-red-400' :
                                                        'bg-yellow-500/20 text-yellow-400'
                                                    }`}>
                                                    {data.recommendation}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                ) : null}

                                {/* === MOVING AVERAGES (Stock) === */}
                                {data.type === 'stock' && (data.fifty_day_average || data.two_hundred_day_average) ? (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <TrendingUp className="w-4 h-4 text-orange-400" />
                                            Moving Averages
                                        </h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            {data.fifty_day_average ? (
                                                <StatBox
                                                    label="50-Day MA"
                                                    value={formatPrice(data.fifty_day_average)}
                                                    sub={
                                                        <span className={`text-[10px] ${data.price > data.fifty_day_average ? 'text-green-400' : 'text-red-400'}`}>
                                                            {data.price > data.fifty_day_average ? '▲ Above' : '▼ Below'} ({((data.price - data.fifty_day_average) / data.fifty_day_average * 100).toFixed(1)}%)
                                                        </span>
                                                    }
                                                />
                                            ) : null}
                                            {data.two_hundred_day_average ? (
                                                <StatBox
                                                    label="200-Day MA"
                                                    value={formatPrice(data.two_hundred_day_average)}
                                                    sub={
                                                        <span className={`text-[10px] ${data.price > data.two_hundred_day_average ? 'text-green-400' : 'text-red-400'}`}>
                                                            {data.price > data.two_hundred_day_average ? '▲ Above' : '▼ Below'} ({((data.price - data.two_hundred_day_average) / data.two_hundred_day_average * 100).toFixed(1)}%)
                                                        </span>
                                                    }
                                                />
                                            ) : null}
                                        </div>
                                    </div>
                                ) : null}

                                {/* === LINKS === */}
                                {Object.keys(data.links).length > 0 && (
                                    <div>
                                        <h3 className="text-sm font-semibold text-white flex items-center gap-2 mb-3">
                                            <Link2 className="w-4 h-4 text-cyan" />
                                            Links
                                        </h3>
                                        <div className="grid grid-cols-2 gap-2">
                                            {data.links.website && <LinkButton href={data.links.website} icon={Globe} label="Website" />}
                                            {data.links.explorer && <LinkButton href={data.links.explorer} icon={ExternalLink} label="Explorer" />}
                                            {data.links.github && <LinkButton href={data.links.github} icon={Github} label="GitHub" />}
                                            {data.links.twitter && <LinkButton href={data.links.twitter} icon={Twitter} label="Twitter" />}
                                            {data.links.reddit && <LinkButton href={data.links.reddit} icon={Users} label="Reddit" />}
                                        </div>
                                    </div>
                                )}
                            </>
                        ) : null}
                    </div>
                </div>
            </div>
        </div>
    );
}
