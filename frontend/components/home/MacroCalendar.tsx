import { MacroEvent } from '@/lib/api';
import { CalendarDays, TrendingUp, AlertCircle } from 'lucide-react';

interface MacroCalendarProps {
    data: MacroEvent[];
    isLoading: boolean;
}

export default function MacroCalendar({ data, isLoading }: MacroCalendarProps) {
    // Helper to format date nicely "Mon, Feb 2"
    const formatDate = (dateStr: string) => {
        // Input: "02-02-2026"
        if (!dateStr) return "";
        try {
            const [m, d, y] = dateStr.split('-');
            const date = new Date(parseInt(y), parseInt(m) - 1, parseInt(d));
            return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
        } catch {
            return dateStr;
        }
    };

    // Helper to determine impact color
    const getImpactColor = (impact: string) => {
        switch (impact) {
            case 'High': return 'text-red-400';
            case 'Medium': return 'text-amber-400';
            default: return 'text-gray-400';
        }
    };

    // Group items by date for cleaner list
    // Or just list them chronologically. Let's just list them since the list is short (weekly).

    if (isLoading) {
        return (
            <div className="bg-oracle-card border border-oracle-border rounded-xl p-5 h-full shimmer">
                <div className="flex items-center gap-3 mb-4">
                    <CalendarDays className="w-5 h-5 text-gray-500" />
                    <h3 className="font-semibold text-gray-400">Macro Calendar</h3>
                </div>
                <div className="space-y-3">
                    {[...Array(5)].map((_, i) => (
                        <div key={i} className="h-10 bg-white/5 rounded mx-auto" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="bg-oracle-card border border-oracle-border rounded-xl flex flex-col h-full overflow-hidden">
            {/* Header */}
            <div className="p-4 border-b border-oracle-border/50 flex items-center justify-between bg-oracle-dark/50">
                <div className="flex items-center gap-2">
                    <CalendarDays className="w-5 h-5 text-blue-400" />
                    <h3 className="font-bold text-white tracking-wide">Macro Calendar (USA)</h3>
                </div>
                <span className="text-[10px] uppercase font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded">
                    High Impact
                </span>
            </div>

            {/* Content List */}
            <div className="overflow-y-auto flex-1 custom-scrollbar">
                {data.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-40 text-gray-500 gap-2">
                        <AlertCircle className="w-6 h-6 opacity-50" />
                        <span className="text-sm">No major events this week</span>
                    </div>
                ) : (
                    <table className="w-full text-left border-collapse">
                        <thead className="bg-white/5 text-gray-400 text-xs uppercase tracking-wider sticky top-0 backdrop-blur-sm">
                            <tr>
                                <th className="px-4 py-2 font-medium">Date</th>
                                <th className="px-4 py-2 font-medium">Event</th>
                                <th className="px-4 py-2 font-medium text-right">Fcst</th>
                                <th className="px-4 py-2 font-medium text-right">Prev</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5 text-sm">
                            {data.map((event, idx) => (
                                <tr key={idx} className="hover:bg-white/5 transition-colors group">
                                    <td className="px-4 py-3 whitespace-nowrap">
                                        <div className="flex flex-col">
                                            <span className="font-medium text-gray-300">{formatDate(event.date)}</span>
                                            <span className="text-[11px] text-gray-500 font-mono">{event.time}</span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3">
                                        <div className="flex items-center gap-2">
                                            <div className={`w-1.5 h-1.5 rounded-full ${event.impact === 'High' ? 'bg-red-500 animate-pulse' : 'bg-amber-500'}`} />
                                            <span className={`font-medium ${event.impact === 'High' ? 'text-white' : 'text-gray-300'}`}>
                                                {event.title}
                                            </span>
                                        </div>
                                    </td>
                                    <td className="px-4 py-3 text-right font-mono text-gray-400">{event.forecast || '-'}</td>
                                    <td className="px-4 py-3 text-right font-mono text-gray-500">{event.previous || '-'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            <div className="p-2 bg-oracle-dark/30 border-t border-oracle-border text-[10px] text-gray-500 text-center flex justify-center gap-4">
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-red-500"></span> High Impact</span>
                <span className="flex items-center gap-1"><span className="w-1.5 h-1.5 rounded-full bg-amber-500"></span> Medium Impact</span>
            </div>
        </div>
    );
}
