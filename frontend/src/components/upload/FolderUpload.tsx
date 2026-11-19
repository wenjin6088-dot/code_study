import { useEffect, useRef, type ChangeEvent } from 'react'

declare global {
  interface HTMLInputElement {
    webkitdirectory: boolean
  }
}

export interface FolderUploadProps {
  onFilesSelected: (files: File[]) => void
}

export function FolderUpload({ onFilesSelected }: FolderUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.webkitdirectory = true
    }
  }, [])

  function handleChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files) {
      onFilesSelected(Array.from(e.target.files))
    }
  }

  return (
    <div>
      <label htmlFor="folder-upload-input">폴더 선택</label>
      <input
        ref={inputRef}
        id="folder-upload-input"
        data-testid="folder-upload-input"
        type="file"
        multiple
        onChange={handleChange}
      />
    </div>
  )
}
