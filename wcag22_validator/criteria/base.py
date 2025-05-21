"""
Base class for WCAG 2.2 criteria.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from bs4 import BeautifulSoup

from ..reporter import ValidationIssue


class BaseCriterion(ABC):
    """
    Base class for all WCAG 2.2 criteria.
    
    Each criterion must implement the validate method to check
    HTML content against specific WCAG requirements.
    """
    
    def __init__(self):
        """Initialize the criterion."""
        # These will be set by implementing classes
        self.id = ""  # e.g., "1.1.1"
        self.name = ""  # e.g., "Non-text Content"
        self.level = ""  # "A", "AA", or "AAA"
        self.description = ""
        self.url = ""  # Reference URL to WCAG documentation
        
    @abstractmethod
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against this criterion.
        
        Args:
            soup: BeautifulSoup object of the HTML content.
            html_content: Original HTML content as string.
            
        Returns:
            List of ValidationIssue objects for issues found.
        """
        pass
    
    def create_issue(
        self,
        element_path: str,
        element_html: str,
        description: str,
        impact: str = "serious",
        how_to_fix: str = "",
        code_solution: str = "",
        line_number: Optional[int] = None,
        column_number: Optional[int] = None
    ) -> ValidationIssue:
        """
        Create a ValidationIssue for this criterion.
        
        Args:
            element_path: XPath or CSS selector to identify the element.
            element_html: HTML snippet of the element.
            description: Description of the issue.
            impact: Impact level ('critical', 'serious', 'moderate', or 'minor').
            how_to_fix: Guide on how to fix the issue.
            code_solution: Example code solution.
            line_number: Line number in the source code.
            column_number: Column number in the source code.
            
        Returns:
            ValidationIssue object.
        """
        return ValidationIssue(
            criterion_id=self.id,
            criterion_name=self.name,
            level=self.level,
            element_path=element_path,
            element_html=element_html,
            line_number=line_number,
            column_number=column_number,
            description=description,
            impact=impact,
            how_to_fix=how_to_fix,
            code_solution=code_solution,
            ref_url=self.url
        )
    
    def get_element_path(self, element) -> str:
        """
        Generate a CSS selector path for an element.
        
        Args:
            element: BeautifulSoup element.
            
        Returns:
            CSS selector string.
        """
        if not element:
            return ""
            
        if element.name == '[document]':
            return ""
            
        if element.get('id'):
            return f"#{element['id']}"
            
        if element.parent:
            parent_path = self.get_element_path(element.parent)
            if parent_path:
                # Get index of element among siblings of same type
                siblings = element.parent.find_all(element.name, recursive=False)
                index = siblings.index(element) + 1
                
                if len(siblings) > 1:
                    return f"{parent_path} > {element.name}:nth-of-type({index})"
                else:
                    return f"{parent_path} > {element.name}"
            
        return element.name
        
    def get_line_number(self, element, html_content: str) -> Optional[int]:
        """
        Try to find the line number for an element in the HTML content.
        
        Args:
            element: BeautifulSoup element.
            html_content: Original HTML content.
            
        Returns:
            Line number if found, None otherwise.
        """
        try:
            # This is approximate and may not work perfectly in all cases
            if hasattr(element, 'sourceline'):
                return element.sourceline
                
            # Alternative approach using string search
            # This is very basic and won't work well for complex HTML
            element_str = str(element)
            pos = html_content.find(element_str)
            
            if pos != -1:
                # Count newlines up to this position
                return html_content[:pos].count('\n') + 1
                
        except Exception:
            pass
            
        return None