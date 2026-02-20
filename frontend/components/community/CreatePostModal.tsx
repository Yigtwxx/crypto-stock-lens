'use client';

import { useState } from 'react';
import { X, Bitcoin, Image, Type } from 'lucide-react';

interface CreatePostModalProps {
    isOpen: boolean;
    onClose: () => void;
    onPost: (data: { title: string; content: string; type: string; asset_symbol: string }) => Promise<void>;
}

export default function CreatePostModal({ isOpen, onClose, onPost }: CreatePostModalProps) {
    const [title, setTitle] = useState('');
    const [content, setContent] = useState('');
    const [type, setType] = useState('thought');
    const [assetSymbol, setAssetSymbol] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            await onPost({
                title,
                content,
                type,
                asset_symbol: assetSymbol
            });

            // Close handled by parent often, but we can do it here too after success
            onClose();

            // Reset form
            setTitle('');
            setContent('');
            setType('thought');
            setAssetSymbol('');
        } catch (error) {
            console.error('Failed to post', error);
        } finally {
            setIsLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
            <div className="bg-oracle-card border border-oracle-border rounded-xl w-full max-w-lg shadow-2xl animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-center p-4 border-b border-oracle-border">
                    <h3 className="text-lg font-bold text-white">Share with Community</h3>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-4 space-y-4">
                    {/* Type Selection */}
                    <div className="flex gap-2">
                        {['thought', 'question', 'analysis'].map(t => (
                            <button
                                key={t}
                                type="button"
                                onClick={() => setType(t)}
                                className={`flex-1 py-2 rounded-lg text-sm font-medium capitalize transition-all border ${type === t
                                        ? 'bg-violet/20 border-violet text-white'
                                        : 'bg-oracle-dark border-oracle-border text-gray-400 hover:text-gray-200'
                                    }`}
                            >
                                {t}
                            </button>
                        ))}
                    </div>

                    {/* Title */}
                    <div>
                        <input
                            type="text"
                            placeholder="Title (optional)"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            className="w-full bg-oracle-dark border border-oracle-border rounded-lg px-4 py-2 text-white focus:outline-none focus:border-violet placeholder-gray-500"
                        />
                    </div>

                    {/* Content */}
                    <div>
                        <textarea
                            placeholder="What's on your mind?"
                            value={content}
                            onChange={e => setContent(e.target.value)}
                            rows={5}
                            required
                            className="w-full bg-oracle-dark border border-oracle-border rounded-lg px-4 py-3 text-white focus:outline-none focus:border-violet placeholder-gray-500 resize-none"
                        />
                    </div>

                    {/* Asset Symbol */}
                    <div className="flex items-center gap-2 bg-oracle-dark border border-oracle-border rounded-lg px-4 py-2">
                        <Bitcoin className="w-4 h-4 text-orange-400" />
                        <input
                            type="text"
                            placeholder="Related Asset (e.g. BTC, AAPL) - Optional"
                            value={assetSymbol}
                            onChange={e => setAssetSymbol(e.target.value.toUpperCase())}
                            className="flex-1 bg-transparent text-white focus:outline-none placeholder-gray-500 text-sm uppercase"
                        />
                    </div>

                    {/* Footer Actions */}
                    <div className="flex justify-end pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-400 hover:text-white mr-2"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !content.trim()}
                            className="bg-gradient-to-r from-violet to-pink text-white px-6 py-2 rounded-lg font-medium hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                        >
                            {isLoading ? 'Posting...' : 'Post'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
