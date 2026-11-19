import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { CreateProjectModal } from '../components/project/CreateProjectModal'
import { ProjectCard } from '../components/project/ProjectCard'
import { Button } from '../components/ui/button'
import { listProjects, type Project } from '../services/project-service'

function Dashboard() {
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [isModalOpen, setIsModalOpen] = useState(false)

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: listProjects,
  })

  function handleCreate(_project: Project) {
    setIsModalOpen(false)
    queryClient.invalidateQueries({ queryKey: ['projects'] })
  }

  return (
    <div>
      <Button onClick={() => setIsModalOpen(true)}>Create Project</Button>
      <Link to="/trash">휴지통 보기</Link>
      {isLoading ? (
        <div role="status">Loading...</div>
      ) : !projects || projects.length === 0 ? (
        <p>아직 프로젝트가 없습니다</p>
      ) : (
        <div>
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onClick={(p) => navigate(`/projects/${p.id}`)}
            />
          ))}
        </div>
      )}
      <CreateProjectModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreate={handleCreate}
      />
    </div>
  )
}

export default Dashboard
