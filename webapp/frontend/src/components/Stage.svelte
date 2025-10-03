<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type { Project } from '../lib/api'
  import { laserPosition, executionStatus } from '../lib/stores'

  export let project: Project

  let canvas: HTMLCanvasElement
  let ctx: CanvasRenderingContext2D | null

  const CANVAS_WIDTH = 800
  const CANVAS_HEIGHT = 600
  const WORK_AREA_WIDTH = 300
  const WORK_AREA_HEIGHT = 200

  onMount(() => {
    ctx = canvas.getContext('2d')
    drawStage()
  })

  $: if (ctx) {
    drawStage()
  }

  $: if ($laserPosition && ctx) {
    drawStage()
  }

  function drawStage() {
    if (!ctx) return

    ctx.fillStyle = '#0a0a0a'
    ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT)

    ctx.strokeStyle = '#333'
    ctx.lineWidth = 2
    ctx.strokeRect(50, 50, CANVAS_WIDTH - 100, CANVAS_HEIGHT - 100)

    ctx.strokeStyle = '#555'
    ctx.lineWidth = 1
    const gridSize = 50
    for (let x = 50; x <= CANVAS_WIDTH - 50; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 50)
      ctx.lineTo(x, CANVAS_HEIGHT - 50)
      ctx.stroke()
    }
    for (let y = 50; y <= CANVAS_HEIGHT - 50; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(50, y)
      ctx.lineTo(CANVAS_WIDTH - 50, y)
      ctx.stroke()
    }

    project.svg_files.forEach(svg => {
      svg.paths.forEach(path => {
        if (path.action === 'ignore') return

        ctx!.strokeStyle = path.action === 'cut' ? '#ff4444' : '#4444ff'
        ctx!.lineWidth = 2
        ctx!.globalAlpha = 0.5

        ctx!.beginPath()
        const startX = 50 + Math.random() * (CANVAS_WIDTH - 100)
        const startY = 50 + Math.random() * (CANVAS_HEIGHT - 100)
        ctx!.moveTo(startX, startY)
        ctx!.lineTo(startX + 50, startY + 50)
        ctx!.stroke()

        ctx!.globalAlpha = 1.0
      })
    })

    const laserX = 50 + ($laserPosition.x / WORK_AREA_WIDTH) * (CANVAS_WIDTH - 100)
    const laserY = 50 + ($laserPosition.y / WORK_AREA_HEIGHT) * (CANVAS_HEIGHT - 100)

    ctx.fillStyle = $executionStatus.running ? '#ff0000' : '#00ff00'
    ctx.beginPath()
    ctx.arc(laserX, laserY, 8, 0, Math.PI * 2)
    ctx.fill()

    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2
    ctx.beginPath()
    ctx.arc(laserX, laserY, 8, 0, Math.PI * 2)
    ctx.stroke()

    ctx.beginPath()
    ctx.moveTo(laserX - 15, laserY)
    ctx.lineTo(laserX + 15, laserY)
    ctx.stroke()
    ctx.beginPath()
    ctx.moveTo(laserX, laserY - 15)
    ctx.lineTo(laserX, laserY + 15)
    ctx.stroke()
  }

  onDestroy(() => {
  })
</script>

<div class="stage">
  <canvas bind:this={canvas} width={CANVAS_WIDTH} height={CANVAS_HEIGHT}></canvas>
  
  <div class="info">
    <div>Position: X={$laserPosition.x.toFixed(2)}mm Y={$laserPosition.y.toFixed(2)}mm</div>
    {#if $executionStatus.running}
      <div class="status-running">Ausführung läuft... ({$executionStatus.progress}%)</div>
    {/if}
  </div>
</div>

<style>
  .stage {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 1rem;
  }

  canvas {
    border: 1px solid #333;
    border-radius: 4px;
  }

  .info {
    margin-top: 1rem;
    display: flex;
    gap: 2rem;
    color: #ccc;
    font-family: monospace;
  }

  .status-running {
    color: #ff4444;
    font-weight: bold;
  }
</style>
