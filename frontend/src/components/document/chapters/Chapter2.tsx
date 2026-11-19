import type { DocumentChapter2 } from '../../../services/document-service'

export interface Chapter2PrerequisitesProps {
  chapter: DocumentChapter2
}

export function Chapter2Prerequisites({ chapter }: Chapter2PrerequisitesProps) {
  return (
    <section aria-label={chapter.title}>
      <h2>{chapter.title}</h2>
      <ul>
        {chapter.concepts.map((concept) => (
          <li key={concept.name}>
            <h3>{concept.name}</h3>
            <p>{concept.explanation}</p>
            <p>{concept.analogy}</p>
            <pre>{concept.example}</pre>
            <p>{concept.use_cases}</p>
          </li>
        ))}
      </ul>
    </section>
  )
}
