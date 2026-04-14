import { Link } from 'react-router-dom'
import { loadLatestResult } from '../lib/storage'

export default function ResultsPage() {
  const result = loadLatestResult()

  if (!result) {
    return (
      <section className="panel">
        <h2>Latest Results</h2>
        <p>No scan results yet. Run a scan first.</p>
        <Link className="inline-link" to="/scan">
          Go to Scan
        </Link>
      </section>
    )
  }

  const critical = result.vulnerabilities.filter((v) => v.severity.toLowerCase() === 'critical').length
  const high = result.vulnerabilities.filter((v) => v.severity.toLowerCase() === 'high').length

  return (
    <section className="panel">
      <h2>Latest Results</h2>
      <div className="stats-grid">
        <article>
          <h3>Contract</h3>
          <p>{result.contract_name}</p>
        </article>
        <article>
          <h3>Total Findings</h3>
          <p>{result.vulnerabilities.length}</p>
        </article>
        <article>
          <h3>Critical / High</h3>
          <p>
            {critical} / {high}
          </p>
        </article>
        <article>
          <h3>Risk Score</h3>
          <p>{result.risk_score ?? 'n/a'}</p>
        </article>
      </div>

      <div className="results-list">
        {result.vulnerabilities.map((finding, index) => (
          <article key={`${finding.type}-${index}`} className={`result-card sev-${finding.severity.toLowerCase()}`}>
            <div>
              <strong>{finding.type}</strong>
              <span className="chip">{finding.severity}</span>
              {finding.swc_id ? <span className="chip">{finding.swc_id}</span> : null}
            </div>
            <p>{finding.description || 'No description provided.'}</p>
            {finding.recommendation ? <p className="recommendation">Fix: {finding.recommendation}</p> : null}
          </article>
        ))}
      </div>
    </section>
  )
}
