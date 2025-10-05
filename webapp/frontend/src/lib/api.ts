import axios from 'axios'

const API_BASE = '/api/v1'

export interface Project {
  id: string
  name: string
  created_at: string
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
  action: 'ignore' | 'engrave' | 'cut'
  speed_mm_s: number
  repetitions: number
  order_index: number
  virtual_group_id?: string
}

export interface VirtualGroup {
  id: string
  name: string
  order_index: number
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
    axios.post(`${API_BASE}/project/projects/${projectId}/virtual-groups`, { name }),
  delete: (projectId: string, groupId: string) =>
    axios.delete(`${API_BASE}/project/projects/${projectId}/virtual-groups/${groupId}`),
  movePath: (projectId: string, pathId: string, groupId: string | null) =>
    axios.put(`${API_BASE}/project/projects/${projectId}/paths/${pathId}/move`, { virtual_group_id: groupId }),
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
