<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type { Project } from '../lib/api'
  import { laserPosition, executionStatus, animationState } from '../lib/stores'

  export let project: Project

  let canvas: HTMLCanvasElement
  let ctx: CanvasRenderingContext2D | null
  let zoom = 1.0
  let panX = 0
  let panY = 0
  let isPanning = false
  let lastMouseX = 0
  let lastMouseY = 0

  const WORK_AREA_WIDTH = 300
  const WORK_AREA_HEIGHT = 200
  const RULER_SIZE = 30

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

  $: if ($animationState && ctx) {
    drawStage()
  }

  function handleWheel(e: WheelEvent) {
    e.preventDefault()
    const delta = e.deltaY > 0 ? 0.9 : 1.1
    zoom = Math.max(0.1, Math.min(5, zoom * delta))
    drawStage()
  }

  function handleMouseDown(e: MouseEvent) {
    if (e.ctrlKey || e.metaKey) {
      isPanning = true
      lastMouseX = e.clientX
      lastMouseY = e.clientY
      e.preventDefault()
    }
  }

  function handleMouseMove(e: MouseEvent) {
    if (isPanning) {
      const dx = e.clientX - lastMouseX
      const dy = e.clientY - lastMouseY
      panX += dx
      panY += dy
      lastMouseX = e.clientX
      lastMouseY = e.clientY
      drawStage()
    }
  }

  function handleMouseUp() {
    isPanning = false
  }

  function zoomIn() {
    zoom = Math.min(5, zoom * 1.2)
    drawStage()
  }

  function zoomOut() {
    zoom = Math.max(0.1, zoom / 1.2)
    drawStage()
  }

  function drawStage() {
    if (!ctx || !canvas) return

    ctx.fillStyle = '#999999'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    ctx.save()
    ctx.translate(panX + RULER_SIZE, panY + RULER_SIZE)
    ctx.scale(zoom, zoom)

    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, WORK_AREA_WIDTH, WORK_AREA_HEIGHT)

    ctx.strokeStyle = '#333'
    ctx.lineWidth = 2 / zoom
    ctx.strokeRect(0, 0, WORK_AREA_WIDTH, WORK_AREA_HEIGHT)

    ctx.strokeStyle = '#ddd'
    ctx.lineWidth = 1 / zoom
    const gridSize = 10
    for (let x = gridSize; x < WORK_AREA_WIDTH; x += gridSize) {
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, WORK_AREA_HEIGHT)
      ctx.stroke()
    }
    for (let y = gridSize; y < WORK_AREA_HEIGHT; y += gridSize) {
      ctx.beginPath()
      ctx.moveTo(0, y)
      ctx.lineTo(WORK_AREA_WIDTH, y)
      ctx.stroke()
    }

    project.svg_files.forEach(svg => {
      svg.paths.forEach(path => {
        if (path.action === 'ignore') return

        ctx!.strokeStyle = path.action === 'cut' ? '#ff4444' : '#4444ff'
        ctx!.lineWidth = 2 / zoom
        ctx!.globalAlpha = 0.6

        ctx!.beginPath()
        const startX = Math.random() * WORK_AREA_WIDTH
        const startY = Math.random() * WORK_AREA_HEIGHT
        ctx!.moveTo(startX, startY)
        
        for (let i = 0; i < 5; i++) {
          ctx!.lineTo(
            Math.random() * WORK_AREA_WIDTH,
            Math.random() * WORK_AREA_HEIGHT
          )
        }
        ctx!.stroke()
        ctx!.globalAlpha = 1.0
      })
    })

    ctx.fillStyle = $executionStatus.running ? '#ff0000' : '#00ff00'
    ctx.beginPath()
    ctx.arc($laserPosition.x, $laserPosition.y, 5 / zoom, 0, Math.PI * 2)
    ctx.fill()

    ctx.strokeStyle = '#ffffff'
    ctx.lineWidth = 2 / zoom
    ctx.beginPath()
    ctx.arc($laserPosition.x, $laserPosition.y, 5 / zoom, 0, Math.PI * 2)
    ctx.stroke()

    ctx.restore()

    drawRulers()
  }

  function drawRulers() {
    if (!ctx || !canvas) return

    ctx.fillStyle = '#666'
    ctx.fillRect(0, 0, canvas.width, RULER_SIZE)
    ctx.fillRect(0, 0, RULER_SIZE, canvas.height)

    ctx.fillStyle = '#ffffff'
    ctx.font = '10px monospace'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'

    for (let i = 0; i <= WORK_AREA_WIDTH; i += 50) {
      const x = RULER_SIZE + panX + i * zoom
      if (x >= RULER_SIZE && x <= canvas.width) {
        ctx.fillText(`${i}`, x, RULER_SIZE / 2)
      }
    }

    ctx.textAlign = 'right'
    for (let i = 0; i <= WORK_AREA_HEIGHT; i += 50) {
      const y = RULER_SIZE + panY + i * zoom
      if (y >= RULER_SIZE && y <= canvas.height) {
        ctx.fillText(`${i}`, RULER_SIZE - 5, y)
      }
    }
  }

  function toggleAnimation() {
    animationState.update(state => ({
      ...state,
      isPlaying: !state.isPlaying
    }))
  }

  function stopAnimation() {
    animationState.update(state => ({
      ...state,
      isPlaying: false,
      currentPathIndex: 0,
      currentPathProgress: 0
    }))
  }

  function changeSpeed(delta: number) {
    animationState.update(state => ({
      ...state,
      speed: Math.max(0.1, Math.min(5, state.speed + delta))
    }))
  }

  onDestroy(() => {
  })
