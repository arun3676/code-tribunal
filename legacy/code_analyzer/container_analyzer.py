"""
Container and Kubernetes Analyzer
Detects Docker and Kubernetes configuration issues and suggests improvements.
"""

import re
import yaml
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class ContainerIssue:
    """Represents a container/Kubernetes issue found in configuration."""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int]
    suggestion: str
    code_example: str
    config_type: str  # 'dockerfile', 'kubernetes', 'docker-compose'

class ContainerAnalyzer:
    """Analyzes Docker and Kubernetes configurations for issues."""
    
    def __init__(self):
        self.dockerfile_patterns = {
            'root_user': {
                'pattern': r'USER\s+root',
                'message': 'Running as root user is a security risk',
                'suggestion': 'Create and use a non-root user',
                'example': '''
# Instead of running as root:
# USER root

# Create and use a non-root user:
RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser
'''
            },
            'no_healthcheck': {
                'pattern': r'^FROM\s+',
                'message': 'Dockerfile should include a HEALTHCHECK',
                'suggestion': 'Add a health check to monitor container health',
                'example': '''
# Add health check:
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
  CMD curl -f http://localhost:8080/health || exit 1
'''
            },
            'latest_tag': {
                'pattern': r'FROM\s+\w+:latest',
                'message': 'Using latest tag can cause unpredictable builds',
                'suggestion': 'Use specific version tags for reproducible builds',
                'example': '''
# Instead of:
# FROM python:latest

# Use specific version:
FROM python:3.9-slim
'''
            },
            'no_multi_stage': {
                'pattern': r'^FROM\s+[^#\n]+$',
                'message': 'Consider using multi-stage builds to reduce image size',
                'suggestion': 'Use multi-stage builds to separate build and runtime dependencies',
                'example': '''
# Multi-stage build example:
FROM python:3.9-slim as builder
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.9-slim
COPY --from=builder /root/.local /root/.local
COPY . .
CMD ["python", "app.py"]
'''
            }
        }
        
        self.kubernetes_patterns = {
            'no_resource_limits': {
                'pattern': r'containers:',
                'message': 'Kubernetes pods should have resource limits',
                'suggestion': 'Add CPU and memory limits to prevent resource exhaustion',
                'example': '''
resources:
  limits:
    memory: "512Mi"
    cpu: "500m"
  requests:
    memory: "256Mi"
    cpu: "250m"
'''
            },
            'no_security_context': {
                'pattern': r'containers:',
                'message': 'Kubernetes pods should have security context',
                'suggestion': 'Add security context to run containers securely',
                'example': '''
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
'''
            },
            'latest_image_tag': {
                'pattern': r'image:\s+[^:]+:latest',
                'message': 'Using latest tag in Kubernetes can cause issues',
                'suggestion': 'Use specific image tags for better control',
                'example': '''
# Instead of:
# image: myapp:latest

# Use specific version:
image: myapp:v1.2.3
'''
            },
            'no_liveness_probe': {
                'pattern': r'containers:',
                'message': 'Kubernetes pods should have liveness probes',
                'suggestion': 'Add liveness probe to detect and restart unhealthy containers',
                'example': '''
livenessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10
'''
            }
        }
    
    def analyze_dockerfile(self, content: str) -> List[ContainerIssue]:
        """Analyze Dockerfile for common issues."""
        issues = []
        lines = content.split('\n')
        
        has_healthcheck = False
        has_user = False
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            
            # Check for healthcheck
            if line.startswith('HEALTHCHECK'):
                has_healthcheck = True
            
            # Check for user
            if line.startswith('USER') and 'root' not in line:
                has_user = True
            
            # Check patterns
            for issue_type, pattern_info in self.dockerfile_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    # Skip if we already have a healthcheck
                    if issue_type == 'no_healthcheck' and has_healthcheck:
                        continue
                    
                    issues.append(ContainerIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example'],
                        config_type='dockerfile'
                    ))
        
        return issues
    
    def analyze_kubernetes_yaml(self, content: str) -> List[ContainerIssue]:
        """Analyze Kubernetes YAML for common issues."""
        issues = []
        
        try:
            # Parse YAML
            yaml_data = yaml.safe_load(content)
            
            if not yaml_data:
                return issues
            
            # Check if it's a Pod, Deployment, or similar
            kind = yaml_data.get('kind', '').lower()
            
            if kind in ['pod', 'deployment', 'statefulset', 'daemonset']:
                # Check for containers
                containers = []
                if kind == 'pod':
                    containers = yaml_data.get('spec', {}).get('containers', [])
                else:
                    containers = yaml_data.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                
                for container in containers:
                    # Check for resource limits
                    if 'resources' not in container:
                        issues.append(ContainerIssue(
                            issue_type='no_resource_limits',
                            severity='warning',
                            message='Container should have resource limits',
                            line_number=None,
                            suggestion='Add CPU and memory limits to prevent resource exhaustion',
                            code_example=self.kubernetes_patterns['no_resource_limits']['example'],
                            config_type='kubernetes'
                        ))
                    
                    # Check for security context
                    if 'securityContext' not in container:
                        issues.append(ContainerIssue(
                            issue_type='no_security_context',
                            severity='warning',
                            message='Container should have security context',
                            line_number=None,
                            suggestion='Add security context to run containers securely',
                            code_example=self.kubernetes_patterns['no_security_context']['example'],
                            config_type='kubernetes'
                        ))
                    
                    # Check for liveness probe
                    if 'livenessProbe' not in container:
                        issues.append(ContainerIssue(
                            issue_type='no_liveness_probe',
                            severity='info',
                            message='Consider adding liveness probe',
                            line_number=None,
                            suggestion='Add liveness probe to detect and restart unhealthy containers',
                            code_example=self.kubernetes_patterns['no_liveness_probe']['example'],
                            config_type='kubernetes'
                        ))
                    
                    # Check for latest tag
                    image = container.get('image', '')
                    if image.endswith(':latest'):
                        issues.append(ContainerIssue(
                            issue_type='latest_image_tag',
                            severity='warning',
                            message='Using latest tag can cause deployment issues',
                            line_number=None,
                            suggestion='Use specific image tags for better control',
                            code_example=self.kubernetes_patterns['latest_image_tag']['example'],
                            config_type='kubernetes'
                        ))
        
        except yaml.YAMLError as e:
            issues.append(ContainerIssue(
                issue_type='yaml_syntax_error',
                severity='error',
                message=f'Invalid YAML syntax: {e}',
                line_number=None,
                suggestion='Fix YAML syntax errors',
                code_example='Check your YAML indentation and syntax',
                config_type='kubernetes'
            ))
        
        return issues
    
    def detect_config_type(self, file_path: str, content: str) -> str:
        """Detect the type of container configuration."""
        if file_path.endswith('Dockerfile') or 'Dockerfile' in file_path:
            return 'dockerfile'
        elif file_path.endswith('.yaml') or file_path.endswith('.yml'):
            if 'kind:' in content and ('Pod' in content or 'Deployment' in content):
                return 'kubernetes'
            elif 'version:' in content and 'services:' in content:
                return 'docker-compose'
        
        return 'unknown'
    
    def analyze_code(self, file_path: str, content: str) -> Dict:
        """Main method to analyze container configurations."""
        config_type = self.detect_config_type(file_path, content)
        
        if config_type == 'dockerfile':
            issues = self.analyze_dockerfile(content)
        elif config_type == 'kubernetes':
            issues = self.analyze_kubernetes_yaml(content)
        else:
            issues = []
        
        return {
            'config_type': config_type,
            'issues': [vars(issue) for issue in issues],
            'total_issues': len(issues)
        } 