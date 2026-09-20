import type { CompanyAnalysis } from '../api'
import { DataBadge } from './DataBadge'

export function SourcesSection({ analysis }: { analysis: CompanyAnalysis }) {
  const quality = analysis.data_quality
  return (
    <section className="card" id="sources">
      <header className="card__header">
        <h2>Sources &amp; data quality</h2>
      </header>
      <div className="tablewrap">
        <table>
          <thead>
            <tr>
              <th>Source</th>
              <th>Date / year</th>
              <th>Data type</th>
              <th>Reference</th>
            </tr>
          </thead>
          <tbody>
            {analysis.sources.map((source) => (
              <tr key={source.id}>
                <td>
                  {source.name}
                  {source.notes && <div className="footnote">{source.notes}</div>}
                </td>
                <td className={source.published_date ? '' : 'cell--empty'}>
                  {source.published_date ?? 'No verified public data available.'}
                </td>
                <td>
                  <DataBadge type={source.data_type} />
                </td>
                <td>
                  {source.url ? (
                    <a href={source.url} target="_blank" rel="noreferrer">
                      Open
                    </a>
                  ) : (
                    <span className="cell--empty">No link available</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <ul className="quality">
        <li>Job descriptions analysed: {String(quality.job_postings)}</li>
        <li>Historical records: {String(quality.placement_records)}</li>
        <li>Records without a verified offer count: {String(quality.records_without_offer_count)}</li>
        <li>Records without a verified stipend: {String(quality.records_without_stipend)}</li>
        <li>Records without a verified drive date: {String(quality.records_without_drive_date)}</li>
      </ul>
    </section>
  )
}
