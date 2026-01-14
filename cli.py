#!/usr/bin/env python3
"""
CLI Tool for Solidity Vuln Scanner
Command-line interface for contract analysis
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Optional
import asyncio

from static_analyzer import StaticAnalyzer
from llm_auditor import LLMAuditor
from app_config import get_config
from logger_config import setup_logging, get_logger
from report_generator import generate_html_report, generate_markdown_report, generate_sarif_report
from pdf_report import generate_pdf_report
from input_validator import validate_contract_code, sanitize_contract_code

logger = setup_logging(log_level="INFO")
config = get_config()


def read_contract_file(file_path: str) -> str:
    """Read contract from file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


def analyze_contract(
    contract_code: str,
    contract_name: str,
    use_llm: bool = False,
    output_format: str = "json"
) -> dict:
    """Analyze a contract"""
    # Validate input
    is_valid, error_msg = validate_contract_code(contract_code)
    if not is_valid:
        print(f"❌ Validation error: {error_msg}", file=sys.stderr)
        sys.exit(1)
    
    sanitized_code = sanitize_contract_code(contract_code)
    
    # Run static analysis
    print("🔍 Running static analysis...", file=sys.stderr)
    analyzer = StaticAnalyzer()
    result = analyzer.analyze(sanitized_code, contract_name)
    
    # Run LLM audit if requested
    llm_result = None
    if use_llm:
        if not config.use_llm or not config.llm_api_key:
            print("⚠️  LLM not configured. Skipping LLM audit.", file=sys.stderr)
        else:
            print("🤖 Running LLM audit...", file=sys.stderr)
            try:
                auditor = LLMAuditor(
                    api_key=config.llm_api_key,
                    model=config.llm_model,
                    provider=config.llm_provider
                )
                llm_result = auditor.audit(sanitized_code, contract_name)
            except Exception as e:
                print(f"⚠️  LLM audit failed: {e}", file=sys.stderr)
    
    # Build result
    result_dict = result.to_dict()
    if llm_result:
        result_dict["llm_audit"] = llm_result.to_dict()
    
    return result_dict


def format_output(result: dict, output_format: str) -> str:
    """Format output based on format type"""
    if output_format == "json":
        return json.dumps(result, indent=2)
    elif output_format == "markdown":
        return generate_markdown_report(result)
    elif output_format == "html":
        return generate_html_report(result)
    elif output_format == "sarif":
        return json.dumps(generate_sarif_report(result), indent=2)
    else:
        raise ValueError(f"Unknown output format: {output_format}")


def save_pdf(result: dict, output_path: str):
    """Save PDF report"""
    try:
        generate_pdf_report(result, output_path)
        print(f"✅ PDF report saved to: {output_path}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Failed to generate PDF: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Solidity Vulnerability Scanner CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a contract file
  %(prog)s contract.sol
  
  # Analyze with LLM audit
  %(prog)s contract.sol --llm
  
  # Output as markdown
  %(prog)s contract.sol --format markdown
  
  # Save PDF report
  %(prog)s contract.sol --pdf report.pdf
  
  # Analyze from stdin
  cat contract.sol | %(prog)s -
        """
    )
    
    parser.add_argument(
        "input",
        help="Contract file path or '-' for stdin"
    )
    
    parser.add_argument(
        "--name",
        default="Contract",
        help="Contract name (default: Contract)"
    )
    
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM audit (requires API key)"
    )
    
    parser.add_argument(
        "--format",
        choices=["json", "markdown", "html", "sarif"],
        default="json",
        help="Output format (default: json)"
    )
    
    parser.add_argument(
        "--output", "-o",
        help="Output file path (default: stdout)"
    )
    
    parser.add_argument(
        "--pdf",
        help="Generate PDF report (specify output path)"
    )
    
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress progress messages"
    )
    
    args = parser.parse_args()
    
    # Read contract
    if args.input == "-":
        contract_code = sys.stdin.read()
        contract_name = args.name
    else:
        contract_path = Path(args.input)
        if not contract_path.exists():
            print(f"❌ File not found: {args.input}", file=sys.stderr)
            sys.exit(1)
        contract_code = read_contract_file(str(contract_path))
        contract_name = args.name or contract_path.stem
    
    if not args.quiet:
        print(f"📄 Analyzing contract: {contract_name}", file=sys.stderr)
    
    # Analyze
    try:
        result = analyze_contract(
            contract_code,
            contract_name,
            use_llm=args.llm,
            output_format=args.format
        )
    except Exception as e:
        print(f"❌ Analysis failed: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Generate PDF if requested
    if args.pdf:
        save_pdf(result, args.pdf)
    
    # Format output
    output = format_output(result, args.format)
    
    # Write output
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        if not args.quiet:
            print(f"✅ Output saved to: {args.output}", file=sys.stderr)
    else:
        print(output)
    
    # Exit with error code if vulnerabilities found
    if result.get('severity') in ['CRITICAL', 'HIGH']:
        sys.exit(1)
    elif result.get('vulnerabilities'):
        sys.exit(0)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
