/** Typed client for the PlacementLens AI API. */

export const API_BASE_URL: string =
  (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? 'http://localhost:8000'

export type DataType =
  | 'verified_historical'
  | 'current_posting'
  | 'ai_analysis'
  | 'user_provided'
  | 'demo_data'

export interface Source {
  id: number
  name: string
  url: string | null
  published_date: string | null
  data_type: DataType
  is_demo: boolean
  notes: string | null
}

export interface CompanySummary {
  id: number
  name: string
  slug: string
  industry: string | null
  headquarters: string | null
  is_demo: boolean
}

export interface SearchResponse {
  query: string
  match: CompanySummary | null
  match_type: 'exact' | 'alias' | 'fuzzy' | 'none'
  suggestions: CompanySummary[]
  message: string | null
}

export interface CompanyOverview {
  id: number
  name: string
  slug: string
  industry: string | null
  description: string | null
  website: string | null
  headquarters: string | null
  locations: string[]
  technology_areas: string[]
  typical_roles: string[]
  required_skills: string[]
  is_demo: boolean
  data_type: DataType
  notes: string | null
}

export interface PlacementRecord {
  id: number
  year: number
  role: string
  opening_type: string | null
  offers_count: number | null
  offers_count_display: string
  stipend_display: string
  drive_date: string | null
  drive_date_display: string
  skills_requested: string[]
  data_type: DataType
  is_demo: boolean
  source: Source | null
}

export interface HistoricalAnalysis {
  has_data: boolean
  message: string | null
  records: PlacementRecord[]
  by_year: { year: number; records: number; offers_count: number | null; offers_count_display: string }[]
  roles: { role: string; record_count: number; years: number[]; offers_count: number | null }[]
  hiring_frequency: {
    years_with_records?: number
    year_span?: number
    first_year?: number | null
    last_year?: number | null
    records_per_year?: number | null
    label?: string
  }
  stipend_observations: {
    year: number
    role: string
    display: string
    amount: number | null
    currency: string | null
    period: string | null
    source: Source | null
  }[]
  data_type: DataType
  contains_demo_data: boolean
}

export interface SkillStat {
  skill: string
  category: string
  document_count: number
  mention_count: number
  frequency: number
}

export interface SkillAnalysis {
  has_data: boolean
  message: string | null
  analysed_document_count: number
  skills: SkillStat[]
  by_category: Record<string, SkillStat[]>
  heatmap: { years?: number[]; categories?: string[]; values?: number[][] }
  data_type: DataType
}

export interface AIAnalysis {
  has_data: boolean
  message: string | null
  method: Record<string, string | number>
  keywords: { term: string; weight: number }[]
  emerging_skills: {
    skill: string
    category: string
    recent_share: number
    earlier_share: number
    delta: number
    recent_period: string
    earlier_period: string
  }[]
  role_distribution: { role: string; count: number; share: number }[]
  data_type: DataType
}

export interface PreparationArea {
  area: string
  priority_score: number
  topics: { skill: string; frequency: number; document_count: number; already_listed_by_user: boolean }[]
}

export interface CompanyAnalysis {
  overview: CompanyOverview
  historical: HistoricalAnalysis
  skill_analysis: SkillAnalysis
  ai_analysis: AIAnalysis
  preparation_areas: PreparationArea[]
  sources: Source[]
  data_quality: Record<string, number | boolean | string>
}

export interface SkillAlignment {
  has_data: boolean
  message: string | null
  disclaimer: string
  company: CompanySummary | null
  skills_i_have: { skill: string; category: string; frequency: number; document_count: number }[]
  skills_frequently_requested: {
    skill: string
    category: string
    frequency: number
    document_count: number
    user_has_it: boolean
  }[]
  skills_to_learn: { skill: string; category: string; frequency: number; document_count: number }[]
  skills_not_recognised: string[]
  additional_skills: string[]
  coverage: number
  tfidf_similarity: number
  semantic_similarity: number
  semantic_backend: string
  per_document_similarity: {
    document_id: number
    title: string
    year: number | null
    tfidf_similarity: number
    semantic_similarity: number
  }[]
}

export interface JobPosting {
  id: number
  title: string
  role_family: string | null
  employment_type: string | null
  location: string | null
  posted_date: string | null
  description: string
  data_type: DataType
  is_demo: boolean
  source: Source | null
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!response.ok) {
    const detail = await response.json().catch(() => ({ detail: response.statusText }))
    throw new Error(detail.detail ?? `Request failed with ${response.status}`)
  }
  return (await response.json()) as T
}

export const api = {
  listCompanies: () => request<CompanySummary[]>('/api/companies'),
  search: (query: string) => request<SearchResponse>(`/api/companies/search?q=${encodeURIComponent(query)}`),
  analysis: (slug: string) => request<CompanyAnalysis>(`/api/companies/${slug}/analysis`),
  postings: (slug: string) => request<JobPosting[]>(`/api/companies/${slug}/postings`),
  skillAlignment: (slug: string, skills: string[]) =>
    request<SkillAlignment>(`/api/companies/${slug}/skill-alignment`, {
      method: 'POST',
      body: JSON.stringify({ skills }),
    }),
}
