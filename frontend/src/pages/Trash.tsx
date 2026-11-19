import { useQuery, useQueryClient } from '@tanstack/react-query'

import { TrashedProjectCard } from '../components/trash/TrashedProjectCard'
import { listTrash } from '../services/trash-service'

function Trash() {
  const queryClient = useQueryClient()

  const { data: projects, isLoading } = useQuery({
    queryKey: ['trash'],
    queryFn: listTrash,
  })

  function handleActed() {
    queryClient.invalidateQueries({ queryKey: ['trash'] })
    queryClient.invalidateQueries({ queryKey: ['projects'] })
  }

  if (isLoading) {
    return <div role="status">Loading...</div>
  }

  return (
    <div>
      <h1>Trash</h1>
      {!projects || projects.length === 0 ? (
        <p>휴지통이 비어 있습니다</p>
      ) : (
        <div>
          {projects.map((project) => (
            <TrashedProjectCard
              key={project.id}
              project={project}
              onRestore={handleActed}
              onPermanentDelete={handleActed}
            />
          ))}
        </div>
      )}
    </div>
  )
}

export default Trash
