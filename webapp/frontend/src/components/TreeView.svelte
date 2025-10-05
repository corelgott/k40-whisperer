<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import { dndzone } from 'svelte-dnd-action'
  import type { Project, PathConfig } from '../lib/api'
  import { projectsAPI } from '../lib/api'
  import PathSettings from './PathSettings.svelte'

  export let project: Project

  const dispatch = createEventDispatcher()

  let selectedPathId: string | null = null
  let expandedSvgs = new Set<string>()
  let expandedGroups = new Set<string>()
  let showNewGroupInput = false
  let newGroupName = ''
  let isReordering = false

  function toggleSvg(svgId: string) {
    if (expandedSvgs.has(svgId)) {
      expandedSvgs.delete(svgId)
    } else {
      expandedSvgs.add(svgId)
    }
    expandedSvgs = expandedSvgs
  }

  function toggleGroup(groupId: string) {
    if (expandedGroups.has(groupId)) {
      expandedGroups.delete(groupId)
    } else {
      expandedGroups.add(groupId)
    }
    expandedGroups = expandedGroups
  }

  function selectPath(pathId: string) {
    selectedPathId = pathId
  }

  function getPathConfig(svgId: string, pathId: string): PathConfig | undefined {
    const svg = project.svg_files.find(s => s.id === svgId)
    return svg?.paths.find(p => p.path_id === pathId)
  }

  async function createVirtualGroup() {
    if (!newGroupName.trim()) return
    
    try {
      await projectsAPI.createVirtualGroup(project.id, newGroupName.trim())
      newGroupName = ''
      showNewGroupInput = false
      dispatch('update')
    } catch (error) {
      console.error('Failed to create virtual group:', error)
    }
  }

  async function handleSvgPathsReorder(svgId: string, e: CustomEvent) {
    if (isReordering) return
    isReordering = true

    const items = e.detail.items
    const pathIds = items.map((item: any) => item.path_id)
    
    try {
      await projectsAPI.reorderPaths(project.id, pathIds)
      dispatch('update')
    } catch (error) {
      console.error('Failed to reorder paths:', error)
    } finally {
      isReordering = false
    }
  }

  async function handleGroupPathsReorder(groupId: string, e: CustomEvent) {
    if (isReordering) return
    isReordering = true

    const items = e.detail.items
    const pathIds = items.map((item: any) => item.path_id)
    
    try {
      await projectsAPI.reorderPaths(project.id, pathIds)
      dispatch('update')
    } catch (error) {
      console.error('Failed to reorder paths:', error)
    } finally {
      isReordering = false
    }
  }

  async function handlePathDrop(targetGroupId: string | null, pathId: string, sourceSvgId: string) {
    try {
      await projectsAPI.movePathToGroup(project.id, pathId, targetGroupId)
      dispatch('update')
    } catch (error) {
      console.error('Failed to move path:', error)
    }
  }

  function getPathsForSvg(svgId: string) {
    const svg = project.svg_files.find(s => s.id === svgId)
    if (!svg) return []
    return svg.paths
      .filter(p => !p.virtual_group_id)
      .sort((a, b) => a.order_index - b.order_index)
      .map(p => ({ ...p, id: p.path_id }))
  }

  function getPathsForGroup(groupId: string) {
    return project.svg_files.flatMap(svg => 
      svg.paths.filter(p => p.virtual_group_id === groupId)
    ).sort((a, b) => a.order_index - b.order_index)
      .map(p => ({ ...p, id: p.path_id }))
  }

  $: allPaths = project.svg_files.flatMap(svg => 
    svg.paths.map(path => ({ ...path, svg }))
  ).sort((a, b) => a.order_index - b.order_index)
</script>

