<script lang="ts">
  import ProjectList from './components/ProjectList.svelte'
  import ProjectEditor from './components/ProjectEditor.svelte'
  import { selectedProjectId } from './lib/stores'

  let currentView: 'list' | 'editor' = 'list'
  
  $: if ($selectedProjectId) {
    currentView = 'editor'
  }
  
  function backToList() {
    selectedProjectId.set(null)
    currentView = 'list'
  }
</script>

<main>
  <header>
    <h1>K40 Whisperer Web</h1>
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
