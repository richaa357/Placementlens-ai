import type { HistoricalAnalysis } from '../api'
import { DataBadge } from './DataBadge'
import { Plot } from './Plot'

export function HistoricalSection({ historical }: { historical: HistoricalAnalysis }) {
  if (!historical.has_data) {
    return (
      <section className="card" id="historical">
        <header className="card__header">
          <h2>Historical placement analysis</h2>
        </header>
        <p className="empty">{historical.message ?? 'No verified public data available.'}</p>
      </section>
    )
  }

  const yearsWithCounts = historical.by_year.filter((point) => point.offers_count !== null)
  const frequency = historical.hiring_frequency

  return (
    <section className="card" id="historical">
      <header className="card__header">
        <div>
          <h2>Historical placement analysis</h2>
          <p className="muted">{frequency.label}</p>
        </div>
        <DataBadge type={historical.contains_demo_data ? 'demo_data' : historical.data_type} />
      </header>

      <div className="grid grid--3">
        <Stat label="Years with records" value={frequency.years_with_records ?? '—'} />
        <Stat
          label="Period covered"
          value={frequency.first_year ? `${frequency.first_year}–${frequency.last_year}` : '—'}
        />
        <Stat label="Records per year" value={frequency.records_per_year ?? '—'} />
      </div>

      <div className="grid grid--2">
        <div className="chart">
          <h3>Recorded offers per year</h3>
          {yearsWithCounts.length > 0 ? (
            <Plot
              ariaLabel="Recorded offers per year"
              data={[
                {
                  type: 'bar',
                  x: yearsWithCounts.map((point) => point.year),
                  y: yearsWithCounts.map((point) => point.offers_count as number),
                  hovertemplate: '%{x}: %{y} recorded offers<extra></extra>',
                },
              ]}
              layout={{ xaxis: { title: { text: 'Year' }, dtick: 1 }, yaxis: { title: { text: 'Offers in records' } } }}
            />
          ) : (
            <p className="empty">No verified public data available.</p>
          )}
        </div>
        <div className="chart">
          <h3>Roles in historical records</h3>
          <Plot
            ariaLabel="Distribution of roles across historical records"
            data={[
              {
                type: 'pie',
                hole: 0.55,
                labels: historical.roles.map((role) => role.role),
                values: historical.roles.map((role) => role.record_count),
                textinfo: 'percent',
                hovertemplate: '%{label}: %{value} record(s)<extra></extra>',
              },
            ]}
            layout={{ showlegend: true, legend: { orientation: 'h', y: -0.15 } }}
          />
        </div>
      </div>

      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Year</th>
              <th>Role</th>
              <th>Type</th>
              <th>Offers recorded</th>
              <th>Stipend</th>
              <th>Drive date</th>
              <th>Skills requested</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {historical.records.map((record) => (
              <tr key={record.id}>
                <td>{record.year}</td>
                <td>{record.role}</td>
                <td>{record.opening_type ?? '—'}</td>
                <td className={record.offers_count === null ? 'cell--empty' : ''}>{record.offers_count_display}</td>
                <td className={record.stipend_display.startsWith('No verified') ? 'cell--empty' : ''}>
                  {record.stipend_display}
                </td>
                <td className={record.drive_date === null ? 'cell--empty' : ''}>{record.drive_date_display}</td>
                <td>{record.skills_requested.join(', ') || '—'}</td>
                <td>
                  <DataBadge type={record.data_type} />
                  <div className="footnote">{record.source?.name ?? 'Unsourced'}</div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="stat">
      <span className="stat__value">{value}</span>
      <span className="stat__label">{label}</span>
    </div>
  )
}
