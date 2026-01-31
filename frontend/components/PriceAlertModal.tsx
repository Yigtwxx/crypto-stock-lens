'use client';

import { useState } from 'react';
import { useStore } from '@/store/useStore';
import { X, Bell, Trash2, TrendingUp, TrendingDown, Plus } from 'lucide-react';

export default function PriceAlertModal() {
    const {
        chartSymbol,
        isAlertModalOpen,
        toggleAlertModal,
        priceAlerts,
        addAlert,
        removeAlert
    } = useStore();

    const [targetPrice, setTargetPrice] = useState('');
    const [condition, setCondition] = useState<'above' | 'below'>('above');

    const displaySymbol = chartSymbol.includes(':')
        ? chartSymbol.split(':')[1]
        : chartSymbol;

    const handleAddAlert = () => {
        const price = parseFloat(targetPrice);
        if (isNaN(price) || price <= 0) return;

        addAlert({
            symbol: chartSymbol,
            displaySymbol,
            targetPrice: price,
            condition,
        });

        setTargetPrice('');

        // Request notification permission if not granted
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    };

    if (!isAlertModalOpen) return null;

    // Alerts for current symbol
    const currentSymbolAlerts = priceAlerts.filter(a => a.symbol === chartSymbol);
    // Alerts for other symbols
    const otherAlerts = priceAlerts.filter(a => a.symbol !== chartSymbol);
    const activeAlerts = priceAlerts.filter(a => a.isActive);

    const AlertItem = ({ alert }: { alert: typeof priceAlerts[0] }) => (
        <div
            className={`flex items-center justify-between p-3 rounded-lg border ${alert.isTriggered
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-oracle-card border-oracle-border'
                }`}
        >
            <div className="flex items-center gap-3">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${alert.condition === 'above' ? 'bg-green-500/20' : 'bg-red-500/20'
                    }`}>
                    {alert.condition === 'above'
                        ? <TrendingUp className="w-4 h-4 text-green-400" />
                        : <TrendingDown className="w-4 h-4 text-red-400" />
                    }
                </div>
                <div>
                    <p className="text-sm font-medium text-white">
                        {alert.displaySymbol} <span className="text-gray-500">→</span> ${alert.targetPrice.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">
                        {alert.isTriggered ? '✓ Triggered' : `${alert.condition === 'above' ? 'Above' : 'Below'} target`}
                    </p>
                </div>
            </div>
            <button
                onClick={() => removeAlert(alert.id)}
                className="p-2 rounded-lg hover:bg-red-500/20 transition-colors group"
            >
                <Trash2 className="w-4 h-4 text-gray-500 group-hover:text-red-400" />
            </button>
        </div>
    );

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-oracle-dark border border-oracle-border rounded-2xl w-full max-w-md shadow-2xl">
                {/* Header */}
                <div className="p-4 border-b border-oracle-border flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500/20 to-orange-500/20 border border-amber-500/30 flex items-center justify-center">
                            <Bell className="w-5 h-5 text-amber-400" />
                        </div>
                        <div>
                            <h2 className="font-semibold text-white">Price Alerts</h2>
                            <p className="text-xs text-gray-500">Add alert for {displaySymbol}</p>
                        </div>
                    </div>
                    <button
                        onClick={() => toggleAlertModal(false)}
                        className="p-2 rounded-lg hover:bg-white/5 transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-400" />
                    </button>
                </div>

                {/* Add Alert Form */}
                <div className="p-4 border-b border-oracle-border">
                    <div className="flex gap-2">
                        {/* Condition Toggle */}
                        <div className="flex rounded-lg border border-oracle-border overflow-hidden">
                            <button
                                onClick={() => setCondition('above')}
                                className={`px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1 ${condition === 'above'
                                        ? 'bg-green-500/20 text-green-400'
                                        : 'text-gray-400 hover:bg-white/5'
                                    }`}
                            >
                                <TrendingUp className="w-4 h-4" />
                                Above
                            </button>
                            <button
                                onClick={() => setCondition('below')}
                                className={`px-3 py-2 text-sm font-medium transition-colors flex items-center gap-1 ${condition === 'below'
                                        ? 'bg-red-500/20 text-red-400'
                                        : 'text-gray-400 hover:bg-white/5'
                                    }`}
                            >
                                <TrendingDown className="w-4 h-4" />
                                Below
                            </button>
                        </div>

                        {/* Price Input */}
                        <div className="flex-1 relative">
                            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500">$</span>
                            <input
                                type="number"
                                value={targetPrice}
                                onChange={(e) => setTargetPrice(e.target.value)}
                                placeholder="Target price"
                                className="w-full pl-7 pr-3 py-2 bg-oracle-card border border-oracle-border rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-amber-500/50"
                            />
                        </div>

                        {/* Add Button */}
                        <button
                            onClick={handleAddAlert}
                            disabled={!targetPrice || parseFloat(targetPrice) <= 0}
                            className="px-4 py-2 bg-gradient-to-r from-amber-500 to-orange-500 text-white font-medium rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
                        >
                            <Plus className="w-4 h-4" />
                            Add
                        </button>
                    </div>
                </div>

                {/* All Alerts List */}
                <div className="p-4 max-h-80 overflow-y-auto">
                    {priceAlerts.length === 0 ? (
                        <div className="text-center py-8">
                            <Bell className="w-10 h-10 text-gray-600 mx-auto mb-3" />
                            <p className="text-gray-500 text-sm">No alerts yet</p>
                            <p className="text-gray-600 text-xs mt-1">Add an alert above</p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {/* Current Symbol Alerts */}
                            {currentSymbolAlerts.length > 0 && (
                                <div>
                                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">
                                        📍 {displaySymbol}
                                    </p>
                                    <div className="space-y-2">
                                        {currentSymbolAlerts.map((alert) => (
                                            <AlertItem key={alert.id} alert={alert} />
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Other Alerts */}
                            {otherAlerts.length > 0 && (
                                <div>
                                    <p className="text-xs text-gray-500 uppercase tracking-wider mb-2 mt-4">
                                        🔔 Other Alerts
                                    </p>
                                    <div className="space-y-2">
                                        {otherAlerts.map((alert) => (
                                            <AlertItem key={alert.id} alert={alert} />
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                {activeAlerts.length > 0 && (
                    <div className="p-4 border-t border-oracle-border">
                        <p className="text-xs text-gray-500 text-center">
                            🔔 {activeAlerts.length} active alert{activeAlerts.length > 1 ? 's' : ''} • Checking every 10 seconds • 🔊 Sound enabled
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
