import { useState } from 'react'
import type { FormEvent } from 'react'
import type { SkillAlignment } from '../api'
import { DataBadge } from './DataBadge'
import { Plot } from './Plot'

interface Props {
  alignment: SkillAlignment | null
  loading: boolean
  error: string | null
  onSubmit: (skills: string[]) => void
}

export function SkillAlignmentSection({ alignment, loading, error, onSubmit }: Props) {
  const [value, setValue] = useState('')

  const submit = (event: FormEvent) => {
    event.preventDefault()
    const skills = value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean)
    if (skills.length) onSubmit(skills)
  }

  return (
    <section className="card" id="alignment">
      <header className="card__header">
        <div>
          <h2>Skill alignment analysis</h2>
          <p className="muted">Optional. Compare your skills with the skills found in the analysed documents.</p>
        </div>
        <DataBadge type="user_provided" />
      </header>

      <form className="skillform" onSubmit={submit}>
        <input
          className="skillform__input"
          type="text"
          value={value}
          aria-label="Your skills, comma separated"
          placeholder="Python, SQL, Machine Learning, NLP, Deep Learning, Streamlit, DSA"
          onChange={(event) => setValue(event.target.value)}
        />
        <button type="submit" disabled={loading || !value.trim()}>
          {loading ? 'Comparing…' : 'Compare skills'}
        </button>
      </form>

      {error && <p className="error">{error}</p>}

      {alignment && !alignment.has_data && <p className="empty">{alignment.message ?? 'Insufficient verified data'}</p>}

      {alignment?.has_data && (
        <>
          <p className="notice">{alignment.disclaimer}</p>

          <div className="grid grid--3">
            <Column
              title="Skills I have"
              empty="None of your skills matched the analysed requirements."
              items={alignment.skills_i_have.map((item) => ({
                key: item.skill,
                primary: item.skill,
                secondary: `${item.category} · in ${Math.round(item.frequency * 100)}% of documents`,
                tone: 'have' as const,
              }))}
            />
            <Column
              title="Skills frequently requested"
              empty="Insufficient verified data"
              items={alignment.skills_frequently_requested.map((item) => ({
                key: item.skill,
                primary: item.skill,
                secondary: `${Math.round(item.frequency * 100)}% of documents${item.user_has_it ? ' · you listed this' : ''}`,
                tone: item.user_has_it ? ('have' as const) : ('neutral' as const),
              }))}
            />
            <Column
              title="Skills to learn"
              empty="Nothing outstanding in the analysed documents."
              items={alignment.skills_to_learn.map((item) => ({
                key: item.skill,
                primary: item.skill,
                secondary: `${item.category} · in ${Math.round(item.frequency * 100)}% of documents`,
                tone: 'learn' as const,
              }))}
            />
          </div>

          <div className="grid grid--3">
            <Metric
              label="Requirement coverage"
              value={`${Math.round(alignment.coverage * 100)}%`}
              hint="Share of the skills found in the documents that you listed"
            />
            <Metric
              label="TF-IDF cosine similarity"
              value={alignment.tfidf_similarity.toFixed(2)}
              hint="Best match between your skill text and a single job description"
            />
            <Metric
              label="Semantic cosine similarity"
              value={alignment.semantic_similarity.toFixed(2)}
              hint={`Embedding model: ${alignment.semantic_backend}`}
            />
          </div>

          {alignment.per_document_similarity.length > 0 && (
            <div className="chart">
              <h3>Similarity to each analysed document</h3>
              <Plot
                height={Math.max(260, alignment.per_document_similarity.length * 26)}
                ariaLabel="Similarity between your skills and each document"
                data={[
                  {
                    type: 'bar',
                    orientation: 'h',
                    name: 'TF-IDF',
                    x: alignment.per_document_similarity.map((row) => row.tfidf_similarity),
                    y: alignment.per_document_similarity.map((row) => row.title),
                  },
                  {
                    type: 'bar',
                    orientation: 'h',
                    name: 'Semantic',
                    x: alignment.per_document_similarity.map((row) => row.semantic_similarity),
                    y: alignment.per_document_similarity.map((row) => row.title),
                    marker: { color: '#7c3aed' },
                  },
                ]}
                layout={{
                  barmode: 'group',
                  margin: { l: 230, r: 16, t: 8, b: 40 },
                  xaxis: { title: { text: 'Cosine similarity' }, range: [0, 1] },
                  legend: { orientation: 'h', y: -0.2 },
                }}
              />
            </div>
          )}

          {alignment.skills_not_recognised.length > 0 && (
            <p className="footnote">
              Not recognised in the skill taxonomy (still used for the similarity calculation):{' '}
              {alignment.skills_not_recognised.join(', ')}
            </p>
          )}
          {alignment.additional_skills.length > 0 && (
            <p className="footnote">
              Skills you listed that do not appear in the analysed documents: {alignment.additional_skills.join(', ')}
            </p>
          )}
        </>
      )}
    </section>
  )
}

interface ColumnItem {
  key: string
  primary: string
  secondary: string
  tone: 'have' | 'learn' | 'neutral'
}

function Column({ title, items, empty }: { title: string; items: ColumnItem[]; empty: string }) {
  return (
    <div className="subcard">
      <h4>{title}</h4>
      {items.length === 0 ? (
        <p className="empty empty--small">{empty}</p>
      ) : (
        <ul className="alignlist">
          {items.map((item) => (
            <li key={item.key} className={`alignlist__item alignlist__item--${item.tone}`}>
              <strong>{item.primary}</strong>
              <span className="muted">{item.secondary}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Metric({ label, value, hint }: { label: string; value: string; hint: string }) {
  return (
    <div className="stat">
      <span className="stat__value">{value}</span>
      <span className="stat__label">{label}</span>
      <span className="footnote">{hint}</span>
    </div>
  )
}
