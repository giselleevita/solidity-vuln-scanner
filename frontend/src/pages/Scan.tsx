import { FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { runScan } from '../lib/api'
import { saveLatestResult } from '../lib/storage'

const EXAMPLE_CONTRACT = `pragma solidity ^0.8.0;

contract DemoVault {
    mapping(address => uint256) balances;

    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount, \"insufficient\");
        (bool ok, ) = msg.sender.call{value: amount}(\"\");
        require(ok, \"transfer failed\");
        balances[msg.sender] -= amount;
    }
}`

export default function ScanPage() {
  const navigate = useNavigate()
  const [contractName, setContractName] = useState('DemoVault')
  const [contractCode, setContractCode] = useState(EXAMPLE_CONTRACT)
  const [isScanning, setIsScanning] = useState(false)
  const [error, setError] = useState('')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    setError('')
    setIsScanning(true)

    try {
      const result = await runScan(contractName.trim() || 'UnnamedContract', contractCode)
      saveLatestResult(result)
      navigate('/results')
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : 'Scan failed.')
    } finally {
      setIsScanning(false)
    }
  }

  return (
    <section className="panel">
      <h2>Run Contract Scan</h2>
      <p>Paste Solidity source, submit, and inspect vulnerabilities in the results dashboard.</p>
      <form className="scan-form" onSubmit={onSubmit}>
        <label>
          Contract name
          <input
            value={contractName}
            onChange={(event) => setContractName(event.target.value)}
            placeholder="Vault"
            required
          />
        </label>
        <label>
          Solidity source
          <textarea
            value={contractCode}
            onChange={(event) => setContractCode(event.target.value)}
            rows={18}
            required
          />
        </label>
        <button type="submit" disabled={isScanning}>
          {isScanning ? 'Scanning...' : 'Scan Contract'}
        </button>
      </form>
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  )
}
