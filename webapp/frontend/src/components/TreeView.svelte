<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte'
  import type { Project, SVGFile, PathConfig, VirtualGroup } from '../lib/api'
  import { pathAPI, virtualGroupAPI, projectDefaultsAPI, svgTransformAPI } from '../lib/api'

  export let project: Project

  const dispatch = createEventDispatcher()

  const STORAGE_KEY = 'k40-tree-collapsed-nodes'
  
  let collapsedNodes: Set<string> = (() => {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      try {
        return new Set(JSON.parse(stored))
      } catch (e) {
        console.error('Failed to parse stored collapse state:', e)
      }
    }
    return new Set()
  })()
  
  let expandedTransforms: Set<string> = new Set()
  let fileInput: HTMLInputElement
  let selectedPathId: string | null = null

  function toggleExpand(nodeId: string) {
    if (collapsedNodes.has(nodeId)) {
      collapsedNodes.delete(nodeId)
    } else {
      collapsedNodes.add(nodeId)
    }
    collapsedNodes = new Set(collapsedNodes)
    localStorage.setItem(STORAGE_KEY, JSON.stringify([...collapsedNodes]))
  }

  function isExpanded(nodeId: string, nodes: Set<string>): boolean {
    return !nodes.has(nodeId)
  }

  function toggleTransform(svgId: string) {
    if (expandedTransforms.has(svgId)) {
      expandedTransforms.delete(svgId)
    } else {
      expandedTransforms.add(svgId)
    }
    expandedTransforms = new Set(expandedTransforms)
  }

  async function updateProjectDefault(field: string, value: any) {
    try {
      await projectDefaultsAPI.update(project.id, { [field]: value })
      dispatch('update')
    } catch (error) {
      console.error('Failed to update project defaults:', error)
    }
  }

  async function updateGroupDefault(groupId: string, field: string, value: any) {
    try {
      await virtualGroupAPI.update(project.id, groupId, { [field]: value })
      dispatch('update')
    } catch (error) {
      console.error('Failed to update group defaults:', error)
    }
  }

  async function updatePathConfig(pathId: string, field: string, value: any) {
    try {
      await pathAPI.update(project.id, pathId, { [field]: value })
      dispatch('update')
    } catch (error: any) {
      console.error('Failed to update path config:', error)
      console.error('Error response:', JSON.stringify(error.response?.data, null, 2))
    }
  }

  async function updateSvgTransform(svgId: string, field: string, value: number) {
    try {
      await svgTransformAPI.update(project.id, svgId, { [field]: value })
      dispatch('update')
    } catch (error) {
      console.error('Failed to update SVG transform:', error)
    }
  }

  function handleFileUpload() {
    fileInput.click()
  }

  async function onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement
    if (!input.files || input.files.length === 0) return

    for (const file of Array.from(input.files)) {
      if (file.name.endsWith('.svg')) {
        try {
          const { svgAPI } = await import('../lib/api')
          await svgAPI.upload(project.id, file)
        } catch (error) {
          console.error('Failed to upload SVG:', error)
        }
      }
    }
    dispatch('update')
    input.value = ''
  }

  async function handleDrop(event: DragEvent) {
    event.preventDefault()
    if (!event.dataTransfer?.files) return

    for (const file of Array.from(event.dataTransfer.files)) {
      if (file.name.endsWith('.svg')) {
        try {
          const { svgAPI } = await import('../lib/api')
          await svgAPI.upload(project.id, file)
        } catch (error) {
          console.error('Failed to upload SVG:', error)
        }
      }
    }
    dispatch('update')
  }

  function handleDragOver(event: DragEvent) {
    event.preventDefault()
  }

  async function createVirtualGroup() {
    const name = prompt('Name der virtuellen Gruppe:')
    if (!name) return

    try {
      await virtualGroupAPI.create(project.id, name)
      dispatch('update')
    } catch (error) {
      console.error('Failed to create virtual group:', error)
    }
  }

  function selectPath(pathId: string) {
    selectedPathId = pathId
    dispatch('pathSelected', { pathId })
  }

  function getPathsForGroup(groupId: string): PathConfig[] {
    const group = project.virtual_groups.find(g => g.id === groupId)
    if (!group) return []
    return project.svg_files.flatMap(svg => 
      svg.paths.filter(p => p.virtual_group_id === groupId)
    )
  }
