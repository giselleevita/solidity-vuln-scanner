import type { ScanResult } from './api'

const LATEST_RESULT_KEY = 'solidity-vuln-scanner.latest-result'
const HISTORY_KEY = 'solidity-vuln-scanner.history'

export interface HistoryEntry {
  id: string
  createdAt: string
  contractName: string
  vulnerabilities: number
  criticalCount: number
}

export function loadLatestResult(): ScanResult | null {
  const value = localStorage.getItem(LATEST_RESULT_KEY)
  return value ? (JSON.parse(value) as ScanResult) : null
}

export function loadHistory(): HistoryEntry[] {
  const value = localStorage.getItem(HISTORY_KEY)
  return value ? (JSON.parse(value) as HistoryEntry[]) : []
}

export function saveLatestResult(result: ScanResult): void {
  localStorage.setItem(LATEST_RESULT_KEY, JSON.stringify(result))
  const entry: HistoryEntry = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    contractName: result.contract_name,
    vulnerabilities: result.vulnerabilities.length,
    criticalCount: result.vulnerabilities.filter(
      (finding) => finding.severity.toLowerCase() === 'critical',
    ).length,
  }
  localStorage.setItem(HISTORY_KEY, JSON.stringify([entry, ...loadHistory()].slice(0, 50)))
}
