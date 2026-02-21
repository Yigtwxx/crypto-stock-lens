'use client';

import { useState, useEffect } from 'react';
import { Plus, Users, RefreshCw, Filter, MessageSquare, Loader2 } from 'lucide-react';
import PostCard from './community/PostCard';
import CreatePostModal from './community/CreatePostModal';
import { useAuth } from '@/contexts/AuthContext';

export default function CommunityPage() {
    const { user } = useAuth();
    const [activeTab, setActiveTab] = useState<'feed' | 'myposts'>('feed');
    const [filterType, setFilterType] = useState<string>('all');
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [posts, setPosts] = useState<any[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);

    const fetchPosts = async () => {
        try {
            const endpoint = activeTab === 'myposts' && user
                ? `http://localhost:8000/api/community/posts/user/${user.id}`
                : `http://localhost:8000/api/community/posts?type=${filterType === 'all' ? '' : filterType}`;

            const res = await fetch(endpoint);
            if (res.ok) {
                const data = await res.json();
                setPosts(data.posts || []);
            }
        } catch (error) {
            console.error('Error fetching posts:', error);
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    };

    useEffect(() => {
        setIsLoading(true);
        fetchPosts();
    }, [activeTab, filterType, user]); // Re-fetch when filters change

    const handleRefresh = () => {
        setIsRefreshing(true);
        fetchPosts();
    };

    const handleCreatePost = async (data: { title: string; content: string; type: string; asset_symbol: string }) => {
        if (!user) return;

        try {
            const res = await fetch('http://localhost:8000/api/community/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    ...data
                })
            });

            if (res.ok) {
                // Refresh posts
                fetchPosts();
            }
        } catch (error) {
            console.error('Error creating post:', error);
        }
    };

    const handleLike = async (postId: string) => {
        if (!user) {
            alert("Please login to like posts");
            return;
        }

        try {
            await fetch(`http://localhost:8000/api/community/posts/${postId}/like`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ user_id: user.id })
            });
            // Optimistic update is done in PostCard, but we could refresh
        } catch (error) {
            console.error('Error liking post:', error);
        }
    };

    const handleComment = (postId: string) => {
        // For MVP, just alerting or simple prompt logic could be here, 
        // but PostCard already has a basic button. 
        // Ideally opens a PostDetail view or expands comments.
        // For now, let's just log or show a "Coming Soon" for detailed comment view 
        // unless I implement a PostDetailModal.
        console.log("Open comments for", postId);
        // Could implement a view logic here later
    };

    return (
        <div className="h-full flex flex-col bg-oracle-darker overflow-hidden">
            {/* Header Section */}
            <div className="relative p-8 overflow-hidden flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6 border-b border-oracle-border/50">
                <div className="absolute inset-x-0 top-0 h-40 bg-gradient-to-br from-violet/20 via-transparent to-transparent pointer-events-none" />
                <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-orange-500/5 rounded-full blur-[100px] pointer-events-none" />

                <div className="relative z-10">
                    <h2 className="text-3xl font-black text-white mb-2 flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-orange-400/20 to-orange-600/20 rounded-xl border border-orange-500/30">
                            <Users className="w-6 h-6 text-orange-400" />
                        </div>
                        Community Intelligence
                    </h2>
                    <p className="text-gray-400 text-sm max-w-xl">Collaborate with other traders, share your market insights, and stay updated with live discussions.</p>
                </div>

                <div className="relative z-10 flex items-center gap-4 w-full sm:w-auto">
                    <button
                        onClick={handleRefresh}
                        className={`p-2.5 rounded-xl bg-oracle-darker border border-oracle-border text-gray-400 hover:text-white hover:border-violet/50 hover:bg-violet/10 transition-all shadow-sm ${isRefreshing ? 'animate-spin border-violet text-violet' : ''}`}
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>

                    {user && (
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="flex-1 sm:flex-none bg-gradient-to-r from-violet to-pink hover:to-orange-500 hover:scale-[1.02] active:scale-[0.98] text-white px-5 py-2.5 rounded-xl flex items-center justify-center gap-2 font-bold text-sm transition-all shadow-lg shadow-violet/25 border border-white/10"
                        >
                            <Plus className="w-5 h-5" />
                            <span>Create Post</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs & Filters */}
            <div className="px-6 py-4 border-b border-oracle-border/50 bg-black/20 backdrop-blur-md flex flex-wrap gap-4 items-center justify-between sticky top-0 z-20">
                <div className="flex gap-2 p-1 bg-oracle-darker/80 border border-oracle-border rounded-xl">
                    <button
                        onClick={() => setActiveTab('feed')}
                        className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === 'feed'
                            ? 'bg-gradient-to-r from-violet/20 to-pink/20 text-white shadow-sm border border-violet/30'
                            : 'text-gray-500 hover:text-gray-300 border border-transparent'
                            }`}
                    >
                        Live Feed
                    </button>
                    {user && (
                        <button
                            onClick={() => setActiveTab('myposts')}
                            className={`px-4 py-1.5 rounded-lg text-sm font-semibold transition-all duration-300 ${activeTab === 'myposts'
                                ? 'bg-gradient-to-r from-violet/20 to-pink/20 text-white shadow-sm border border-violet/30'
                                : 'text-gray-500 hover:text-gray-300 border border-transparent'
                                }`}
                        >
                            My Posts
                        </button>
                    )}
                </div>

                <div className="flex items-center gap-3 bg-oracle-darker/80 border border-oracle-border rounded-xl px-4 py-1.5 focus-within:border-violet/50 transition-colors">
                    <Filter className="w-4 h-4 text-violet" />
                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="bg-transparent text-sm font-medium text-gray-300 focus:outline-none cursor-pointer py-1"
                    >
                        <option value="all" className="bg-oracle-darker text-gray-300">All Posts</option>
                        <option value="thought" className="bg-oracle-darker text-gray-300">Thoughts</option>
                        <option value="question" className="bg-oracle-darker text-gray-300">Questions</option>
                        <option value="analysis" className="bg-oracle-darker text-gray-300">Analysis</option>
                    </select>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 bg-[#0a0f16]">
                {isLoading ? (
                    <div className="flex items-center justify-center h-full">
                        <div className="flex flex-col items-center gap-4">
                            <div className="w-12 h-12 rounded-full border-4 border-oracle-border border-t-violet animate-spin"></div>
                            <p className="text-gray-400 font-medium">Loading intelligence...</p>
                        </div>
                    </div>
                ) : posts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full max-w-md mx-auto text-center">
                        <div className="w-24 h-24 mb-6 rounded-3xl bg-gradient-to-br from-violet/10 to-transparent border border-violet/20 flex items-center justify-center shadow-lg shadow-violet/5">
                            <MessageSquare className="w-10 h-10 text-violet" />
                        </div>
                        <h3 className="text-2xl font-bold text-white mb-2">No Posts Yet</h3>
                        <p className="text-gray-400 mb-8">
                            {activeTab === 'myposts'
                                ? "You haven't shared any insights with the community yet."
                                : "The feed is quiet right now. Be the spark that starts the conversation!"}
                        </p>
                        {user && (
                            <button
                                onClick={() => setShowCreateModal(true)}
                                className="bg-oracle-darker border border-oracle-border hover:border-violet/50 hover:bg-violet/10 text-white px-6 py-3 rounded-xl flex items-center gap-2 font-bold transition-all shadow-sm group"
                            >
                                <Plus className="w-5 h-5 text-violet group-hover:scale-110 transition-transform" />
                                <span>Create Your First Post</span>
                            </button>
                        )}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-7xl mx-auto">
                        {posts.map(post => (
                            <PostCard
                                key={post.id}
                                post={post}
                                onLike={handleLike}
                                onComment={handleComment}
                            />
                        ))}
                    </div>
                )}
            </div>

            <CreatePostModal
                isOpen={showCreateModal}
                onClose={() => setShowCreateModal(false)}
                onPost={handleCreatePost}
            />
        </div>
    );
}
