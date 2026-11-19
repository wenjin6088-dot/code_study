import { describe, expect, it } from 'vitest'

// syncScroll (T105) does not exist yet — frontend/src/components/document/syncScroll.ts
//
// Pure function used to drive the one-direction sync scroll: given the
// chapter4 line-by-line explanations, the file currently visible in
// CodePanel, and the line number currently visible, find the index of the
// explanation entry that covers that line (or -1 when none matches).
import { findExplanationForLine } from '@/components/document/syncScroll'
import type { DocumentExplanation } from '@/services/document-service'

function makeExplanation(
  overrides: Partial<DocumentExplanation>,
): DocumentExplanation {
  return {
    file: 'main.py',
    line_start: 1,
    line_end: 1,
    code: '',
    what_it_does: '',
    syntax_breakdown: '',
    analogy: '',
    alternative_example: '',
    notes: '',
    ...overrides,
  }
}

describe('findExplanationForLine', () => {
  const explanations: DocumentExplanation[] = [
    makeExplanation({ file: 'main.py', line_start: 1, line_end: 3 }),
    makeExplanation({ file: 'main.py', line_start: 4, line_end: 10 }),
    makeExplanation({ file: 'utils.py', line_start: 1, line_end: 5 }),
  ]

  it('should find the explanation whose range contains the line', () => {
    expect(findExplanationForLine(explanations, 'main.py', 5)).toBe(1)
  })

  it('should match the inclusive lower boundary of a range', () => {
    expect(findExplanationForLine(explanations, 'main.py', 4)).toBe(1)
  })

  it('should match the inclusive upper boundary of a range', () => {
    expect(findExplanationForLine(explanations, 'main.py', 3)).toBe(0)
  })

  it('should only match explanations for the given file', () => {
    expect(findExplanationForLine(explanations, 'utils.py', 2)).toBe(2)
  })

  it('should return -1 when no explanation covers the line', () => {
    expect(findExplanationForLine(explanations, 'main.py', 999)).toBe(-1)
  })

  it('should return -1 when the file has no explanations at all', () => {
    expect(findExplanationForLine(explanations, 'missing.py', 1)).toBe(-1)
  })
})
