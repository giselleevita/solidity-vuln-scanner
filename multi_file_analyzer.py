"""
Multi-File Contract Analyzer
Supports analyzing projects with imports and multiple files
"""

from typing import List, Dict, Set, Optional
from pathlib import Path
import re
from app_config import get_config
from logger_config import get_logger
from static_analyzer import StaticAnalyzer, AnalysisResult, Vulnerability

logger = get_logger(__name__)
config = get_config()


class MultiFileAnalyzer:
    """
    Analyzer for multi-file Solidity projects
    Handles imports, dependencies, and cross-file analysis
    """
    
    def __init__(self):
        self.static_analyzer = StaticAnalyzer()
        self.resolved_files: Dict[str, str] = {}  # Cache resolved file contents
        logger.info("Multi-file analyzer initialized")
    
    def detect_project_type(self, project_path: Path) -> Optional[str]:
        """
        Detect project type (Foundry, Hardhat, Truffle, or plain)
        
        Args:
            project_path: Path to project root
            
        Returns:
            Project type or None
        """
        if (project_path / "foundry.toml").exists():
            return "foundry"
        elif (project_path / "hardhat.config.js").exists() or (project_path / "hardhat.config.ts").exists():
            return "hardhat"
        elif (project_path / "truffle-config.js").exists():
            return "truffle"
        elif (project_path / "contracts").exists():
            return "plain"
        return None
    
    def find_contract_files(self, project_path: Path, project_type: Optional[str] = None) -> List[Path]:
        """
        Find all Solidity contract files in project
        
        Args:
            project_path: Project root path
            project_type: Project type (auto-detected if None)
            
        Returns:
            List of contract file paths
        """
        if project_type is None:
            project_type = self.detect_project_type(project_path)
        
        contract_files = []
        
        if project_type == "foundry":
            contracts_dir = project_path / "src"
        elif project_type in ["hardhat", "truffle", "plain"]:
            contracts_dir = project_path / "contracts"
        else:
            contracts_dir = project_path
        
        if contracts_dir.exists():
            contract_files.extend(contracts_dir.rglob("*.sol"))
        
        logger.info(f"Found {len(contract_files)} contract files in {project_path}")
        return contract_files
    
    def resolve_imports(self, contract_code: str, base_path: Path) -> str:
        """
        Resolve import statements in contract code
        
        Args:
            contract_code: Contract source code
            base_path: Base path for resolving relative imports
            
        Returns:
            Contract code with imports resolved (concatenated)
        """
        import_pattern = r'import\s+["\']([^"\']+)["\']\s*;'
        imports = re.findall(import_pattern, contract_code)
        
        resolved_code = contract_code
        resolved_imports: Set[str] = set()
        
        for import_path in imports:
            if import_path in resolved_imports:
                continue  # Already resolved
            
            # Try different import path formats
            import_file = self._resolve_import_path(import_path, base_path)
            
            if import_file and import_file.exists():
                try:
                    with open(import_file, 'r', encoding='utf-8') as f:
                        import_code = f.read()
                    
                    # Recursively resolve imports in imported file
                    import_code = self.resolve_imports(import_code, import_file.parent)
                    
                    # Remove import statement and add imported code
                    import_stmt = f'import "{import_path}";'
                    resolved_code = resolved_code.replace(import_stmt, f"\n// Imported: {import_path}\n{import_code}\n")
                    resolved_imports.add(import_path)
                except Exception as e:
                    logger.warning(f"Failed to resolve import {import_path}: {e}")
        
        return resolved_code
    
    def _resolve_import_path(self, import_path: str, base_path: Path) -> Optional[Path]:
        """Resolve an import path to a file"""
        # Try relative to base path
        candidate = base_path / import_path
        if candidate.exists():
            return candidate
        
        # Try relative to base_path parent
        candidate = base_path.parent / import_path
        if candidate.exists():
            return candidate
        
        # Try node_modules style (for npm packages)
        candidate = base_path / "node_modules" / import_path
        if candidate.exists():
            return candidate
        
        # Try @openzeppelin style
        if import_path.startswith("@openzeppelin/"):
            candidate = base_path / "node_modules" / import_path
            if candidate.exists():
                return candidate
        
        return None
    
    def analyze_project(self, project_path: Path) -> Dict[str, AnalysisResult]:
        """
        Analyze entire project
        
        Args:
            project_path: Path to project root
            
        Returns:
            Dictionary mapping file paths to analysis results
        """
        project_type = self.detect_project_type(project_path)
        contract_files = self.find_contract_files(project_path, project_type)
        
        results = {}
        
        for contract_file in contract_files:
            try:
                with open(contract_file, 'r', encoding='utf-8') as f:
                    contract_code = f.read()
                
                # Resolve imports
                resolved_code = self.resolve_imports(contract_code, contract_file.parent)
                
                # Analyze
                contract_name = contract_file.stem
                result = self.static_analyzer.analyze(resolved_code, contract_name)
                
                results[str(contract_file)] = result
                logger.info(f"Analyzed {contract_file}: {len(result.vulnerabilities)} vulnerabilities")
                
            except Exception as e:
                logger.error(f"Failed to analyze {contract_file}: {e}")
                results[str(contract_file)] = AnalysisResult(
                    contract_name=contract_file.stem,
                    vulnerabilities=[]
                )
        
        return results
    
    def analyze_with_imports(self, contract_code: str, contract_name: str, base_path: Optional[Path] = None) -> AnalysisResult:
        """
        Analyze a single contract with imports resolved
        
        Args:
            contract_code: Contract source code
            contract_name: Contract name
            base_path: Base path for imports (current dir if None)
            
        Returns:
            Analysis result
        """
        if base_path is None:
            base_path = Path.cwd()
        
        # Resolve imports
        resolved_code = self.resolve_imports(contract_code, base_path)
        
        # Analyze
        return self.static_analyzer.analyze(resolved_code, contract_name)


# Global instance
multi_file_analyzer = MultiFileAnalyzer()
