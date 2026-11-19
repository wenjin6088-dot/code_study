import { Button } from '../ui/button'

const tailwindClassExplanations = [
  { className: 'bg-blue-500', description: '배경색을 파란색(blue-500)으로 지정' },
  { className: 'text-white', description: '글자색을 흰색으로 지정' },
  { className: 'p-4', description: '상하좌우 안쪽 여백(padding)을 1rem(16px)으로 지정' },
  { className: 'rounded-lg', description: '모서리를 둥글게(border-radius: 0.5rem) 처리' },
]

export function TailwindShadcnTest() {
  return (
    <div>
      <section data-testid="tailwind-class-test">
        <h2>Tailwind 클래스 테스트</h2>
        <div className="bg-blue-500 text-white p-4 rounded-lg">
          bg-blue-500 text-white p-4 rounded-lg
        </div>
        <ul>
          {tailwindClassExplanations.map(({ className, description }) => (
            <li key={className}>
              <code>{className}</code>: {description}
            </li>
          ))}
        </ul>
      </section>

      <section data-testid="shadcn-variant-test">
        <h2>shadcn/ui 버튼 테스트</h2>
        <Button variant="default" onClick={() => alert('variant: default')}>
          Default
        </Button>
        <Button variant="outline" onClick={() => alert('variant: outline')}>
          Outline
        </Button>
        <Button variant="ghost" onClick={() => alert('variant: ghost')}>
          Ghost
        </Button>
      </section>

      <section data-testid="responsive-grid-test">
        <h2>반응형 디자인 테스트</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div className="border rounded-lg p-4">카드 1</div>
          <div className="border rounded-lg p-4">카드 2</div>
          <div className="border rounded-lg p-4">카드 3</div>
        </div>
      </section>
    </div>
  )
}
