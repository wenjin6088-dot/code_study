import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

// HintReveal (T123) does not exist yet — frontend/src/components/practice/HintReveal.tsx
import { HintReveal } from '@/components/practice/HintReveal'

describe('HintReveal', () => {
  it('should render nothing when there are no hints', () => {
    const { container } = render(<HintReveal hints={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  it('should not show any hint initially', () => {
    render(<HintReveal hints={['Hint 1', 'Hint 2', 'Hint 3']} />)

    expect(screen.queryByText('Hint 1')).not.toBeInTheDocument()
  })

  it('should reveal one more hint each time the reveal button is clicked', () => {
    render(<HintReveal hints={['Hint 1', 'Hint 2', 'Hint 3']} />)

    fireEvent.click(screen.getByRole('button', { name: /힌트/ }))
    expect(screen.getByText('Hint 1')).toBeInTheDocument()
    expect(screen.queryByText('Hint 2')).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('button', { name: /힌트/ }))
    expect(screen.getByText('Hint 2')).toBeInTheDocument()
  })

  it('should hide the reveal button once all hints are shown', () => {
    render(<HintReveal hints={['Hint 1']} />)

    fireEvent.click(screen.getByRole('button', { name: /힌트/ }))

    expect(screen.queryByRole('button', { name: /힌트/ })).not.toBeInTheDocument()
  })
})
