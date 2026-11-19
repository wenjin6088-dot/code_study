import { useEffect, useRef } from 'react'

import type { DocumentChapter4 } from '../../../services/document-service'

export interface Chapter4LineByLineProps {
  chapter: DocumentChapter4
  activeIndex?: number
}

export function Chapter4LineByLine({ chapter, activeIndex }: Chapter4LineByLineProps) {
  const itemRefs = useRef<Array<HTMLLIElement | null>>([])

  useEffect(() => {
    if (activeIndex != null && activeIndex >= 0) {
      itemRefs.current[activeIndex]?.scrollIntoView?.({ block: 'nearest' })
    }
  }, [activeIndex])

  return (
    <section aria-label={chapter.title}>
      <h2>{chapter.title}</h2>
      <ol>
        {chapter.explanations.map((explanation, index) => (
          <li
            key={`${explanation.file}:${explanation.line_start}-${explanation.line_end}`}
            ref={(el) => {
              itemRefs.current[index] = el
            }}
            aria-current={activeIndex === index ? 'true' : undefined}
          >
            <p>
              {explanation.file} (L{explanation.line_start}-{explanation.line_end})
            </p>
            <pre>{explanation.code}</pre>
            <p>{explanation.what_it_does}</p>
            <p>{explanation.syntax_breakdown}</p>
            <p>{explanation.analogy}</p>
            <p>{explanation.alternative_example}</p>
            <p>{explanation.notes}</p>
          </li>
        ))}
      </ol>
    </section>
  )
}
