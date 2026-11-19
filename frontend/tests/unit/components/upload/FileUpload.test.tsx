import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

// FileUpload (T076) does not exist yet — frontend/src/components/upload/FileUpload.tsx
//
// Expected contract:
//   export interface FileUploadProps {
//     onFilesSelected: (files: File[]) => void
//   }
//   export function FileUpload({ onFilesSelected }: FileUploadProps)
//
// Design decisions:
//   - A drag-and-drop area + a hidden <input type="file" multiple> + a
//     "파일 선택" button that triggers the hidden input's click.
//   - Selecting files via the input calls onFilesSelected with the files
//     as a plain File[] (not a FileList), unchanged.
//   - Dropping files onto the drop zone calls onFilesSelected with the
//     dropped files as a plain File[], unchanged.
import { FileUpload } from '@/components/upload/FileUpload'

function makeFile(name: string, content = 'console.log(1)') {
  return new File([content], name, { type: 'text/plain' })
}

describe('FileUpload', () => {
  it('should render a "파일 선택" button and a hidden multiple file input', () => {
    render(<FileUpload onFilesSelected={vi.fn()} />)

    expect(screen.getByRole('button', { name: '파일 선택' })).toBeInTheDocument()
    const input = screen.getByTestId('file-upload-input') as HTMLInputElement
    expect(input).toBeInTheDocument()
    expect(input.multiple).toBe(true)
  })

  it('should call onFilesSelected with the selected files via the input', () => {
    const handleFiles = vi.fn()
    render(<FileUpload onFilesSelected={handleFiles} />)

    const file1 = makeFile('a.py')
    const file2 = makeFile('b.py')
    const input = screen.getByTestId('file-upload-input') as HTMLInputElement

    fireEvent.change(input, { target: { files: [file1, file2] } })

    expect(handleFiles).toHaveBeenCalledWith([file1, file2])
  })

  it('should call onFilesSelected with dropped files', () => {
    const handleFiles = vi.fn()
    render(<FileUpload onFilesSelected={handleFiles} />)

    const file1 = makeFile('dropped.py')
    const dropZone = screen.getByTestId('file-upload-dropzone')

    fireEvent.drop(dropZone, {
      dataTransfer: { files: [file1] },
    })

    expect(handleFiles).toHaveBeenCalledWith([file1])
  })

  it('should open the file picker when the "파일 선택" button is clicked', () => {
    render(<FileUpload onFilesSelected={vi.fn()} />)

    const input = screen.getByTestId('file-upload-input') as HTMLInputElement
    const clickSpy = vi.spyOn(input, 'click')

    fireEvent.click(screen.getByRole('button', { name: '파일 선택' }))

    expect(clickSpy).toHaveBeenCalled()
  })
})
