import axios from 'axios'

const API_BASE = '/api/v1'

export interface Project {
  id: string
  name: string
  created_at: string
  default_action?: string | null
  default_speed_mm_s?: number | null
  default_repetitions?: number | null
  svg_files: SVGFile[]
  virtual_groups: VirtualGroup[]
}

export interface SVGFile {
  id: string
  filename: string
  paths: PathConfig[]
}

export interface PathConfig {
  path_id: string
  svg_id: string
  action?: 'ignore' | 'engrave' | 'cut' | null
  speed_mm_s?: number | null
  repetitions?: number | null
  order_index: number
  virtual_group_id?: string | null
  coordinates?: [number, number][]
}

export interface VirtualGroup {
  id: string
  name: string
  project_id: string
  default_action?: string | null
  default_speed_mm_s?: number | null
  default_repetitions?: number | null
  order_index: number
  path_ids: string[]
}

export const projectsAPI = {
  list: () => axios.get<Project[]>(`${API_BASE}/project/projects`),
  create: (name: string) => axios.post<Project>(`${API_BASE}/project/projects`, { name }),
  get: (id: string) => axios.get<Project>(`${API_BASE}/project/projects/${id}`),
  delete: (id: string) => axios.delete(`${API_BASE}/project/projects/${id}`),
  history: (id: string) => axios.get(`${API_BASE}/project/projects/${id}/history`),
  reorderPaths: (projectId: string, pathIds: string[]) =>
    axios.post(`${API_BASE}/project/projects/${projectId}/paths/reorder`, pathIds),
  createVirtualGroup: (projectId: string, name: string) =>
    axios.post(`${API_BASE}/project/projects/${projectId}/virtual-groups`, { 
      name, 
      project_id: projectId 
    }),
  movePathToGroup: (projectId: string, pathId: string, groupId: string | null) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/paths/${pathId}/move`, null, {
      params: { target_group_id: groupId }
    }),
}

export const svgAPI = {
  upload: (projectId: string, file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return axios.post<SVGFile>(`${API_BASE}/project/projects/${projectId}/svgs`, formData)
  },
  delete: (projectId: string, svgId: string) => 
    axios.delete(`${API_BASE}/project/projects/${projectId}/svgs/${svgId}`),
}

export const pathAPI = {
  update: (projectId: string, pathId: string, config: Partial<PathConfig>) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/paths/${pathId}`, config),
  reorder: (projectId: string, pathOrders: { path_id: string, order_index: number }[]) =>
    axios.post(`${API_BASE}/project/projects/${projectId}/paths/reorder`, { path_orders: pathOrders }),
}

export const virtualGroupAPI = {
  create: (projectId: string, name: string) =>
    axios.post(`${API_BASE}/project/projects/${projectId}/virtual-groups`, { name, project_id: projectId }),
  delete: (projectId: string, groupId: string) =>
    axios.delete(`${API_BASE}/project/projects/${projectId}/virtual-groups/${groupId}`),
  movePath: (projectId: string, pathId: string, groupId: string | null) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/paths/${pathId}/move`, { virtual_group_id: groupId }),
  update: (projectId: string, groupId: string, updates: {
    name?: string
    default_action?: string | null
    default_speed_mm_s?: number | null
    default_repetitions?: number | null
  }) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/virtual-groups/${groupId}`, null, { params: updates }),
  list: (projectId: string) =>
    axios.get<VirtualGroup[]>(`${API_BASE}/project/projects/${projectId}/virtual-groups`),
}

export const projectDefaultsAPI = {
  update: (projectId: string, defaults: {
    default_action?: string | null
    default_speed_mm_s?: number | null
    default_repetitions?: number | null
  }) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/defaults`, null, { params: defaults }),
}

export const svgTransformAPI = {
  update: async (projectId: string, svgId: string, transform: {
    position_x?: number,
    position_y?: number,
    scale_x?: number,
    scale_y?: number,
    rotation?: number
  }) => {
    const params = new URLSearchParams()
    Object.entries(transform).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, value.toString())
    })
    const response = await axios.put(`${API_BASE}/project/projects/${projectId}/svgs/${svgId}/transform?${params}`)
    return response.data
  }
}

export const laserAPI = {
  move: (dx: number, dy: number) =>
    axios.post(`${API_BASE}/k40/move`, { dx, dy }),
  home: () =>
    axios.post(`${API_BASE}/k40/home`),
  getPosition: () =>
    axios.get<{ x: number, y: number }>(`${API_BASE}/k40/position`),
  execute: (projectId: string) =>
    axios.post(`${API_BASE}/k40/execute/${projectId}`),
  stop: () =>
    axios.post(`${API_BASE}/k40/stop`),
  getStatus: () =>
    axios.get(`${API_BASE}/k40/status`),
}
