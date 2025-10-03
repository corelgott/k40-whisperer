<script lang="ts">
  import { onMount } from 'svelte'
  import { projectsAPI, type Project } from '../lib/api'
  import { selectedProjectId } from '../lib/stores'

  let projects: Project[] = []
  let loading = true
  let error = ''
  let newProjectName = ''
  let creating = false

  onMount(async () => {
    await loadProjects()
  })

  async function loadProjects() {
    loading = true
    error = ''
    try {
      const response = await projectsAPI.list()
      projects = response.data
    } catch (e: any) {
      error = e.message || 'Fehler beim Laden der Projekte'
    } finally {
      loading = false
    }
  }

  async function createProject() {
    if (!newProjectName.trim()) return
    
    creating = true
    error = ''
    try {
      await projectsAPI.create(newProjectName)
      newProjectName = ''
      await loadProjects()
    } catch (e: any) {
      error = e.message || 'Fehler beim Erstellen des Projekts'
    } finally {
      creating = false
    }
  }

  async function deleteProject(id: string, event: Event) {
    event.stopPropagation()
    if (!confirm('Projekt wirklich löschen?')) return
    
    try {
      await projectsAPI.delete(id)
      await loadProjects()
    } catch (e: any) {
      error = e.message || 'Fehler beim Löschen des Projekts'
    }
  }

  function selectProject(id: string) {
    selectedProjectId.set(id)
  }
</script>

<div class="project-list">
  <h2>Projekte</h2>
  
  {#if error}
    <div class="error">{error}</div>
  {/if}
  
  <div class="create-project">
    <input 
      type="text" 
      placeholder="Neues Projekt..." 
      bind:value={newProjectName}
      on:keydown={(e) => e.key === 'Enter' && createProject()}
      disabled={creating}
    />
    <button on:click={createProject} disabled={creating || !newProjectName.trim()}>
      {creating ? 'Erstelle...' : 'Erstellen'}
    </button>
  </div>

  {#if loading}
    <div class="loading">Lade Projekte...</div>
  {:else if projects.length === 0}
    <div class="empty">Keine Projekte vorhanden. Erstelle ein neues Projekt.</div>
  {:else}
    <div class="projects">
      {#each projects as project}
        <div class="project-card" on:click={() => selectProject(project.id)}>
          <div class="project-info">
            <h3>{project.name}</h3>
            <p>{project.svg_files.length} SVG(s)</p>
            <small>{new Date(project.created_at).toLocaleString('de-DE')}</small>
          </div>
          <button class="delete-btn" on:click={(e) => deleteProject(project.id, e)}>
            ×
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .project-list {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
  }

  h2 {
    margin-bottom: 1.5rem;
  }

  .error {
    background-color: #ff4444;
    color: white;
    padding: 1rem;
    border-radius: 4px;
    margin-bottom: 1rem;
  }

  .create-project {
    display: flex;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .create-project input {
    flex: 1;
    padding: 0.75rem;
    border: 1px solid #333;
    border-radius: 4px;
    background-color: #1a1a1a;
    color: white;
    font-size: 1rem;
  }

  .loading, .empty {
    text-align: center;
    padding: 3rem;
    color: #999;
  }

  .projects {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
  }

  .project-card {
    background-color: #1a1a1a;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 1.5rem;
    cursor: pointer;
    transition: all 0.2s;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .project-card:hover {
    border-color: #646cff;
    transform: translateY(-2px);
  }

  .project-info {
    flex: 1;
  }

  .project-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.2rem;
  }

  .project-info p {
    margin: 0.25rem 0;
    color: #999;
  }

  .project-info small {
    color: #666;
  }

  .delete-btn {
    background-color: transparent;
    border: 1px solid #ff4444;
    color: #ff4444;
    width: 2rem;
    height: 2rem;
    border-radius: 4px;
    font-size: 1.5rem;
    line-height: 1;
    padding: 0;
    cursor: pointer;
  }

  .delete-btn:hover {
    background-color: #ff4444;
    color: white;
  }
</style>
