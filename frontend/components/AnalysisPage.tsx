'use client';

import React, { useState, useEffect } from 'react';
import { RefreshCw, FileText, Plus, Trash2, Calendar, BrainCircuit, PenLine } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

type TimeFrame = 'daily' | 'weekly' | 'monthly';

interface Note {
    id: string;
    title: string;
    content: string;
    date: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function AnalysisPage() {
    const [timeframe, setTimeframe] = useState<TimeFrame>('daily');
    const [report, setReport] = useState<string>('');
    const [reportTimestamp, setReportTimestamp] = useState<string | null>(null);
    const [loadingReport, setLoadingReport] = useState(false);

    const [notes, setNotes] = useState<Note[]>([]);
    const [noteTitle, setNoteTitle] = useState('');
    const [noteContent, setNoteContent] = useState('');
    const [isCreatingNote, setIsCreatingNote] = useState(false);
    const [loadingNotes, setLoadingNotes] = useState(false);

    // Initial Load
    useEffect(() => {
        fetchReport(timeframe);
        fetchNotes();
    }, []);

    // Fetch report when timeframe changes
    useEffect(() => {
        fetchReport(timeframe);
    }, [timeframe]);

    const fetchReport = async (tf: TimeFrame) => {
        try {
            setLoadingReport(true);
            const res = await fetch(`${API_BASE}/api/analysis/report/${tf}`);
            if (res.ok) {
                const data = await res.json();
                setReport(data.content);
                setReportTimestamp(data.timestamp);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingReport(false);
        }
    };

    const regenerateReport = async () => {
        try {
            setLoadingReport(true);
            const res = await fetch(`${API_BASE}/api/analysis/generate/${timeframe}`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                setReport(data.content);
                setReportTimestamp(data.timestamp);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingReport(false);
        }
    };

    const fetchNotes = async () => {
        try {
            setLoadingNotes(true);
            const res = await fetch(`${API_BASE}/api/analysis/notes`);
            if (res.ok) {
                const data = await res.json();
                setNotes(data);
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoadingNotes(false);
        }
    };

    const createNote = async () => {
        if (!noteTitle.trim() || !noteContent.trim()) return;
        try {
            const res = await fetch(`${API_BASE}/api/analysis/notes`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: noteTitle, content: noteContent })
            });
            if (res.ok) {
                const updatedNotes = await res.json();
                setNotes(updatedNotes);
                setNoteTitle('');
                setNoteContent('');
                setIsCreatingNote(false);
            }
        } catch (error) {
            console.error(error);
        }
    };

    const deleteNote = async (id: string) => {
        if (!confirm("Delete this note?")) return;
        try {
            const res = await fetch(`${API_BASE}/api/analysis/notes/${id}`, { method: 'DELETE' });
            if (res.ok) {
                const updatedNotes = await res.json();
                setNotes(updatedNotes);
            }
        } catch (error) {
            console.error(error);
        }
    };

    return (
        <div className="h-full grid grid-cols-1 lg:grid-cols-[65%_35%] gap-0 bg-[#0b0b15] overflow-hidden">

            {/* LEFT PANE: ANALYSIS REPORT */}
            <div className="flex flex-col border-r border-oracle-border overflow-hidden p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg">
                            <BrainCircuit className="w-5 h-5 text-white" />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Market Intelligence</h2>
                            <p className="text-xs text-gray-400">AI-generated deep dive analysis</p>
                        </div>
                    </div>

                    <div className="flex bg-black/30 p-1 rounded-lg border border-oracle-border">
                        {(['daily', 'weekly', 'monthly'] as TimeFrame[]).map(tf => (
                            <button
                                key={tf}
                                onClick={() => setTimeframe(tf)}
                                className={`px-4 py-1.5 text-xs font-medium rounded-md capitalize transition-all ${timeframe === tf ? 'bg-purple-500 text-white shadow-lg shadow-purple-500/20' : 'text-gray-400 hover:text-white'
                                    }`}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                </div>

                <div className="flex-1 bg-oracle-card border border-oracle-border rounded-xl p-6 overflow-y-auto custom-scrollbar relative">
                    {loadingReport ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-oracle-card/90 z-10">
                            <RefreshCw className="w-8 h-8 text-purple-500 animate-spin mb-2" />
                            <p className="text-sm text-gray-400 animate-pulse">Analyzing market data...</p>
                        </div>
                    ) : (
                        <>
                            <div className="flex items-center justify-between border-b border-oracle-border/50 pb-4 mb-4">
                                <div className="flex items-center gap-2 text-xs text-gray-500">
                                    <Calendar className="w-3.5 h-3.5" />
                                    <span>Generated: {reportTimestamp ? new Date(reportTimestamp).toLocaleString() : 'Never'}</span>
                                </div>
                                <button
                                    onClick={regenerateReport}
                                    className="flex items-center gap-2 px-3 py-1.5 bg-purple-500/10 hover:bg-purple-500/20 text-purple-400 text-xs rounded-lg transition-colors border border-purple-500/20"
                                >
                                    <RefreshCw className="w-3.5 h-3.5" />
                                    Regenerate Analysis
                                </button>
                            </div>

                            <div className="prose prose-invert prose-sm max-w-none">
                                <ReactMarkdown>
                                    {report || "*No report generated yet. Click 'Regenerate' to start.*"}
                                </ReactMarkdown>
                            </div>
                        </>
                    )}
                </div>
            </div>

            {/* RIGHT PANE: USER NOTES */}
            <div className="flex flex-col overflow-hidden bg-oracle-dark/30 p-6">
                <div className="flex items-center justify-between mb-6">
                    <div className="flex items-center gap-2">
                        <PenLine className="w-5 h-5 text-teal" />
                        <h2 className="text-lg font-bold text-white">My Notes</h2>
                    </div>
                    <button
                        onClick={() => setIsCreatingNote(!isCreatingNote)}
                        className={`p-2 rounded-lg transition-all ${isCreatingNote ? 'bg-red-500/20 text-red-400 rotate-45' : 'bg-teal/10 text-teal hover:bg-teal/20'}`}
                    >
                        <Plus className="w-5 h-5" />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
                    {isCreatingNote && (
                        <div className="bg-oracle-card border border-teal/30 rounded-xl p-4 shadow-lg shadow-teal/5 animate-in slide-in-from-top-4 fade-in">
                            <input
                                value={noteTitle}
                                onChange={(e) => setNoteTitle(e.target.value)}
                                placeholder="Note Title..."
                                className="w-full bg-transparent border-none text-white font-bold placeholder-gray-600 focus:ring-0 mb-2"
                                autoFocus
                            />
                            <textarea
                                value={noteContent}
                                onChange={(e) => setNoteContent(e.target.value)}
                                placeholder="Write your thoughts here..."
                                className="w-full bg-black/20 rounded-lg p-3 text-sm text-gray-300 min-h-[100px] border-none focus:ring-1 focus:ring-teal/50 mb-3 resize-none"
                            />
                            <div className="flex justify-end gap-2">
                                <button
                                    onClick={() => setIsCreatingNote(false)}
                                    className="px-3 py-1.5 text-xs text-gray-400 hover:text-white"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createNote}
                                    disabled={!noteTitle || !noteContent}
                                    className="px-3 py-1.5 bg-teal text-black text-xs font-bold rounded-lg hover:bg-teal/90 disabled:opacity-50"
                                >
                                    Save Note
                                </button>
                            </div>
                        </div>
                    )}

                    {loadingNotes ? (
                        <div className="text-center py-10">
                            <RefreshCw className="w-5 h-5 text-gray-600 animate-spin mx-auto" />
                        </div>
                    ) : notes.length === 0 && !isCreatingNote ? (
                        <div className="text-center py-10 border border-dashed border-gray-800 rounded-xl">
                            <FileText className="w-8 h-8 text-gray-700 mx-auto mb-2" />
                            <p className="text-gray-500 text-sm">No notes yet.</p>
                        </div>
                    ) : (
                        notes.map(note => (
                            <div key={note.id} className="bg-oracle-card border border-oracle-border rounded-xl p-4 group hover:border-gray-600 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <h3 className="font-semibold text-white truncate pr-4">{note.title}</h3>
                                    <button
                                        onClick={() => deleteNote(note.id)}
                                        className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-red-400 transition-opacity"
                                    >
                                        <Trash2 className="w-3.5 h-3.5" />
                                    </button>
                                </div>
                                <p className="text-sm text-gray-400 line-clamp-4 whitespace-pre-wrap">{note.content}</p>
                                <div className="mt-3 pt-3 border-t border-white/5 flex justify-end">
                                    <span className="text-[10px] text-gray-600">
                                        {new Date(note.date).toLocaleDateString()}
                                    </span>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
