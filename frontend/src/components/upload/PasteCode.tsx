export interface LanguageOption {
  label: string
  value: string
  filename: string
}

export const LANGUAGE_OPTIONS: LanguageOption[] = [
  { label: 'Python', value: 'python', filename: 'pasted.py' },
  { label: 'JavaScript', value: 'javascript', filename: 'pasted.js' },
  { label: 'TypeScript', value: 'typescript', filename: 'pasted.ts' },
  { label: 'HTML', value: 'html', filename: 'pasted.html' },
  { label: 'CSS', value: 'css', filename: 'pasted.css' },
  { label: 'Java', value: 'java', filename: 'pasted.java' },
  { label: 'C++', value: 'cpp', filename: 'pasted.cpp' },
  { label: 'C', value: 'c', filename: 'pasted.c' },
  { label: 'Markdown', value: 'markdown', filename: 'pasted.md' },
]

export interface PasteCodeProps {
  content: string
  onContentChange: (v: string) => void
  language: string
  onLanguageChange: (v: string) => void
}

export function PasteCode({
  content,
  onContentChange,
  language,
  onLanguageChange,
}: PasteCodeProps) {
  return (
    <div>
      <div>
        <label htmlFor="paste-code-textarea">코드 붙여넣기</label>
        <textarea
          id="paste-code-textarea"
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
        />
      </div>
      <div>
        <label htmlFor="paste-code-language">언어 선택</label>
        <select
          id="paste-code-language"
          value={language}
          onChange={(e) => onLanguageChange(e.target.value)}
        >
          {LANGUAGE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
