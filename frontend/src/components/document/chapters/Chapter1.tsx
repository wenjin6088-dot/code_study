import type { DocumentChapter1 } from '../../../services/document-service'

export interface Chapter1SummaryProps {
  chapter: DocumentChapter1
}

export function Chapter1Summary({ chapter }: Chapter1SummaryProps) {
  return (
    <section aria-label={chapter.title}>
      <h2>{chapter.title}</h2>
      <p>{chapter.summary}</p>
    </section>
  )
}
