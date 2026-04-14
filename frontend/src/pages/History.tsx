import { loadHistory } from '../lib/storage'

export default function HistoryPage() {
  const entries = loadHistory()

  return (
    <section className="panel">
      <h2>Scan History</h2>
      <p>Recent scans are kept locally in your browser for fast triage hand-offs.</p>
      {entries.length === 0 ? (
        <p>No history yet.</p>
      ) : (
        <table className="history-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Contract</th>
              <th>Findings</th>
              <th>Critical</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td>{new Date(entry.createdAt).toLocaleString()}</td>
                <td>{entry.contractName}</td>
                <td>{entry.vulnerabilities}</td>
                <td>{entry.criticalCount}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
