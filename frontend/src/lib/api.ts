export interface Vulnerability {
  type: string
  severity: string
  description?: string
  recommendation?: string
  swc_id?: string
}

export interface ScanResult {
  contract_name: string
  vulnerabilities: Vulnerability[]
  risk_score?: number
}

export async function runScan(contractName: string, contractCode: string): Promise<ScanResult> {
  const response = await fetch('/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      contract_name: contractName,
      contract_code: contractCode,
      use_llm_audit: false,
    }),
  })
  if (!response.ok) {
    throw new Error(`Scan failed with HTTP ${response.status}`)
  }
  return response.json() as Promise<ScanResult>
}
