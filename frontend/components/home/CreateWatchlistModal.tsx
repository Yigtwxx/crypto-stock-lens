'use client';

import { useState, useEffect } from 'react';
import { X, Search, Plus, Check } from 'lucide-react';
import { fetchMarketOverview, fetchNasdaqOverview } from '@/lib/api';

interface Asset {
    symbol: string;
    name: string;
    type: 'STOCK' | 'CRYPTO';
    logo?: string;
}

interface CreateWatchlistModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (name: string, items: { symbol: string, type: 'STOCK' | 'CRYPTO' }[]) => void;
}

export default function CreateWatchlistModal({ isOpen, onClose, onCreate }: CreateWatchlistModalProps) {
    const [name, setName] = useState('');
    const [searchTerm, setSearchTerm] = useState('');
    const [availableAssets, setAvailableAssets] = useState<Asset[]>([]);
    const [selectedAssets, setSelectedAssets] = useState<Asset[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    // Fetch assets on mount
    useEffect(() => {
        if (isOpen && availableAssets.length === 0) {
            loadAssets();
        }
    }, [isOpen]);

    const loadAssets = async () => {
        setIsLoading(true);
        try {
            // Fetch both crypto and stocks
            const [cryptoData, stockData] = await Promise.all([
                fetchMarketOverview(),
                fetchNasdaqOverview()
            ]);

            const assets: Asset[] = [];

            // Process Crypto
            cryptoData.coins.forEach((c: any) => {
                assets.push({
                    symbol: c.symbol,
                    name: c.name,
                    type: 'CRYPTO',
                    logo: c.logo
                });
            });

            // Process Stocks
            stockData.coins.forEach((s: any) => {
                assets.push({
                    symbol: s.symbol,
                    name: s.name,
                    type: 'STOCK',
                    logo: s.logo
                });
            });

            setAvailableAssets(assets);
        } catch (error) {
            console.error("Failed to load assets", error);
        } finally {
            setIsLoading(false);
        }
    };

    const toggleAsset = (asset: Asset) => {
        if (selectedAssets.find(a => a.symbol === asset.symbol)) {
            setSelectedAssets(prev => prev.filter(a => a.symbol !== asset.symbol));
        } else {
            setSelectedAssets(prev => [...prev, asset]);
        }
    };

    const handleCreate = () => {
        if (!name.trim()) return;
        const items = selectedAssets.map(a => ({
            symbol: a.symbol,
            type: a.type
        }));
        onCreate(name, items);
        // Reset
        setName('');
        setSelectedAssets([]);
        onClose();
    };

    if (!isOpen) return null;

    const filteredAssets = availableAssets.filter(a =>
        a.symbol.toLowerCase().includes(searchTerm.toLowerCase()) ||
        a.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
            <div className="bg-[#18181b] border border-white/10 rounded-xl w-[500px] max-h-[80vh] flex flex-col shadow-2xl">
                {/* Header */}
                <div className="p-4 border-b border-white/5 flex justify-between items-center">
                    <h2 className="text-lg font-semibold text-white">New Watchlist</h2>
                    <button onClick={onClose} className="p-1 hover:bg-white/5 rounded-lg transition-colors">
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* Body */}
                <div className="p-4 space-y-4 flex-1 overflow-auto">
                    {/* Name Input */}
                    <div>
                        <label className="block text-xs uppercase tracking-wider text-gray-400 font-medium mb-1.5">
                            Watchlist Name
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g., My Portfolio"
                            className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg px-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-[#d946ef] transition-colors"
                        />
                    </div>

                    {/* Search */}
                    <div>
                        <label className="block text-xs uppercase tracking-wider text-gray-400 font-medium mb-1.5">
                            Add Assets ({selectedAssets.length})
                        </label>
                        <div className="relative mb-2">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
                            <input
                                type="text"
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                placeholder="Search stocks or crypto..."
                                className="w-full bg-[#0a0a0a] border border-white/10 rounded-lg pl-9 pr-3 py-2 text-white placeholder-gray-600 focus:outline-none focus:border-[#d946ef] transition-colors"
                            />
                        </div>

                        {/* List */}
                        <div className="h-48 overflow-y-auto border border-white/5 rounded-lg bg-[#0a0a0a]/50">
                            {isLoading ? (
                                <div className="flex items-center justify-center h-full text-gray-500 text-sm">
                                    Loading assets...
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {filteredAssets.map(asset => {
                                        const isSelected = !!selectedAssets.find(a => a.symbol === asset.symbol);
                                        return (
                                            <button
                                                key={`${asset.type}-${asset.symbol}`}
                                                onClick={() => toggleAsset(asset)}
                                                className={`w-full flex items-center justify-between p-2.5 hover:bg-white/5 transition-colors text-left ${isSelected ? 'bg-white/5' : ''}`}
                                            >
                                                <div className="flex items-center gap-3">
                                                    {asset.logo ? (
                                                        <img src={asset.logo} alt={asset.symbol} className="w-5 h-5 rounded-full" />
                                                    ) : (
                                                        <div className="w-5 h-5 rounded-full bg-white/10" />
                                                    )}
                                                    <div>
                                                        <div className="text-white font-medium text-sm">{asset.symbol}</div>
                                                        <div className="text-gray-500 text-xs truncate max-w-[200px]">{asset.name}</div>
                                                    </div>
                                                </div>
                                                {isSelected ? (
                                                    <Check className="w-4 h-4 text-[#d946ef]" />
                                                ) : (
                                                    <Plus className="w-4 h-4 text-gray-600" />
                                                )}
                                            </button>
                                        );
                                    })}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-white/5 flex justify-end gap-2">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleCreate}
                        disabled={!name.trim() || selectedAssets.length === 0}
                        className="px-4 py-2 rounded-lg text-sm font-medium bg-[#d946ef] text-white hover:bg-[#d946ef]/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        Create Watchlist
                    </button>
                </div>
            </div>
        </div>
    );
}
