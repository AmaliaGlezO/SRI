import { useEffect, useRef, useState } from 'react'
import { Bot, BookOpen, ExternalLink, Loader2, Menu, Send, User, X } from 'lucide-react'
import { FormattedText, SidebarSettings, StreamingText, WelcomePanel } from './components'

const suggestionCards = [
    { label: 'Mejores móviles de 2026', icon: '📱' },
    { label: 'PC gaming calidad-precio', icon: '🖥️' },
    { label: 'Laptops para estudiar y programar', icon: '💻' },
    { label: 'Teléfonos Android con mejor cámara', icon: '📷' },
]

function App() {
    const [query, setQuery] = useState('')
    const [messages, setMessages] = useState([])
    const [loading, setLoading] = useState(false)
    const [modelName, setModelName] = useState('TinyLlama 1.1B')
    const [showAllSources, setShowAllSources] = useState(null)
    const [sidebarOpen, setSidebarOpen] = useState(() => {
        if (typeof window === 'undefined') return true
        return window.innerWidth >= 1024
    })
    const [useRag, setUseRag] = useState(true)
    const [topK, setTopK] = useState(5)
    const [temperature, setTemperature] = useState(0.2)
    const [relevanceThreshold, setRelevanceThreshold] = useState(0.45)
    const [maxDocChars, setMaxDocChars] = useState(3500)
    const [usePrf, setUsePrf] = useState(true)
    const [useInternetSearch, setUseInternetSearch] = useState(true)
    const [apiError, setApiError] = useState('')
    const chatEndRef = useRef(null)

    useEffect(() => {
        chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    useEffect(() => {
        const fetchStatus = async () => {
            try {
                const res = await fetch('/api/status')
                const data = await res.json()
                if (data.model_info) {
                    setModelName(String(data.model_info).split('/').pop())
                }
            } catch (error) {
                console.error('Failed to fetch status:', error)
            }
        }

        fetchStatus()
    }, [])

    const handleSearch = async (event) => {
        event.preventDefault()
        if (!query.trim() || loading) return

        const userQuery = query
        setQuery('')
        setApiError('')

        // Agregar mensaje del usuario
        setMessages((previous) => [...previous, { role: 'user', content: userQuery }])

        // Crear un mensaje vacío del asistente con isStreaming=true para mostrar los tres puntos
        setMessages((previous) => [
            ...previous,
            {
                role: 'assistant',
                content: '',
                sources: [],
                isStreaming: true,
            },
        ])

        setLoading(true)

        try {
            const response = await fetch('/api/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    query: userQuery,
                    use_rag: useRag,
                    top_k: topK,
                    temperature,
                    relevance_threshold: relevanceThreshold,
                    max_doc_chars: maxDocChars,
                    use_prf: usePrf,
                    use_internet_search: useInternetSearch,
                }),
            })

            if (!response.ok) throw new Error('API Error')

            const data = await response.json()

            // Actualizar el mensaje del asistente con la respuesta real
            setMessages((previous) => {
                const updated = [...previous]
                const lastIndex = updated.length - 1
                if (updated[lastIndex] && updated[lastIndex].role === 'assistant') {
                    updated[lastIndex] = {
                        ...updated[lastIndex],
                        content: data.answer || 'No se pudo generar una respuesta.',
                        sources: data.retrieved_documents || [],
                        isStreaming: false,
                    }
                }
                return updated
            })
        } catch (error) {
            console.error(error)
            setApiError('No se pudo completar la consulta. Revisa el estado de la API o ajusta los parámetros de RAG.')

            // Actualizar el mensaje del asistente con el error
            setMessages((previous) => {
                const updated = [...previous]
                const lastIndex = updated.length - 1
                if (updated[lastIndex] && updated[lastIndex].role === 'assistant') {
                    updated[lastIndex] = {
                        ...updated[lastIndex],
                        content: 'Hubo un error al procesar tu solicitud. Por favor, inténtalo de nuevo.',
                        isError: true,
                        isStreaming: false,
                    }
                }
                return updated
            })
        } finally {
            setLoading(false)
        }
    }

    const markStreamingComplete = (index) => {
        setMessages((previous) => {
            const nextMessages = [...previous]
            if (nextMessages[index]) {
                nextMessages[index].isStreaming = false
            }
            return nextMessages
        })
    }

    return (
        <div className="min-h-screen bg-[#0A0A0A] text-slate-200 lg:flex">
            {sidebarOpen && (
                <button
                    type="button"
                    className="fixed inset-0 z-30 bg-black/60 lg:hidden"
                    aria-label="Cerrar barra lateral"
                    onClick={() => setSidebarOpen(false)}
                />
            )}
            <SidebarSettings
                isOpen={sidebarOpen}
                onClose={() => setSidebarOpen(false)}
                useRag={useRag}
                setUseRag={setUseRag}
                topK={topK}
                setTopK={setTopK}
                temperature={temperature}
                setTemperature={setTemperature}
                relevanceThreshold={relevanceThreshold}
                setRelevanceThreshold={setRelevanceThreshold}
                maxDocChars={maxDocChars}
                setMaxDocChars={setMaxDocChars}
                usePrf={usePrf}
                setUsePrf={setUsePrf}
                useInternetSearch={useInternetSearch}
                setUseInternetSearch={setUseInternetSearch}
            />

            <div className={`flex min-h-screen flex-1 flex-col transition-[padding-left] duration-300 ${sidebarOpen ? 'lg:pl-[22rem]' : 'lg:pl-0'}`}>
                <nav className="sticky top-0 z-30 border-b border-white/5 bg-[#0A0A0A]/85 backdrop-blur-xl">
                    <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
                        <div className="flex items-center gap-3">
                            <button className="flex items-center gap-3" type="button" onClick={() => setMessages([])}>
                                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-purple-600 shadow-lg shadow-indigo-500/20">
                                    <BookOpen className="h-5 w-5 text-white" />
                                </div>
                                <h1 className="text-xl font-bold tracking-tight text-white">
                                    SRI <span className="font-light text-indigo-400">Search</span>
                                </h1>
                            </button>
                        </div>
                        {!sidebarOpen && (
                            <button
                                type="button"
                                className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-slate-200"
                                aria-label="Abrir barra lateral"
                                onClick={() => setSidebarOpen(true)}
                            >
                                <Menu className="h-5 w-5" />
                            </button>
                        )}
                    </div>
                </nav>

                <main className="mx-auto flex w-full max-w-3xl flex-1 px-4 py-6">
                    <div className="w-full">
                        {messages.length === 0 ? (
                            <WelcomePanel
                                suggestions={suggestionCards}
                                onSuggestionClick={setQuery}
                            />
                        ) : (
                            <div className="space-y-8">
                                {messages.map((message, index) => (
                                    <div key={index} className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                                        {message.role === 'user' && (
                                            <div className="flex items-end justify-end gap-2">
                                                <div className="max-w-[75%]">
                                                    <div className="bg-indigo-600 rounded-2xl px-4 py-3 text-white text-base font-medium">
                                                        {message.content}
                                                    </div>
                                                </div>
                                                <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-white/10 bg-slate-700">
                                                    <User className="h-3.5 w-3.5 text-slate-300" />
                                                </div>
                                            </div>
                                        )}

                                        {message.role === 'assistant' && (
                                            <div className="flex items-start gap-3">
                                                <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-[#1a1a2e] border border-white/10 shadow-lg">
                                                    <Bot className="h-4 w-4 text-white" />
                                                </div>
                                                <div className="flex-1 space-y-4">
                                                    {message.sources && message.sources.length > 0 && (
                                                        <div className="space-y-4">
                                                            <div className="flex items-center gap-3 text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">
                                                                <div className="h-px w-4 bg-slate-800"></div>
                                                                Fuentes Consultadas
                                                            </div>
                                                            <div className="flex flex-wrap gap-3">
                                                                {message.sources.slice(0, 3).map((source, sourceIndex) => (
                                                                    <a
                                                                        key={sourceIndex}
                                                                        href={source.url}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="flex max-w-[220px] items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-2.5 shadow-sm transition-all hover:border-indigo-500/30 hover:bg-indigo-500/10"
                                                                    >
                                                                        <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg bg-indigo-500/10 text-[10px] font-bold text-indigo-400 shadow-inner transition-all hover:bg-indigo-600 hover:text-white">
                                                                            {sourceIndex + 1}
                                                                        </div>
                                                                        <div className="flex min-w-0 flex-col">
                                                                            <span className="truncate text-[11px] font-bold text-slate-200">{source.title}</span>
                                                                            <span className="truncate text-[9px] text-slate-500">{source.url ? new URL(source.url).hostname : 'Fuente local'}</span>
                                                                        </div>
                                                                        <ExternalLink className="ml-auto h-3 w-3 text-slate-700" />
                                                                    </a>
                                                                ))}
                                                                {message.sources.length > 3 && (
                                                                    <button
                                                                        type="button"
                                                                        onClick={() => setShowAllSources(index)}
                                                                        className="rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-[11px] font-black text-slate-400 shadow-sm transition-all hover:bg-white/10 hover:text-white"
                                                                    >
                                                                        +{message.sources.length - 3} MÁS
                                                                    </button>
                                                                )}
                                                            </div>
                                                        </div>
                                                    )}

                                                    <div className="relative group">
                                                        <div className="prose prose-invert max-w-none">
                                                            {/* Mostrar tres puntos mientras está en streaming y no hay contenido */}
                                                            {message.isStreaming && !message.content && !message.isError ? (
                                                                <div className="flex items-center gap-1 py-2.5">
                                                                    <span className="block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                                                                    <span className="block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                                                                    <span className="block w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                                                                </div>
                                                            ) : message.isStreaming && message.content ? (
                                                                <StreamingText text={message.content} onComplete={() => markStreamingComplete(index)} />
                                                            ) : (
                                                                <FormattedText text={message.content} />
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                                <div ref={chatEndRef} />
                            </div>
                        )}
                    </div>
                </main>

                {showAllSources !== null && (
                    <div
                        className="fixed inset-0 z-50 flex items-center justify-center bg-black/90 p-6 backdrop-blur-md"
                        onClick={() => setShowAllSources(null)}
                    >
                        <div
                            className="scale-in-center flex max-h-[85vh] w-full max-w-2xl flex-col overflow-hidden rounded-[2.5rem] border border-white/10 bg-[#111111] shadow-2xl"
                            onClick={(event) => event.stopPropagation()}
                        >
                            <div className="flex items-center justify-between border-b border-white/5 bg-white/[0.01] p-8">
                                <h3 className="flex items-center gap-4 text-2xl font-extrabold text-white">
                                    <div className="rounded-xl bg-indigo-500/10 p-2">
                                        <BookOpen className="h-6 w-6 text-indigo-500" />
                                    </div>
                                    Todas las fuentes
                                </h3>
                                <button type="button" onClick={() => setShowAllSources(null)} className="rounded-full bg-white/5 p-3 text-slate-400 transition-all hover:bg-white/10 hover:text-white">
                                    ✕
                                </button>
                            </div>
                            <div className="custom-scrollbar space-y-4 overflow-y-auto p-8">
                                {messages[showAllSources]?.sources?.map((source, sourceIndex) => (
                                    <a
                                        key={sourceIndex}
                                        href={source.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="flex items-center gap-5 rounded-3xl border border-white/5 bg-white/[0.02] p-5 shadow-sm transition-all hover:border-indigo-500/30 hover:bg-white/[0.05]"
                                    >
                                        <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-2xl bg-indigo-600/10 text-sm font-black text-indigo-400 shadow-inner transition-all hover:bg-indigo-600 hover:text-white">
                                            {sourceIndex + 1}
                                        </div>
                                        <div className="min-w-0 flex-1 space-y-1">
                                            <p className="truncate text-base font-bold text-white transition-colors hover:text-indigo-100">{source.title}</p>
                                            <p className="truncate font-mono text-[11px] tracking-tighter text-slate-500">{source.url}</p>
                                        </div>
                                        <ExternalLink className="h-5 w-5 text-slate-700 transition-colors hover:text-slate-400" />
                                    </a>
                                ))}
                            </div>
                        </div>
                    </div>
                )}

                <div className="sticky bottom-0 border-t border-white/5 bg-[#0A0A0A]/95 px-4 py-3 backdrop-blur-sm">
                    <div className="mx-auto max-w-2xl">
                        {apiError && (
                            <div className="mb-2 rounded-xl border border-rose-500/20 bg-rose-500/10 px-3 py-2 text-xs text-rose-200">
                                {apiError}
                            </div>
                        )}
                        <form
                            onSubmit={handleSearch}
                            className="relative flex h-11 items-center rounded-xl border border-white/10 bg-[#1A1A1A] shadow-lg transition-all duration-300 focus-within:border-indigo-500/50 focus-within:ring-3 focus-within:ring-indigo-500/10"
                        >
                            <input
                                type="text"
                                value={query}
                                onChange={(event) => setQuery(event.target.value)}
                                placeholder="Escribe tu pregunta..."
                                className="flex-1 border-none bg-transparent px-3 text-sm text-white outline-none placeholder:text-slate-500"
                            />
                            <button
                                type="submit"
                                disabled={loading || !query.trim()}
                                className={`flex h-9 w-9 items-center justify-center rounded-lg mr-1 transition-all ${loading || !query.trim()
                                    ? 'opacity-40 cursor-not-allowed'
                                    : 'bg-indigo-600 hover:bg-indigo-500'
                                    }`}
                            >
                                {loading ? (
                                    <Loader2 className="h-4 w-4 animate-spin text-white" />
                                ) : (
                                    <Send className="h-4 w-4 text-white" />
                                )}
                            </button>
                        </form>

                        <div className="mt-6 flex flex-col items-center gap-2">
                            <div className="flex items-center gap-3 rounded-full border border-white/5 bg-white/[0.03] px-4 py-1.5">
                                <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Engine</span>
                                <div className="h-3 w-px bg-slate-800"></div>
                                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-indigo-400">{modelName}</span>
                            </div>
                            <div className="flex flex-wrap items-center justify-center gap-2 text-[10px] text-slate-500">
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">RAG {useRag ? 'on' : 'off'}</span>
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">top_k {topK}</span>
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">temp {temperature.toFixed(1)}</span>
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">threshold {relevanceThreshold.toFixed(2)}</span>
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">PRF {usePrf ? 'on' : 'off'}</span>
                                <span className="rounded-full border border-white/5 bg-white/[0.03] px-3 py-1">web {useInternetSearch ? 'on' : 'off'}</span>
                            </div>
                            <p className="text-[9px] font-black uppercase tracking-[0.4em] text-slate-600">SRI RAG AI SYSTEM • 2026</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default App