</script>

<div class="stage">
  <canvas 
    bind:this={canvas} 
    width={800} 
    height={600}
    on:wheel={handleWheel}
    on:mousedown={handleMouseDown}
    on:mousemove={handleMouseMove}
    on:mouseup={handleMouseUp}
    on:mouseleave={handleMouseUp}
  ></canvas>
  
  <div class="zoom-controls">
    <button on:click={zoomOut}>−</button>
    <span>{Math.round(zoom * 100)}%</span>
    <button on:click={zoomIn}>+</button>
  </div>

  <div class="animation-controls">
    <button on:click={toggleAnimation}>
      {$animationState.isPlaying ? '⏸' : '▶️'}
    </button>
    <button on:click={stopAnimation}>⏹</button>
    <button on:click={() => changeSpeed(-0.1)}>−</button>
    <span>{$animationState.speed.toFixed(1)}x</span>
    <button on:click={() => changeSpeed(0.1)}>+</button>
  </div>

  <div class="progress-bar">
    <div class="progress-track">
      {#each project.svg_files as svg}
        {#each svg.paths as path, i}
          <div 
            class="progress-segment"
            class:active={i === $animationState.currentPathIndex}
            style="flex: 1"
          ></div>
        {/each}
      {/each}
    </div>
  </div>
</div>

<style>
  .stage {
    width: 100%;
    height: 100%;
    position: relative;
    background-color: #999999;
    overflow: hidden;
  }

  canvas {
    width: 100%;
    height: 100%;
    cursor: crosshair;
  }

  canvas:active {
    cursor: grabbing;
  }

  .zoom-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    display: flex;
    gap: 8px;
    align-items: center;
    background: rgba(0, 0, 0, 0.7);
    padding: 8px 12px;
    border-radius: 4px;
    color: #fff;
  }

  .zoom-controls button {
    background: #333;
    border: 1px solid #555;
    color: #fff;
    width: 28px;
    height: 28px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .zoom-controls button:hover {
    background: #444;
  }

  .zoom-controls span {
    min-width: 50px;
    text-align: center;
    font-size: 14px;
  }

  .animation-controls {
    position: absolute;
    bottom: 60px;
    right: 10px;
    display: flex;
    gap: 8px;
    align-items: center;
    background: rgba(0, 0, 0, 0.7);
    padding: 8px 12px;
    border-radius: 4px;
    color: #fff;
  }

  .animation-controls button {
    background: #333;
    border: 1px solid #555;
    color: #fff;
    width: 32px;
    height: 32px;
    border-radius: 4px;
    cursor: pointer;
    font-size: 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .animation-controls button:hover {
    background: #444;
  }

  .animation-controls span {
    min-width: 40px;
    text-align: center;
    font-size: 14px;
  }

  .progress-bar {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    height: 40px;
    background: rgba(0, 0, 0, 0.7);
    padding: 8px;
  }

  .progress-track {
    display: flex;
    height: 100%;
    gap: 2px;
  }

  .progress-segment {
    background: #333;
    border-radius: 2px;
    transition: background 0.2s;
  }

  .progress-segment.active {
    background: #646cff;
  }

  .progress-segment:hover {
    background: #555;
    cursor: pointer;
  }
</style>
