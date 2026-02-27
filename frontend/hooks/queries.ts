'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
    fetchOnChainData,
    fetchFundingRates,
    fetchLiquidations,
    fetchMacroCalendar,
    fetchMarketOverview,
    fetchFearGreedIndex,
    fetchNasdaqOverview,
    fetchNews,
    fetchWatchlists,
    createWatchlist,
    deleteWatchlist,
} from '@/lib/api';

// ==========================================
// Query Keys — centralized for consistency
// ==========================================
export const queryKeys = {
    onChainData: ['onChainData'] as const,
    fundingRates: ['fundingRates'] as const,
    liquidations: ['liquidations'] as const,
    macroCalendar: ['macroCalendar'] as const,
    marketOverview: ['marketOverview'] as const,
    fearGreedIndex: ['fearGreedIndex'] as const,
    nasdaqOverview: ['nasdaqOverview'] as const,
    news: (assetType?: string) => ['news', assetType] as const,
    watchlists: ['watchlists'] as const,
};

// ==========================================
// HOME PAGE HOOKS
// ==========================================

export function useOnChainData() {
    return useQuery({
        queryKey: queryKeys.onChainData,
        queryFn: fetchOnChainData,
        staleTime: 30 * 1000,       // 30s
        refetchInterval: 60 * 1000, // 60s auto-refresh
    });
}

export function useFundingRates() {
    return useQuery({
        queryKey: queryKeys.fundingRates,
        queryFn: fetchFundingRates,
        staleTime: 30 * 1000,
        refetchInterval: 60 * 1000,
    });
}

export function useLiquidations() {
    return useQuery({
        queryKey: queryKeys.liquidations,
        queryFn: fetchLiquidations,
        staleTime: 15 * 1000,       // 15s — liquidations change fast
        refetchInterval: 30 * 1000,
    });
}

export function useMacroCalendar() {
    return useQuery({
        queryKey: queryKeys.macroCalendar,
        queryFn: fetchMacroCalendar,
        staleTime: 5 * 60 * 1000,   // 5 min — macroeconomic events rarely change
    });
}

// ==========================================
// OVERVIEW PAGE HOOKS
// ==========================================

export function useMarketOverview(enabled: boolean = true) {
    return useQuery({
        queryKey: queryKeys.marketOverview,
        queryFn: fetchMarketOverview,
        staleTime: 30 * 1000,
        refetchInterval: 120 * 1000,
        enabled,
    });
}

export function useFearGreedIndex(enabled: boolean = true) {
    return useQuery({
        queryKey: queryKeys.fearGreedIndex,
        queryFn: fetchFearGreedIndex,
        staleTime: 2 * 60 * 1000,   // 2 min
        enabled,
    });
}

export function useNasdaqOverview(enabled: boolean = true) {
    return useQuery({
        queryKey: queryKeys.nasdaqOverview,
        queryFn: fetchNasdaqOverview,
        staleTime: 30 * 1000,
        refetchInterval: 120 * 1000,
        enabled,
    });
}

// ==========================================
// NEWS HOOKS
// ==========================================

export function useNews(assetType?: string) {
    return useQuery({
        queryKey: queryKeys.news(assetType),
        queryFn: () => fetchNews(assetType),
        staleTime: 30 * 1000,
        refetchInterval: 30 * 1000,
    });
}

// ==========================================
// WATCHLIST HOOKS
// ==========================================

export function useWatchlists() {
    return useQuery({
        queryKey: queryKeys.watchlists,
        queryFn: fetchWatchlists,
        staleTime: 30 * 1000,
        refetchInterval: 30 * 1000,
    });
}

export function useCreateWatchlist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: ({ name, items }: { name: string; items: { symbol: string; type: 'STOCK' | 'CRYPTO' }[] }) =>
            createWatchlist(name, items),
        onSuccess: (data) => {
            // Update cache directly with the returned data
            queryClient.setQueryData(queryKeys.watchlists, data);
        },
    });
}

export function useDeleteWatchlist() {
    const queryClient = useQueryClient();
    return useMutation({
        mutationFn: (id: string) => deleteWatchlist(id),
        onMutate: async (deletedId) => {
            // Optimistic update — remove from cache immediately
            await queryClient.cancelQueries({ queryKey: queryKeys.watchlists });
            const previous = queryClient.getQueryData(queryKeys.watchlists);
            queryClient.setQueryData(queryKeys.watchlists, (old: unknown) => {
                if (!Array.isArray(old)) return old;
                return old.filter((w: { id: string }) => w.id !== deletedId);
            });
            return { previous };
        },
        onError: (_err, _id, context) => {
            // Rollback on error
            if (context?.previous) {
                queryClient.setQueryData(queryKeys.watchlists, context.previous);
            }
        },
        onSettled: () => {
            queryClient.invalidateQueries({ queryKey: queryKeys.watchlists });
        },
    });
}
