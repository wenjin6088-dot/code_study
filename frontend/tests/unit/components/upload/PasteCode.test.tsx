import { render, screen, fireEvent } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// PasteCode (T078) does not exist yet — frontend/src/components/upload/PasteCode.tsx
//
// Expected contract:
//   export interface PasteCodeProps {
//     content: string
//     onContentChange: (v: string) => void
//     language: string
//     onLanguageChange: (v: string) => void
//   }
//   export function PasteCode(props: PasteCodeProps)
//   export const LANGUAGE_OPTIONS: { label: string; value: string; filename: string }[]
import { PasteCode, LANGUAGE_OPTIONS } from '@/components/upload/PasteCode'

describe('LANGUAGE_OPTIONS', () => {
  it('should export 9 language options with label/value/filename', () => {
    expect(LANGUAGE_OPTIONS).toHaveLength(9)
    for (const opt of LANGUAGE_OPTIONS) {
      expect(opt).toHaveProperty('label')
      expect(opt).toHaveProperty('value')
      expect(opt).toHaveProperty('filename')
    }
    expect(LANGUAGE_OPTIONS.find((o) => o.value === 'python')?.filename).toBe('pasted.py')
  })
})

describe('PasteCode', () => {
  it('should render a labelled textarea for pasting code', () => {
    render(
      <PasteCode
        content=""
        onContentChange={vi.fn()}
        language="python"
        onLanguageChange={vi.fn()}
      />,
    )

    expect(screen.getByLabelText('코드 붙여넣기')).toBeInTheDocument()
  })

  it('should render a labelled select for choosing the language', () => {
    render(
      <PasteCode
        content=""
        onContentChange={vi.fn()}
        language="python"
        onLanguageChange={vi.fn()}
      />,
    )

    expect(screen.getByLabelText('언어 선택')).toBeInTheDocument()
  })

  it('should call onContentChange when the textarea changes', () => {
    const handleChange = vi.fn()
    render(
      <PasteCode
        content=""
        onContentChange={handleChange}
        language="python"
        onLanguageChange={vi.fn()}
      />,
    )

    fireEvent.change(screen.getByLabelText('코드 붙여넣기'), {
      target: { value: 'print(1)' },
    })

    expect(handleChange).toHaveBeenCalledWith('print(1)')
  })

  it('should call onLanguageChange when the select changes', () => {
    const handleChange = vi.fn()
    render(
      <PasteCode
        content=""
        onContentChange={vi.fn()}
        language="python"
        onLanguageChange={handleChange}
      />,
    )

    fireEvent.change(screen.getByLabelText('언어 선택'), {
      target: { value: 'javascript' },
    })

    expect(handleChange).toHaveBeenCalledWith('javascript')
  })

  it('should display the given content and language values', () => {
    render(
      <PasteCode
        content="print(1)"
        onContentChange={vi.fn()}
        language="javascript"
        onLanguageChange={vi.fn()}
      />,
    )

    expect(screen.getByLabelText('코드 붙여넣기')).toHaveValue('print(1)')
    expect(screen.getByLabelText('언어 선택')).toHaveValue('javascript')
  })
})
