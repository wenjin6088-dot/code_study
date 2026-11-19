import type { DocumentExplanation } from '../../services/document-service'

/**
 * Finds the chapter4 explanation entry covering `lineNumber` in `file`, used
 * to drive the one-direction sync scroll from CodePanel into ExplanationPanel
 * (CodePanel scroll -> matching explanation; the reverse is not required).
 *
 * Returns the matching index, or -1 when no explanation covers that line.
 */
export function findExplanationForLine(
  explanations: DocumentExplanation[],
  file: string,
  lineNumber: number,
): number {
  return explanations.findIndex(
    (explanation) =>
      explanation.file === file &&
      lineNumber >= explanation.line_start &&
      lineNumber <= explanation.line_end,
  )
}
