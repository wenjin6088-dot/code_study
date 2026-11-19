import type { DocumentContent } from '../../services/document-service'
import { Chapter1Summary } from './chapters/Chapter1'
import { Chapter2Prerequisites } from './chapters/Chapter2'
import { Chapter4LineByLine } from './chapters/Chapter4'

export type ChapterKey =
  | 'chapter1'
  | 'chapter2'
  | 'chapter3'
  | 'chapter4'
  | 'chapter5'
  | 'chapter6'
  | 'chapter7'

const CHAPTER_ORDER: ChapterKey[] = [
  'chapter1',
  'chapter2',
  'chapter3',
  'chapter4',
  'chapter5',
  'chapter6',
  'chapter7',
]

export interface ExplanationPanelProps {
  document: DocumentContent
  activeChapter: ChapterKey
  onChapterChange: (chapter: ChapterKey) => void
  activeExplanationIndex?: number
}

export function ExplanationPanel({
  document: doc,
  activeChapter,
  onChapterChange,
  activeExplanationIndex,
}: ExplanationPanelProps) {
  return (
    <div>
      <div role="tablist">
        {CHAPTER_ORDER.map((key) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={activeChapter === key}
            onClick={() => onChapterChange(key)}
          >
            {doc[key].title}
          </button>
        ))}
      </div>
      <div role="tabpanel">
        {activeChapter === 'chapter1' && <Chapter1Summary chapter={doc.chapter1} />}
        {activeChapter === 'chapter2' && <Chapter2Prerequisites chapter={doc.chapter2} />}
        {activeChapter === 'chapter3' && (
          <section aria-label={doc.chapter3.title}>
            <h2>{doc.chapter3.title}</h2>
            <pre>{doc.chapter3.flowchart}</pre>
            <ul>
              {Object.entries(doc.chapter3.file_breakdown).map(([path, description]) => (
                <li key={path}>
                  <strong>{path}</strong>: {description}
                </li>
              ))}
            </ul>
          </section>
        )}
        {activeChapter === 'chapter4' && (
          <Chapter4LineByLine chapter={doc.chapter4} activeIndex={activeExplanationIndex} />
        )}
        {activeChapter === 'chapter5' && (
          <section aria-label={doc.chapter5.title}>
            <h2>{doc.chapter5.title}</h2>
            <ol>
              {doc.chapter5.steps.map((step) => (
                <li key={step.step}>
                  <p>{step.description}</p>
                  <p>{step.data_state}</p>
                </li>
              ))}
            </ol>
          </section>
        )}
        {activeChapter === 'chapter6' && (
          <section aria-label={doc.chapter6.title}>
            <h2>{doc.chapter6.title}</h2>
            <ul>
              {doc.chapter6.concepts.map((concept) => (
                <li key={concept.name}>
                  <h3>{concept.name}</h3>
                  <p>{concept.what_it_is}</p>
                  <p>{concept.why_used}</p>
                  <p>{concept.where_applied}</p>
                </li>
              ))}
            </ul>
          </section>
        )}
        {activeChapter === 'chapter7' && (
          <section aria-label={doc.chapter7.title}>
            <h2>{doc.chapter7.title}</h2>
            <ul>
              {doc.chapter7.mistakes.map((mistake, index) => (
                <li key={index}>
                  <pre>{mistake.wrong}</pre>
                  <pre>{mistake.right}</pre>
                  <p>{mistake.why}</p>
                  <p>{mistake.fix}</p>
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </div>
  )
}
