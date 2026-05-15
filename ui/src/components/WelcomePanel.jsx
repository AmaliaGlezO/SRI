export default function WelcomePanel({ suggestions, onSuggestionClick }) {
    return (
        <div className="h-[65vh] flex flex-col items-center justify-center text-center space-y-8">
            <div className="relative">
                <div className="absolute inset-0 rounded-full bg-indigo-500/20 blur-3xl"></div>
                <div className="relative flex h-24 w-24 items-center justify-center rounded-full border border-indigo-500/20 bg-gradient-to-b from-indigo-500/10 to-transparent">
                    <div className="text-4xl">🔎</div>
                </div>
            </div>

            <div className="space-y-3">
                <h2 className="bg-gradient-to-b from-white to-slate-400 bg-clip-text text-4xl font-extrabold tracking-tight text-transparent lg:text-5xl">
                    ¿Qué quieres saber?
                </h2>
                <p className="mx-auto max-w-md text-lg text-slate-400">
                    Tu motor de búsqueda inteligente potenciado por RAG e Inteligencia Artificial local.
                </p>
            </div>

            <div className="grid w-full max-w-2xl grid-cols-1 gap-4 pt-6 sm:grid-cols-2">
                {suggestions.map((suggestion) => (
                    <button
                        key={suggestion.label}
                        onClick={() => onSuggestionClick(suggestion.label)}
                        className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.03] p-4 text-left text-sm transition-all hover:border-slate-400/30 hover:bg-white/[0.05]"
                    >
                        <span className="text-xl">{suggestion.icon}</span>
                        <span className="font-medium text-slate-300 transition-colors hover:text-white">{suggestion.label}</span>
                    </button>
                ))}
            </div>
        </div>
    )
}