<div class="tree-view">
  <div class="tree-content">
    <div class="project-node">
      <span class="node-icon">📁</span>
      <span class="node-label">{project.name}</span>
    </div>

    {#each project.svg_files as svg}
      <div class="svg-node">
        <button class="expand-btn" on:click={() => toggleSvg(svg.id)}>
          {expandedSvgs.has(svg.id) ? '▼' : '▶'}
        </button>
        <span class="node-icon">📄</span>
        <span class="node-label">{svg.filename}</span>
        <span class="badge">{getPathsForSvg(svg.id).length}</span>
      </div>

      {#if expandedSvgs.has(svg.id)}
        {@const svgPaths = getPathsForSvg(svg.id)}
        {#if svgPaths.length > 0}
          <div 
            class="paths-container"
            use:dndzone={{ items: svgPaths, dropTargetStyle: {} }}
            on:consider={(e) => handleSvgPathsReorder(svg.id, e)}
            on:finalize={(e) => handleSvgPathsReorder(svg.id, e)}
          >
            {#each svgPaths as path (path.path_id)}
              <div 
                class="path-node draggable" 
                class:selected={selectedPathId === path.path_id}
                on:click={() => selectPath(path.path_id)}
              >
                <span class="drag-handle">⋮⋮</span>
                <span class="node-icon" class:cut={path.action === 'cut'} class:engrave={path.action === 'engrave'} class:ignore={path.action === 'ignore'}>
                  {path.action === 'cut' ? '✂' : path.action === 'engrave' ? '🖊' : '⊘'}
                </span>
                <span class="node-label">{path.path_id}</span>
                <span class="speed-badge">{path.speed_mm_s} mm/s</span>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-message">Alle Pfade in Gruppen verschoben</div>
        {/if}
      {/if}
    {/each}

    <div class="separator">
      <span>Virtuelle Gruppen</span>
      <button class="add-group-btn" on:click={() => showNewGroupInput = !showNewGroupInput}>
        {showNewGroupInput ? '✕' : '+'}
      </button>
    </div>

    {#if showNewGroupInput}
      <div class="new-group-input">
        <input 
          type="text" 
          placeholder="Gruppenname..." 
          bind:value={newGroupName}
          on:keydown={(e) => e.key === 'Enter' && createVirtualGroup()}
        />
        <button on:click={createVirtualGroup}>Erstellen</button>
      </div>
    {/if}

    {#each project.virtual_groups as group}
      <div class="group-node">
        <button class="expand-btn" on:click={() => toggleGroup(group.id)}>
          {expandedGroups.has(group.id) ? '▼' : '▶'}
        </button>
        <span class="node-icon">📦</span>
        <span class="node-label">{group.name}</span>
        <span class="badge">{getPathsForGroup(group.id).length}</span>
      </div>

      {#if expandedGroups.has(group.id)}
        {@const groupPaths = getPathsForGroup(group.id)}
        {#if groupPaths.length > 0}
          <div 
            class="paths-container group-paths"
            use:dndzone={{ items: groupPaths, dropTargetStyle: {} }}
            on:consider={(e) => handleGroupPathsReorder(group.id, e)}
            on:finalize={(e) => handleGroupPathsReorder(group.id, e)}
          >
            {#each groupPaths as path (path.path_id)}
              <div 
                class="path-node draggable" 
                class:selected={selectedPathId === path.path_id}
                on:click={() => selectPath(path.path_id)}
              >
                <span class="drag-handle">⋮⋮</span>
                <span class="node-icon" class:cut={path.action === 'cut'} class:engrave={path.action === 'engrave'} class:ignore={path.action === 'ignore'}>
                  {path.action === 'cut' ? '✂' : path.action === 'engrave' ? '🖊' : '⊘'}
                </span>
                <span class="node-label">{path.path_id}</span>
                <span class="speed-badge">{path.speed_mm_s} mm/s</span>
                <button 
                  class="remove-from-group-btn"
                  on:click|stopPropagation={() => handlePathDrop(null, path.path_id, path.svg_id)}
                  title="Zurück zu SVG"
                >
                  ↩
                </button>
              </div>
            {/each}
          </div>
        {:else}
          <div class="empty-message">Keine Pfade in dieser Gruppe</div>
        {/if}
      {/if}
    {/each}
  </div>

  {#if selectedPathId}
    {@const pathData = allPaths.find(p => p.path_id === selectedPathId)}
    {#if pathData}
      <div class="path-settings-panel">
        <PathSettings 
          pathConfig={pathData} 
          on:update={() => dispatch('update')}
        />
      </div>
    {/if}
  {/if}
</div>

<style>
  .tree-view {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .tree-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }

  .project-node, .svg-node, .path-node, .group-node {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-radius: 4px;
    cursor: pointer;
    user-select: none;
  }

  .project-node {
    font-weight: bold;
    margin-bottom: 0.5rem;
  }

  .svg-node {
    margin-left: 1rem;
    margin-bottom: 0.25rem;
  }

  .path-node {
    margin-left: 2rem;
    font-size: 0.9rem;
  }

  .path-node:hover, .svg-node:hover {
    background-color: #2a2a2a;
  }

  .path-node.selected {
    background-color: #646cff;
  }

  .group-node {
    margin-left: 1rem;
    background-color: #2a2a2a;
  }

  .expand-btn {
    background: none;
    border: none;
    color: white;
    cursor: pointer;
    padding: 0;
    width: 1.5rem;
    text-align: center;
  }

  .node-icon {
    font-size: 1.2rem;
  }

  .node-icon.cut {
    color: #ff4444;
  }

  .node-icon.engrave {
    color: #4444ff;
  }

  .node-icon.ignore {
    color: #666;
  }

  .node-label {
    flex: 1;
  }

  .badge, .speed-badge {
    background-color: #333;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
  }

  .separator {
    margin: 1rem 0 0.5rem 0;
    padding: 0.5rem;
    font-weight: bold;
    color: #999;
    font-size: 0.9rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .add-group-btn {
    background-color: #646cff;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.2rem 0.6rem;
    cursor: pointer;
    font-size: 1rem;
    font-weight: bold;
  }

  .add-group-btn:hover {
    background-color: #535bf2;
  }

  .new-group-input {
    display: flex;
    gap: 0.5rem;
    margin: 0 1rem 0.5rem 1rem;
  }

  .new-group-input input {
    flex: 1;
    padding: 0.5rem;
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 4px;
    color: white;
  }

  .new-group-input button {
    padding: 0.5rem 1rem;
    background-color: #646cff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .new-group-input button:hover {
    background-color: #535bf2;
  }

  .paths-container {
    margin-left: 2rem;
  }

  .paths-container.group-paths {
    margin-left: 2rem;
  }

  .path-node.draggable {
    cursor: move;
    transition: background-color 0.2s;
  }

  .path-node.draggable:active {
    cursor: grabbing;
  }

  .drag-handle {
    color: #666;
    font-size: 0.8rem;
    margin-right: 0.3rem;
    cursor: grab;
  }

  .drag-handle:active {
    cursor: grabbing;
  }

  .remove-from-group-btn {
    background-color: #444;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 0.2rem 0.5rem;
    cursor: pointer;
    font-size: 0.9rem;
    margin-left: 0.5rem;
  }

  .remove-from-group-btn:hover {
    background-color: #666;
  }

  .empty-message {
    margin-left: 2rem;
    padding: 0.5rem;
    color: #666;
    font-size: 0.9rem;
    font-style: italic;
  }

  .path-settings-panel {
    border-top: 1px solid #333;
    padding: 1rem;
    background-color: #0a0a0a;
  }
</style>
