<script lang="ts">
  import { laserAPI } from '../lib/api'
  import { selectedProjectId, laserPosition } from '../lib/stores'

  let moving = false
  let homing = false
  let executing = false
  let error = ''

  const moveAmount = 10

  async function move(dx: number, dy: number) {
    moving = true
    error = ''
    try {
      const response = await laserAPI.move(dx, dy)
      laserPosition.set({ x: response.data.x, y: response.data.y })
    } catch (e: any) {
      error = e.message || 'Bewegungsfehler'
    } finally {
      moving = false
    }
  }

  async function home() {
    homing = true
    error = ''
    try {
      const response = await laserAPI.home()
      laserPosition.set({ x: response.data.x, y: response.data.y })
    } catch (e: any) {
      error = e.message || 'Home-Fehler'
    } finally {
      homing = false
    }
  }

  async function execute() {
    if (!$selectedProjectId) return
    
    executing = true
    error = ''
    try {
      await laserAPI.execute($selectedProjectId)
    } catch (e: any) {
      error = e.message || 'Ausführungsfehler'
    } finally {
      executing = false
    }
  }

  async function stop() {
    try {
      await laserAPI.stop()
    } catch (e: any) {
      error = e.message || 'Stop-Fehler'
    }
  }
</script>

<div class="laser-controls">
  <h3>Laser-Steuerung</h3>

  {#if error}
    <div class="error">{error}</div>
  {/if}

  <div class="control-grid">
    <div class="movement-controls">
      <div class="move-row">
        <button on:click={() => move(0, moveAmount)} disabled={moving}>↑</button>
      </div>
      <div class="move-row">
        <button on:click={() => move(-moveAmount, 0)} disabled={moving}>←</button>
        <button on:click={home} disabled={homing}>
          {homing ? '...' : '⌂'}
        </button>
        <button on:click={() => move(moveAmount, 0)} disabled={moving}>→</button>
      </div>
      <div class="move-row">
        <button on:click={() => move(0, -moveAmount)} disabled={moving}>↓</button>
      </div>
    </div>

    <div class="action-controls">
      <button class="execute-btn" on:click={execute} disabled={executing || !$selectedProjectId}>
        {executing ? 'Ausführung läuft...' : 'Projekt ausführen'}
      </button>
      <button class="stop-btn" on:click={stop}>
        Stop
      </button>
    </div>
  </div>
</div>

<style>
  .laser-controls {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  h3 {
    margin: 0;
  }

  .error {
    background-color: #ff4444;
    color: white;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.9rem;
  }

  .control-grid {
    display: flex;
    gap: 2rem;
    align-items: center;
  }

  .movement-controls {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .move-row {
    display: flex;
    gap: 0.5rem;
    justify-content: center;
  }

  .movement-controls button {
    width: 3rem;
    height: 3rem;
    font-size: 1.5rem;
  }

  .action-controls {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex: 1;
  }

  .execute-btn {
    background-color: #4caf50;
    font-weight: bold;
  }

  .execute-btn:hover:not(:disabled) {
    background-color: #45a049;
  }

  .stop-btn {
    background-color: #ff4444;
    font-weight: bold;
  }

  .stop-btn:hover {
    background-color: #cc0000;
  }
</style>