</script>

<div class="tree-container" on:drop={handleDrop} on:dragover={handleDragOver}>
  <div class="tree-header">
    <button class="create-group-btn" on:click={createVirtualGroup}>+ Gruppe</button>
    <button class="upload-btn" on:click={handleFileUpload}>+ SVG</button>
    <input
      bind:this={fileInput}
      type="file"
      accept=".svg"
      multiple
      style="display: none"
      on:change={onFileSelected}
    />
  </div>

  <div class="tree-table">
    <div class="tree-row tree-row-header">
      <div class="col-handle"></div>
      <div class="col-name">Name</div>
      <div class="col-action">Aktion</div>
      <div class="col-speed">Geschw.</div>
      <div class="col-reps">Wdh.</div>
    </div>

    <div class="tree-row tree-row-project">
      <div class="col-handle">⋮⋮</div>
      <div class="col-name" on:click={() => toggleExpand('project')}>
        <span class="expand-icon">{isExpanded('project', collapsedNodes) ? '▼' : '▶'}</span>
        <span class="node-name">{project.name}</span>
      </div>
      <div class="col-action">
        <select
          value={project.default_action || 'cut'}
          on:change={(e) => updateProjectDefault('default_action', e.currentTarget.value)}
        >
          <option value="cut">✂️ Cut</option>
          <option value="engrave">🔨 Engrave</option>
          <option value="ignore">⊘ Ignore</option>
        </select>
      </div>
      <div class="col-speed">
        <input
          type="number"
          value={project.default_speed_mm_s || 100}
          min="0.1"
          max="500"
          step="0.1"
          on:change={(e) => updateProjectDefault('default_speed_mm_s', parseFloat(e.currentTarget.value))}
        />
      </div>
      <div class="col-reps">
        <input
          type="number"
          value={project.default_repetitions || 1}
          min="1"
          max="100"
          on:change={(e) => updateProjectDefault('default_repetitions', parseInt(e.currentTarget.value))}
        />
      </div>
    </div>

    {#if isExpanded('project', collapsedNodes)}
      {#each project.virtual_groups as group}
        <div class="tree-row tree-row-group" style="padding-left: 20px">
          <div class="col-handle">⋮⋮</div>
          <div class="col-name" on:click={() => toggleExpand(`group-${group.id}`)}>
            <span class="expand-icon">{isExpanded(`group-${group.id}`, collapsedNodes) ? '▼' : '▶'}</span>
            <span class="node-name">📁 {group.name}</span>
          </div>
          <div class="col-action">
            <div class="action-buttons">
              <button
                class="action-btn"
                class:active={group.default_action === null || group.default_action === undefined}
                title="Inherit from project"
                on:click={() => updateGroupDefault(group.id, 'default_action', null)}
              >⬆️</button>
              <button
                class="action-btn"
                class:active={group.default_action === 'cut'}
                title="Cut"
                on:click={() => updateGroupDefault(group.id, 'default_action', 'cut')}
              >✂️</button>
              <button
                class="action-btn"
                class:active={group.default_action === 'engrave'}
                title="Engrave"
                on:click={() => updateGroupDefault(group.id, 'default_action', 'engrave')}
              >🔨</button>
              <button
                class="action-btn"
                class:active={group.default_action === 'ignore'}
                title="Ignore"
                on:click={() => updateGroupDefault(group.id, 'default_action', 'ignore')}
              >⊘</button>
            </div>
          </div>
          {#if group.default_action !== null && group.default_action !== undefined}
            <div class="col-speed">
              <input
                type="number"
                placeholder="⬆️"
                value={group.default_speed_mm_s ?? ''}
                min="0.1"
                max="500"
                step="0.1"
                on:change={(e) => updateGroupDefault(group.id, 'default_speed_mm_s', e.currentTarget.value ? parseFloat(e.currentTarget.value) : null)}
              />
            </div>
            <div class="col-reps">
              <input
                type="number"
                placeholder="⬆️"
                value={group.default_repetitions ?? ''}
                min="1"
                max="100"
                on:change={(e) => updateGroupDefault(group.id, 'default_repetitions', e.currentTarget.value ? parseInt(e.currentTarget.value) : null)}
              />
            </div>
          {:else}
            <div class="col-speed"></div>
            <div class="col-reps"></div>
          {/if}
          <div class="col-gear"></div>
        </div>

        {#if isExpanded(`group-${group.id}`, collapsedNodes)}
          {#each getPathsForGroup(group.id) as path}
            <div
              class="tree-row tree-row-path"
              class:selected={selectedPathId === path.path_id}
              style="padding-left: 40px"
              on:click={() => selectPath(path.path_id)}
            >
              <div class="col-handle">⋮⋮</div>
              <div class="col-name">
                <span class="node-name">🔹 {path.path_id}</span>
              </div>
              <div class="col-action">
                <div class="action-buttons">
                  <button
                    class="action-btn"
                    class:active={path.action === null || path.action === undefined}
                    title="Inherit from group"
                    on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', null)}
                  >⬆️</button>
                  <button
                    class="action-btn"
                    class:active={path.action === 'cut'}
                    title="Cut"
                    on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'cut')}
                  >✂️</button>
                  <button
                    class="action-btn"
                    class:active={path.action === 'engrave'}
                    title="Engrave"
                    on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'engrave')}
                  >🔨</button>
                  <button
                    class="action-btn"
                    class:active={path.action === 'ignore'}
                    title="Ignore"
                    on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'ignore')}
                  >⊘</button>
                </div>
              </div>
              {#if path.action !== null && path.action !== undefined}
                <div class="col-speed">
                  <input
                    type="number"
                    placeholder="⬆️"
                    value={path.speed_mm_s ?? ''}
                    min="0.1"
                    max="500"
                    step="0.1"
                    on:click|stopPropagation
                    on:change={(e) => updatePathConfig(path.path_id, 'speed_mm_s', e.currentTarget.value ? parseFloat(e.currentTarget.value) : null)}
                  />
                </div>
                <div class="col-reps">
                  <input
                    type="number"
                    placeholder="⬆️"
                    value={path.repetitions ?? ''}
                    min="1"
                    max="100"
                    on:click|stopPropagation
                    on:change={(e) => updatePathConfig(path.path_id, 'repetitions', e.currentTarget.value ? parseInt(e.currentTarget.value) : null)}
                  />
                </div>
              {:else}
                <div class="col-speed"></div>
                <div class="col-reps"></div>
              {/if}
              <div class="col-gear"></div>
            </div>
          {/each}
        {/if}
      {/each}

      {#each project.svg_files as svgFile}
        <div class="tree-row tree-row-svg" style="padding-left: 20px">
          <div class="col-handle">⋮⋮</div>
          <div class="col-name" on:click={() => toggleExpand(`svg-${svgFile.id}`)}>
            <span class="expand-icon">{isExpanded(`svg-${svgFile.id}`, collapsedNodes) ? '▼' : '▶'}</span>
            <span class="node-name">📄 {svgFile.filename}</span>
          </div>
          <div class="col-action"></div>
          <div class="col-speed"></div>
          <div class="col-reps"></div>
          <div class="col-gear">
            <button 
              class="gear-btn" 
              class:active={expandedTransforms.has(svgFile.id)}
              on:click={() => toggleTransform(svgFile.id)}
              title="Transform settings"
            >⚙️</button>
          </div>
        </div>
        
        {#if expandedTransforms.has(svgFile.id)}
          <div class="tree-row tree-row-transform" style="padding-left: 40px">
            <div class="col-handle"></div>
            <div class="transform-controls">
              <label>
                X: <input 
                  type="number" 
                  value={svgFile.transform?.position_x ?? 0} 
                  step="0.1"
                  on:change={(e) => updateSvgTransform(svgFile.id, 'position_x', parseFloat(e.currentTarget.value))}
                />
              </label>
              <label>
                Y: <input 
                  type="number" 
                  value={svgFile.transform?.position_y ?? 0} 
                  step="0.1"
                  on:change={(e) => updateSvgTransform(svgFile.id, 'position_y', parseFloat(e.currentTarget.value))}
                />
              </label>
              <label>
                Scale: <input 
                  type="number" 
                  value={svgFile.transform?.scale_x ?? 1.0} 
                  step="0.01"
                  min="0.01"
                  on:change={(e) => {
                    const val = parseFloat(e.currentTarget.value)
                    updateSvgTransform(svgFile.id, 'scale_x', val)
                    updateSvgTransform(svgFile.id, 'scale_y', val)
                  }}
                />
              </label>
              <label>
                Rotation: <input 
                  type="number" 
                  value={svgFile.transform?.rotation ?? 0} 
                  step="1"
                  on:change={(e) => updateSvgTransform(svgFile.id, 'rotation', parseFloat(e.currentTarget.value))}
                /> °
              </label>
            </div>
          </div>
        {/if}

        {#if isExpanded(`svg-${svgFile.id}`, collapsedNodes)}
          {#each svgFile.paths as path}
            {#if !path.virtual_group_id}
              <div
                class="tree-row tree-row-path"
                class:selected={selectedPathId === path.path_id}
                style="padding-left: 40px"
                on:click={() => selectPath(path.path_id)}
              >
                <div class="col-handle">⋮⋮</div>
                <div class="col-name">
                  <span class="node-name">🔹 {path.path_id}</span>
                </div>
                <div class="col-action">
                  <div class="action-buttons">
                    <button
                      class="action-btn"
                      class:active={path.action === null || path.action === undefined}
                      title="Inherit from project"
                      on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', null)}
                    >⬆️</button>
                    <button
                      class="action-btn"
                      class:active={path.action === 'cut'}
                      title="Cut"
                      on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'cut')}
                    >✂️</button>
                    <button
                      class="action-btn"
                      class:active={path.action === 'engrave'}
                      title="Engrave"
                      on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'engrave')}
                    >🔨</button>
                    <button
                      class="action-btn"
                      class:active={path.action === 'ignore'}
                      title="Ignore"
                      on:click|stopPropagation={() => updatePathConfig(path.path_id, 'action', 'ignore')}
                    >⊘</button>
                  </div>
                </div>
                {#if path.action !== null && path.action !== undefined}
                  <div class="col-speed">
                    <input
                      type="number"
                      placeholder="⬆️"
                      value={path.speed_mm_s ?? ''}
                      min="0.1"
                      max="500"
                      step="0.1"
                      on:click|stopPropagation
                      on:change={(e) => updatePathConfig(path.path_id, 'speed_mm_s', e.currentTarget.value ? parseFloat(e.currentTarget.value) : null)}
                    />
                  </div>
                  <div class="col-reps">
                    <input
                      type="number"
                      placeholder="⬆️"
                      value={path.repetitions ?? ''}
                      min="1"
                      max="100"
                      on:click|stopPropagation
                      on:change={(e) => updatePathConfig(path.path_id, 'repetitions', e.currentTarget.value ? parseInt(e.currentTarget.value) : null)}
                    />
                  </div>
                {:else}
                  <div class="col-speed"></div>
                  <div class="col-reps"></div>
                {/if}
                <div class="col-gear"></div>
              </div>
            {/if}
          {/each}
        {/if}
      {/each}
    {/if}
  </div>
</div>

<style>
  .tree-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #1a1a1a;
    color: #e0e0e0;
    overflow: hidden;
  }

  .tree-header {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    padding: 8px;
    border-bottom: 1px solid #333;
  }

  .upload-btn,
  .create-group-btn {
    padding: 4px 12px;
    background: #2a2a2a;
    border: 1px solid #444;
    color: #e0e0e0;
    cursor: pointer;
    border-radius: 4px;
    font-size: 12px;
  }

  .upload-btn:hover,
  .create-group-btn:hover {
    background: #333;
  }

  .tree-table {
    flex: 1;
    overflow-y: auto;
    font-size: 13px;
  }

  .tree-row {
    display: grid;
    grid-template-columns: 30px 1fr 160px 80px 60px 30px;
    gap: 4px;
    align-items: center;
    padding: 4px 8px;
    border-bottom: 1px solid #2a2a2a;
    min-height: 32px;
  }

  .tree-row-header {
    background: #252525;
    font-weight: bold;
    position: sticky;
    top: 0;
    z-index: 10;
    border-bottom: 2px solid #444;
  }

  .tree-row-project {
    background: #2a2a2a;
    font-weight: bold;
  }

  .tree-row-group {
    background: #222;
  }

  .tree-row-svg {
    background: #1e1e1e;
  }

  .tree-row-path {
    background: #1a1a1a;
    cursor: pointer;
  }

  .tree-row-path:hover {
    background: #252525;
  }

  .tree-row-path.selected {
    background: #2d4a6d;
  }

  .col-handle {
    cursor: grab;
    color: #666;
    text-align: center;
    user-select: none;
  }

  .col-name {
    display: flex;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    overflow: hidden;
  }

  .expand-icon {
    font-size: 10px;
    width: 12px;
    display: inline-block;
  }

  .node-name {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .action-buttons {
    display: flex;
    gap: 2px;
  }

  .action-btn {
    padding: 2px 6px;
    background: #2a2a2a;
    border: 1px solid #444;
    color: #e0e0e0;
    cursor: pointer;
    border-radius: 3px;
    font-size: 14px;
    transition: background 0.2s;
    flex: 1;
  }

  .action-btn:hover {
    background: #333;
  }

  .action-btn.active {
    background: #4a6fa5;
    border-color: #6a8fc5;
  }

  .col-gear {
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .gear-btn {
    padding: 2px 6px;
    background: transparent;
    border: 1px solid transparent;
    color: #888;
    cursor: pointer;
    border-radius: 3px;
    font-size: 14px;
  }

  .gear-btn:hover {
    color: #e0e0e0;
    border-color: #444;
  }

  .gear-btn.active {
    background: #2a2a2a;
    border-color: #4a6fa5;
    color: #e0e0e0;
  }

  .tree-row-transform {
    background: #1a1a1a;
    padding: 8px;
  }

  .transform-controls {
    display: flex;
    gap: 12px;
    align-items: center;
    flex-wrap: wrap;
    grid-column: 2 / -1;
  }

  .transform-controls label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
  }

  .transform-controls input {
    width: 70px;
    background: #2a2a2a;
    color: #e0e0e0;
    border: 1px solid #444;
    padding: 2px 4px;
    border-radius: 3px;
  }

  .col-speed input,
  .col-reps input {
    width: 100%;
    background: #1a1a1a;
    color: #e0e0e0;
    border: 1px solid #444;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 12px;
  }

  .col-speed input::placeholder,
  .col-reps input::placeholder {
    color: #666;
    font-style: italic;
  }

  input[type="number"]::-webkit-inner-spin-button,
  input[type="number"]::-webkit-outer-spin-button {
    opacity: 1;
  }
</style>
