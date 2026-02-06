'use client';

import { OnChainData } from '@/lib/api';
import { Activity, ArrowDownRight, ArrowUpRight, Wallet, Zap, Layers, ArrowRightLeft } from 'lucide-react';

interface OnChainStatsProps {
    data: OnChainData | null;
    isLoading: boolean;
}

export default function OnChainStats({ data, isLoading }: OnChainStatsProps) {
    if (isLoading || !data) {
        return (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
                {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-32 bg-oracle-card/50 rounded-xl border border-oracle-border/50"></div>
                ))}
            </div>
        );
    }

    const { active_addresses, network_load, exchange_flows } = data;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">

            {/* BTC Active Addresses */}
            <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border relative overflow-hidden group hover:border-orange-500/30 transition-colors">
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Wallet className="w-16 h-16 text-orange-500" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-orange-500/20 flex items-center justify-center">
                        <Activity className="w-4 h-4 text-orange-400" />
                    </div>
                    <span className="text-sm text-gray-400">BTC Active Addresses</span>
                </div>
                <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">
                        {active_addresses.btc.toLocaleString()}
                    </span>
                    <span className={`text-xs font-medium mb-1 flex items-center ${active_addresses.btc_change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {active_addresses.btc_change_24h > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {Math.abs(active_addresses.btc_change_24h)}%
                    </span>
                </div>
                <div className="mt-2 text-xs text-gray-500">Daily Active Users</div>
            </div>

            {/* ETH Active Addresses */}
            <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border relative overflow-hidden group hover:border-blue-500/30 transition-colors">
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Layers className="w-16 h-16 text-blue-500" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                        <Activity className="w-4 h-4 text-blue-400" />
                    </div>
                    <span className="text-sm text-gray-400">ETH Active Addresses</span>
                </div>
                <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">
                        {active_addresses.eth.toLocaleString()}
                    </span>
                    <span className={`text-xs font-medium mb-1 flex items-center ${active_addresses.eth_change_24h >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {active_addresses.eth_change_24h > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                        {Math.abs(active_addresses.eth_change_24h)}%
                    </span>
                </div>
                <div className="mt-2 text-xs text-gray-500">Daily Active Users</div>
            </div>

            {/* Network Load (Gas) */}
            <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border relative overflow-hidden group hover:border-purple-500/30 transition-colors">
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <Zap className="w-16 h-16 text-purple-500" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                        <Zap className="w-4 h-4 text-purple-400" />
                    </div>
                    <span className="text-sm text-gray-400">Network Gas (ETH)</span>
                </div>
                <div className="flex items-end gap-2">
                    <span className="text-2xl font-bold text-white">
                        {network_load.eth_gas_gwei} <span className="text-sm font-normal text-gray-500">Gwei</span>
                    </span>
                </div>
                <div className="mt-2 text-xs text-gray-500 flex items-center justify-between">
                    <span>Low cost</span>
                    <div className="w-16 h-1.5 bg-gray-700 rounded-full overflow-hidden">
                        <div
                            className="h-full bg-gradient-to-r from-green-400 to-yellow-400"
                            style={{ width: `${Math.min(network_load.eth_gas_gwei * 2, 100)}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Exchange Flows */}
            <div className="p-4 rounded-xl bg-oracle-card border border-oracle-border relative overflow-hidden group hover:border-green-500/30 transition-colors">
                <div className="absolute top-0 right-0 p-3 opacity-10 group-hover:opacity-20 transition-opacity">
                    <ArrowRightLeft className="w-16 h-16 text-green-500" />
                </div>
                <div className="flex items-center gap-2 mb-2">
                    <div className="w-8 h-8 rounded-lg bg-green-500/20 flex items-center justify-center">
                        <ArrowRightLeft className="w-4 h-4 text-green-400" />
                    </div>
                    <span className="text-sm text-gray-400">BTC Exchange Flow</span>
                </div>
                <div className="flex items-end gap-2">
                    <span className={`text-xl font-bold ${exchange_flows.btc_net_flow_usd < 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {exchange_flows.btc_net_flow_usd < 0 ? '-' : '+'}$
                        {Math.abs(exchange_flows.btc_net_flow_usd / 1000000).toFixed(1)}M
                    </span>
                </div>
                <div className="mt-2 text-xs text-gray-500">
                    {exchange_flows.btc_net_flow_usd < 0 ? 'Net Outflow (Bullish)' : 'Net Inflow (Bearish)'}
                </div>
            </div>

        </div>
    );
}
