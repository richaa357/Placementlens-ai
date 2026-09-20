import type { PreparationArea } from '../api'
import { DataBadge } from './DataBadge'

export function PreparationSection({ areas }: { areas: PreparationArea[] }) {
  return (
    <section className="card" id="prepare">
      <header className="card__header">
        <div>
          <h2>What should I prepare?</h2>
          <p className="muted">
            Preparation areas derived only from the skills observed in the analysed job descriptions and historical
            records for this company.
          </p>
        </div>
        <DataBadge type="ai_analysis" />
      </header>
      {areas.length === 0 ? (
        <p className="empty">Insufficient verified data</p>
      ) : (
        <div className="grid grid--3">
          {areas.map((area) => (
            <div className="subcard" key={area.area}>
              <h4>{area.area}</h4>
              <ul className="preplist">
                {area.topics.map((topic) => (
                  <li key={topic.skill}>
                    <span>{topic.skill}</span>
                    <span className="muted">{Math.round(topic.frequency * 100)}% of documents</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
