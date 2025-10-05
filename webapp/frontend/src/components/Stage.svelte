<script lang="ts">
  import { onMount, onDestroy } from 'svelte'
  import type { Project } from '../lib/api'
  import { laserPosition, executionStatus, animationState } from '../lib/stores'

  export let project: Project

  let canvas: HTMLCanvasElement | undefined
  let ctx: CanvasRenderingContext2D | null = null
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
    if (canvas) {
      ctx = canvas.getContext('2d')
      drawStage()
    }
  })

  onDestroy(() => {
    if (animationFrameId !== null) {
      cancelAnimationFrame(animationFrameId)
    }
  })

  $: if (ctx && project) {
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

  let coordTransform = { scaleX: 1, scaleY: 1, offsetX: 0, offsetY: 0 }
  
  $: if (project && project.svg_files) {
    const allCoords: Array<[number, number]> = []
    project.svg_files.forEach(svg => {
      svg.paths.forEach(path => {
        if (path.action !== 'ignore' && path.coordinates && path.coordinates.length > 0) {
          allCoords.push(...path.coordinates)
        }
      })
    })

    if (allCoords.length > 0) {
      const xs = allCoords.map(c => c[0])
      const ys = allCoords.map(c => c[1])
      const minX = Math.min(...xs)
      const maxX = Math.max(...xs)
      const minY = Math.min(...ys)
      const maxY = Math.max(...ys)
      
      const svgWidth = maxX - minX
      const svgHeight = maxY - minY
      
      const padding = 20
      const scaleX = (WORK_AREA_WIDTH - 2 * padding) / svgWidth
      const scaleY = (WORK_AREA_HEIGHT - 2 * padding) / svgHeight
      const scale = Math.min(scaleX, scaleY)
      
      const scaledWidth = svgWidth * scale
      const scaledHeight = svgHeight * scale
      const offsetX = (WORK_AREA_WIDTH - scaledWidth) / 2 - minX * scale
      const offsetY = (WORK_AREA_HEIGHT - scaledHeight) / 2 - minY * scale
      
      coordTransform = { scaleX: scale, scaleY: scale, offsetX, offsetY }
    }
  }

  function drawStage() {
    if (!canvas || !ctx) return

    ctx.clearRect(0, 0, canvas.width, canvas.height)
    ctx.save()
    
    ctx.fillStyle = '#999999'
    ctx.fillRect(0, 0, canvas.width, canvas.height)
    
    ctx.translate(panX, panY)
    ctx.scale(zoom, zoom)
    
    ctx.strokeStyle = '#666'
    ctx.lineWidth = 1 / zoom
    ctx.strokeRect(RULER_SIZE, RULER_SIZE, WORK_AREA_WIDTH, WORK_AREA_HEIGHT)
    
    ctx.fillStyle = '#ddd'
    ctx.font = `${10 / zoom}px sans-serif`
    for (let i = 0; i <= WORK_AREA_WIDTH; i += 50) {
      ctx.fillText(`${i}`, RULER_SIZE + i, RULER_SIZE - 5 / zoom)
      ctx.beginPath()
      ctx.moveTo(RULER_SIZE + i, RULER_SIZE)
      ctx.lineTo(RULER_SIZE + i, RULER_SIZE + 5 / zoom)
      ctx.stroke()
    }
    for (let i = 0; i <= WORK_AREA_HEIGHT; i += 50) {
      ctx.fillText(`${i}`, 5 / zoom, RULER_SIZE + i)
      ctx.beginPath()
      ctx.moveTo(RULER_SIZE, RULER_SIZE + i)
      ctx.lineTo(RULER_SIZE + 5 / zoom, RULER_SIZE + i)
      ctx.stroke()
    }
    
    if (!project || !project.svg_files) {
      ctx.restore()
      return
    }

    project.svg_files.forEach(svg => {
      svg.paths.forEach(path => {
        if (path.action === 'ignore') return
        if (!path.coordinates || path.coordinates.length === 0) return

        ctx!.strokeStyle = path.action === 'cut' ? '#ff4444' : '#4444ff'
        ctx!.lineWidth = 2 / zoom
        ctx!.globalAlpha = 0.6

        ctx!.beginPath()
        const coords = path.coordinates
        if (coords.length > 0) {
          const x0 = RULER_SIZE + coords[0][0] * coordTransform.scaleX + coordTransform.offsetX
          const y0 = RULER_SIZE + coords[0][1] * coordTransform.scaleY + coordTransform.offsetY
          ctx!.moveTo(x0, y0)
          
          for (let i = 1; i < coords.length; i++) {
            const x = RULER_SIZE + coords[i][0] * coordTransform.scaleX + coordTransform.offsetX
            const y = RULER_SIZE + coords[i][1] * coordTransform.scaleY + coordTransform.offsetY
            ctx!.lineTo(x, y)
          }
        }
        ctx!.stroke()
        ctx!.globalAlpha = 1.0
      })
    })
    
    if ($laserPosition) {
      const laserX = RULER_SIZE + $laserPosition.x * coordTransform.scaleX + coordTransform.offsetX
      const laserY = RULER_SIZE + $laserPosition.y * coordTransform.scaleY + coordTransform.offsetY
      
      ctx.fillStyle = '#ff0000'
      ctx.beginPath()
      ctx.arc(laserX, laserY, 3 / zoom, 0, Math.PI * 2)
      ctx.fill()
      
      ctx.strokeStyle = '#ff0000'
      ctx.lineWidth = 1 / zoom
      ctx.beginPath()
      ctx.moveTo(laserX - 10 / zoom, laserY)
      ctx.lineTo(laserX + 10 / zoom, laserY)
      ctx.moveTo(laserX, laserY - 10 / zoom)
      ctx.lineTo(laserX, laserY + 10 / zoom)
      ctx.stroke()
    }
    
    ctx.restore()
  }

  let animationFrameId: number | null = null
  let lastAnimationTime = 0
  let allPaths: any[] = []

  $: allPaths = (project && project.svg_files) ? project.svg_files.flatMap(svg => 
    svg.paths.filter(p => p.action !== 'ignore' && p.coordinates && p.coordinates.length > 0)
  ) : []

  function animationLoop(timestamp: number) {
    if (!$animationState.isPlaying) {
      animationFrameId = null
      return
    }

    const deltaTime = lastAnimationTime ? timestamp - lastAnimationTime : 0
    lastAnimationTime = timestamp

    if (allPaths.length === 0) {
      stopAnimation()
      return
    }

    const currentPath = allPaths[$animationState.currentPathIndex]
    if (!currentPath || !currentPath.coordinates) {
      stopAnimation()
      return
    }

    const pathLength = calculatePathLength(currentPath.coordinates)
    const progressIncrement = (deltaTime / 1000) * $animationState.speed * 50 / pathLength
    
    animationState.update(state => {
      let newProgress = state.currentPathProgress + progressIncrement
      let newPathIndex = state.currentPathIndex

      if (newProgress >= 1.0) {
        newProgress = 0
        newPathIndex++
        
        if (newPathIndex >= allPaths.length) {
          return {
            ...state,
            isPlaying: false,
            currentPathIndex: 0,
            currentPathProgress: 0
          }
        }
      }

      const path = allPaths[newPathIndex]
      if (path && path.coordinates) {
        const pos = interpolatePathPosition(path.coordinates, newProgress)
        laserPosition.set(pos)
      }

      return {
        ...state,
        currentPathIndex: newPathIndex,
        currentPathProgress: newProgress
      }
    })

    animationFrameId = requestAnimationFrame(animationLoop)
  }

  function calculatePathLength(coords: Array<[number, number]>): number {
    let length = 0
    for (let i = 1; i < coords.length; i++) {
      const dx = coords[i][0] - coords[i-1][0]
      const dy = coords[i][1] - coords[i-1][1]
      length += Math.sqrt(dx * dx + dy * dy)
    }
    return length || 1
  }

  function interpolatePathPosition(coords: Array<[number, number]>, progress: number): { x: number, y: number } {
    if (coords.length === 0) return { x: 0, y: 0 }
    if (coords.length === 1) return { x: coords[0][0], y: coords[0][1] }
    
    const totalLength = calculatePathLength(coords)
    const targetDistance = progress * totalLength
    
    let currentDistance = 0
    for (let i = 1; i < coords.length; i++) {
      const dx = coords[i][0] - coords[i-1][0]
      const dy = coords[i][1] - coords[i-1][1]
      const segmentLength = Math.sqrt(dx * dx + dy * dy)
      
      if (currentDistance + segmentLength >= targetDistance) {
        const segmentProgress = (targetDistance - currentDistance) / segmentLength
        return {
          x: coords[i-1][0] + dx * segmentProgress,
          y: coords[i-1][1] + dy * segmentProgress
        }
      }
      
      currentDistance += segmentLength
    }
    
    return { x: coords[coords.length-1][0], y: coords[coords.length-1][1] }
  }

  $: if ($animationState.isPlaying && !animationFrameId) {
    lastAnimationTime = 0
    animationFrameId = requestAnimationFrame(animationLoop)
  }

  function toggleAnimation() {
    animationState.update(state => {
      const newIsPlaying = !state.isPlaying
      if (newIsPlaying) {
        lastAnimationTime = 0
      }
      return {
        ...state,
        isPlaying: newIsPlaying
      }
    })
  }

  function stopAnimation() {
    animationState.update(state => ({
      ...state,
      isPlaying: false,
      currentPathIndex: 0,
      currentPathProgress: 0
    }))
    laserPosition.set({ x: 0, y: 0 })
  }

  function increaseSpeed() {
    animationState.update(state => ({
      ...state,
      speed: Math.min(5, state.speed + 0.5)
    }))
  }

  function decreaseSpeed() {
    animationState.update(state => ({
      ...state,
      speed: Math.max(0.5, state.speed - 0.5)
    }))
  }

  function handleProgressClick(pathIndex: number) {
    animationState.update(state => ({
      ...state,
      isPlaying: false,
      currentPathIndex: pathIndex,
      currentPathProgress: 0
    }))
    
    const path = allPaths[pathIndex]
    if (path && path.coordinates && path.coordinates.length > 0) {
      laserPosition.set({ x: path.coordinates[0][0], y: path.coordinates[0][1] })
    }
  }
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
      {$animationState.isPlaying ? '⏸' : '▶'}
    </button>
    <button on:click={stopAnimation}>⏹</button>
    <button on:click={decreaseSpeed}>−</button>
    <span>{$animationState.speed.toFixed(1)}x</span>
    <button on:click={increaseSpeed}>+</button>
  </div>
  
  <div class="progress-bar">
    <div class="progress-track">
      {#each allPaths as path, i}
        <div 
          class="progress-segment"
          class:active={i === $animationState.currentPathIndex}
          style="flex: 1"
          on:click={() => handleProgressClick(i)}
          role="button"
          tabindex="0"
        ></div>
      {/each}
    </div>
  </div>
</div>

<style>
  .stage {
    width: 100%;
    height: 100%;
    position: relative;
    background-color: #0a0a0a;
    display: flex;
    flex-direction: column;
  }

  canvas {
    flex: 1;
    cursor: crosshair;
  }

  .zoom-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    border-radius: 4px;
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .zoom-controls button {
    background-color: #333;
    color: white;
    border: none;
    padding: 0.3rem 0.6rem;
    cursor: pointer;
    border-radius: 3px;
    font-size: 1rem;
  }

  .zoom-controls button:hover {
    background-color: #555;
  }

  .zoom-controls span {
    color: white;
    min-width: 50px;
    text-align: center;
  }

  .animation-controls {
    position: absolute;
    bottom: 50px;
    right: 10px;
    background-color: rgba(0, 0, 0, 0.7);
    padding: 0.5rem;
    border-radius: 4px;
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }

  .animation-controls button {
    background-color: #333;
    color: white;
    border: none;
    padding: 0.4rem 0.7rem;
    cursor: pointer;
    border-radius: 3px;
    font-size: 1.2rem;
  }

  .animation-controls button:hover {
    background-color: #555;
  }

  .animation-controls span {
    color: white;
    min-width: 40px;
    text-align: center;
  }

  .progress-bar {
    height: 30px;
    background-color: #1a1a1a;
    border-top: 1px solid #333;
    padding: 5px;
  }

  .progress-track {
    height: 100%;
    display: flex;
    gap: 2px;
  }

  .progress-segment {
    background-color: #333;
    cursor: pointer;
    transition: background-color 0.2s;
  }

  .progress-segment:hover {
    background-color: #555;
  }

  .progress-segment.active {
    background-color: #646cff;
  }
</style>
