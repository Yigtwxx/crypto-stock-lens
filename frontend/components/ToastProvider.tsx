'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { setToastCallback } from '@/lib/queryClient';
import { AlertTriangle, X, CheckCircle } from 'lucide-react';

interface Toast {
    id: number;
    message: string;
    type: 'error' | 'success';
}

let idCounter = 0;

export default function ToastProvider() {
    const [toasts, setToasts] = useState<Toast[]>([]);
    const initialized = useRef(false);

    const addToast = useCallback((message: string, type: 'error' | 'success' = 'error') => {
        const id = ++idCounter;
        setToasts(prev => {
            // Prevent duplicate messages
            if (prev.some(t => t.message === message)) return prev;
            // Limit to 3 toasts
            const updated = [...prev, { id, message, type }];
            return updated.slice(-3);
        });

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            setToasts(prev => prev.filter(t => t.id !== id));
        }, 5000);
    }, []);

    const removeToast = useCallback((id: number) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    useEffect(() => {
        if (!initialized.current) {
            setToastCallback((msg) => addToast(msg, 'error'));
            initialized.current = true;
        }
    }, [addToast]);

    if (toasts.length === 0) return null;

    return (
        <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
            {toasts.map(toast => (
                <div
                    key={toast.id}
                    className={`flex items-start gap-3 px-4 py-3 rounded-xl border shadow-2xl backdrop-blur-md animate-slide-in-right ${toast.type === 'error'
                            ? 'bg-red-950/80 border-red-500/30 text-red-200'
                            : 'bg-green-950/80 border-green-500/30 text-green-200'
                        }`}
                >
                    {toast.type === 'error' ? (
                        <AlertTriangle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-400" />
                    ) : (
                        <CheckCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-green-400" />
                    )}
                    <p className="text-sm flex-1">{toast.message}</p>
                    <button
                        onClick={() => removeToast(toast.id)}
                        className="flex-shrink-0 p-0.5 hover:bg-white/10 rounded transition-colors"
                    >
                        <X className="w-3.5 h-3.5" />
                    </button>
                </div>
            ))}
        </div>
    );
}
