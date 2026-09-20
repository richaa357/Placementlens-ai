import { useEffect, useState } from 'react'
import { api } from './api'
import type { CompanyAnalysis, CompanySummary, SkillAlignment } from './api'
import { AIAnalysisSection } from './components/AIAnalysisSection'
import { CompanyOverviewCard } from './components/CompanyOverviewCard'
import { HistoricalSection } from './components/HistoricalSection'
import { PreparationSection } from './components/PreparationSection'
import { SearchBar } from './components/SearchBar'
import { SkillAlignmentSection } from './components/SkillAlignmentSection'
import { SkillSection } from './components/SkillSection'
import { SourcesSection } from './components/SourcesSection'
import './App.css'

export default function App() {
  const [companies, setCompanies] = useState<CompanySummary[]>([])
  const [query, setQuery] = useState('')
  const [analysis, setAnalysis] = useState<CompanyAnalysis | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState<{ query: string; suggestions: CompanySummary[] } | null>(null)
  const [alignment, setAlignment] = useState<SkillAlignment | null>(null)
  const [alignmentLoading, setAlignmentLoading] = useState(false)
  const [alignmentError, setAlignmentError] = useState<string | null>(null)

  useEffect(() => {
    api.listCompanies().then(setCompanies).catch(() => setCompanies([]))
  }, [])

  const runSearch = async (value: string) => {
    setQuery(value)
    setLoading(true)
    setError(null)
    setNotFound(null)
    setAlignment(null)
    setAlignmentError(null)
    try {
      const result = await api.search(value)
      if (!result.match) {
        setAnalysis(null)
        setNotFound({ query: value, suggestions: result.suggestions })
        return
      }
      setAnalysis(await api.analysis(result.match.slug))
    } catch (err) {
      setAnalysis(null)
      setError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  const runAlignment = async (skills: string[]) => {
    if (!analysis) return
    setAlignmentLoading(true)
    setAlignmentError(null)
    try {
      setAlignment(await api.skillAlignment(analysis.overview.slug, skills))
    } catch (err) {
      setAlignmentError(err instanceof Error ? err.message : 'Something went wrong')
    } finally {
      setAlignmentLoading(false)
    }
  }

  const showDashboard = Boolean(analysis)

  return (
    <div className="app">
      <header className="topbar">
        <button
          className="brand"
          type="button"
          onClick={() => {
            setAnalysis(null)
            setNotFound(null)
            setQuery('')
          }}
        >
          <span className="brand__mark">PL</span>
          <span>
            <strong>PlacementLens AI</strong>
            <em>Company placement research</em>
          </span>
        </button>
        {showDashboard && (
          <SearchBar compact knownCompanies={companies} initialValue={query} loading={loading} onSearch={runSearch} />
        )}
      </header>

      {!showDashboard && (
        <main className="landing">
          <h1>PlacementLens AI</h1>
          <p className="landing__lead">
            Research companies and understand their placement opportunities using historical data and AI.
          </p>
          <SearchBar knownCompanies={companies} loading={loading} onSearch={runSearch} />
          {companies.length > 0 && (
            <div className="chips">
              <span className="muted">Companies in the dataset:</span>
              {companies.map((company) => (
                <button key={company.slug} className="chip" type="button" onClick={() => runSearch(company.name)}>
                  {company.name}
                </button>
              ))}
            </div>
          )}
          <p className="landing__note">
            This project never invents placement data. Where a value cannot be verified it shows
            “No verified public data available.” instead of a number.
          </p>
          {error && <p className="error">{error}</p>}
          {notFound && (
            <div className="notfound">
              <strong>No verified public data available.</strong>
              <p>
                “{notFound.query}” is not in the configured dataset, so there is nothing verified to analyse.
                {notFound.suggestions.length > 0 && ' Did you mean:'}
              </p>
              {notFound.suggestions.length > 0 && (
                <div className="chips">
                  {notFound.suggestions.map((company) => (
                    <button key={company.slug} className="chip" type="button" onClick={() => runSearch(company.name)}>
                      {company.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}
        </main>
      )}

      {analysis && (
        <main className="dashboard">
          {Boolean(analysis.data_quality.contains_demo_data) && (
            <div className="demobanner">
              <strong>Demonstration data.</strong> This company is served from the bundled demo dataset. The job
              descriptions are illustrative texts and the placement records are sample values used to exercise the
              charts — they are not verified facts. Point <code>DATASET_PATH</code> at your placement cell&apos;s export
              to analyse real data.
            </div>
          )}
          <CompanyOverviewCard overview={analysis.overview} />
          <HistoricalSection historical={analysis.historical} />
          <SkillSection skills={analysis.skill_analysis} ai={analysis.ai_analysis} />
          <AIAnalysisSection ai={analysis.ai_analysis} />
          <SkillAlignmentSection
            alignment={alignment}
            loading={alignmentLoading}
            error={alignmentError}
            onSubmit={runAlignment}
          />
          <PreparationSection areas={analysis.preparation_areas} />
          <SourcesSection analysis={analysis} />
        </main>
      )}

      <footer className="footer">
        PlacementLens AI · Analysis is generated from the documents listed under Sources. It does not rank companies
        and does not predict selection outcomes.
      </footer>
    </div>
  )
}
