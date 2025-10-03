<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import type { Project, PathConfig } from '../lib/api'
  import PathSettings from './PathSettings.svelte'

  export let project: Project

  const dispatch = createEventDispatcher()

  let selectedPathId: string | null = null
  let expandedSvgs = new Set<string>()

  function toggleSvg(svgId: string) {
    if (expandedSvgs.has(svgId)) {
      expandedSvgs.delete(svgId)
    } else {
      expandedSvgs.add(svgId)
    }
    expandedSvgs = expandedSvgs
  }

  function selectPath(pathId: string) {
    selectedPathId = pathId
  }

  function getPathConfig(svgId: string, pathId: string): PathConfig | undefined {
    const svg = project.svg_files.find(s => s.id === svgId)
    return svg?.paths.find(p => p.path_id === pathId)
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
        <span class="badge">{svg.paths.length}</span>
      </div>

      {#if expandedSvgs.has(svg.id)}
        {#each svg.paths as path}
          <div 
            class="path-node" 
            class:selected={selectedPathId === path.path_id}
            on:click={() => selectPath(path.path_id)}
          >
            <span class="node-icon" class:cut={path.action === 'cut'} class:engrave={path.action === 'engrave'} class:ignore={path.action === 'ignore'}>
              {path.action === 'cut' ? '✂' : path.action === 'engrave' ? '🖊' : '⊘'}
            </span>
            <span class="node-label">{path.path_id}</span>
            <span class="speed-badge">{path.speed_mm_s} mm/s</span>
          </div>
        {/each}
      {/if}
    {/each}

    {#if project.virtual_groups.length > 0}
      <div class="separator">Virtuelle Gruppen</div>
      {#each project.virtual_groups as group}
        <div class="group-node">
          <span class="node-icon">📦</span>
          <span class="node-label">{group.name}</span>
        </div>
      {/each}
    {/if}
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
  }

  .path-settings-panel {
    border-top: 1px solid #333;
    padding: 1rem;
    background-color: #0a0a0a;
  }
</style>
