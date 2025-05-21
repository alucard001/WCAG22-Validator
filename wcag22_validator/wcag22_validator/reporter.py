"""
Reporter module for WCAG 2.2 validation results.
"""

from typing import Dict, List, Optional, Union
from dataclasses import dataclass
import json
from collections import defaultdict
import html as html_escape_module  # Alias to avoid conflict


@dataclass
class ValidationIssue:
    """
    Represents a WCAG validation issue.
    """
    criterion_id: str  # e.g., '1.1.1'
    criterion_name: str  # e.g., 'Non-text Content'
    level: str  # 'A', 'AA', or 'AAA'
    element_path: str  # XPath or CSS selector to identify the element
    element_html: str  # HTML snippet of the element
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    issue_type: str = "error"  # 'error', 'warning', or 'info'
    description: str = ""  # Description of the issue
    impact: str = "serious"  # 'critical', 'serious', 'moderate', or 'minor'
    how_to_fix: str = ""  # Guide on how to fix the issue
    code_solution: str = ""  # Example code solution
    ref_url: str = ""  # URL to WCAG reference


class WCAGReporter:
    """
    Reporter class for WCAG 2.2 validation results.
    
    This class collects and organizes validation issues, and provides
    methods to generate reports in various formats.
    """
    
    def __init__(self):
        """Initialize the reporter."""
        self.issues: List[ValidationIssue] = []
        self.errors: Dict[str, str] = {}  # Criterion ID -> error message
        self.url: Optional[str] = None
        self.execution_time: float = 0
        
    def clear(self):
        """Clear all issues and errors."""
        self.issues = []
        self.errors = {}
        self.url = None
        self.execution_time = 0
        
    def add_issue(self, issue: ValidationIssue):
        """
        Add a validation issue.
        
        Args:
            issue: The validation issue to add.
        """
        self.issues.append(issue)
        
    def add_error(self, criterion_id: str, error_message: str):
        """
        Add an error that occurred during validation.
        
        Args:
            criterion_id: ID of the criterion where the error occurred.
            error_message: Error message.
        """
        self.errors[criterion_id] = error_message
        
    def get_issues_by_impact(self) -> Dict[str, List[ValidationIssue]]:
        """
        Group issues by impact level.
        
        Returns:
            Dictionary mapping impact level to list of issues.
        """
        result = defaultdict(list)
        for issue in self.issues:
            result[issue.impact].append(issue)
        return dict(result)
        
    def get_issues_by_criterion(self) -> Dict[str, List[ValidationIssue]]:
        """
        Group issues by criterion ID.
        
        Returns:
            Dictionary mapping criterion ID to list of issues.
        """
        result = defaultdict(list)
        for issue in self.issues:
            result[issue.criterion_id].append(issue)
        return dict(result)
        
    def get_issues_by_level(self) -> Dict[str, List[ValidationIssue]]:
        """
        Group issues by conformance level.
        
        Returns:
            Dictionary mapping conformance level to list of issues.
        """
        result = defaultdict(list)
        for issue in self.issues:
            result[issue.level].append(issue)
        return dict(result)
    
    @property
    def has_issues(self) -> bool:
        """
        Check if there are any issues.
        
        Returns:
            True if there are issues, False otherwise.
        """
        return len(self.issues) > 0
    
    @property
    def total_issues(self) -> int:
        """
        Get the total number of issues.
        
        Returns:
            Total number of issues.
        """
        return len(self.issues)
    
    @property
    def has_errors(self) -> bool:
        """
        Check if there were any errors during validation.
        
        Returns:
            True if there were errors, False otherwise.
        """
        return len(self.errors) > 0
        
    def to_dict(self) -> Dict:
        """
        Convert report to dictionary.
        
        Returns:
            Dictionary representation of the report.
        """
        return {
            "url": self.url,
            "total_issues": self.total_issues,
            "issues_by_impact": {
                impact: [issue.__dict__ for issue in issues]
                for impact, issues in self.get_issues_by_impact().items()
            },
            "issues_by_criterion": {
                criterion: [issue.__dict__ for issue in issues]
                for criterion, issues in self.get_issues_by_criterion().items()
            },
            "issues_by_level": {
                level: [issue.__dict__ for issue in issues]
                for level, issues in self.get_issues_by_level().items()
            },
            "errors": self.errors,
            "execution_time": self.execution_time
        }
        
    def to_json(self) -> str:
        """
        Convert report to JSON.
        
        Returns:
            JSON string representation of the report.
        """
        return json.dumps(self.to_dict(), indent=2)
        
    def to_html(self) -> str:
        """
        Generate an HTML report.
        
        Returns:
            HTML string representation of the report.
        """
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>WCAG 2.2 Validation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 20px; }}
                h1, h2, h3 {{ color: #333; }}
                .summary {{ background-color: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                .issues {{ margin-bottom: 30px; }}
                .issue {{ border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 5px; }}
                .critical {{ border-left: 5px solid #d9534f; }}
                .serious {{ border-left: 5px solid #f0ad4e; }}
                .moderate {{ border-left: 5px solid #5bc0de; }}
                .minor {{ border-left: 5px solid #5cb85c; }}
                .element {{ background-color: #f8f9fa; padding: 10px; border-radius: 3px; overflow-x: auto; }}
                .how-to-fix {{ background-color: #e9f7ef; padding: 10px; border-radius: 3px; margin-top: 10px; }}
                .code-solution {{ background-color: #f0f0f0; padding: 10px; border-radius: 3px; margin-top: 10px; font-family: monospace; white-space: pre-wrap; }}
                .errors {{ color: #d9534f; }}
                a {{ color: #0275d8; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                
                /* Styles for highlighting code */
                .highlight-issue {{ background-color: #ffdddd; border: 1px solid #ffaaaa; padding: 2px; border-radius: 2px; }}
                .highlight-fix {{ background-color: #ddffdd; border: 1px solid #aaffaa; padding: 2px; border-radius: 2px; }}
                
                /* Tabs for switching between issue/solution */
                .tabs {{ display: flex; margin-bottom: 10px; }}
                .tab {{ padding: 10px 15px; cursor: pointer; border: 1px solid #ddd; border-bottom: none; border-radius: 5px 5px 0 0; background-color: #f0f0f0; }}
                .tab.active {{ background-color: #fff; border-bottom: 1px solid #fff; }}
                .tab-content {{ padding: 15px; border: 1px solid #ddd; border-top: none; border-radius: 0 0 5px 5px; }}
            </style>
            <script>
                function openTab(evt, tabName, issueId) {{
                    // Get all elements with class="tab-content" and hide them
                    var tabcontent = document.querySelectorAll('.issue-' + issueId + ' .tab-content');
                    for (var i = 0; i < tabcontent.length; i++) {{
                        tabcontent[i].style.display = "none";
                    }}

                    // Get all elements with class="tab" and remove the class "active"
                    var tablinks = document.querySelectorAll('.issue-' + issueId + ' .tab');
                    for (var i = 0; i < tablinks.length; i++) {{
                        tablinks[i].className = tablinks[i].className.replace(" active", "");
                    }}

                    // Show the current tab, and add an "active" class to the button that opened the tab
                    document.getElementById(tabName).style.display = "block";
                    evt.currentTarget.className += " active";
                }}
            </script>
        </head>
        <body>
            <h1>WCAG 2.2 Validation Report</h1>
            
            <div class="summary">
                <h2>Summary</h2>
                <p><strong>URL:</strong> {self.url or 'N/A'}</p>
                <p><strong>Total Issues:</strong> {self.total_issues}</p>
                <p><strong>Execution Time:</strong> {self.execution_time:.2f} seconds</p>
            </div>
        """
        
        if self.has_errors:
            html += f"""
            <div class="errors">
                <h2>Validation Errors</h2>
                <p>The following errors occurred during validation:</p>
                <ul>
            """
            for criterion_id, error_message in self.errors.items():
                html += f"<li><strong>{criterion_id}:</strong> {html_escape_module.escape(error_message)}</li>"
            html += "</ul></div>"
        
        # Group by impact
        impacts = ["critical", "serious", "moderate", "minor"]
        issues_by_impact = self.get_issues_by_impact()
        
        html += '<div class="issues"><h2>Issues by Impact</h2>'
        
        for i, impact in enumerate(impacts):
            if impact in issues_by_impact:
                html += f'<h3>{impact.capitalize()} Impact ({len(issues_by_impact[impact])} issues)</h3>'
                
                for j, issue in enumerate(issues_by_impact[impact]):
                    issue_id = f"issue-{i}-{j}"
                    
                    html += f"""
                    <div class="issue {impact} issue-{issue_id}">
                        <h4>
                            <a href="{issue.ref_url}" target="_blank">
                                {issue.criterion_id} {issue.criterion_name} (Level {issue.level})
                            </a>
                        </h4>
                        <p><strong>Description:</strong> {html_escape_module.escape(issue.description)}</p>
                        
                        <div class="tabs">
                            <button class="tab active" onclick="openTab(event, '{issue_id}-element', '{issue_id}')">Element</button>
                            <button class="tab" onclick="openTab(event, '{issue_id}-fix', '{issue_id}')">How to Fix</button>
                        </div>
                        
                        <div id="{issue_id}-element" class="tab-content" style="display: block;">
                            <p><strong>Element:</strong> {html_escape_module.escape(issue.element_path)}</p>
                            <div class="element">
                                <pre>{html_escape_module.escape(issue.element_html)}</pre>
                            </div>
                        </div>
                        
                        <div id="{issue_id}-fix" class="tab-content" style="display: none;">
                    """
                    
                    if issue.how_to_fix:
                        html += f"""
                        <div class="how-to-fix">
                            <p><strong>How to Fix:</strong></p>
                            <p>{html_escape_module.escape(issue.how_to_fix)}</p>
                        </div>
                        """
                        
                    if issue.code_solution:
                        html += f"""
                        <div class="code-solution">
                            <p><strong>Code Solution:</strong></p>
                            <pre>{html_escape_module.escape(issue.code_solution)}</pre>
                        </div>
                        """
                        
                    html += "</div></div>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html
        
    def to_markdown(self) -> str:
        """
        Generate a Markdown report.
        
        Returns:
            Markdown string representation of the report.
        """
        md = f"# WCAG 2.2 Validation Report\n\n"
        
        md += "## Summary\n\n"
        md += f"- **URL:** {self.url or 'N/A'}\n"
        md += f"- **Total Issues:** {self.total_issues}\n"
        md += f"- **Execution Time:** {self.execution_time:.2f} seconds\n\n"
        
        if self.has_errors:
            md += "## Validation Errors\n\n"
            md += "The following errors occurred during validation:\n\n"
            for criterion_id, error_message in self.errors.items():
                md += f"- **{criterion_id}:** {error_message}\n"
            md += "\n"
        
        # Group by impact
        impacts = ["critical", "serious", "moderate", "minor"]
        issues_by_impact = self.get_issues_by_impact()
        
        md += "## Issues by Impact\n\n"
        
        for impact in impacts:
            if impact in issues_by_impact:
                md += f"### {impact.capitalize()} Impact ({len(issues_by_impact[impact])} issues)\n\n"
                
                for i, issue in enumerate(issues_by_impact[impact], 1):
                    md += f"#### {i}. {issue.criterion_id} {issue.criterion_name} (Level {issue.level})\n\n"
                    md += f"- **Description:** {issue.description}\n"
                    md += f"- **Element:** {issue.element_path}\n"
                    md += f"- **HTML:** `{issue.element_html}`\n"
                    
                    if issue.how_to_fix:
                        md += f"- **How to Fix:** {issue.how_to_fix}\n"
                        
                    if issue.code_solution:
                        md += f"- **Code Solution:**\n\n```html\n{issue.code_solution}\n```\n"
                        
                    if issue.ref_url:
                        md += f"- **Reference:** [{issue.criterion_id} {issue.criterion_name}]({issue.ref_url})\n"
                        
                    md += "\n"
        
        return md
    
    def summary(self) -> str:
        """
        Generate a brief summary of issues.
        
        Returns:
            String containing a summary of issues.
        """
        issues_by_level = self.get_issues_by_level()
        issues_by_impact = self.get_issues_by_impact()
        
        summary = "WCAG 2.2 Validation Summary\n"
        summary += "=========================\n\n"
        
        summary += f"Total Issues: {self.total_issues}\n\n"
        
        summary += "Issues by Level:\n"
        for level in ["A", "AA", "AAA"]:
            if level in issues_by_level:
                summary += f"- Level {level}: {len(issues_by_level[level])} issues\n"
                
        summary += "\nIssues by Impact:\n"
        for impact in ["critical", "serious", "moderate", "minor"]:
            if impact in issues_by_impact:
                summary += f"- {impact.capitalize()}: {len(issues_by_impact[impact])} issues\n"
                
        return summary