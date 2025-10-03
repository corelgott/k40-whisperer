<script lang="ts">
  import { createEventDispatcher } from 'svelte'
  import { pathAPI } from '../lib/api'
  import type { PathConfig } from '../lib/api'
  import { selectedProjectId } from '../lib/stores'

  export let pathConfig: PathConfig

  const dispatch = createEventDispatcher()

  let action = pathConfig.action
  let speed = pathConfig.speed_mm_s
  let repetitions = pathConfig.repetitions
  let updating = false

  async function updatePath() {
    if (!$selectedProjectId) return

    updating = true
    try {
      await pathAPI.update($selectedProjectId, pathConfig.path_id, {
        action,
        speed_mm_s: speed,
        repetitions
      })
      dispatch('update')
    } catch (e) {
      console.error('Fehler beim Aktualisieren des Pfads:', e)
    } finally {
      updating = false
    }
  }
</script>

<div class="path-settings">
  <h3>Pfad-Einstellungen</h3>
  <p class="path-id">{pathConfig.path_id}</p>

  <div class="setting-group">
    <label>
      Aktion:
      <select bind:value={action} on:change={updatePath} disabled={updating}>
        <option value="ignore">Ignorieren</option>
        <option value="engrave">Gravieren</option>
        <option value="cut">Schneiden</option>
      </select>
    </label>
  </div>

  <div class="setting-group">
    <label>
      Geschwindigkeit (mm/s):
      <input 
        type="number" 
        bind:value={speed} 
        on:change={updatePath}
        min="0.1"
        max="100"
        step="0.1"
        disabled={updating}
      />
    </label>
  </div>

  <div class="setting-group">
    <label>
      Wiederholungen:
      <input 
        type="number" 
        bind:value={repetitions} 
        on:change={updatePath}
        min="1"
        max="100"
        disabled={updating}
      />
    </label>
  </div>

  {#if updating}
    <div class="updating">Aktualisiere...</div>
  {/if}
</div>

<style>
  .path-settings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  h3 {
    margin: 0;
    font-size: 1.1rem;
  }

  .path-id {
    color: #999;
    font-size: 0.9rem;
    margin: 0;
  }

  .setting-group {
    display: flex;
    flex-direction: column;
  }

  label {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    font-size: 0.9rem;
    color: #ccc;
  }

  select, input {
    padding: 0.5rem;
    border: 1px solid #333;
    border-radius: 4px;
    background-color: #1a1a1a;
    color: white;
    font-size: 1rem;
  }

  input[type="number"] {
    width: 100%;
  }

  .updating {
    color: #646cff;
    font-size: 0.9rem;
    text-align: center;
  }
</style>
