import { describe, expect, it } from 'vitest'

// monacoConfig (T099) does not exist yet — frontend/src/components/document/monacoConfig.ts
//
// Maps a file extension (as returned by getTaskCode's TaskCodeFile.file_extension)
// to the Monaco Editor language id, so CodePanel gets real syntax highlighting.
import { getMonacoLanguage } from '@/components/document/monacoConfig'

describe('getMonacoLanguage', () => {
  it('should map known extensions to their Monaco language id', () => {
    expect(getMonacoLanguage('.py')).toBe('python')
    expect(getMonacoLanguage('.js')).toBe('javascript')
    expect(getMonacoLanguage('.ts')).toBe('typescript')
    expect(getMonacoLanguage('.tsx')).toBe('typescript')
    expect(getMonacoLanguage('.java')).toBe('java')
  })

  it('should be case-insensitive', () => {
    expect(getMonacoLanguage('.PY')).toBe('python')
  })

  it('should return plaintext for an unknown extension', () => {
    expect(getMonacoLanguage('.weird')).toBe('plaintext')
  })

  it('should return plaintext for a null extension', () => {
    expect(getMonacoLanguage(null)).toBe('plaintext')
  })
})
