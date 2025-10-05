import { writable } from 'svelte/store'

export const selectedProjectId = writable<string | null>(null)

export const laserPosition = writable({ x: 0, y: 0 })

export const executionStatus = writable({
  running: false,
  progress: 0,
  currentPath: ''
})

export const animationState = writable({
  isPlaying: false,
  currentPathIndex: 0,
  currentPathProgress: 0,
  speed: 1.0,
  paths: [] as any[]
})
