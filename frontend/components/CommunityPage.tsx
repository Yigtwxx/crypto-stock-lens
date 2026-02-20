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
            <div className="p-6 border-b border-oracle-border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-gradient-to-r from-oracle-dark to-violet/5">
                <div>
                    <h2 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
                        <Users className="w-6 h-6 text-orange-400" />
                        Community Intelligence
                    </h2>
                    <p className="text-gray-400 text-sm">Collaborate, share insights, and discuss market trends.</p>
                </div>

                <div className="flex items-center gap-3">
                    <button
                        onClick={handleRefresh}
                        className={`p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 transition-all ${isRefreshing ? 'animate-spin' : ''}`}
                    >
                        <RefreshCw className="w-5 h-5" />
                    </button>

                    {user && (
                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="bg-gradient-to-r from-violet to-pink hover:opacity-90 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-bold text-sm transition-all shadow-lg shadow-purple-500/20"
                        >
                            <Plus className="w-4 h-4" />
                            <span>Create Post</span>
                        </button>
                    )}
                </div>
            </div>

            {/* Tabs & Filters */}
            <div className="px-6 py-3 border-b border-oracle-border bg-oracle-dark/30 flex items-center justify-between">
                <div className="flex gap-4">
                    <button
                        onClick={() => setActiveTab('feed')}
                        className={`text-sm font-medium pb-1 relative transition-colors ${activeTab === 'feed' ? 'text-white' : 'text-gray-500 hover:text-gray-300'
                            }`}
                    >
                        feed
                        {activeTab === 'feed' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-orange-400 rounded-full"></span>}
                    </button>
                    {user && (
                        <button
                            onClick={() => setActiveTab('myposts')}
                            className={`text-sm font-medium pb-1 relative transition-colors ${activeTab === 'myposts' ? 'text-white' : 'text-gray-500 hover:text-gray-300'
                                }`}
                        >
                            My Posts
                            {activeTab === 'myposts' && <span className="absolute bottom-0 left-0 w-full h-0.5 bg-orange-400 rounded-full"></span>}
                        </button>
                    )}
                </div>

                <div className="flex items-center gap-2">
                    <Filter className="w-3 h-3 text-gray-500" />
                    <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="bg-transparent text-xs text-gray-400 focus:outline-none cursor-pointer"
                    >
                        <option value="all">All Types</option>
                        <option value="thought">Thoughts</option>
                        <option value="question">Questions</option>
                        <option value="analysis">Analysis</option>
                    </select>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                {isLoading ? (
                    <div className="flex items-center justify-center h-full text-gray-500">
                        <Loader2 className="w-8 h-8 animate-spin text-orange-400" />
                    </div>
                ) : posts.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500 opacity-60">
                        <MessageSquare className="w-12 h-12 mb-2" />
                        <p>No posts found. Be the first to share!</p>
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
