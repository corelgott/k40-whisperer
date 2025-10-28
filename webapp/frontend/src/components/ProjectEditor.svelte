<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import { selectedProjectId, laserPosition, executionStatus } from '../lib/stores'
  import { projectsAPI, type Project } from '../lib/api'
  import TreeView from './TreeView.svelte'
  import Stage from './Stage.svelte'
  import LaserControls from './LaserControls.svelte'

  let project: Project | null = null
  let loading = true
  let error = ''
  let positionWs: WebSocket | null = null
  let statusWs: WebSocket | null = null
  let sidebarWidth = 350
  let sidebarCollapsed = false
  let isResizing = false

  $: if ($selectedProjectId) {
    loadProject($selectedProjectId)
  }

  onMount(() => {
    connectWebSockets()
  })

  onDestroy(() => {
    disconnectWebSockets()
  })

  function connectWebSockets() {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsHost = window.location.host
    
    positionWs = new WebSocket(`${wsProtocol}//${wsHost}/ws/position`)
    positionWs.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'position') {
        laserPosition.set({ x: data.x, y: data.y })
      }
    }
    positionWs.onerror = (error) => {
      console.error('Position WebSocket error:', error)
    }
    positionWs.onclose = () => {
      console.log('Position WebSocket closed')
    }

    statusWs = new WebSocket(`${wsProtocol}//${wsHost}/ws/status`)
    statusWs.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'status') {
        executionStatus.set({
          running: data.is_running || false,
          progress: Math.round((data.progress || 0) * 100),
          currentPath: data.current_project || ''
        })
      }
    }
    statusWs.onerror = (error) => {
      console.error('Status WebSocket error:', error)
    }
    statusWs.onclose = () => {
      console.log('Status WebSocket closed')
    }
  }

  function disconnectWebSockets() {
    if (positionWs) {
      positionWs.close()
      positionWs = null
    }
    if (statusWs) {
      statusWs.close()
      statusWs = null
    }
  }

  async function loadProject(id: string) {
    loading = true
    error = ''
    try {
      const response = await projectsAPI.get(id)
      project = response.data
    } catch (e: any) {
      error = e.message || 'Fehler beim Laden des Projekts'
    } finally {
      loading = false
    }
  }

  async function handleFileUpload(event: Event) {
    const target = event.target as HTMLInputElement
    const file = target.files?.[0]
    if (!file || !$selectedProjectId) return

    try {
      const { svgAPI } = await import('../lib/api')
      await svgAPI.upload($selectedProjectId, file)
      await loadProject($selectedProjectId)
      target.value = ''
    } catch (e: any) {
      error = e.message || 'Fehler beim Hochladen der SVG-Datei'
    }
  }

  function startResize() {
    isResizing = true
    document.addEventListener('mousemove', handleResize)
    document.addEventListener('mouseup', stopResize)
  }

  function handleResize(e: MouseEvent) {
    if (!isResizing) return
    sidebarWidth = Math.max(250, Math.min(600, e.clientX))
  }

  function stopResize() {
    isResizing = false
    document.removeEventListener('mousemove', handleResize)
    document.removeEventListener('mouseup', stopResize)
  }

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed
  }
</script>

<div class="project-editor">
  {#if loading}
    <div class="loading">Lade Projekt...</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else if project}
    <div class="editor-layout">
      <div class="sidebar" style="width: {sidebarCollapsed ? 40 : sidebarWidth}px">
        {#if !sidebarCollapsed}
          <LaserControls compact={true} />
          <TreeView {project} on:update={() => loadProject($selectedProjectId!)} on:pathSelected />
        {/if}
        <button class="collapse-btn" on:click={toggleSidebar} title={sidebarCollapsed ? 'Sidebar ausklappen' : 'Sidebar einklappen'}>
          {sidebarCollapsed ? '▶' : '◀'}
        </button>
      </div>

      {#if !sidebarCollapsed}
        <div class="resize-handle" on:mousedown={startResize}></div>
      {/if}

      <div class="main-area">
        <div class="stage-container">
          <Stage {project} />
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .project-editor {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .loading, .error {
    display: flex;
    justify-content: center;
    align-items: center;
    height: 100%;
    font-size: 1.2rem;
  }

  .error {
    color: #ff4444;
  }

  .editor-layout {
    flex: 1;
    display: flex;
    gap: 1rem;
    overflow: hidden;
  }

  .sidebar {
    background-color: #1a1a1a;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    flex-shrink: 0;
    position: relative;
  }

  .collapse-btn {
    position: absolute;
    top: 50%;
    right: 4px;
    transform: translateY(-50%);
    background: #2a2a2a;
    border: 1px solid #444;
    color: #e0e0e0;
    cursor: pointer;
    padding: 8px 4px;
    border-radius: 3px;
    font-size: 12px;
    z-index: 10;
  }

  .collapse-btn:hover {
    background: #333;
  }

  .resize-handle {
    width: 4px;
    background-color: #333;
    cursor: col-resize;
    flex-shrink: 0;
  }

  .resize-handle:hover {
    background-color: #555;
  }

  .laser-controls-wrapper {
    border-top: 1px solid #333;
  }

  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .stage-container {
    flex: 1;
    background-color: #0a0a0a;
    overflow: hidden;
  }
</style>
