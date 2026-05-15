import { X } from 'lucide-react'

export default function SidebarSettings({
    isOpen,
    onClose,
    useRag,
    setUseRag,
    topK,
    setTopK,
    temperature,
    setTemperature,
    relevanceThreshold,
    setRelevanceThreshold,
    maxDocChars,
    setMaxDocChars,
    usePrf,
    setUsePrf,
    useInternetSearch,
    setUseInternetSearch,
}) {
    const disabledClass = useRag ? '' : 'opacity-45 pointer-events-none'

    return (
        <aside className={`fixed inset-0 z-40 w-full border-r border-white/10 bg-[#0E0E0E]/98 px-5 py-5 backdrop-blur-xl transition-transform duration-300 lg:inset-y-0 lg:left-0 lg:w-[22rem] ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
            <div className="flex h-full flex-col gap-5 overflow-y-auto pr-1">
                <div className="flex items-center justify-end">
                    <button
                        type="button"
                        onClick={onClose}
                        className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 bg-white/[0.05] text-slate-300"
                        aria-label="Cerrar ajustes"
                    >
                        <X className="h-5 w-5" />
                    </button>
                </div>

                <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.03] p-4">
                    <div className="flex items-center justify-between gap-4">
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-[0.35em] text-slate-500">RAG</p>
                            <h3 className="text-sm font-bold text-white">Activar</h3>
                        </div>
                        <button
                            type="button"
                            onClick={() => setUseRag((prev) => !prev)}
                            className={`relative inline-flex h-7 w-14 items-center rounded-full border transition-all ${useRag ? 'border-slate-500/50 bg-slate-700/80' : 'border-white/10 bg-white/[0.06]'}`}
                            aria-pressed={useRag}
                        >
                            <span className={`absolute left-1.5 text-[8px] font-black uppercase tracking-[0.15em] transition-opacity ${useRag ? 'opacity-100 text-slate-100' : 'opacity-35 text-slate-500'}`}>ON</span>
                            <span className={`absolute right-1.5 text-[8px] font-black uppercase tracking-[0.15em] transition-opacity ${useRag ? 'opacity-35 text-slate-500' : 'opacity-100 text-slate-200'}`}>OFF</span>
                            <span className={`relative z-10 ml-0.5 inline-block h-5 w-5 rounded-full border border-slate-300/60 bg-slate-200 shadow-md transition-transform duration-200 ${useRag ? 'translate-x-7' : 'translate-x-0'}`}></span>
                        </button>
                    </div>

                </div>

                <div className={`grid gap-4 overflow-y-auto pr-1 ${disabledClass}`}>
                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">top_k</div>
                            <div className="text-[11px] text-slate-500">Cantidad de documentos locales recuperados.</div>
                        </div>
                        <input type="range" min="1" max="50" value={topK} onChange={(e) => setTopK(Number(e.target.value) || 1)} className="sri-slider" />
                        <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>Menos contexto</span>
                            <span className="font-bold text-white">{topK}</span>
                            <span>Más contexto</span>
                        </div>
                    </label>

                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">temperature</div>
                            <div className="text-[11px] text-slate-500">Controla la creatividad de la respuesta.</div>
                        </div>
                        <input type="range" min="0" max="2" step="0.1" value={temperature} onChange={(e) => setTemperature(Number(e.target.value))} className="sri-slider" />
                        <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>Más exacto</span>
                            <span className="font-bold text-white">{temperature.toFixed(1)}</span>
                            <span>Más creativo</span>
                        </div>
                    </label>

                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">relevance threshold</div>
                            <div className="text-[11px] text-slate-500">Si el resultado local baja de aquí, puede ir a Internet.</div>
                        </div>
                        <input type="range" min="0" max="1" step="0.05" value={relevanceThreshold} onChange={(e) => setRelevanceThreshold(Number(e.target.value))} className="sri-slider" />
                        <div className="flex items-center justify-between text-xs text-slate-400">
                            <span>Más estricto</span>
                            <span className="font-bold text-white">{relevanceThreshold.toFixed(2)}</span>
                            <span>Más permisivo</span>
                        </div>
                    </label>

                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">max_doc_chars</div>
                            <div className="text-[11px] text-slate-500">Máximo de caracteres por documento.</div>
                        </div>
                        <input
                            type="number"
                            min="500"
                            step="100"
                            value={maxDocChars}
                            onChange={(e) => setMaxDocChars(Number(e.target.value) || 500)}
                            className="w-full rounded-2xl border border-white/10 bg-black/40 px-4 py-3 text-white outline-none focus:border-indigo-500/40"
                        />
                    </label>

                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">use_prf</div>
                            <div className="text-[11px] text-slate-500">Expansión pseudo-relevante de la consulta.</div>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-sm text-slate-300">Mejorar la consulta inicial</span>
                            <input type="checkbox" checked={usePrf} onChange={(e) => setUsePrf(e.target.checked)} className="h-5 w-5 accent-indigo-500" />
                        </div>
                    </label>

                    <label className="rounded-[1.5rem] border border-white/10 bg-black/25 p-4 space-y-4">
                        <div>
                            <div className="text-[10px] font-black uppercase tracking-[0.25em] text-slate-400">use_internet_search</div>
                            <div className="text-[11px] text-slate-500">Permite fallback a Internet si falta evidencia local.</div>
                        </div>
                        <div className="flex items-center justify-between gap-4">
                            <span className="text-sm text-slate-300">Buscar en Internet</span>
                            <input type="checkbox" checked={useInternetSearch} onChange={(e) => setUseInternetSearch(e.target.checked)} className="h-5 w-5 accent-indigo-500" />
                        </div>
                    </label>
                </div>

                {!useRag && (
                    <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
                        RAG está desactivado. Los ajustes avanzados quedan bloqueados hasta que lo actives.
                    </div>
                )}
            </div>
        </aside>
    )
}
