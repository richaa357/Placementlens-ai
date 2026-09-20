import type { CompanyOverview } from '../api'
import { DataBadge } from './DataBadge'

export function CompanyOverviewCard({ overview }: { overview: CompanyOverview }) {
  return (
    <section className="card" id="overview">
      <header className="card__header">
        <div>
          <h2>{overview.name}</h2>
          <p className="muted">{overview.description ?? 'No verified public data available.'}</p>
        </div>
        <DataBadge type={overview.is_demo ? 'demo_data' : 'verified_historical'} />
      </header>

      <div className="grid grid--2">
        <Field label="Industry" value={overview.industry} />
        <Field label="Headquarters" value={overview.headquarters} />
        <Field label="Locations" value={overview.locations.join(' · ')} />
        <Field
          label="Website"
          value={
            overview.website ? (
              <a href={overview.website} target="_blank" rel="noreferrer">
                {overview.website}
              </a>
            ) : null
          }
        />
      </div>

      <TagRow title="Major technology areas" items={overview.technology_areas} />
      <TagRow title="Typical roles / internships" items={overview.typical_roles} />
      <TagRow
        title="Required technical skills (extracted from analysed job descriptions)"
        items={overview.required_skills}
        variant="skill"
      />
      {overview.notes && <p className="footnote">{overview.notes}</p>}
    </section>
  )
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  const empty = value === null || value === undefined || value === ''
  return (
    <div className="field">
      <span className="field__label">{label}</span>
      <span className={empty ? 'field__value field__value--empty' : 'field__value'}>
        {empty ? 'No verified public data available.' : value}
      </span>
    </div>
  )
}

function TagRow({ title, items, variant }: { title: string; items: string[]; variant?: 'skill' }) {
  return (
    <div className="tagrow">
      <span className="field__label">{title}</span>
      {items.length === 0 ? (
        <span className="field__value field__value--empty">Insufficient verified data</span>
      ) : (
        <div className="tags">
          {items.map((item) => (
            <span className={variant === 'skill' ? 'tag tag--skill' : 'tag'} key={item}>
              {item}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
