"""
Code Quality Dashboard
This module provides a comprehensive dashboard for tracking code quality trends over time.
"""

import os
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from io import BytesIO
import base64

@dataclass
class QualityMetric:
    """Represents a single quality metric measurement."""
    timestamp: str
    file_path: str
    language: str
    quality_score: float
    model_name: str
    execution_time: float
    bug_count: int
    suggestion_count: int
    complexity_score: Optional[float] = None
    performance_score: Optional[float] = None
    security_score: Optional[float] = None
    maintainability_score: Optional[float] = None

@dataclass
class TrendData:
    """Represents trend data for a specific metric."""
    metric_name: str
    values: List[float]
    timestamps: List[str]
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # -1 to 1
    average_value: float
    min_value: float
    max_value: float

@dataclass
class DashboardReport:
    """Complete dashboard report with all metrics and trends."""
    overall_quality_trend: TrendData
    language_breakdown: Dict[str, Dict[str, Any]]
    model_performance: Dict[str, Dict[str, Any]]
    top_issues: List[Dict[str, Any]]
    improvement_areas: List[str]
    recommendations: List[str]
    generated_at: str
    time_period: str
    total_analyses: int

class CodeQualityDashboard:
    """
    Dashboard for tracking and visualizing code quality trends.
    """
    
    def __init__(self, db_path: str = "quality_metrics.db"):
        """Initialize the dashboard with database connection."""
        self.db_path = db_path
        self._init_database()
        
        # Set up matplotlib style for better visualizations
        plt.style.use('dark_background')
        sns.set_palette("husl")
    
    def _init_database(self):
        """Initialize the SQLite database for storing metrics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                file_path TEXT NOT NULL,
                language TEXT NOT NULL,
                quality_score REAL NOT NULL,
                model_name TEXT NOT NULL,
                execution_time REAL NOT NULL,
                bug_count INTEGER NOT NULL,
                suggestion_count INTEGER NOT NULL,
                complexity_score REAL,
                performance_score REAL,
                security_score REAL,
                maintainability_score REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON quality_metrics(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_language ON quality_metrics(language)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model ON quality_metrics(model_name)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_file_path ON quality_metrics(file_path)')
        
        conn.commit()
        conn.close()
    
    def record_analysis(self, analysis_result: Any, file_path: str, language: str, model_name: str):
        """
        Record a code analysis result in the database.
        
        Args:
            analysis_result: Result from code analyzer
            file_path: Path to the analyzed file
            language: Programming language
            model_name: Name of the model used
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract metrics from analysis result
        quality_score = getattr(analysis_result, 'code_quality_score', 0.0)
        execution_time = getattr(analysis_result, 'execution_time', 0.0)
        bug_count = len(getattr(analysis_result, 'potential_bugs', []))
        suggestion_count = len(getattr(analysis_result, 'improvement_suggestions', []))
        
        # Calculate additional scores if available
        complexity_score = None
        performance_score = None
        security_score = None
        maintainability_score = None
        
        if hasattr(analysis_result, 'fix_suggestions') and analysis_result.fix_suggestions:
            # Calculate scores based on fix suggestions
            severity_scores = {
                'critical': 1.0,
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            }
            
            total_severity = 0
            for fix in analysis_result.fix_suggestions:
                if hasattr(fix, 'severity') and fix.severity in severity_scores:
                    total_severity += severity_scores[fix.severity]
            
            if total_severity > 0:
                maintainability_score = max(0, 1 - (total_severity / len(analysis_result.fix_suggestions)))
        
        cursor.execute('''
            INSERT INTO quality_metrics 
            (timestamp, file_path, language, quality_score, model_name, execution_time, 
             bug_count, suggestion_count, complexity_score, performance_score, security_score, maintainability_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            file_path,
            language,
            quality_score,
            model_name,
            execution_time,
            bug_count,
            suggestion_count,
            complexity_score,
            performance_score,
            security_score,
            maintainability_score
        ))
        
        conn.commit()
        conn.close()
    
    def get_metrics(self, days: int = 30, language_filter: Optional[str] = None, 
                   model_filter: Optional[str] = None) -> List[QualityMetric]:
        """
        Retrieve metrics from the database.
        
        Args:
            days: Number of days to look back
            language_filter: Optional language filter
            model_filter: Optional model filter
            
        Returns:
            List of QualityMetric objects
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build query
        query = '''
            SELECT timestamp, file_path, language, quality_score, model_name, execution_time,
                   bug_count, suggestion_count, complexity_score, performance_score, security_score, maintainability_score
            FROM quality_metrics
            WHERE timestamp >= ?
        '''
        params = [(datetime.now() - timedelta(days=days)).isoformat()]
        
        if language_filter:
            query += ' AND language = ?'
            params.append(language_filter)
        
        if model_filter:
            query += ' AND model_name = ?'
            params.append(model_filter)
        
        query += ' ORDER BY timestamp DESC'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        metrics = []
        for row in rows:
            metrics.append(QualityMetric(
                timestamp=row[0],
                file_path=row[1],
                language=row[2],
                quality_score=row[3],
                model_name=row[4],
                execution_time=row[5],
                bug_count=row[6],
                suggestion_count=row[7],
                complexity_score=row[8],
                performance_score=row[9],
                security_score=row[10],
                maintainability_score=row[11]
            ))
        
        return metrics
    
    def calculate_trends(self, metrics: List[QualityMetric]) -> Dict[str, TrendData]:
        """
        Calculate trends for various metrics.
        
        Args:
            metrics: List of quality metrics
            
        Returns:
            Dictionary of trend data for each metric
        """
        if not metrics:
            return {}
        
        # Group metrics by type
        quality_scores = [(m.timestamp, m.quality_score) for m in metrics]
        bug_counts = [(m.timestamp, m.bug_count) for m in metrics]
        suggestion_counts = [(m.timestamp, m.suggestion_count) for m in metrics]
        execution_times = [(m.timestamp, m.execution_time) for m in metrics]
        
        trends = {}
        
        # Calculate quality score trend
        if quality_scores:
            trends['quality_score'] = self._calculate_single_trend('Quality Score', quality_scores)
        
        # Calculate bug count trend (inverted - lower is better)
        if bug_counts:
            bug_trend = self._calculate_single_trend('Bug Count', bug_counts)
            bug_trend.trend_direction = 'improving' if bug_trend.trend_direction == 'declining' else 'declining'
            trends['bug_count'] = bug_trend
        
        # Calculate suggestion count trend
        if suggestion_counts:
            trends['suggestion_count'] = self._calculate_single_trend('Suggestion Count', suggestion_counts)
        
        # Calculate execution time trend (inverted - lower is better)
        if execution_times:
            time_trend = self._calculate_single_trend('Execution Time', execution_times)
            time_trend.trend_direction = 'improving' if time_trend.trend_direction == 'declining' else 'declining'
            trends['execution_time'] = time_trend
        
        return trends
    
    def _calculate_single_trend(self, metric_name: str, data: List[Tuple[str, float]]) -> TrendData:
        """Calculate trend for a single metric."""
        # Sort by timestamp
        data.sort(key=lambda x: x[0])
        
        timestamps = [x[0] for x in data]
        values = [x[1] for x in data]
        
        if len(values) < 2:
            return TrendData(
                metric_name=metric_name,
                values=values,
                timestamps=timestamps,
                trend_direction='stable',
                trend_strength=0.0,
                average_value=statistics.mean(values) if values else 0.0,
                min_value=min(values) if values else 0.0,
                max_value=max(values) if values else 0.0
            )
        
        # Calculate trend using linear regression
        x = np.arange(len(values))
        y = np.array(values)
        
        # Simple linear regression
        slope = np.polyfit(x, y, 1)[0]
        
        # Normalize slope to get trend strength (-1 to 1)
        value_range = max(values) - min(values)
        if value_range == 0:
            trend_strength = 0.0
        else:
            trend_strength = np.clip(slope / value_range * len(values), -1, 1)
        
        # Determine trend direction
        if abs(trend_strength) < 0.1:
            trend_direction = 'stable'
        elif trend_strength > 0:
            trend_direction = 'improving'
        else:
            trend_direction = 'declining'
        
        return TrendData(
            metric_name=metric_name,
            values=values,
            timestamps=timestamps,
            trend_direction=trend_direction,
            trend_strength=trend_strength,
            average_value=statistics.mean(values),
            min_value=min(values),
            max_value=max(values)
        )
    
    def generate_dashboard_report(self, days: int = 30) -> DashboardReport:
        """
        Generate a comprehensive dashboard report.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            DashboardReport with all metrics and insights
        """
        metrics = self.get_metrics(days=days)
        
        if not metrics:
            return DashboardReport(
                overall_quality_trend=TrendData("Quality Score", [], [], "stable", 0.0, 0.0, 0.0, 0.0),
                language_breakdown={},
                model_performance={},
                top_issues=[],
                improvement_areas=[],
                recommendations=[],
                generated_at=datetime.now().isoformat(),
                time_period=f"Last {days} days",
                total_analyses=0
            )
        
        # Calculate trends
        trends = self.calculate_trends(metrics)
        overall_quality_trend = trends.get('quality_score', 
            TrendData("Quality Score", [], [], "stable", 0.0, 0.0, 0.0, 0.0))
        
        # Language breakdown
        language_breakdown = self._analyze_language_breakdown(metrics)
        
        # Model performance
        model_performance = self._analyze_model_performance(metrics)
        
        # Top issues
        top_issues = self._identify_top_issues(metrics)
        
        # Improvement areas
        improvement_areas = self._identify_improvement_areas(metrics, trends)
        
        # Recommendations
        recommendations = self._generate_recommendations(metrics, trends)
        
        return DashboardReport(
            overall_quality_trend=overall_quality_trend,
            language_breakdown=language_breakdown,
            model_performance=model_performance,
            top_issues=top_issues,
            improvement_areas=improvement_areas,
            recommendations=recommendations,
            generated_at=datetime.now().isoformat(),
            time_period=f"Last {days} days",
            total_analyses=len(metrics)
        )
    
    def _analyze_language_breakdown(self, metrics: List[QualityMetric]) -> Dict[str, Dict[str, Any]]:
        """Analyze metrics by programming language."""
        language_stats = defaultdict(lambda: {
            'count': 0,
            'avg_quality': 0.0,
            'avg_bugs': 0.0,
            'avg_suggestions': 0.0,
            'files': set()
        })
        
        for metric in metrics:
            lang = metric.language
            language_stats[lang]['count'] += 1
            language_stats[lang]['avg_quality'] += metric.quality_score
            language_stats[lang]['avg_bugs'] += metric.bug_count
            language_stats[lang]['avg_suggestions'] += metric.suggestion_count
            language_stats[lang]['files'].add(metric.file_path)
        
        # Calculate averages
        for lang, stats in language_stats.items():
            count = stats['count']
            stats['avg_quality'] /= count
            stats['avg_bugs'] /= count
            stats['avg_suggestions'] /= count
            stats['unique_files'] = len(stats['files'])
            del stats['files']  # Remove set for JSON serialization
        
        return dict(language_stats)
    
    def _analyze_model_performance(self, metrics: List[QualityMetric]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance of different models."""
        model_stats = defaultdict(lambda: {
            'count': 0,
            'avg_quality': 0.0,
            'avg_execution_time': 0.0,
            'avg_bugs': 0.0,
            'avg_suggestions': 0.0
        })
        
        for metric in metrics:
            model = metric.model_name
            model_stats[model]['count'] += 1
            model_stats[model]['avg_quality'] += metric.quality_score
            model_stats[model]['avg_execution_time'] += metric.execution_time
            model_stats[model]['avg_bugs'] += metric.bug_count
            model_stats[model]['avg_suggestions'] += metric.suggestion_count
        
        # Calculate averages
        for model, stats in model_stats.items():
            count = stats['count']
            stats['avg_quality'] /= count
            stats['avg_execution_time'] /= count
            stats['avg_bugs'] /= count
            stats['avg_suggestions'] /= count
        
        return dict(model_stats)
    
    def _identify_top_issues(self, metrics: List[QualityMetric]) -> List[Dict[str, Any]]:
        """Identify the most common issues across the codebase."""
        # This would be enhanced with actual issue categorization
        # For now, we'll focus on files with the most bugs and suggestions
        
        file_issues = defaultdict(lambda: {'bugs': 0, 'suggestions': 0, 'quality_scores': []})
        
        for metric in metrics:
            file_issues[metric.file_path]['bugs'] += metric.bug_count
            file_issues[metric.file_path]['suggestions'] += metric.suggestion_count
            file_issues[metric.file_path]['quality_scores'].append(metric.quality_score)
        
        # Calculate average quality scores and sort by total issues
        top_issues = []
        for file_path, stats in file_issues.items():
            total_issues = stats['bugs'] + stats['suggestions']
            avg_quality = statistics.mean(stats['quality_scores'])
            
            top_issues.append({
                'file_path': file_path,
                'total_issues': total_issues,
                'bug_count': stats['bugs'],
                'suggestion_count': stats['suggestions'],
                'avg_quality_score': avg_quality,
                'priority': 'high' if total_issues > 10 or avg_quality < 0.5 else 'medium'
            })
        
        # Sort by total issues (descending)
        top_issues.sort(key=lambda x: x['total_issues'], reverse=True)
        return top_issues[:10]  # Return top 10
    
    def _identify_improvement_areas(self, metrics: List[QualityMetric], trends: Dict[str, TrendData]) -> List[str]:
        """Identify areas that need improvement."""
        improvement_areas = []
        
        # Check quality score trend
        quality_trend = trends.get('quality_score')
        if quality_trend and quality_trend.trend_direction == 'declining':
            improvement_areas.append("Overall code quality is declining - review recent changes")
        
        # Check for high bug counts
        avg_bugs = statistics.mean([m.bug_count for m in metrics])
        if avg_bugs > 5:
            improvement_areas.append(f"High average bug count ({avg_bugs:.1f}) - focus on testing and code review")
        
        # Check for performance issues
        avg_execution_time = statistics.mean([m.execution_time for m in metrics])
        if avg_execution_time > 2.0:
            improvement_areas.append(f"Slow analysis execution time ({avg_execution_time:.1f}s) - optimize analyzer performance")
        
        # Check language-specific issues
        language_stats = self._analyze_language_breakdown(metrics)
        for lang, stats in language_stats.items():
            if stats['avg_quality'] < 0.6:
                improvement_areas.append(f"Low quality code in {lang} files (avg: {stats['avg_quality']:.2f})")
        
        return improvement_areas
    
    def _generate_recommendations(self, metrics: List[QualityMetric], trends: Dict[str, TrendData]) -> List[str]:
        """Generate actionable recommendations based on trends."""
        recommendations = []
        
        # Quality score recommendations
        quality_trend = trends.get('quality_score')
        if quality_trend:
            if quality_trend.trend_direction == 'declining':
                recommendations.append("Implement stricter code review processes")
                recommendations.append("Add automated quality gates in CI/CD pipeline")
            elif quality_trend.trend_direction == 'improving':
                recommendations.append("Maintain current quality standards and processes")
        
        # Bug count recommendations
        bug_trend = trends.get('bug_count')
        if bug_trend and bug_trend.trend_direction == 'declining':
            recommendations.append("Continue current testing practices - they're working well")
        elif bug_trend and bug_trend.trend_direction == 'improving':
            recommendations.append("Increase test coverage and implement static analysis tools")
        
        # Model performance recommendations
        model_stats = self._analyze_model_performance(metrics)
        if len(model_stats) > 1:
            best_model = max(model_stats.items(), key=lambda x: x[1]['avg_quality'])
            recommendations.append(f"Consider using {best_model[0]} more frequently for better quality analysis")
        
        # General recommendations
        if len(metrics) < 10:
            recommendations.append("Increase analysis frequency to get better trend data")
        
        return recommendations
    
    def generate_charts(self, days: int = 30) -> Dict[str, str]:
        """
        Generate chart images as base64 strings.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary of chart images as base64 strings
        """
        metrics = self.get_metrics(days=days)
        if not metrics:
            return {}
        
        charts = {}
        
        # Quality score trend chart
        charts['quality_trend'] = self._create_quality_trend_chart(metrics)
        
        # Language breakdown chart
        charts['language_breakdown'] = self._create_language_breakdown_chart(metrics)
        
        # Model performance chart
        charts['model_performance'] = self._create_model_performance_chart(metrics)
        
        # Bug count trend chart
        charts['bug_trend'] = self._create_bug_trend_chart(metrics)
        
        return charts
    
    def _create_quality_trend_chart(self, metrics: List[QualityMetric]) -> str:
        """Create quality score trend chart."""
        plt.figure(figsize=(12, 6))
        
        # Group by date and calculate daily averages
        daily_quality = defaultdict(list)
        for metric in metrics:
            date = metric.timestamp.split('T')[0]
            daily_quality[date].append(metric.quality_score)
        
        dates = sorted(daily_quality.keys())
        avg_quality = [statistics.mean(daily_quality[date]) for date in dates]
        
        plt.plot(dates, avg_quality, marker='o', linewidth=2, markersize=6)
        plt.title('Code Quality Score Trend', fontsize=16, color='white')
        plt.xlabel('Date', fontsize=12, color='white')
        plt.ylabel('Average Quality Score', fontsize=12, color='white')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Add trend line
        if len(dates) > 1:
            x = np.arange(len(dates))
            z = np.polyfit(x, avg_quality, 1)
            p = np.poly1d(z)
            plt.plot(dates, p(x), "r--", alpha=0.8, label='Trend')
            plt.legend()
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_language_breakdown_chart(self, metrics: List[QualityMetric]) -> str:
        """Create language breakdown pie chart."""
        plt.figure(figsize=(10, 8))
        
        language_counts = Counter([m.language for m in metrics])
        
        if language_counts:
            labels = list(language_counts.keys())
            sizes = list(language_counts.values())
            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
            
            plt.pie(sizes, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            plt.title('Code Analysis by Language', fontsize=16, color='white')
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def _create_model_performance_chart(self, metrics: List[QualityMetric]) -> str:
        """Create model performance comparison chart."""
        plt.figure(figsize=(12, 6))
        
        model_stats = self._analyze_model_performance(metrics)
        
        if model_stats:
            models = list(model_stats.keys())
            avg_quality = [model_stats[model]['avg_quality'] for model in models]
            avg_time = [model_stats[model]['avg_execution_time'] for model in models]
            
            x = np.arange(len(models))
            width = 0.35
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Quality scores
            bars1 = ax1.bar(x - width/2, avg_quality, width, label='Avg Quality Score')
            ax1.set_xlabel('Model', color='white')
            ax1.set_ylabel('Average Quality Score', color='white')
            ax1.set_title('Model Quality Performance', color='white')
            ax1.set_xticks(x)
            ax1.set_xticklabels(models, rotation=45)
            ax1.grid(True, alpha=0.3)
            
            # Execution times
            bars2 = ax2.bar(x + width/2, avg_time, width, label='Avg Execution Time (s)')
            ax2.set_xlabel('Model', color='white')
            ax2.set_ylabel('Average Execution Time (s)', color='white')
            ax2.set_title('Model Performance', color='white')
            ax2.set_xticks(x)
            ax2.set_xticklabels(models, rotation=45)
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Convert to base64
            buffer = BytesIO()
            plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                       facecolor='#1a1a1a', edgecolor='none')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode()
            plt.close()
            
            return image_base64
        
        return ""
    
    def _create_bug_trend_chart(self, metrics: List[QualityMetric]) -> str:
        """Create bug count trend chart."""
        plt.figure(figsize=(12, 6))
        
        # Group by date and calculate daily averages
        daily_bugs = defaultdict(list)
        for metric in metrics:
            date = metric.timestamp.split('T')[0]
            daily_bugs[date].append(metric.bug_count)
        
        dates = sorted(daily_bugs.keys())
        avg_bugs = [statistics.mean(daily_bugs[date]) for date in dates]
        
        plt.plot(dates, avg_bugs, marker='o', linewidth=2, markersize=6, color='red')
        plt.title('Bug Count Trend', fontsize=16, color='white')
        plt.xlabel('Date', fontsize=12, color='white')
        plt.ylabel('Average Bug Count', fontsize=12, color='white')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        
        # Add trend line
        if len(dates) > 1:
            x = np.arange(len(dates))
            z = np.polyfit(x, avg_bugs, 1)
            p = np.poly1d(z)
            plt.plot(dates, p(x), "r--", alpha=0.8, label='Trend')
            plt.legend()
        
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=300, bbox_inches='tight', 
                   facecolor='#1a1a1a', edgecolor='none')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
