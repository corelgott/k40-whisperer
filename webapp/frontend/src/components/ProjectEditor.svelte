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
</script>

<div class="project-editor">
  {#if loading}
    <div class="loading">Lade Projekt...</div>
  {:else if error}
    <div class="error">{error}</div>
  {:else if project}
    <div class="editor-layout">
      <div class="sidebar">
        <div class="sidebar-header">
          <h2>{project.name}</h2>
          <label class="upload-btn">
            SVG hochladen
            <input type="file" accept=".svg" on:change={handleFileUpload} style="display: none;" />
          </label>
        </div>
        
        <TreeView {project} on:update={() => loadProject($selectedProjectId!)} />
      </div>

      <div class="main-area">
        <div class="stage-container">
          <Stage {project} />
        </div>
        
        <div class="controls-container">
          <LaserControls />
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
    width: 350px;
    background-color: #1a1a1a;
    border-right: 1px solid #333;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .sidebar-header {
    padding: 1rem;
    border-bottom: 1px solid #333;
  }

  .sidebar-header h2 {
    margin: 0 0 1rem 0;
    font-size: 1.3rem;
  }

  .upload-btn {
    display: inline-block;
    padding: 0.6em 1.2em;
    background-color: #646cff;
    color: white;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.9rem;
    transition: background-color 0.2s;
  }

  .upload-btn:hover {
    background-color: #535bf2;
  }

  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
    overflow: hidden;
  }

  .stage-container {
    flex: 1;
    background-color: #0a0a0a;
    border-radius: 8px;
    overflow: hidden;
  }

  .controls-container {
    height: 200px;
    background-color: #1a1a1a;
    border-radius: 8px;
    padding: 1rem;
  }
</style>
