"""
System Issues Management
Tracks technical system issues that require admin attention
"""

from datetime import datetime
from enum import Enum
from models import db
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Enum as SQLEnum

class IssueType(Enum):
    DATABASE_ERROR = "database_error"
    API_FAILURE = "api_failure"
    EXCEL_SYNC_ERROR = "excel_sync_error"
    SERVICE_DOWN = "service_down"
    CONFIG_MISSING = "config_missing"
    DATA_INTEGRITY = "data_integrity"
    NETWORK_ERROR = "network_error"
    AUTHENTICATION_ERROR = "authentication_error"

class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SystemIssue(db.Model):
    __tablename__ = 'system_issues'
    
    id = Column(Integer, primary_key=True)
    issue_type = Column(SQLEnum(IssueType), nullable=False)
    severity = Column(SQLEnum(IssueSeverity), nullable=False, default=IssueSeverity.MEDIUM)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    api_endpoint = Column(String(200), nullable=True)  # Which API broke
    error_details = Column(Text, nullable=True)  # Full error message
    first_occurred = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_occurred = Column(DateTime, nullable=False, default=datetime.utcnow)
    occurrence_count = Column(Integer, nullable=False, default=1)
    is_resolved = Column(Boolean, nullable=False, default=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, nullable=True)  # User ID who resolved
    resolution_notes = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'issue_type': self.issue_type.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'api_endpoint': self.api_endpoint,
            'error_details': self.error_details,
            'first_occurred': self.first_occurred.strftime('%Y-%m-%d %H:%M:%S'),
            'last_occurred': self.last_occurred.strftime('%Y-%m-%d %H:%M:%S'),
            'occurrence_count': self.occurrence_count,
            'is_resolved': self.is_resolved,
            'resolved_at': self.resolved_at.strftime('%Y-%m-%d %H:%M:%S') if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

class SystemIssueManager:
    """Manager class for handling system issues"""
    
    @staticmethod
    def report_issue(issue_type: IssueType, title: str, description: str, 
                    severity: IssueSeverity = IssueSeverity.MEDIUM,
                    api_endpoint: str = None, error_details: str = None):
        """Report a new system issue or update existing one"""
        
        # Check if similar issue exists (not resolved)
        existing_issue = SystemIssue.query.filter_by(
            issue_type=issue_type,
            title=title,
            is_resolved=False
        ).first()
        
        if existing_issue:
            # Update existing issue
            existing_issue.last_occurred = datetime.utcnow()
            existing_issue.occurrence_count += 1
            existing_issue.updated_at = datetime.utcnow()
            if error_details:
                existing_issue.error_details = error_details
            db.session.commit()
            return existing_issue
        else:
            # Create new issue
            new_issue = SystemIssue(
                issue_type=issue_type,
                severity=severity,
                title=title,
                description=description,
                api_endpoint=api_endpoint,
                error_details=error_details
            )
            db.session.add(new_issue)
            db.session.commit()
            return new_issue
    
    @staticmethod
    def resolve_issue(issue_id: int, resolved_by: int, resolution_notes: str = None):
        """Mark an issue as resolved"""
        issue = SystemIssue.query.get(issue_id)
        if issue and not issue.is_resolved:
            issue.is_resolved = True
            issue.resolved_at = datetime.utcnow()
            issue.resolved_by = resolved_by
            issue.resolution_notes = resolution_notes
            issue.updated_at = datetime.utcnow()
            db.session.commit()
            return True
        return False
    
    @staticmethod
    def get_active_issues():
        """Get all unresolved issues"""
        return SystemIssue.query.filter_by(is_resolved=False).order_by(
            SystemIssue.severity.desc(), 
            SystemIssue.last_occurred.desc()
        ).all()
    
    @staticmethod
    def get_active_issues_count():
        """Get count of unresolved issues"""
        return SystemIssue.query.filter_by(is_resolved=False).count()
    
    @staticmethod
    def get_issues_by_type(issue_type: IssueType):
        """Get issues by type"""
        return SystemIssue.query.filter_by(
            issue_type=issue_type,
            is_resolved=False
        ).all()

# Helper functions for common issue types
def report_api_failure(endpoint: str, error_message: str, severity: IssueSeverity = IssueSeverity.HIGH):
    """Report API failure"""
    return SystemIssueManager.report_issue(
        issue_type=IssueType.API_FAILURE,
        title=f"API Failure: {endpoint}",
        description=f"API endpoint {endpoint} is failing",
        api_endpoint=endpoint,
        error_details=error_message,
        severity=severity
    )

def report_database_error(error_message: str, severity: IssueSeverity = IssueSeverity.CRITICAL):
    """Report database connectivity issue"""
    return SystemIssueManager.report_issue(
        issue_type=IssueType.DATABASE_ERROR,
        title="Database Connection Error",
        description="Database connectivity issues detected",
        error_details=error_message,
        severity=severity
    )

def report_excel_sync_error(error_message: str, severity: IssueSeverity = IssueSeverity.MEDIUM):
    """Report Excel sync issue"""
    return SystemIssueManager.report_issue(
        issue_type=IssueType.EXCEL_SYNC_ERROR,
        title="Excel Sync Service Error",
        description="Excel synchronization service encountered errors",
        error_details=error_message,
        severity=severity
    )

def report_service_down(service_name: str, severity: IssueSeverity = IssueSeverity.HIGH):
    """Report service down"""
    return SystemIssueManager.report_issue(
        issue_type=IssueType.SERVICE_DOWN,
        title=f"Service Down: {service_name}",
        description=f"Critical service {service_name} is not running",
        severity=severity
    )
