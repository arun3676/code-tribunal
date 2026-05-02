"""
Cloud Platform Integration Analyzer
Detects cloud-specific patterns and suggests improvements for AWS, Azure, and GCP.
"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class CloudIssue:
    """Represents a cloud platform issue found in code."""
    issue_type: str
    severity: str  # 'error', 'warning', 'info'
    message: str
    line_number: Optional[int]
    suggestion: str
    code_example: str
    platform: str  # 'aws', 'azure', 'gcp'

class CloudAnalyzer:
    """Analyzes code for cloud platform integration patterns and issues."""
    
    def __init__(self):
        self.aws_patterns = {
            'hardcoded_credentials': {
                'pattern': r'aws_access_key_id\s*=\s*[\'"][^\'"]+[\'"]',
                'message': 'Hardcoded AWS credentials are a security risk',
                'suggestion': 'Use environment variables or AWS IAM roles',
                'example': '''
# Instead of hardcoded credentials:
# aws_access_key_id = "AKIA..."

# Use environment variables:
import os
aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
'''
            },
            'no_error_handling': {
                'pattern': r'boto3\.client\([^)]+\)\.\w+\([^)]*\)',
                'message': 'AWS API calls should have error handling',
                'suggestion': 'Wrap AWS calls in try-catch blocks',
                'example': '''
try:
    s3.upload_file('file.txt', 'bucket', 'file.txt')
except ClientError as e:
    print(f"Error uploading file: {e}")
'''
            },
            'public_bucket_access': {
                'pattern': r's3\.get_object\([^)]*\)',
                'message': 'Check if S3 bucket access is properly secured',
                'suggestion': 'Ensure S3 buckets have proper access controls',
                'example': '''
# Make sure your S3 bucket has proper IAM policies
# and is not publicly accessible unless intended
'''
            }
        }
        
        self.azure_patterns = {
            'hardcoded_connection_string': {
                'pattern': r'DefaultEndpointsProtocol[^;]+;',
                'message': 'Hardcoded Azure connection strings are a security risk',
                'suggestion': 'Use Azure Key Vault or environment variables',
                'example': '''
# Instead of hardcoded connection string:
# connection_string = "DefaultEndpointsProtocol=https;..."

# Use environment variables:
connection_string = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
'''
            },
            'missing_retry_policy': {
                'pattern': r'BlobServiceClient\([^)]*\)',
                'message': 'Azure operations should have retry policies',
                'suggestion': 'Implement retry policies for Azure operations',
                'example': '''
from azure.core.policies import ExponentialRetryPolicy

retry_policy = ExponentialRetryPolicy(max_retries=3)
blob_service_client = BlobServiceClient.from_connection_string(
    connection_string, retry_policy=retry_policy
)
'''
            }
        }
        
        self.gcp_patterns = {
            'hardcoded_project_id': {
                'pattern': r'project_id\s*=\s*[\'"][^\'"]+[\'"]',
                'message': 'Hardcoded GCP project ID should be configurable',
                'suggestion': 'Use environment variables for project configuration',
                'example': '''
# Instead of hardcoded project ID:
# project_id = "my-project-123"

# Use environment variables:
project_id = os.environ.get('GCP_PROJECT_ID')
'''
            },
            'missing_authentication': {
                'pattern': r'storage\.Client\([^)]*\)',
                'message': 'GCP client should have proper authentication',
                'suggestion': 'Use service account keys or default credentials',
                'example': '''
# Use service account authentication:
from google.oauth2 import service_account

credentials = service_account.Credentials.from_service_account_file(
    'path/to/service-account-key.json'
)
client = storage.Client(credentials=credentials, project=project_id)
'''
            }
        }
    
    def analyze_aws_code(self, code: str) -> List[CloudIssue]:
        """Analyze AWS code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.aws_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(CloudIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example'],
                        platform='aws'
                    ))
        
        return issues
    
    def analyze_azure_code(self, code: str) -> List[CloudIssue]:
        """Analyze Azure code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.azure_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(CloudIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example'],
                        platform='azure'
                    ))
        
        return issues
    
    def analyze_gcp_code(self, code: str) -> List[CloudIssue]:
        """Analyze GCP code for common issues."""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            for issue_type, pattern_info in self.gcp_patterns.items():
                if re.search(pattern_info['pattern'], line):
                    issues.append(CloudIssue(
                        issue_type=issue_type,
                        severity='warning',
                        message=pattern_info['message'],
                        line_number=i,
                        suggestion=pattern_info['suggestion'],
                        code_example=pattern_info['example'],
                        platform='gcp'
                    ))
        
        return issues
    
    def detect_cloud_platform(self, file_path: str, code: str) -> str:
        """Detect which cloud platform the code is using."""
        if 'boto3' in code or 'aws' in code.lower():
            return 'aws'
        elif 'azure' in code.lower() or 'azure.storage' in code:
            return 'azure'
        elif 'google.cloud' in code or 'gcp' in code.lower():
            return 'gcp'
        
        return 'unknown'
    
    def analyze_code(self, file_path: str, code: str) -> Dict:
        """Main method to analyze code for cloud platform issues."""
        platform = self.detect_cloud_platform(file_path, code)
        
        if platform == 'aws':
            issues = self.analyze_aws_code(code)
        elif platform == 'azure':
            issues = self.analyze_azure_code(code)
        elif platform == 'gcp':
            issues = self.analyze_gcp_code(code)
        else:
            issues = []
        
        return {
            'platform': platform,
            'issues': [vars(issue) for issue in issues],
            'total_issues': len(issues)
        } 