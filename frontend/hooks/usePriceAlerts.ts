'use client';

import { useEffect, useRef, useCallback } from 'react';
import { useStore } from '@/store/useStore';

const BINANCE_API = 'https://api.binance.com/api/v3/ticker/price';

export function usePriceAlerts() {
    const { priceAlerts, triggerAlert } = useStore();
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const notifiedRef = useRef<Set<string>>(new Set());

    // Request notification permission on mount
    useEffect(() => {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }, []);

    // Play alert sound
    const playAlertSound = useCallback(() => {
        try {
            // Create a simple beep sound using Web Audio API
            const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();

            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);

            oscillator.frequency.value = 880; // A5 note
            oscillator.type = 'sine';

            gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
            gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + 0.5);

            // Play a second beep
            setTimeout(() => {
                const osc2 = audioContext.createOscillator();
                const gain2 = audioContext.createGain();
                osc2.connect(gain2);
                gain2.connect(audioContext.destination);
                osc2.frequency.value = 1100;
                osc2.type = 'sine';
                gain2.gain.setValueAtTime(0.3, audioContext.currentTime);
                gain2.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
                osc2.start(audioContext.currentTime);
                osc2.stop(audioContext.currentTime + 0.5);
            }, 200);
        } catch (e) {
            console.log('Could not play alert sound');
        }
    }, []);

    const showNotification = useCallback((alert: typeof priceAlerts[0], currentPrice: number) => {
        // Play sound first
        playAlertSound();

        if ('Notification' in window && Notification.permission === 'granted') {
            const title = `🔔 Price Alert: ${alert.displaySymbol}`;
            const body = `${alert.displaySymbol} is now $${currentPrice.toLocaleString()} (${alert.condition} $${alert.targetPrice.toLocaleString()})`;

            new Notification(title, {
                body,
                icon: '/favicon.ico',
                tag: alert.id,
                requireInteraction: true,
            });
        }
    }, [playAlertSound]);

    const checkPrices = useCallback(async () => {
        const activeAlerts = priceAlerts.filter(a => a.isActive && !a.isTriggered);

        if (activeAlerts.length === 0) return;

        // Group alerts by symbol to minimize API calls
        const symbolsToCheck = Array.from(new Set(activeAlerts.map(a => a.symbol)));

        for (const symbol of symbolsToCheck) {
            try {
                // Extract clean symbol (e.g., BINANCE:BTCUSDT -> BTCUSDT)
                const cleanSymbol = symbol.includes(':') ? symbol.split(':')[1] : symbol;

                const response = await fetch(`${BINANCE_API}?symbol=${cleanSymbol}`);
                if (!response.ok) continue;

                const data = await response.json();
                const currentPrice = parseFloat(data.price);

                // Check all alerts for this symbol
                const symbolAlerts = activeAlerts.filter(a => a.symbol === symbol);

                for (const alert of symbolAlerts) {
                    // Skip if already notified in this session
                    if (notifiedRef.current.has(alert.id)) continue;

                    const conditionMet = alert.condition === 'above'
                        ? currentPrice >= alert.targetPrice
                        : currentPrice <= alert.targetPrice;

                    if (conditionMet) {
                        showNotification(alert, currentPrice);
                        triggerAlert(alert.id);
                        notifiedRef.current.add(alert.id);

                        console.log(`🔔 Alert triggered: ${alert.displaySymbol} ${alert.condition} $${alert.targetPrice}`);
                    }
                }
            } catch (error) {
                console.error(`Failed to check price for ${symbol}:`, error);
            }
        }
    }, [priceAlerts, triggerAlert, showNotification]);

    // Start/stop price checking interval
    useEffect(() => {
        const activeCount = priceAlerts.filter(a => a.isActive).length;

        if (activeCount > 0) {
            // Check immediately, then every 10 seconds
            checkPrices();
            intervalRef.current = setInterval(checkPrices, 10000);
            console.log(`📊 Price monitoring started: ${activeCount} active alerts`);
        }

        return () => {
            if (intervalRef.current) {
                clearInterval(intervalRef.current);
                intervalRef.current = null;
            }
        };
    }, [priceAlerts, checkPrices]);

    return {
        activeAlerts: priceAlerts.filter(a => a.isActive),
        triggeredAlerts: priceAlerts.filter(a => a.isTriggered),
    };
}
