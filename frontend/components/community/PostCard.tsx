'use client';

import { useState } from 'react';
import { MessageSquare, Heart, Share2, MoreHorizontal, User, Bitcoin } from 'lucide-react';
// import { formatDistanceToNow } from 'date-fns'; // Assuming date-fns is available, or use custom formatter
import { formatDistanceToNow } from 'date-fns';

interface PostCardProps {
    post: {
        id: string;
        content: string;
        type: 'question' | 'thought' | 'analysis';
        title?: string;
        asset_symbol?: string;
        created_at: string;
        likes_count: number;
        comments_count: number;
        profiles: {
            full_name: string;
            avatar_url?: string;
            subscription_plan?: string;
        };
    };
    onLike: (id: string) => void;
    onComment: (id: string) => void;
}

export default function PostCard({ post, onLike, onComment }: PostCardProps) {
    const [isLiked, setIsLiked] = useState(false); // In a real app, strict check from backend response
    const [likesCount, setLikesCount] = useState(post.likes_count);

    const handleLike = () => {
        setIsLiked(!isLiked);
        setLikesCount(prev => isLiked ? prev - 1 : prev + 1);
        onLike(post.id);
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'analysis': return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
            case 'question': return 'text-orange-400 bg-orange-400/10 border-orange-400/20';
            default: return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
        }
    };

    const getPlanBadge = (plan?: string) => {
        if (plan === 'whale') return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-cyan/20 text-cyan border border-cyan/30">WHALE</span>;
        if (plan === 'pro') return <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-pink/20 text-pink border border-pink/30">PRO</span>;
        return null;
    };

    return (
        <div className="bg-oracle-card border border-oracle-border rounded-xl p-5 hover:border-oracle-border/80 transition-all group">
            {/* Header */}
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-oracle-darker border border-oracle-border flex items-center justify-center overflow-hidden">
                        {post.profiles?.avatar_url ? (
                            <img src={post.profiles.avatar_url} alt={post.profiles.full_name} className="w-full h-full object-cover" />
                        ) : (
                            <User className="w-5 h-5 text-gray-400" />
                        )}
                    </div>
                    <div>
                        <div className="flex items-center gap-2">
                            <h3 className="font-semibold text-gray-200">{post.profiles?.full_name || 'Anonymous User'}</h3>
                            {getPlanBadge(post.profiles?.subscription_plan)}
                        </div>
                        <p className="text-xs text-gray-500">
                            {formatDistanceToNow(new Date(post.created_at), { addSuffix: true })}
                        </p>
                    </div>
                </div>
                <button className="text-gray-500 hover:text-white transition-colors">
                    <MoreHorizontal className="w-5 h-5" />
                </button>
            </div>

            {/* Content */}
            <div className="mb-4">
                <div className="flex items-center gap-2 mb-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getTypeColor(post.type)} uppercase`}>
                        {post.type}
                    </span>
                    {post.asset_symbol && (
                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-oracle-dark border border-oracle-border text-gray-300 flex items-center gap-1">
                            <Bitcoin className="w-3 h-3 text-orange-400" />
                            {post.asset_symbol}
                        </span>
                    )}
                </div>

                {post.title && (
                    <h4 className="text-lg font-bold text-white mb-2">{post.title}</h4>
                )}

                <p className="text-gray-300 whitespace-pre-wrap leading-relaxed">
                    {post.content}
                </p>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-6 pt-3 border-t border-oracle-border/50">
                <button
                    onClick={handleLike}
                    className={`flex items-center gap-2 text-sm transition-colors ${isLiked ? 'text-pink' : 'text-gray-500 hover:text-pink'}`}
                >
                    <Heart className={`w-4 h-4 ${isLiked ? 'fill-current' : ''}`} />
                    <span>{likesCount} Likes</span>
                </button>

                <button
                    onClick={() => onComment(post.id)}
                    className="flex items-center gap-2 text-sm text-gray-500 hover:text-cyan transition-colors"
                >
                    <MessageSquare className="w-4 h-4" />
                    <span>{post.comments_count} Comments</span>
                </button>

                <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-white transition-colors ml-auto">
                    <Share2 className="w-4 h-4" />
                    <span>Share</span>
                </button>
            </div>
        </div>
    );
}
