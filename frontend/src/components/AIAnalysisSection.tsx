import type { AIAnalysis } from '../api'
import { DataBadge } from './DataBadge'
import { Plot } from './Plot'

export function AIAnalysisSection({ ai }: { ai: AIAnalysis }) {
  if (!ai.has_data) {
    return (
      <section className="card" id="ai">
        <header className="card__header">
          <h2>AI analysis</h2>
        </header>
        <p className="empty">{ai.message ?? 'Insufficient verified data'}</p>
      </section>
    )
  }

  const keywords = ai.keywords.slice(0, 15).reverse()

  return (
    <section className="card" id="ai">
      <header className="card__header">
        <div>
          <h2>AI analysis of job descriptions</h2>
          <p className="muted">
            {ai.method.preprocessing_backend} preprocessing · {ai.method.keyword_extraction} ·{' '}
            {ai.method.semantic_model} embeddings · {ai.method.similarity}
          </p>
        </div>
        <DataBadge type="ai_analysis" />
      </header>

      <div className="grid grid--2">
        <div className="chart">
          <h3>Top TF-IDF keywords</h3>
          <Plot
            height={420}
            ariaLabel="Top TF-IDF keywords"
            data={[
              {
                type: 'bar',
                orientation: 'h',
                x: keywords.map((keyword) => keyword.weight),
                y: keywords.map((keyword) => keyword.term),
                marker: { color: '#0ea5e9' },
                hovertemplate: '%{y}: mean TF-IDF %{x:.3f}<extra></extra>',
              },
            ]}
            layout={{ margin: { l: 190, r: 16, t: 8, b: 40 }, xaxis: { title: { text: 'Mean TF-IDF weight' } } }}
          />
        </div>
        <div>
          <h3>Emerging skills</h3>
          {ai.emerging_skills.length === 0 ? (
            <p className="empty">Insufficient verified data to compare periods.</p>
          ) : (
            <ul className="emerging">
              {ai.emerging_skills.map((item) => (
                <li key={item.skill}>
                  <div>
                    <strong>{item.skill}</strong> <span className="muted">({item.category})</span>
                  </div>
                  <div className="muted">
                    {Math.round(item.earlier_share * 100)}% of documents {item.earlier_period} →{' '}
                    {Math.round(item.recent_share * 100)}% {item.recent_period}
                  </div>
                </li>
              ))}
            </ul>
          )}
          <p className="footnote">{ai.method.note}</p>
        </div>
      </div>
    </section>
  )
}
