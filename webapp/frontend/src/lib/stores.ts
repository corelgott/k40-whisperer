import { writable } from 'svelte/store'

export const selectedProjectId = writable<string | null>(null)

export const laserPosition = writable({ x: 0, y: 0 })

export const executionStatus = writable({ 
  running: false, 
  progress: 0,
  currentPath: ''
})
