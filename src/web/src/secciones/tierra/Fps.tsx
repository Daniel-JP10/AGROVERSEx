// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef } from 'react'

/** Contador de fps solo en desarrollo; deja el último valor en window.__fps. */
export function Fps() {
  const el = useRef<HTMLDivElement>(null)
  useEffect(() => {
    let n = 0, t0 = performance.now(), r = 0
    const f = (t: number) => {
      n++
      if (t - t0 >= 500) {
        const fps = Math.round((n * 1000) / (t - t0))
        ;(window as unknown as { __fps: number }).__fps = fps
        if (el.current) el.current.textContent = `${fps} fps`
        n = 0; t0 = t
      }
      r = requestAnimationFrame(f)
    }
    r = requestAnimationFrame(f)
    return () => cancelAnimationFrame(r)
  }, [])
  return <div ref={el} className="fps" />
}
