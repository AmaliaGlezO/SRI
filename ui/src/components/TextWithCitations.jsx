import { useEffect, useState } from 'react'

export const FormattedText = ({ text }) => {
    if (!text) return null

    const sanitizedText = text
        .replace(/\[[^\]]+\]\((https?:\/\/[^)]+)\)/g, '')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/\s{2,}/g, ' ')

    const parts = sanitizedText.split(/(\[\d+\])/g)

    return (
        <p className="text-slate-200 leading-relaxed whitespace-pre-wrap">
            {parts.map((part, index) => {
                const match = part.match(/\[(\d+)\]/)
                if (match) {
                    return (
                        <sup
                            key={index}
                            className="mx-0.5 rounded border border-indigo-500/30 bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-bold text-indigo-300 transition-colors hover:bg-indigo-500 hover:text-white"
                        >
                            {match[1]}
                        </sup>
                    )
                }
                return part
            })}
        </p>
    )
}

export const StreamingText = ({ text, onComplete }) => {
    const [displayedText, setDisplayedText] = useState('')
    const [index, setIndex] = useState(0)

    useEffect(() => {
        if (index < text.length) {
            const timeout = setTimeout(() => {
                setDisplayedText((prev) => prev + text[index])
                setIndex((prev) => prev + 1)
            }, 5)

            return () => clearTimeout(timeout)
        }

        if (onComplete) onComplete()
    }, [index, text, onComplete])

    return <FormattedText text={displayedText} />
}
