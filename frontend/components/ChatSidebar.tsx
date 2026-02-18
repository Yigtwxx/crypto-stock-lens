'use client';

import { useState, useEffect } from 'react';
import { MessageSquare, Plus, Trash2, Menu, X, MessageCircle } from 'lucide-react';
import { format, isToday, isYesterday, parseISO } from 'date-fns';
import { tr } from 'date-fns/locale';

interface ChatSession {
    id: string;
    title: string;
    created_at: string;
    updated_at: string;
}

interface ChatSidebarProps {
    sessions: ChatSession[];
    currentSessionId: string | null;
    onSelectSession: (sessionId: string) => void;
    onNewChat: () => void;
    onDeleteSession: (sessionId: string) => void;
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
}

export default function ChatSidebar({
    sessions,
    currentSessionId,
    onSelectSession,
    onNewChat,
    onDeleteSession,
    isOpen,
    setIsOpen
}: ChatSidebarProps) {
    const [groupedSessions, setGroupedSessions] = useState<{ [key: string]: ChatSession[] }>({});

    useEffect(() => {
        const groups: { [key: string]: ChatSession[] } = {
            'Bugün': [],
            'Dün': [],
            'Önceki 7 Gün': []
        };

        sessions.forEach(session => {
            const date = parseISO(session.updated_at);
            if (isToday(date)) {
                groups['Bugün'].push(session);
            } else if (isYesterday(date)) {
                groups['Dün'].push(session);
            } else {
                groups['Önceki 7 Gün'].push(session);
            }
        });

        setGroupedSessions(groups);
    }, [sessions]);

    return (
        <>
            {/* Mobile Overlay */}
            {isOpen && (
                <div
                    className="fixed inset-0 bg-black/50 z-40 md:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <div className={`
                fixed md:static inset-y-0 left-0 z-50
                w-72 bg-oracle-dark border-r border-oracle-border transform transition-transform duration-300 ease-in-out
                flex flex-col
                ${isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
            `}>
                {/* Header / New Chat */}
                <div className="p-4 border-b border-oracle-border">
                    <button
                        onClick={onNewChat}
                        className="w-full flex items-center gap-2 px-4 py-3 rounded-xl bg-oracle-card hover:bg-pink/10 border border-oracle-border hover:border-pink/50 transition-all group"
                    >
                        <Plus className="w-5 h-5 text-pink group-hover:scale-110 transition-transform" />
                        <span className="text-sm font-medium text-gray-200 group-hover:text-white">Yeni Sohbet</span>
                    </button>
                </div>

                {/* Session List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-6">
                    {Object.entries(groupedSessions).map(([group, groupSessions]) => (
                        groupSessions.length > 0 && (
                            <div key={group}>
                                <h3 className="text-xs font-semibold text-gray-500 mb-3 px-2 uppercase tracking-wider">
                                    {group}
                                </h3>
                                <div className="space-y-1">
                                    {groupSessions.map(session => (
                                        <div
                                            key={session.id}
                                            className={`
                                                group flex items-center gap-3 px-3 py-2.5 rounded-lg cursor-pointer transition-all
                                                ${currentSessionId === session.id
                                                    ? 'bg-pink/10 text-white shadow-sm shadow-pink/5'
                                                    : 'text-gray-400 hover:text-gray-200 hover:bg-oracle-card'
                                                }
                                            `}
                                            onClick={() => {
                                                onSelectSession(session.id);
                                                if (window.innerWidth < 768) setIsOpen(false);
                                            }}
                                        >
                                            <MessageSquare className={`w-4 h-4 ${currentSessionId === session.id ? 'text-pink' : 'text-gray-500 group-hover:text-gray-400'}`} />
                                            <span className="flex-1 text-sm truncate">{session.title}</span>

                                            {/* Delete Button (Visible on Hover/Active) */}
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    onDeleteSession(session.id);
                                                }}
                                                className={`
                                                    p-1 rounded bg-oracle-dark/50 hover:bg-red-500/20 text-gray-500 hover:text-red-400 transition-all opacity-0 group-hover:opacity-100
                                                    ${currentSessionId === session.id ? 'opacity-100' : ''}
                                                `}
                                                title="Sohbeti sil"
                                            >
                                                <Trash2 className="w-3.5 h-3.5" />
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )
                    ))}

                    {sessions.length === 0 && (
                        <div className="text-center py-10 px-4">
                            <div className="w-12 h-12 rounded-full bg-oracle-card flex items-center justify-center mx-auto mb-3">
                                <MessageCircle className="w-6 h-6 text-gray-600" />
                            </div>
                            <p className="text-sm text-gray-500">Henüz sohbet geçmişi yok.</p>
                            <p className="text-xs text-gray-600 mt-1">Sohbetleriniz 7 gün saklanır.</p>
                        </div>
                    )}
                </div>

                {/* Footer / User Info */}
                <div className="p-4 border-t border-oracle-border bg-oracle-darker">
                    <div className="text-xs text-center text-gray-600">
                        <p>Oracle AI &copy; 2024</p>
                    </div>
                </div>
            </div>
        </>
    );
}
