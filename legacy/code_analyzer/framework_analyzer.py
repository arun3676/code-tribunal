"""
Framework-Specific Code Analyzer
Detects framework-specific patterns and suggests improvements for React, Angular, Django, and Spring.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class FrameworkIssue:
    """Represents a framework-specific issue found in code."""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int]
    suggestion: str
    code_example: str

class FrameworkAnalyzer:
    """Analyzes code for framework-specific patterns and issues."""
    
    def __init__(self):
        self.react_patterns = {
            'use_effect_missing': {
                'pattern': r'fetch\([^)]+\)\.then\([^)]+\)',
                'message': 'API calls should be wrapped in useEffect',
                'suggestion': 'Wrap API calls in useEffect with proper dependencies',
                'example': '''
useEffect(() => {
    fetch('/api/data')
        .then(res => res.json())
        .then(data => setData(data));
}, []); // Empty dependency array for component mount
'''
            },
            'missing_key_prop': {
                'pattern': r'\.map\([^)]*=>\s*<[^>]+>[^<]*</[^>]+>\s*\)',
                'message': 'List items should have unique key props',
                'suggestion': 'Add a unique key prop to each list item',
                'example': '''
{items.map((item, index) => (
    <div key={item.id || index}>{item.name}</div>
))}
'''
            }
        }
        
        self.django_patterns = {
            'raw_sql_in_views': {
                'pattern': r'User\.objects\.raw\([^)]+\)',
                'message': 'Avoid raw SQL queries in views',
                'suggestion': 'Use Django ORM methods instead of raw SQL',
                'example': '''
# Instead of raw SQL, use:
users = User.objects.filter(active=True)
'''
            },
            'missing_csrf': {
                'pattern': r'@csrf_exempt',
                'message': 'CSRF exemption can be a security risk',
                'suggestion': 'Only use @csrf_exempt when absolutely necessary',
                'example': '''
# Use @csrf_protect instead:
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def my_view(request):
    # Your view logic
'''
            }
        }
        
        self.spring_patterns = {
            'autowired_field': {
                'pattern': r'@Autowired\s+private\s+\w+\s+\w+;',
                'message': 'Field injection is not recommended',
                'suggestion': 'Use constructor injection instead of field injection',
                'example': '''
// Instead of field injection:
@Autowired
private UserService userService;

// Use constructor injection:
private final UserService userService;

public MyController(UserService userService) {
    this.userService = userService;
}
'''
            },
            'missing_transactional': {
                'pattern': r'public\s+\w+\s+\w+\([^)]*\)\s*\{[^}]*save\([^}]*\}',
                'message': 'Database operations should be transactional',
                'suggestion': 'Add @Transactional annotation to methods that modify data',
                'example': '''
@Transactional
public void saveUser(User user) {
    userRepository.save(user);
}
'''
            }
        }
    
    def analyze_react_code(self, code: str) -> List[FrameworkIssue]:
        """Analyze React code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.react_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(FrameworkIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example']
                    ))
        
        return issues
    
    def analyze_django_code(self, code: str) -> List[FrameworkIssue]:
        """Analyze Django code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.django_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(FrameworkIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example']
                    ))
        
        return issues
    
    def analyze_spring_code(self, code: str) -> List[FrameworkIssue]:
        """Analyze Spring code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.spring_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(FrameworkIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example']
                    ))
        
        return issues
    
    def detect_framework(self, file_path: str, code: str) -> str:
        """Detect which framework the code belongs to."""
        if file_path.endswith('.jsx') or file_path.endswith('.tsx'):
            return 'react'
        elif file_path.endswith('.js') and ('import React' in code or 'useState' in code):
            return 'react'
        elif file_path.endswith('.py') and ('from django' in code or 'import django' in code):
            return 'django'
        elif file_path.endswith('.java') and ('@SpringBootApplication' in code or '@RestController' in code):
            return 'spring'
        elif file_path.endswith('.ts') and ('@Component' in code or '@Injectable' in code):
            return 'angular'
        
        return 'unknown'
    
    def analyze_code(self, file_path: str, code: str) -> Dict:
        """Main method to analyze code for framework-specific issues."""
        framework = self.detect_framework(file_path, code)
        
        if framework == 'react':
            issues = self.analyze_react_code(code)
        elif framework == 'django':
            issues = self.analyze_django_code(code)
        elif framework == 'spring':
            issues = self.analyze_spring_code(code)
        else:
            issues = []
        
        return {
            'framework': framework,
            'issues': [vars(issue) for issue in issues],
            'total_issues': len(issues)
        } 