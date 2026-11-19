import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// FolderUpload (T077) does not exist yet — frontend/src/components/upload/FolderUpload.tsx
//
// Expected contract:
//   export interface FolderUploadProps {
//     onFilesSelected: (files: File[]) => void
//   }
//   export function FolderUpload({ onFilesSelected }: FolderUploadProps)
//
// Design decisions:
//   - A single <input type="file" webkitdirectory multiple> — selecting a
//     folder calls onFilesSelected with the FileList converted to a plain
//     File[], unchanged (webkitRelativePath is set by the browser itself on
//     each File and is read later by task-service.ts).
import { FolderUpload } from '@/components/upload/FolderUpload'

function makeFile(name: string, relativePath: string) {
  const file = new File(['code'], name, { type: 'text/plain' })
  Object.defineProperty(file, 'webkitRelativePath', { value: relativePath })
  return file
}

describe('FolderUpload', () => {
  it('should render a folder input with webkitdirectory and multiple set', () => {
    render(<FolderUpload onFilesSelected={vi.fn()} />)

    const input = screen.getByTestId('folder-upload-input') as HTMLInputElement
    expect(input).toBeInTheDocument()
    expect(input.multiple).toBe(true)
    expect(input.webkitdirectory).toBe(true)
  })

  it('should call onFilesSelected with the selected folder files, preserving webkitRelativePath', () => {
    const handleFiles = vi.fn()
    render(<FolderUpload onFilesSelected={handleFiles} />)

    const file1 = makeFile('a.py', 'myfolder/a.py')
    const file2 = makeFile('b.py', 'myfolder/sub/b.py')
    const input = screen.getByTestId('folder-upload-input') as HTMLInputElement

    fireEvent.change(input, { target: { files: [file1, file2] } })

    expect(handleFiles).toHaveBeenCalledWith([file1, file2])
    const received: File[] = handleFiles.mock.calls[0][0]
    expect(received[0].webkitRelativePath).toBe('myfolder/a.py')
    expect(received[1].webkitRelativePath).toBe('myfolder/sub/b.py')
  })
})
