import type { AIAnalysis, SkillAnalysis } from '../api'
import { DataBadge } from './DataBadge'
import { Plot } from './Plot'

const CATEGORY_ORDER = ['Machine Learning', 'Deep Learning', 'NLP', 'SQL/Data', 'Programming', 'Tools']

export function SkillSection({ skills, ai }: { skills: SkillAnalysis; ai: AIAnalysis }) {
  if (!skills.has_data) {
    return (
      <section className="card" id="skills">
        <header className="card__header">
          <h2>Skill analysis</h2>
        </header>
        <p className="empty">{skills.message ?? 'Insufficient verified data'}</p>
      </section>
    )
  }

  const top = skills.skills.slice(0, 15).reverse()
  const heat = skills.heatmap

  return (
    <section className="card" id="skills">
      <header className="card__header">
        <div>
          <h2>Skill analysis</h2>
          <p className="muted">
            Extracted from {skills.analysed_document_count} analysed documents (job descriptions and historical
            skill lists).
          </p>
        </div>
        <DataBadge type="ai_analysis" />
      </header>

      <div className="grid grid--2">
        <div className="chart">
          <h3>Most frequently requested skills</h3>
          <Plot
            height={420}
            ariaLabel="Skill frequency"
            data={[
              {
                type: 'bar',
                orientation: 'h',
                x: top.map((stat) => stat.document_count),
                y: top.map((stat) => stat.skill),
                hovertemplate: '%{y}: %{x} document(s)<extra></extra>',
              },
            ]}
            layout={{ margin: { l: 190, r: 16, t: 8, b: 40 }, xaxis: { title: { text: 'Documents mentioning skill' } } }}
          />
        </div>
        <div className="chart">
          <h3>Role distribution</h3>
          {ai.has_data && ai.role_distribution.length > 0 ? (
            <Plot
              height={420}
              ariaLabel="Role distribution"
              data={[
                {
                  type: 'bar',
                  x: ai.role_distribution.map((role) => role.count),
                  y: ai.role_distribution.map((role) => role.role),
                  orientation: 'h',
                  marker: { color: '#7c3aed' },
                  hovertemplate: '%{y}: %{x} document(s)<extra></extra>',
                },
              ]}
              layout={{ margin: { l: 190, r: 16, t: 8, b: 40 }, xaxis: { title: { text: 'Documents' } } }}
            />
          ) : (
            <p className="empty">Insufficient verified data</p>
          )}
        </div>
      </div>

      {heat.years && heat.years.length > 0 && heat.categories && heat.categories.length > 0 && (
        <div className="chart">
          <h3>Technology / skill heatmap (skill mentions by category and year)</h3>
          <Plot
            height={300}
            ariaLabel="Skill category heatmap by year"
            data={[
              {
                type: 'heatmap',
                x: heat.years,
                y: heat.categories,
                z: heat.values,
                colorscale: 'Blues',
                hovertemplate: '%{y} · %{x}: %{z} skill mentions<extra></extra>',
              },
            ]}
            layout={{ margin: { l: 140, r: 16, t: 8, b: 40 }, xaxis: { dtick: 1 } }}
          />
        </div>
      )}

      <div className="grid grid--3">
        {CATEGORY_ORDER.filter((category) => skills.by_category[category]?.length).map((category) => (
          <div className="subcard" key={category}>
            <h4>{category}</h4>
            <ul className="skilllist">
              {skills.by_category[category].map((stat) => (
                <li key={stat.skill}>
                  <span>{stat.skill}</span>
                  <span className="bar">
                    <span className="bar__fill" style={{ width: `${Math.round(stat.frequency * 100)}%` }} />
                  </span>
                  <span className="muted">{Math.round(stat.frequency * 100)}%</span>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  )
}
