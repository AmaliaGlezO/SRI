import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { Brain, TrendingUp, BarChart3, Clock, Zap, Globe, Target, X } from 'lucide-react'

export function StatsTooltip({ globalStats, sessionStats, userProfile }) {
    const [showModal, setShowModal] = useState(false)
    const [dashboard, setDashboard] = useState(null)
    const [recentQueries, setRecentQueries] = useState([])

    useEffect(() => {
        if (showModal) {
            fetch('api/query/stats/dashboard')
                .then(r => r.json())
                .then(d => setDashboard(d))
                .catch(() => { })

            fetch('/query/stats/recent?n=15')
                .then(r => r.json())
                .then(d => setRecentQueries(d))
                .catch(() => { })
        }
    }, [showModal])

    return (
        <>
            <button
                onClick={() => setShowModal(true)}
                className="p-2 rounded-lg bg-teal-500/10 text-teal-400 hover:bg-teal-500/20 hover:scale-105 transition-all outline-none"
                title="Abrir Dashboard de Estadísticas"
            >
                <div className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5" />
                    <span className="text-sm font-bold tracking-wide">DASHBOARD</span>
                </div>
            </button>

            {showModal && typeof document !== 'undefined' && createPortal(
                <div className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-md animate-in fade-in duration-300">
                    <div className="relative w-full max-w-5xl max-h-[90vh] overflow-y-auto rounded-3xl border border-white/10 bg-[#0f111a] shadow-2xl p-6 sm:p-8 custom-scrollbar">
                        <button
                            onClick={() => setShowModal(false)}
                            className="absolute right-6 top-6 p-2 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors"
                        >
                            <X className="h-5 w-5" />
                        </button>

                        <div className="flex items-center gap-3 mb-8">
                            <div className="p-3 bg-indigo-500/20 rounded-xl text-indigo-400">
                                <BarChart3 className="h-6 w-6" />
                            </div>
                            <div>
                                <h2 className="text-2xl font-black text-white">System Dashboard</h2>
                                <p className="text-sm text-slate-400">Métricas y rendimiento de RAG en tiempo real</p>
                            </div>
                        </div>

                        {!dashboard ? (
                            <div className="flex items-center justify-center h-64">
                                <span className="text-slate-500 animate-pulse">Cargando métricas...</span>
                            </div>
                        ) : (
                            <div className="space-y-6">
                                {/* Global KPI Cards */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                                            <Brain className="h-4 w-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Total Queries</span>
                                        </div>
                                        <div className="text-3xl font-black text-white">{dashboard.global.total_queries}</div>
                                    </div>
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                                            <Target className="h-4 w-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Avg Score</span>
                                        </div>
                                        <div className="text-3xl font-black text-purple-400">
                                            {dashboard.global.avg_top_score.toFixed(2)}
                                        </div>
                                    </div>
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                                            <Clock className="h-4 w-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Avg Inference</span>
                                        </div>
                                        <div className="text-3xl font-black text-emerald-400">
                                            {dashboard.global.avg_inference_time.toFixed(2)}s
                                        </div>
                                    </div>
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                                            <Globe className="h-4 w-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Web Fallback</span>
                                        </div>
                                        <div className="text-3xl font-black text-orange-400">
                                            {dashboard.global.internet_search_rate}%
                                        </div>
                                    </div>
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-5 hover:bg-white/10 transition-colors">
                                        <div className="flex items-center gap-2 text-slate-400 mb-3">
                                            <Zap className="h-4 w-4" />
                                            <span className="text-xs font-semibold uppercase tracking-wider">Avg RAG Time</span>
                                        </div>
                                        <div className="text-3xl font-black text-teal-400">
                                            {dashboard.global.avg_rag_time.toFixed(2)}s
                                        </div>
                                    </div>
                                </div>

                                {/* Graph Area */}
                                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                                    {/* Current Query Stats */}
                                    {recentQueries.length > 0 && (
                                        <div className="lg:col-span-2 bg-indigo-500/10 border border-indigo-500/20 rounded-2xl p-6">
                                            <div className="flex items-center gap-2 text-white mb-4">
                                                <Zap className="h-5 w-5 text-indigo-400" />
                                                <span className="font-semibold">Última Consulta</span>
                                                <span className="text-sm text-slate-400 ml-auto truncate max-w-md">"{recentQueries[0].query}"</span>
                                            </div>
                                            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                                                <div className="bg-black/20 p-4 rounded-xl text-center">
                                                    <div className="text-xs text-slate-400">Tokens Input</div>
                                                    <div className="text-lg font-bold text-blue-400">{(recentQueries[0].token_in || 0).toLocaleString()}</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl text-center">
                                                    <div className="text-xs text-slate-400">Tokens Output</div>
                                                    <div className="text-lg font-bold text-emerald-400">{(recentQueries[0].token_out || 0).toLocaleString()}</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl text-center">
                                                    <div className="text-xs text-slate-400">RAG Time</div>
                                                    <div className="text-lg font-bold text-teal-400">{(recentQueries[0].rag_time || 0).toFixed(2)}s</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl text-center">
                                                    <div className="text-xs text-slate-400">Inferencia</div>
                                                    <div className="text-lg font-bold text-indigo-400">{(recentQueries[0].inference_time || 0).toFixed(2)}s</div>
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* Inference Time Bar Chart */}
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                                        <div className="flex items-center justify-between mb-6">
                                            <div className="flex items-center gap-2 text-white">
                                                <TrendingUp className="h-5 w-5 text-indigo-400" />
                                                <span className="font-semibold">Tiempo (Últimas queries)</span>
                                            </div>
                                            <div className="text-xs text-slate-500 flex gap-4">
                                                <span className="flex items-center gap-1"><div className="w-2 h-2 bg-indigo-500 rounded-full"></div> Inferencia</span>
                                                <span className="flex items-center gap-1"><div className="w-2 h-2 bg-teal-500 rounded-full"></div> RAG</span>
                                            </div>
                                        </div>
                                        <div className="flex items-end gap-2 h-48 mt-4 pt-4 border-t border-white/10 relative overflow-visible">
                                            {recentQueries.length === 0 ? (
                                                <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
                                                    Sin consultas recientes
                                                </div>
                                            ) : (
                                                (() => {
                                                    const queries = recentQueries.slice().reverse();
                                                    const maxInf = Math.max(...queries.map(q => q.inference_time || 0), 1);
                                                    const maxRag = Math.max(...queries.map(q => q.rag_time || 0), 1);
                                                    const maxTime = Math.max(maxInf, maxRag);

                                                    const infPoints = queries.map((q, i) => {
                                                        const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                        const y = 100 - (((q.inference_time || 0) / maxTime) * 90);
                                                        return `${x},${y}`;
                                                    }).join(' ');

                                                    const ragPoints = queries.map((q, i) => {
                                                        const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                        const y = 100 - (((q.rag_time || 0) / maxTime) * 90);
                                                        return `${x},${y}`;
                                                    }).join(' ');

                                                    return (
                                                        <div className="relative w-full h-full">
                                                            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
                                                                <polyline points={ragPoints} fill="none" stroke="#14b8a6" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeDasharray="4 4" />
                                                                <polyline points={infPoints} fill="none" stroke="#6366f1" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                                                            </svg>
                                                            {queries.map((q, i) => {
                                                                const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                                const yInf = 100 - (((q.inference_time || 0) / maxTime) * 90);
                                                                const yRag = 100 - (((q.rag_time || 0) / maxTime) * 90);
                                                                return (
                                                                    <div key={i}>
                                                                        <div className="absolute w-3 h-3 -translate-x-1.5 -translate-y-1.5 bg-indigo-500 rounded-full cursor-pointer hover:bg-indigo-400 group transition-all" style={{ left: `${x}%`, top: `${yInf}%` }}>
                                                                            <div className="absolute opacity-0 group-hover:opacity-100 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0f111a] text-xs px-2 py-1 rounded text-white whitespace-nowrap pointer-events-none transition-opacity z-10 shadow-lg border border-white/20">
                                                                                Inf: {(q.inference_time || 0).toFixed(2)}s
                                                                            </div>
                                                                        </div>
                                                                        <div className="absolute w-2 h-2 -translate-x-1 -translate-y-1 bg-teal-500 rounded-full cursor-pointer hover:bg-teal-400 group transition-all" style={{ left: `${x}%`, top: `${yRag}%` }}>
                                                                            <div className="absolute opacity-0 group-hover:opacity-100 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0f111a] text-xs px-2 py-1 rounded text-white whitespace-nowrap pointer-events-none transition-opacity z-10 shadow-lg border border-white/20">
                                                                                RAG: {(q.rag_time || 0).toFixed(2)}s
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    );
                                                })()
                                            )}
                                        </div>
                                        <div className="flex justify-between text-xs text-slate-500 mt-2">
                                            <span>Más antiguas</span>
                                            <span>Recientes</span>
                                        </div>
                                    </div>

                                    {/* Tokens Line Chart */}
                                    <div className="bg-white/5 border border-white/10 rounded-2xl p-6">
                                        <div className="flex items-center justify-between mb-6">
                                            <div className="flex items-center gap-2 text-white">
                                                <Zap className="h-5 w-5 text-amber-400" />
                                                <span className="font-semibold">Historial de Tokens</span>
                                            </div>
                                            <div className="text-xs text-slate-500 flex gap-4">
                                                <span className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-500 rounded-full"></div> Input</span>
                                                <span className="flex items-center gap-1"><div className="w-2 h-2 bg-emerald-500 rounded-full"></div> Output</span>
                                            </div>
                                        </div>
                                        <div className="flex items-end gap-2 h-48 mt-4 pt-4 border-t border-white/10 relative overflow-visible">
                                            {recentQueries.length === 0 ? (
                                                <div className="w-full h-full flex items-center justify-center text-slate-500 text-sm">
                                                    Sin consultas recientes
                                                </div>
                                            ) : (
                                                (() => {
                                                    const queries = recentQueries.slice().reverse();
                                                    const maxIn = Math.max(...queries.map(q => q.token_in || 0), 1);
                                                    const maxOut = Math.max(...queries.map(q => q.token_out || 0), 1);
                                                    const maxTokens = Math.max(maxIn, maxOut);

                                                    const inPoints = queries.map((q, i) => {
                                                        const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                        const y = 100 - (((q.token_in || 0) / maxTokens) * 90);
                                                        return `${x},${y}`;
                                                    }).join(' ');

                                                    const outPoints = queries.map((q, i) => {
                                                        const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                        const y = 100 - (((q.token_out || 0) / maxTokens) * 90);
                                                        return `${x},${y}`;
                                                    }).join(' ');

                                                    return (
                                                        <div className="relative w-full h-full">
                                                            <svg className="w-full h-full overflow-visible" viewBox="0 0 100 100" preserveAspectRatio="none">
                                                                <polyline points={inPoints} fill="none" stroke="#3b82f6" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                                                                <polyline points={outPoints} fill="none" stroke="#10b981" strokeWidth="2" vectorEffect="non-scaling-stroke" />
                                                            </svg>
                                                            {queries.map((q, i) => {
                                                                const x = queries.length > 1 ? (i / (queries.length - 1)) * 100 : 50;
                                                                const yIn = 100 - (((q.token_in || 0) / maxTokens) * 90);
                                                                const yOut = 100 - (((q.token_out || 0) / maxTokens) * 90);
                                                                return (
                                                                    <div key={i}>
                                                                        <div className="absolute w-2 h-2 -translate-x-1 -translate-y-1 bg-blue-500 rounded-full cursor-pointer hover:bg-blue-400 group transition-all" style={{ left: `${x}%`, top: `${yIn}%` }}>
                                                                            <div className="absolute opacity-0 group-hover:opacity-100 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0f111a] text-xs px-2 py-1 rounded text-white whitespace-nowrap pointer-events-none transition-opacity z-10 shadow-lg border border-white/20">
                                                                                In: {(q.token_in || 0).toLocaleString()}
                                                                            </div>
                                                                        </div>
                                                                        <div className="absolute w-2 h-2 -translate-x-1 -translate-y-1 bg-emerald-500 rounded-full cursor-pointer hover:bg-emerald-400 group transition-all" style={{ left: `${x}%`, top: `${yOut}%` }}>
                                                                            <div className="absolute opacity-0 group-hover:opacity-100 bottom-full left-1/2 -translate-x-1/2 mb-2 bg-[#0f111a] text-xs px-2 py-1 rounded text-white whitespace-nowrap pointer-events-none transition-opacity z-10 shadow-lg border border-white/20">
                                                                                Out: {(q.token_out || 0).toLocaleString()}
                                                                            </div>
                                                                        </div>
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    );
                                                })()
                                            )}
                                        </div>
                                        <div className="flex justify-between text-xs text-slate-500 mt-2">
                                            <span>Más antiguas</span>
                                            <span>Recientes</span>
                                        </div>
                                    </div>

                                    {/* Token Usage Stats */}
                                    <div className="lg:col-span-2 bg-white/5 border border-white/10 rounded-2xl p-6">
                                        <div className="flex items-center gap-2 text-white mb-6">
                                            <Zap className="h-5 w-5 text-amber-400" />
                                            <span className="font-semibold">Uso de Tokens Globales</span>
                                        </div>

                                        <div className="space-y-6">
                                            <div>
                                                <div className="flex justify-between text-sm mb-1 line-clamp-1">
                                                    <span className="text-slate-400">Tokens Input</span>
                                                    <span className="text-blue-400 font-bold">{dashboard.global.total_token_in.toLocaleString()}</span>
                                                </div>
                                                <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-blue-500"
                                                        style={{ width: `${(dashboard.global.total_token_in / Math.max(dashboard.global.total_tokens, 1)) * 100}%` }}
                                                    ></div>
                                                </div>
                                            </div>
                                            <div>
                                                <div className="flex justify-between text-sm mb-1 line-clamp-1">
                                                    <span className="text-slate-400">Tokens Output</span>
                                                    <span className="text-emerald-400 font-bold">{dashboard.global.total_token_out.toLocaleString()}</span>
                                                </div>
                                                <div className="w-full h-3 bg-white/5 rounded-full overflow-hidden">
                                                    <div
                                                        className="h-full bg-emerald-500"
                                                        style={{ width: `${(dashboard.global.total_token_out / Math.max(dashboard.global.total_tokens, 1)) * 100}%` }}
                                                    ></div>
                                                </div>
                                            </div>

                                            <div className="mt-8 pt-6 border-t border-white/10 grid grid-cols-2 gap-4">
                                                <div className="bg-black/20 p-4 rounded-xl">
                                                    <div className="text-sm text-slate-400 mb-1">Avg Tokens In</div>
                                                    <div className="text-xl font-bold text-white">{dashboard.global.avg_token_in?.toLocaleString() || 0}</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl">
                                                    <div className="text-sm text-slate-400 mb-1">Avg Tokens Out</div>
                                                    <div className="text-xl font-bold text-white">{dashboard.global.avg_token_out?.toLocaleString() || 0}</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl">
                                                    <div className="text-sm text-slate-400 mb-1">Caracteres Truncados</div>
                                                    <div className="text-xl font-bold text-rose-400">{dashboard.global.total_char_truncated?.toLocaleString() || 0}</div>
                                                </div>
                                                <div className="bg-black/20 p-4 rounded-xl">
                                                    <div className="text-sm text-slate-400 mb-1">Docs Truncados</div>
                                                    <div className="text-xl font-bold text-rose-400">{dashboard.global.total_context_truncated?.toLocaleString() || 0}</div>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>, document.body
            )}
        </>
    )
}

// Legacy component for compatibility
export default function TokenStats({
    globalStats,
    sessionStats,
    userProfile,
    onClose,
}) {
    const [isOpen, setIsOpen] = useState(false)

    return (
        <div className="w-full">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 text-sm text-slate-400 hover:text-slate-300 transition-colors"
            >
                <Brain className="h-4 w-4" />
                <span>Estadísticas</span>
            </button>

            {isOpen && (
                <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.02] p-4">
                    <div className="flex justify-between items-center mb-4">
                        <div className="text-sm font-medium text-slate-400">Tu Sesión</div>
                        {onClose && (
                            <button onClick={onClose} className="text-slate-500 hover:text-slate-300">
                                <X className="h-4 w-4" />
                            </button>
                        )}
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-center mb-4">
                        <div className="rounded-xl bg-blue-500/10 p-2">
                            <div className="text-xs text-slate-500">Input</div>
                            <div className="text-sm font-semibold text-blue-400">
                                {sessionStats.input.toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-xl bg-emerald-500/10 p-2">
                            <div className="text-xs text-slate-500">Output</div>
                            <div className="text-sm font-semibold text-emerald-400">
                                {sessionStats.output.toLocaleString()}
                            </div>
                        </div>
                        <div className="rounded-xl bg-purple-500/10 p-2">
                            <div className="text-xs text-slate-500">Total</div>
                            <div className="text-sm font-semibold text-purple-400">
                                {sessionStats.total.toLocaleString()}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}