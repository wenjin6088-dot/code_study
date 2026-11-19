import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// SolutionDisplay (T124) does not exist yet — frontend/src/components/practice/SolutionDisplay.tsx
import { SolutionDisplay } from '@/components/practice/SolutionDisplay'

describe('SolutionDisplay', () => {
  it('should render nothing when there is no solution', () => {
    const { container } = render(<SolutionDisplay solution={null} expectedOutput={null} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('should not show the solution initially', () => {
    render(<SolutionDisplay solution="print(1)" expectedOutput="1" />)

    expect(screen.queryByText('print(1)')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: /정답/ })).toBeInTheDocument()
  })

  it('should reveal the solution and expected output when the button is clicked', () => {
    render(<SolutionDisplay solution="print(1)" expectedOutput="1" />)

    fireEvent.click(screen.getByRole('button', { name: /정답/ }))

    expect(screen.getByText('print(1)')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /정답/ })).not.toBeInTheDocument()
  })
})
