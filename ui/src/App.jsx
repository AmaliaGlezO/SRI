import { useState } from 'react'
import { Search, MessageSquare, BookOpen, Loader2 } from 'lucide-react'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [answer, setAnswer] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query })
      })
      const data = await res.json()
      
      setAnswer(data.answer || '')
      setResults(data.retrieved_documents || [])
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 to-slate-800 text-white">
      {/* Header */}
      <header className="border-b border-slate-700 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-indigo-600 rounded-lg flex items-center justify-center">
              <BookOpen className="w-6 h-6" />
            </div>
            <h1 className="text-xl font-bold">SRI</h1>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-400">
            <span className="flex items-center gap-1">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              API Conectada
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">
        {/* Search Form */}
        <form onSubmit={handleSearch} className="mb-8">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="¿Qué quieres buscar?"
              className="w-full bg-slate-800 border border-slate-700 rounded-xl py-4 pl-12 pr-4 text-lg placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition"
            />
            <button
              type="submit"
              disabled={loading}
              className="absolute right-2 top-1/2 -translate-y-1/2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-800 px-4 py-2 rounded-lg font-medium transition"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Buscar'}
            </button>
          </div>
        </form>

        {/* Answer (RAG) */}
        {answer && (
          <div className="mb-8 bg-gradient-to-r from-indigo-600/20 to-purple-600/20 border border-indigo-500/30 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-3">
              <MessageSquare className="w-5 h-5 text-indigo-400" />
              <span className="font-medium text-indigo-300">Respuesta</span>
            </div>
            <p className="text-lg leading-relaxed">{answer}</p>
          </div>
        )}

        {/* Results */}
        {results.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-sm font-medium text-slate-400 uppercase tracking-wider">
              {results.length} resultados encontrados
            </h2>
            {results.map((result, i) => (
              <div
                key={i}
                className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 hover:border-slate-600 transition"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-white">{result.title}</h3>
                      <span className={`text-xs px-2 py-0.5 rounded ${
                        result.source === 'web' 
                          ? 'bg-yellow-500/20 text-yellow-400' 
                          : 'bg-green-500/20 text-green-400'
                      }`}>
                        {result.source === 'web' ? 'Web' : 'Local'}
                      </span>
                    </div>
                    <p className="text-sm text-slate-400 mb-2">{result.date}</p>
                    <p className="text-slate-300 text-sm line-clamp-2">
                      {result.content_preview || result.content?.slice(0, 200)}
                    </p>
                  </div>
                  <div className="text-right">
                    <span className="text-lg font-bold text-indigo-400">
                      {(result.score || 0).toFixed(3)}
                    </span>
                  </div>
                </div>
                {result.url && (
                  <a
                    href={result.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 text-sm text-indigo-400 hover:text-indigo-300"
                  >
                    Ver fuente →
                  </a>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && !results.length && !answer && (
          <div className="text-center py-12 text-slate-500">
            <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Realiza una búsqueda para ver resultados</p>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-700 bg-slate-900/50 mt-12">
        <div className="max-w-5xl mx-auto px-4 py-6 text-center text-sm text-slate-500">
          Sistema de Recuperación de Información - RAG
        </div>
      </footer>
    </div>
  )
}

export default App