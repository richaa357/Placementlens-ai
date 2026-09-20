import { useState } from 'react'
import type { FormEvent } from 'react'
import type { CompanySummary } from '../api'

interface Props {
  initialValue?: string
  compact?: boolean
  loading?: boolean
  knownCompanies: CompanySummary[]
  onSearch: (query: string) => void
}

export function SearchBar({ initialValue = '', compact = false, loading = false, knownCompanies, onSearch }: Props) {
  const [value, setValue] = useState(initialValue)

  const submit = (event: FormEvent) => {
    event.preventDefault()
    if (value.trim()) onSearch(value.trim())
  }

  return (
    <form className={compact ? 'search search--compact' : 'search'} onSubmit={submit} role="search">
      <input
        className="search__input"
        type="search"
        list="known-companies"
        placeholder="Enter company name..."
        aria-label="Enter company name"
        value={value}
        onChange={(event) => setValue(event.target.value)}
      />
      <datalist id="known-companies">
        {knownCompanies.map((company) => (
          <option key={company.slug} value={company.name} />
        ))}
      </datalist>
      <button className="search__button" type="submit" disabled={loading || !value.trim()}>
        {loading ? 'Analysing…' : 'Search'}
      </button>
    </form>
  )
}
