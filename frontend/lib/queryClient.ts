'use client';

import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

let toastCallback: ((message: string) => void) | null = null;

export function setToastCallback(cb: (message: string) => void) {
    toastCallback = cb;
}

function handleGlobalError(error: unknown) {
    const message = error instanceof Error ? error.message : 'Bir hata oluştu';
    console.error('[QueryClient Error]', message);
    toastCallback?.(`Bağlantı hatası — ${message}`);
}

export const queryClient = new QueryClient({
    queryCache: new QueryCache({
        onError: handleGlobalError,
    }),
    mutationCache: new MutationCache({
        onError: handleGlobalError,
    }),
    defaultOptions: {
        queries: {
            retry: 3,
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 10000),
            staleTime: 30 * 1000, // 30 seconds default
            gcTime: 5 * 60 * 1000, // 5 minutes garbage collection
            refetchOnWindowFocus: true,
            refetchOnReconnect: true,
        },
        mutations: {
            retry: 1,
        },
    },
});
