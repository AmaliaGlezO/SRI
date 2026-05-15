import { useEffect, useState } from 'react'

const parseMarkdown = (text) => {
    if (!text) return null

    const lines = text.split('\n')
    const elements = []
    let i = 0

    while (i < lines.length) {
        const line = lines[i].trim()
        
        if (line.startsWith('|') && line.includes('|')) {
            const tableLines = []
            while (i < lines.length && lines[i].trim().startsWith('|')) {
                tableLines.push(lines[i].trim())
                i++
            }
            if (tableLines.length > 0) {
                const headers = tableLines[0].split('|').filter(c => c.trim())
                const rows = tableLines.slice(2).map(row => 
                    row.split('|').filter(c => c.trim())
                )
                elements.push(
                    <div key={elements.length} className="overflow-x-auto my-4">
                        <table className="min-w-full border border-white/20 rounded-lg overflow-hidden">
                            <thead className="bg-indigo-500/20">
                                <tr>
                                    {headers.map((h, idx) => (
                                        <th key={idx} className="px-4 py-2 text-left text-xs font-bold text-indigo-300 uppercase tracking-wider border-b border-white/20">
                                            {h.trim()}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="bg-white/[0.02]">
                                {rows.map((row, rowIdx) => (
                                    <tr key={rowIdx} className="border-b border-white/10 hover:bg-white/[0.02]">
                                        {row.map((cell, cellIdx) => (
                                            <td key={cellIdx} className="px-4 py-2 text-sm text-slate-300 border-r border-white/10 last:border-r-0">
                                                {cell.trim()}
                                            </td>
                                        ))}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )
            }
            continue
        }

        if (line.startsWith('### ')) {
            elements.push(
                <h3 key={elements.length} className="text-lg font-bold text-white mt-6 mb-2">
                    {line.replace('### ', '')}
                </h3>
            )
            i++
            continue
        }

        if (line.startsWith('## ')) {
            elements.push(
                <h2 key={elements.length} className="text-xl font-bold text-white mt-8 mb-3">
                    {line.replace('## ', '')}
                </h2>
            )
            i++
            continue
        }

        if (line.startsWith('- ') || line.startsWith('* ')) {
            const listItems = []
            while (i < lines.length && (lines[i].trim().startsWith('- ') || lines[i].trim().startsWith('* '))) {
                let item = lines[i].trim().replace(/^[-*] /, '')
                item = item.replace(/\[\d+\]/g, '')
                listItems.push(item)
                i++
            }
            elements.push(
                <ul key={elements.length} className="list-disc list-inside space-y-1 my-2 ml-4">
                    {listItems.map((item, idx) => (
                        <li key={idx} className="text-slate-300 text-sm">{item}</li>
                    ))}
                </ul>
            )
            continue
        }

        if (line.match(/^\d+\.\s/)) {
            const listItems = []
            while (i < lines.length && lines[i].trim().match(/^\d+\.\s/)) {
                let item = lines[i].trim().replace(/^\d+\.\s/, '')
                item = item.replace(/\[\d+\]/g, '')
                listItems.push(item)
                i++
            }
            elements.push(
                <ol key={elements.length} className="list-decimal list-inside space-y-1 my-2 ml-4">
                    {listItems.map((item, idx) => (
                        <li key={idx} className="text-slate-300 text-sm">{item}</li>
                    ))}
                </ol>
            )
            continue
        }

        if (line.match(/^#{1,6}\s/)) {
            const level = line.match(/^(#{1,6})\s/)[1].length
            const headingText = line.replace(/^#{1,6}\s/, '')
            const classes = level === 1 ? 'text-2xl font-bold text-white mt-8 mb-4' :
                           level === 2 ? 'text-xl font-bold text-white mt-6 mb-3' :
                           'text-lg font-semibold text-white mt-4 mb-2'
            elements.push(
                <h key={elements.length} className={classes}>
                    {headingText}
                </h>
            )
            i++
            continue
        }

        if (line.trim()) {
            let processed = line.replace(/\[\d+\]/g, (match) => {
                const num = match.replace(/[\[\]]/g, '')
                return `<sup class="mx-0.5 rounded border border-indigo-500/30 bg-indigo-500/20 px-1.5 py-0.5 text-[10px] font-bold text-indigo-300">${num}</sup>`
            })
            processed = processed.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-white">$1</strong>')
            processed = processed.replace(/\*([^*]+)\*/g, '<em class="italic">$1</em>')
            
            elements.push(
                <p 
                    key={elements.length} 
                    className="text-slate-200 leading-relaxed my-2"
                    dangerouslySetInnerHTML={{ __html: processed }}
                />
            )
        }
        i++
    }

    return elements
}

export const FormattedText = ({ text }) => {
    if (!text) return null

    const sanitizedText = text
        .replace(/\[[^\]]+\]\((https?:\/\/[^)]+)\)/g, '')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/\s{2,}/g, ' ')

    return (
        <div className="space-y-1">
            {parseMarkdown(sanitizedText)}
        </div>
    )
}

export const StreamingText = ({ text, onComplete, speed = 15 }) => {
    const [displayedText, setDisplayedText] = useState('')
    const [index, setIndex] = useState(0)

    useEffect(() => {
        setIndex(0)
        setDisplayedText('')
    }, [text])

    useEffect(() => {
        if (index < text.length) {
            const timeout = setTimeout(() => {
                setDisplayedText((prev) => prev + text[index])
                setIndex((prev) => prev + 1)
            }, speed)

            return () => clearTimeout(timeout)
        }

        if (onComplete) onComplete()
    }, [index, text, onComplete, speed])

    return <FormattedText text={displayedText} />
}