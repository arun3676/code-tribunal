"""
CI/CD Integration Module for LLM Code Analyzer
Provides automated code quality gates for CI/CD pipelines.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import subprocess
import tempfile
import shutil

from .advanced_analyzer import AdvancedCodeAnalyzer, AnalysisConfig
from .security_analyzer import SecurityAnalyzer
from .performance_analyzer import PerformanceAnalyzer

@dataclass
class QualityGate:
    """Quality gate configuration."""
    min_quality_score: float = 70.0
    max_security_risk: float = 30.0
    max_performance_issues: int = 5
    max_critical_issues: int = 0
    max_high_issues: int = 2
    require_documentation: bool = True
    require_tests: bool = False
    allowed_languages: List[str] = None

@dataclass
class PipelineResult:
    """Result of CI/CD pipeline analysis."""
    passed: bool
    quality_score: float
    security_risk: float
    performance_score: float
    issues_found: int
    critical_issues: int
    high_issues: int
    recommendations: List[str]
    report_path: str
    failed_gates: List[str]

class CICDIntegrator:
    """CI/CD integration for automated code quality analysis."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize CI/CD integrator."""
        self.config = config or {}
        self.quality_gate = QualityGate(**self.config.get('quality_gate', {}))
        
        # Initialize analyzers
        analysis_config = AnalysisConfig(
            enable_rag=True,
            enable_security=True,
            enable_performance=True,
            enable_multimodal=False
        )
        
        self.analyzer = AdvancedCodeAnalyzer(analysis_config)
        self.security_analyzer = SecurityAnalyzer()
        self.performance_analyzer = PerformanceAnalyzer()
    
    def analyze_pull_request(self, 
                           base_branch: str = 'main',
                           head_branch: str = None,
                           repo_path: str = '.',
                           output_format: str = 'json') -> PipelineResult:
        """
        Analyze changes in a pull request.
        
        Args:
            base_branch: Base branch to compare against
            head_branch: Head branch with changes
            repo_path: Path to git repository
            output_format: Output format for reports
            
        Returns:
            PipelineResult with analysis results
        """
        if not head_branch:
            head_branch = self._get_current_branch(repo_path)
        
        # Get changed files
        changed_files = self._get_changed_files(repo_path, base_branch, head_branch)
        
        if not changed_files:
            return PipelineResult(
                passed=True,
                quality_score=100.0,
                security_risk=0.0,
                performance_score=100.0,
                issues_found=0,
                critical_issues=0,
                high_issues=0,
                recommendations=["No code changes detected"],
                report_path="",
                failed_gates=[]
            )
        
        # Analyze changed files
        results = self._analyze_changed_files(changed_files, repo_path)
        
        # Generate report
        report_path = self._generate_report(results, output_format)
        
        # Check quality gates
        passed, failed_gates = self._check_quality_gates(results)
        
        return PipelineResult(
            passed=passed,
            quality_score=results.get('average_quality_score', 0.0),
            security_risk=results.get('max_security_risk', 0.0),
            performance_score=results.get('average_performance_score', 0.0),
            issues_found=results.get('total_issues', 0),
            critical_issues=results.get('critical_issues', 0),
            high_issues=results.get('high_issues', 0),
            recommendations=results.get('recommendations', []),
            report_path=report_path,
            failed_gates=failed_gates
        )
    
    def analyze_commit(self, 
                      commit_hash: str,
                      repo_path: str = '.',
                      output_format: str = 'json') -> PipelineResult:
        """
        Analyze a specific commit.
        
        Args:
            commit_hash: Git commit hash to analyze
            repo_path: Path to git repository
            output_format: Output format for reports
            
        Returns:
            PipelineResult with analysis results
        """
        # Get files changed in commit
        changed_files = self._get_commit_files(repo_path, commit_hash)
        
        if not changed_files:
            return PipelineResult(
                passed=True,
                quality_score=100.0,
                security_risk=0.0,
                performance_score=100.0,
                issues_found=0,
                critical_issues=0,
                high_issues=0,
                recommendations=["No code changes in commit"],
                report_path="",
                failed_gates=[]
            )
        
        # Analyze changed files
        results = self._analyze_changed_files(changed_files, repo_path)
        
        # Generate report
        report_path = self._generate_report(results, output_format)
        
        # Check quality gates
        passed, failed_gates = self._check_quality_gates(results)
        
        return PipelineResult(
            passed=passed,
            quality_score=results.get('average_quality_score', 0.0),
            security_risk=results.get('max_security_risk', 0.0),
            performance_score=results.get('average_performance_score', 0.0),
            issues_found=results.get('total_issues', 0),
            critical_issues=results.get('critical_issues', 0),
            high_issues=results.get('high_issues', 0),
            recommendations=results.get('recommendations', []),
            report_path=report_path,
            failed_gates=failed_gates
        )
    
    def _get_changed_files(self, repo_path: str, base_branch: str, head_branch: str) -> List[str]:
        """Get list of files changed between branches."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', f'{base_branch}..{head_branch}'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = result.stdout.strip().split('\n')
            return [f for f in files if f and self._is_code_file(f)]
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting changed files: {e}")
            return []
    
    def _get_commit_files(self, repo_path: str, commit_hash: str) -> List[str]:
        """Get list of files changed in a commit."""
        try:
            result = subprocess.run(
                ['git', 'show', '--name-only', '--pretty=format:', commit_hash],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = result.stdout.strip().split('\n')
            return [f for f in files if f and self._is_code_file(f)]
            
        except subprocess.CalledProcessError as e:
            print(f"Error getting commit files: {e}")
            return []
    
    def _get_current_branch(self, repo_path: str) -> str:
        """Get current git branch."""
        try:
            result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return 'main'
    
    def _is_code_file(self, file_path: str) -> bool:
        """Check if file is a code file."""
        code_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', 
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala'
        }
        
        return Path(file_path).suffix.lower() in code_extensions
    
    def _analyze_changed_files(self, file_paths: List[str], repo_path: str) -> Dict[str, Any]:
        """Analyze all changed files."""
        results = {
            'files': {},
            'total_issues': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'quality_scores': [],
            'security_risks': [],
            'performance_scores': [],
            'recommendations': []
        }
        
        for file_path in file_paths:
            full_path = Path(repo_path) / file_path
            
            if not full_path.exists():
                continue
            
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Analyze file
                analysis_result = self.analyzer.analyze_code_advanced(
                    code, 
                    self._detect_language(file_path),
                    str(full_path)
                )
                
                # Extract metrics
                quality_score = 0.0
                if analysis_result.code_analysis:
                    quality_score = analysis_result.code_analysis.code_quality_score
                
                security_risk = 0.0
                if analysis_result.security_report:
                    security_risk = analysis_result.security_report.risk_score
                
                performance_score = 0.0
                if analysis_result.performance_report:
                    performance_score = analysis_result.performance_report.overall_score
                
                # Count issues
                issues = []
                if analysis_result.code_analysis:
                    issues.extend(analysis_result.code_analysis.potential_bugs or [])
                
                if analysis_result.security_report:
                    for vuln in analysis_result.security_report.vulnerabilities:
                        issues.append(f"Security: {vuln.vulnerability_type}")
                
                if analysis_result.performance_report:
                    for issue in analysis_result.performance_report.issues:
                        issues.append(f"Performance: {issue.issue_type}")
                
                # Store results
                results['files'][file_path] = {
                    'quality_score': quality_score,
                    'security_risk': security_risk,
                    'performance_score': performance_score,
                    'issues': issues,
                    'recommendations': []
                }
                
                # Aggregate metrics
                results['quality_scores'].append(quality_score)
                results['security_risks'].append(security_risk)
                results['performance_scores'].append(performance_score)
                results['total_issues'] += len(issues)
                
                # Count critical/high issues
                if analysis_result.security_report:
                    for vuln in analysis_result.security_report.vulnerabilities:
                        if vuln.severity == 'critical':
                            results['critical_issues'] += 1
                        elif vuln.severity == 'high':
                            results['high_issues'] += 1
                
            except Exception as e:
                print(f"Error analyzing {file_path}: {e}")
                results['files'][file_path] = {
                    'error': str(e),
                    'quality_score': 0.0,
                    'security_risk': 100.0,
                    'performance_score': 0.0,
                    'issues': [f"Analysis error: {e}"],
                    'recommendations': ["Fix analysis errors"]
                }
        
        # Calculate averages
        if results['quality_scores']:
            results['average_quality_score'] = sum(results['quality_scores']) / len(results['quality_scores'])
        if results['security_risks']:
            results['max_security_risk'] = max(results['security_risks'])
        if results['performance_scores']:
            results['average_performance_score'] = sum(results['performance_scores']) / len(results['performance_scores'])
        
        return results
    
    def _check_quality_gates(self, results: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Check if results pass quality gates."""
        failed_gates = []
        
        # Check quality score
        if results.get('average_quality_score', 0) < self.quality_gate.min_quality_score:
            failed_gates.append(f"Quality score {results.get('average_quality_score', 0):.1f} below threshold {self.quality_gate.min_quality_score}")
        
        # Check security risk
        if results.get('max_security_risk', 0) > self.quality_gate.max_security_risk:
            failed_gates.append(f"Security risk {results.get('max_security_risk', 0):.1f} above threshold {self.quality_gate.max_security_risk}")
        
        # Check total issues
        if results.get('total_issues', 0) > self.quality_gate.max_performance_issues:
            failed_gates.append(f"Total issues {results.get('total_issues', 0)} above threshold {self.quality_gate.max_performance_issues}")
        
        # Check critical issues
        if results.get('critical_issues', 0) > self.quality_gate.max_critical_issues:
            failed_gates.append(f"Critical issues {results.get('critical_issues', 0)} above threshold {self.quality_gate.max_critical_issues}")
        
        # Check high issues
        if results.get('high_issues', 0) > self.quality_gate.max_high_issues:
            failed_gates.append(f"High issues {results.get('high_issues', 0)} above threshold {self.quality_gate.max_high_issues}")
        
        return len(failed_gates) == 0, failed_gates
    
    def _generate_report(self, results: Dict[str, Any], output_format: str) -> str:
        """Generate analysis report."""
        timestamp = self._get_timestamp()
        
        if output_format == 'json':
            report_data = {
                'timestamp': timestamp,
                'summary': {
                    'total_files': len(results['files']),
                    'average_quality_score': results.get('average_quality_score', 0.0),
                    'max_security_risk': results.get('max_security_risk', 0.0),
                    'average_performance_score': results.get('average_performance_score', 0.0),
                    'total_issues': results.get('total_issues', 0),
                    'critical_issues': results.get('critical_issues', 0),
                    'high_issues': results.get('high_issues', 0)
                },
                'files': results['files']
            }
            
            report_path = f"ci_analysis_report_{timestamp.replace(':', '-')}.json"
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            
            return report_path
        
        elif output_format == 'html':
            return self._generate_html_report(results, timestamp)
        
        else:
            return self._generate_text_report(results, timestamp)
    
    def _generate_html_report(self, results: Dict[str, Any], timestamp: str) -> str:
        """Generate HTML report."""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CI/CD Code Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
                .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                .metric {{ background-color: #e8f4fd; padding: 15px; border-radius: 5px; text-align: center; }}
                .file-report {{ margin: 20px 0; border: 1px solid #ddd; padding: 15px; border-radius: 5px; }}
                .issue {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ff4444; background-color: #fff5f5; }}
                .passed {{ color: green; }}
                .failed {{ color: red; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>CI/CD Code Analysis Report</h1>
                <p>Generated on: {timestamp}</p>
            </div>
            
            <div class="summary">
                <div class="metric">
                    <h3>Quality Score</h3>
                    <p>{results.get('average_quality_score', 0.0):.1f}/100</p>
                </div>
                <div class="metric">
                    <h3>Security Risk</h3>
                    <p>{results.get('max_security_risk', 0.0):.1f}/100</p>
                </div>
                <div class="metric">
                    <h3>Performance Score</h3>
                    <p>{results.get('average_performance_score', 0.0):.1f}/100</p>
                </div>
                <div class="metric">
                    <h3>Total Issues</h3>
                    <p>{results.get('total_issues', 0)}</p>
                </div>
            </div>
        """
        
        for file_path, file_result in results['files'].items():
            html += f"""
            <div class="file-report">
                <h2>{file_path}</h2>
                <p>Quality Score: {file_result.get('quality_score', 0.0):.1f}/100</p>
                <p>Security Risk: {file_result.get('security_risk', 0.0):.1f}/100</p>
                <p>Performance Score: {file_result.get('performance_score', 0.0):.1f}/100</p>
            """
            
            for issue in file_result.get('issues', []):
                html += f'<div class="issue">{issue}</div>'
            
            html += "</div>"
        
        html += "</body></html>"
        
        report_path = f"ci_analysis_report_{timestamp.replace(':', '-')}.html"
        with open(report_path, 'w') as f:
            f.write(html)
        
        return report_path
    
    def _generate_text_report(self, results: Dict[str, Any], timestamp: str) -> str:
        """Generate text report."""
        report = f"CI/CD Code Analysis Report\n"
        report += f"Generated on: {timestamp}\n"
        report += f"Total files analyzed: {len(results['files'])}\n\n"
        
        report += f"Summary:\n"
        report += f"  Average Quality Score: {results.get('average_quality_score', 0.0):.1f}/100\n"
        report += f"  Max Security Risk: {results.get('max_security_risk', 0.0):.1f}/100\n"
        report += f"  Average Performance Score: {results.get('average_performance_score', 0.0):.1f}/100\n"
        report += f"  Total Issues: {results.get('total_issues', 0)}\n"
        report += f"  Critical Issues: {results.get('critical_issues', 0)}\n"
        report += f"  High Issues: {results.get('high_issues', 0)}\n\n"
        
        for file_path, file_result in results['files'].items():
            report += f"File: {file_path}\n"
            report += f"  Quality Score: {file_result.get('quality_score', 0.0):.1f}/100\n"
            report += f"  Security Risk: {file_result.get('security_risk', 0.0):.1f}/100\n"
            report += f"  Performance Score: {file_result.get('performance_score', 0.0):.1f}/100\n"
            
            for issue in file_result.get('issues', []):
                report += f"  Issue: {issue}\n"
            
            report += "\n"
        
        report_path = f"ci_analysis_report_{timestamp.replace(':', '-')}.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        return report_path
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        ext = Path(file_path).suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala'
        }
        
        return language_map.get(ext, 'python')
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

def main():
    """CLI interface for CI/CD integration."""
    parser = argparse.ArgumentParser(description='CI/CD Code Analysis')
    parser.add_argument('--mode', choices=['pr', 'commit'], required=True, help='Analysis mode')
    parser.add_argument('--base-branch', default='main', help='Base branch for PR analysis')
    parser.add_argument('--head-branch', help='Head branch for PR analysis')
    parser.add_argument('--commit', help='Commit hash for commit analysis')
    parser.add_argument('--repo-path', default='.', help='Repository path')
    parser.add_argument('--output-format', choices=['json', 'html', 'text'], default='json', help='Output format')
    parser.add_argument('--quality-gate', type=json.loads, default='{}', help='Quality gate configuration (JSON)')
    
    args = parser.parse_args()
    
    # Initialize integrator
    config = {'quality_gate': args.quality_gate}
    integrator = CICDIntegrator(config)
    
    # Run analysis
    if args.mode == 'pr':
        result = integrator.analyze_pull_request(
            base_branch=args.base_branch,
            head_branch=args.head_branch,
            repo_path=args.repo_path,
            output_format=args.output_format
        )
    else:
        result = integrator.analyze_commit(
            commit_hash=args.commit,
            repo_path=args.repo_path,
            output_format=args.output_format
        )
    
    # Output results
    print(f"Pipeline {'PASSED' if result.passed else 'FAILED'}")
    print(f"Quality Score: {result.quality_score:.1f}/100")
    print(f"Security Risk: {result.security_risk:.1f}/100")
    print(f"Performance Score: {result.performance_score:.1f}/100")
    print(f"Total Issues: {result.issues_found}")
    print(f"Critical Issues: {result.critical_issues}")
    print(f"High Issues: {result.high_issues}")
    
    if result.failed_gates:
        print("\nFailed Quality Gates:")
        for gate in result.failed_gates:
            print(f"  - {gate}")
    
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  - {rec}")
    
    print(f"\nReport saved to: {result.report_path}")
    
    # Exit with appropriate code
    sys.exit(0 if result.passed else 1)

if __name__ == "__main__":
    main() 