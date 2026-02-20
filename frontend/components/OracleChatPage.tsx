'use client';

import { useState, useRef, useEffect, ReactNode, useContext } from 'react';
import {
    Brain,
    Send,
    Loader2,
    Sparkles,
    MessageCircle,
    Clock,
    Zap,
    TrendingUp,
    Bitcoin,
    HelpCircle,
    Menu,
    Trash2
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import ChatSidebar from './ChatSidebar';

// Safe auth hook - returns null if not in AuthProvider
function useSafeAuth() {
    try {
        // Dynamic import to avoid build-time issues
        const { useAuth } = require('@/contexts/AuthContext');
        return useAuth();
    } catch {
        return { user: null, session: null, loading: false };
    }
}

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    thinkingTime?: number;
    timestamp: Date;
}

interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Suggested prompts for quick start
const SUGGESTED_PROMPTS = [
    { icon: Bitcoin, text: "Analyze Bitcoin technically", color: "text-orange-400" },
    { icon: TrendingUp, text: "What do you think about NVDA?", color: "text-green-400" },
    { icon: Zap, text: "How is the market today?", color: "text-cyan" },
    { icon: HelpCircle, text: "Best DeFi coins to buy?", color: "text-pink" },
];

export default function OracleChatPage() {
    const { user } = useSafeAuth();
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [inputValue, setInputValue] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [isAvailable, setIsAvailable] = useState<boolean | null>(null);
    const [isLoadingHistory, setIsLoadingHistory] = useState(false);
    const [responseStyle, setResponseStyle] = useState<'detailed' | 'concise'>('detailed');

    // Session State
    const [sessions, setSessions] = useState<ChatSession[]>([]);
    const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
    const [isSidebarOpen, setIsSidebarOpen] = useState(false);

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    // Check chat availability on mount
    useEffect(() => {
        checkAvailability();
    }, []);

    // Load chat sessions when user is available
    useEffect(() => {
        if (user?.id) {
            loadSessions();
        }
    }, [user?.id]);

    // Load messages when session changes
    useEffect(() => {
        if (user?.id && currentSessionId) {
            loadSessionMessages(currentSessionId);
        } else if (!currentSessionId) {
            setMessages([]);
        }
    }, [currentSessionId, user?.id]);

    // Auto-scroll to bottom when new messages arrive
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const checkAvailability = async () => {
        try {
            const response = await fetch(`${API_BASE}/api/chat/status`);
            const data = await response.json();
            setIsAvailable(data.available);
        } catch {
            setIsAvailable(false);
        }
    };

    const loadSessions = async () => {
        if (!user?.id) return;
        try {
            const response = await fetch(`${API_BASE}/api/chat/sessions/${user.id}`);
            const data = await response.json();
            setSessions(data.sessions);
        } catch (error) {
            console.error('Failed to load sessions:', error);
        }
    };

    const loadSessionMessages = async (sessionId: string) => {
        setIsLoadingHistory(true);
        try {
            const response = await fetch(`${API_BASE}/api/chat/sessions/${sessionId}/messages`);
            const data = await response.json();

            if (data.messages) {
                const loadedMessages: ChatMessage[] = data.messages.map((m: any) => ({
                    role: m.role as 'user' | 'assistant',
                    content: m.content,
                    thinkingTime: m.thinking_time,
                    timestamp: new Date(m.created_at)
                }));
                setMessages(loadedMessages);
            }
        } catch (error) {
            console.error('Failed to load session messages:', error);
        } finally {
            setIsLoadingHistory(false);
        }
    };

    const handleNewChat = () => {
        setCurrentSessionId(null);
        setMessages([]);
        setIsSidebarOpen(false); // Mobile UX
    };

    const handleDeleteSession = async (sessionId: string) => {
        if (!user?.id) return;
        try {
            await fetch(`${API_BASE}/api/chat/sessions/${sessionId}?user_id=${user.id}`, {
                method: 'DELETE'
            });
            setSessions(prev => prev.filter(s => s.id !== sessionId));
            if (currentSessionId === sessionId) {
                handleNewChat();
            }
        } catch (error) {
            console.error('Failed to delete session:', error);
        }
    };

    const saveChatMessage = async (role: string, content: string, sessionId?: string, thinkingTime?: number) => {
        if (!user?.id) return;

        try {
            await fetch(`${API_BASE}/api/chat/history`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_id: user.id,
                    role,
                    content,
                    session_id: sessionId,
                    thinking_time: thinkingTime
                })
            });

            // Refresh sessions to update timestamp/order
            // loadSessions(); // Removed: handled optimistically in sendMessage
        } catch (error) {
            console.error('Failed to save chat message:', error);
        }
    };

    const sendMessage = async (text: string) => {
        if (!text.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: text.trim(),
            timestamp: new Date()
        };

        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        // Initialize session if needed
        let activeSessionId = currentSessionId;
        if (!activeSessionId && user?.id) {
            try {
                // Generate title from first message
                const title = text.trim().slice(0, 30) + (text.length > 30 ? "..." : "");
                const res = await fetch(`${API_BASE}/api/chat/sessions`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_id: user.id, title })
                });
                const session = await res.json();
                if (session?.id) {
                    activeSessionId = session.id;
                    setCurrentSessionId(session.id);
                    setSessions(prev => [session, ...prev]);
                }
            } catch (e) {
                console.error("Failed to create session", e);
            }
        }

        // Save user message to DB
        await saveChatMessage('user', text.trim(), activeSessionId || undefined);

        // OPTIMISTIC UPDATE: Move current session to top
        if (activeSessionId) {
            setSessions(prev => {
                const sessionIndex = prev.findIndex(s => s.id === activeSessionId);
                if (sessionIndex > -1) {
                    const updatedSession = {
                        ...prev[sessionIndex],
                        updated_at: new Date().toISOString()
                    };
                    const newSessions = [...prev];
                    newSessions.splice(sessionIndex, 1);
                    return [updatedSession, ...newSessions];
                }
                return prev;
            });
        }

        try {
            // Build history for context (exclude current message)
            const history = messages.map(m => ({
                role: m.role,
                content: m.content
            }));

            const response = await fetch(`${API_BASE}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    message: text.trim(),
                    history: history.length > 0 ? history : undefined,
                    session_id: activeSessionId,
                    style: responseStyle
                })
            });

            const data = await response.json();

            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: data.response,
                thinkingTime: data.thinking_time,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, assistantMessage]);

            // Save assistant message to DB
            await saveChatMessage('assistant', data.response, activeSessionId || undefined, data.thinking_time);
        } catch (error) {
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: '🔴 **Bağlantı Hatası**\n\nOracle\'a ulaşılamıyor. Lütfen daha sonra tekrar deneyin.',
                timestamp: new Date()
            };
            setMessages(prev => [...prev, errorMessage]);
        } finally {
            setIsLoading(false);
            // activeSessionId loadSessions(); // Removed to rely on optimistic updates for speed
            inputRef.current?.focus();
        }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        sendMessage(inputValue);
    };

    const handleSuggestionClick = (text: string) => {
        sendMessage(text);
    };

    return (
        <div className="h-full flex bg-oracle-darker overflow-hidden">
            {/* Sidebar */}
            <ChatSidebar
                sessions={sessions}
                currentSessionId={currentSessionId}
                onSelectSession={setCurrentSessionId}
                onNewChat={handleNewChat}
                onDeleteSession={handleDeleteSession}
                isOpen={isSidebarOpen}
                setIsOpen={setIsSidebarOpen}
            />

            {/* Main Chat Area */}
            <div className="flex-1 flex flex-col h-full min-w-0">
                {/* Header */}
                <div className="h-14 px-4 md:px-6 border-b border-oracle-border flex items-center gap-3 bg-gradient-to-r from-oracle-dark via-oracle-dark to-pink/5 shrink-0">
                    <button
                        onClick={() => setIsSidebarOpen(true)}
                        className="md:hidden p-2 -ml-2 text-gray-400 hover:text-white"
                    >
                        <Menu className="w-5 h-5" />
                    </button>

                    <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet via-pink to-cyan flex items-center justify-center shadow-lg shadow-pink/20 shrink-0">
                        <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div>
                        <h2 className="font-semibold bg-gradient-to-r from-white to-pink bg-clip-text text-transparent flex items-center gap-2 text-sm md:text-base">
                            Oracle Chat
                            <Sparkles className="w-4 h-4 text-pink animate-pulse" />
                        </h2>
                        <p className="text-[10px] md:text-xs text-gray-500 hidden md:block">Crypto, stock and market analysis AI assistant</p>
                    </div>
                    <div className="ml-auto flex items-center gap-3">
                        {isAvailable === true && (
                            <span className="flex items-center gap-1.5 text-[10px] md:text-xs text-green-400">
                                <span className="w-2 h-2 rounded-full bg-green-400 animate-pulse" />
                                <span className="hidden md:inline">Online</span>
                            </span>
                        )}
                        {isAvailable === false && (
                            <span className="flex items-center gap-1.5 text-[10px] md:text-xs text-red-400">
                                <span className="w-2 h-2 rounded-full bg-red-400" />
                                <span className="hidden md:inline">Offline</span>
                            </span>
                        )}
                    </div>
                </div>

                {/* Messages Area */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    {messages.length === 0 ? (
                        // Welcome State
                        <div className="h-full flex flex-col items-center justify-center text-center px-8">
                            <div className="w-24 h-24 rounded-3xl bg-gradient-to-br from-violet/20 via-pink/20 to-cyan/20 border border-oracle-border flex items-center justify-center mb-6">
                                <Brain className="w-12 h-12 text-pink" />
                            </div>
                            <h3 className="text-2xl font-bold bg-gradient-to-r from-white via-pink to-cyan bg-clip-text text-transparent mb-3">
                                Welcome to Oracle
                            </h3>
                            <p className="text-gray-400 max-w-md mb-8">
                                Ask questions about cryptocurrencies, stocks and market analysis.
                                Oracle takes time to provide detailed and accurate answers.
                            </p>

                            {/* Suggested Prompts */}
                            <div className="grid grid-cols-2 gap-3 max-w-lg w-full">
                                {SUGGESTED_PROMPTS.map((prompt, index) => (
                                    <button
                                        key={index}
                                        onClick={() => handleSuggestionClick(prompt.text)}
                                        className="flex items-center gap-3 p-4 rounded-xl bg-oracle-card border border-oracle-border hover:border-pink/50 hover:bg-pink/5 transition-all text-left group"
                                    >
                                        <prompt.icon className={`w-5 h-5 ${prompt.color}`} />
                                        <span className="text-sm text-gray-300 group-hover:text-white transition-colors">
                                            {prompt.text}
                                        </span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    ) : (
                        // Chat Messages
                        <>
                            {messages.map((message, index) => (
                                <div
                                    key={index}
                                    className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                                >
                                    <div
                                        className={`max-w-[80%] rounded-2xl p-4 ${message.role === 'user'
                                            ? 'bg-gradient-to-br from-violet to-pink text-white rounded-br-sm'
                                            : 'bg-oracle-card border border-oracle-border rounded-bl-sm'
                                            }`}
                                    >
                                        {message.role === 'assistant' && (
                                            <div className="flex items-center gap-2 mb-2 pb-2 border-b border-oracle-border/50">
                                                <Brain className="w-4 h-4 text-pink" />
                                                <span className="text-xs font-medium text-pink">Oracle</span>
                                                {message.thinkingTime && (
                                                    <span className="flex items-center gap-1 text-xs text-gray-500 ml-auto">
                                                        <Clock className="w-3 h-3" />
                                                        {message.thinkingTime}s
                                                    </span>
                                                )}
                                            </div>
                                        )}
                                        <div className={`prose prose-sm max-w-none ${message.role === 'user' ? 'prose-invert' : 'prose-invert'}`}>
                                            {message.role === 'assistant' ? (
                                                <ReactMarkdown
                                                    components={{
                                                        // Custom styling for markdown elements
                                                        strong: ({ children }: { children?: ReactNode }) => (
                                                            <strong className="text-cyan font-semibold">{children}</strong>
                                                        ),
                                                        code: ({ children }: { children?: ReactNode }) => (
                                                            <code className="bg-violet/20 text-pink px-1.5 py-0.5 rounded text-sm font-mono">
                                                                {children}
                                                            </code>
                                                        ),
                                                        h1: ({ children }: { children?: ReactNode }) => (
                                                            <h1 className="text-xl font-bold text-white mt-4 mb-2">{children}</h1>
                                                        ),
                                                        h2: ({ children }: { children?: ReactNode }) => (
                                                            <h2 className="text-lg font-bold text-white mt-3 mb-2">{children}</h2>
                                                        ),
                                                        h3: ({ children }: { children?: ReactNode }) => (
                                                            <h3 className="text-base font-semibold text-white mt-2 mb-1">{children}</h3>
                                                        ),
                                                        ul: ({ children }: { children?: ReactNode }) => (
                                                            <ul className="list-disc list-inside space-y-1 text-gray-300">{children}</ul>
                                                        ),
                                                        ol: ({ children }: { children?: ReactNode }) => (
                                                            <ol className="list-decimal list-inside space-y-1 text-gray-300">{children}</ol>
                                                        ),
                                                        li: ({ children }: { children?: ReactNode }) => (
                                                            <li className="text-gray-300">{children}</li>
                                                        ),
                                                        p: ({ children }: { children?: ReactNode }) => (
                                                            <p className="text-gray-300 leading-relaxed mb-2">{children}</p>
                                                        ),
                                                        hr: () => (
                                                            <hr className="border-oracle-border my-4" />
                                                        ),
                                                    }}
                                                >
                                                    {message.content}
                                                </ReactMarkdown>
                                            ) : (
                                                <p className="text-white">{message.content}</p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}

                            {/* Loading indicator */}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-oracle-card border border-oracle-border rounded-2xl rounded-bl-sm p-4 max-w-[80%]">
                                        <div className="flex items-center gap-3">
                                            <div className="relative">
                                                <Brain className="w-6 h-6 text-pink animate-pulse" />
                                                <div className="absolute inset-0 animate-ping">
                                                    <Brain className="w-6 h-6 text-pink/30" />
                                                </div>
                                            </div>
                                            <div>
                                                <p className="text-sm text-pink font-medium">Oracle thinking...</p>
                                                <p className="text-xs text-gray-500">Detail analysis takes time</p>
                                            </div>
                                            <Loader2 className="w-5 h-5 text-pink animate-spin ml-2" />
                                        </div>
                                    </div>
                                </div>
                            )}

                            <div ref={messagesEndRef} />
                        </>
                    )}
                </div>

                {/* Input Area */}
                <div className="p-4 border-t border-oracle-border bg-oracle-dark/80 backdrop-blur-md">
                    <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
                        {/* Style Selector */}
                        <div className="flex justify-center mb-3">
                            <div className="bg-oracle-card border border-oracle-border p-1 rounded-lg flex gap-1">
                                <button
                                    type="button"
                                    onClick={() => setResponseStyle('concise')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${responseStyle === 'concise'
                                        ? 'bg-pink text-white shadow-lg shadow-pink/20'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    Concise
                                </button>
                                <button
                                    type="button"
                                    onClick={() => setResponseStyle('detailed')}
                                    className={`px-3 py-1 rounded-md text-xs font-medium transition-all ${responseStyle === 'detailed'
                                        ? 'bg-cyan text-black shadow-lg shadow-cyan/20'
                                        : 'text-gray-400 hover:text-white hover:bg-white/5'
                                        }`}
                                >
                                    Detailed
                                </button>
                            </div>
                        </div>

                        <div className="flex items-center gap-3 p-2 rounded-2xl bg-oracle-card border border-oracle-border focus-within:border-pink/50 transition-colors">
                            <MessageCircle className="w-5 h-5 text-gray-500 ml-2" />
                            <input
                                ref={inputRef}
                                type="text"
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                placeholder="Oracle'a bir soru sorun..."
                                className="flex-1 bg-transparent text-white placeholder-gray-500 outline-none text-sm py-2"
                                disabled={isLoading || isAvailable === false}
                            />
                            <button
                                type="submit"
                                disabled={!inputValue.trim() || isLoading || isAvailable === false}
                                className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-violet to-pink text-white disabled:opacity-50 disabled:cursor-not-allowed hover:shadow-lg hover:shadow-pink/20 transition-all"
                            >
                                {isLoading ? (
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                ) : (
                                    <Send className="w-5 h-5" />
                                )}
                            </button>
                        </div>
                        <p className="text-center text-xs text-gray-600 mt-2">
                            Oracle takes time to provide detailed and accurate answers. Complex queries may take a minute.
                        </p>
                    </form>
                </div>
            </div>
        </div>
    );
}
