/** Minimal React wrapper around plotly.js (no third-party wrapper dependency). */
import { useEffect, useRef } from 'react'
import Plotly from 'plotly.js-dist-min'
import type { Config, Data, Layout } from 'plotly.js-dist-min'

interface PlotProps {
  data: Data[]
  layout?: Partial<Layout>
  height?: number
  ariaLabel?: string
}

const BASE_LAYOUT: Partial<Layout> = {
  margin: { l: 56, r: 16, t: 16, b: 56 },
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  font: { family: 'Inter, system-ui, sans-serif', size: 12, color: '#334155' },
  colorway: ['#2563eb', '#0ea5e9', '#7c3aed', '#059669', '#d97706', '#db2777'],
  xaxis: { gridcolor: '#e2e8f0', zerolinecolor: '#e2e8f0' },
  yaxis: { gridcolor: '#e2e8f0', zerolinecolor: '#e2e8f0' },
}

const CONFIG: Partial<Config> = { displayModeBar: false, responsive: true }

export function Plot({ data, layout, height = 320, ariaLabel }: PlotProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    void Plotly.react(node, data, { ...BASE_LAYOUT, ...layout, height }, CONFIG)
    return () => {
      Plotly.purge(node)
    }
  }, [data, layout, height])

  return <div className="plot" ref={ref} role="img" aria-label={ariaLabel} />
}
