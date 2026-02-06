'use client';

import { useState, useEffect } from 'react';
import { Plus, MoreHorizontal, Trash2, ArrowUpRight, ArrowDownRight, RefreshCw, Eye } from 'lucide-react';
import { fetchWatchlists, createWatchlist, deleteWatchlist, Watchlist } from '@/lib/api';
import CreateWatchlistModal from './CreateWatchlistModal';

export default function WatchlistWidget() {
    const [watchlists, setWatchlists] = useState<Watchlist[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [autoRefreshCount, setAutoRefreshCount] = useState(0);

    const loadData = async () => {
        try {
            const data = await fetchWatchlists();
            setWatchlists(data);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, [autoRefreshCount]);

    // Auto-refresh every 30 seconds
    useEffect(() => {
        const interval = setInterval(() => {
            setAutoRefreshCount(c => c + 1);
        }, 30000);
        return () => clearInterval(interval);
    }, []);

    const handleCreate = async (name: string, items: { symbol: string, type: 'STOCK' | 'CRYPTO' }[]) => {
        try {
            setIsLoading(true);
            const updatedLists = await createWatchlist(name, items);
            setWatchlists(updatedLists);
        } catch (error) {
            console.error(error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Are you sure you want to delete this watchlist?')) return;
        try {
            await deleteWatchlist(id);
            setWatchlists(prev => prev.filter(w => w.id !== id));
        } catch (error) {
            console.error(error);
        }
    };

    if (isLoading && watchlists.length === 0) {
        return (
            <div className="mt-6 border border-white/5 rounded-xl p-8 bg-[#0a0a0a]/40 text-center animate-pulse">
                <div className="h-6 w-32 mx-auto bg-white/10 rounded mb-4"></div>
                <div className="h-32 w-full bg-white/5 rounded"></div>
            </div>
        );
    }

    return (
        <div className="mt-8">
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Eye className="w-5 h-5 text-[#d946ef]" />
                    <h2 className="text-lg font-bold text-white">Your Watchlists</h2>
                </div>
                <button
                    onClick={() => setIsCreateModalOpen(true)}
                    className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-xs font-medium text-white rounded-lg transition-colors border border-white/5"
                >
                    <Plus className="w-3.5 h-3.5" />
                    New List
                </button>
            </div>

            {watchlists.length === 0 ? (
                <div className="border border-white/5 rounded-xl p-8 bg-[#0a0a0a]/40 text-center">
                    <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-3">
                        <Eye className="w-6 h-6 text-gray-500" />
                    </div>
                    <h3 className="text-gray-300 font-medium mb-1">No Watchlists Yet</h3>
                    <p className="text-gray-500 text-sm mb-4">Create a watchlist to track your favorite stocks and crypto assets.</p>
                    <button
                        onClick={() => setIsCreateModalOpen(true)}
                        className="px-4 py-2 bg-[#d946ef] text-white text-sm font-medium rounded-lg hover:bg-[#d946ef]/90 transition-colors"
                    >
                        Create Watchlist
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {watchlists.map(list => (
                        <div key={list.id} className="bg-[#0a0a0a]/60 border border-white/5 rounded-xl p-4 flex flex-col h-full hover:border-white/10 transition-colors">
                            <div className="flex items-center justify-between mb-3 border-b border-white/5 pb-2">
                                <h3 className="font-semibold text-white">{list.name}</h3>
                                <button
                                    onClick={() => handleDelete(list.id)}
                                    className="p-1 hover:bg-red-500/20 text-gray-500 hover:text-red-500 rounded transition-colors"
                                >
                                    <Trash2 className="w-3.5 h-3.5" />
                                </button>
                            </div>

                            <div className="space-y-1 overflow-auto max-h-[300px] flex-1">
                                {list.items.map((item, idx) => (
                                    <div key={`${item.symbol}-${idx}`} className="flex items-center justify-between p-2 hover:bg-white/5 rounded-lg transition-colors group">
                                        <div className="flex items-center gap-2">
                                            {item.logo ? (
                                                <img src={item.logo} alt={item.symbol} className="w-6 h-6 rounded-full" />
                                            ) : (
                                                <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center text-[8px] text-gray-400">
                                                    {item.symbol[0]}
                                                </div>
                                            )}
                                            <div>
                                                <div className="text-sm font-medium text-white">{item.symbol}</div>
                                                <div className="text-[10px] text-gray-500">{item.type}</div>
                                            </div>
                                        </div>

                                        <div className="text-right">
                                            <div className="text-sm text-white font-mono">
                                                ${item.price?.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: item.price < 1 ? 4 : 2 })}
                                            </div>
                                            <div className={`text-xs font-medium flex items-center justify-end gap-1 ${(item.change_24h || 0) >= 0 ? 'text-[#22c55e]' : 'text-[#ef4444]'}`}>
                                                {(item.change_24h || 0) >= 0 ? (
                                                    <ArrowUpRight className="w-3 h-3" />
                                                ) : (
                                                    <ArrowDownRight className="w-3 h-3" />
                                                )}
                                                {Math.abs(item.change_24h || 0).toFixed(2)}%
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ))}
                </div>
            )}

            <CreateWatchlistModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onCreate={handleCreate}
            />
        </div>
    );
}
