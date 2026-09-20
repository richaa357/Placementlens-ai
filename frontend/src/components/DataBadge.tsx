/** Colour coded provenance badge shown next to every data block. */
import type { DataType } from '../api'

const LABELS: Record<DataType, string> = {
  verified_historical: 'Verified historical data',
  current_posting: 'Current job posting',
  ai_analysis: 'AI analysis',
  user_provided: 'User provided',
  demo_data: 'Demonstration data',
}

export function DataBadge({ type, extra }: { type: DataType; extra?: string }) {
  return (
    <span className={`badge badge--${type.replace('_', '-')}`}>
      {LABELS[type]}
      {extra ? ` · ${extra}` : ''}
    </span>
  )
}
