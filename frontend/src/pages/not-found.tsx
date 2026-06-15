import { Link } from 'react-router-dom'

import { Button, Card, SectionCopy, SectionTitle } from '../components/ui'

export function NotFoundPage() {
  return (
    <Card className="p-10">
      <SectionTitle accent="quietly.">This route does not exist</SectionTitle>
      <SectionCopy className="mt-4">Return to the main explorer and continue with the FastAPI-backed experience.</SectionCopy>
      <div className="mt-6">
        <Link to="/">
          <Button>Back to explorer</Button>
        </Link>
      </div>
    </Card>
  )
}
