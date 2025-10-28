<script lang="ts">
  import ProjectList from './components/ProjectList.svelte'
  import ProjectEditor from './components/ProjectEditor.svelte'
  import { selectedProjectId } from './lib/stores'
  import { projectsAPI, type Project } from './lib/api'
  import { onMount } from 'svelte'

  let currentView: 'list' | 'editor' = 'list'
  let currentProject: Project | null = null
  
  $: if ($selectedProjectId) {
    currentView = 'editor'
    loadCurrentProject($selectedProjectId)
  } else {
    currentProject = null
  }

  async function loadCurrentProject(id: string) {
    try {
      const response = await projectsAPI.get(id)
      currentProject = response.data
    } catch (error) {
      console.error('Failed to load project:', error)
    }
  }
  
  function backToList() {
    selectedProjectId.set(null)
    currentView = 'list'
  }
</script>

<main>
  <header>
    <h1>K40 - {currentProject?.name || 'Kein Projekt'}</h1>
    {#if currentView === 'editor'}
      <button on:click={backToList}>← Zurück zur Projektliste</button>
    {/if}
  </header>
  
  <div class="content">
    {#if currentView === 'list'}
      <ProjectList />
    {:else}
      <ProjectEditor />
    {/if}
  </div>
</main>

<style>
  main {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: #1a1a1a;
    border-bottom: 1px solid #333;
  }
  
  h1 {
    margin: 0;
    font-size: 1.5rem;
  }
  
  .content {
    flex: 1;
    overflow: auto;
    padding: 1rem;
  }
</style>
