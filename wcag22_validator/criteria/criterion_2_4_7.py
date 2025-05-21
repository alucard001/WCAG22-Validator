"""
WCAG 2.2 - 2.4.7 Focus Visible (Level AA)

Any keyboard operable user interface has a mode of operation where the 
keyboard focus indicator is visible.
"""

from typing import List, Dict, Optional, Set
import re
from bs4 import BeautifulSoup, Tag

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_2_4_7(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 2.4.7: Focus Visible.
    
    This criterion requires that keyboard focus indicators are visible when
    interactive elements receive focus.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "2.4.7"
        self.name = "Focus Visible"
        self.level = "AA"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/focus-visible.html"
        self.description = """
        Any keyboard operable user interface has a mode of operation where the 
        keyboard focus indicator is visible.
        """
        
        # CSS properties that might hide focus indicators
        self.focus_hiding_css = [
            'outline: none', 
            'outline:none',
            'outline: 0',
            'outline:0',
            ':focus { outline: none',
            ':focus{outline:none',
            'outline-style: none',
            'outline-width: 0'
        ]
        
        # CSS selectors that might indicate focus styles
        self.focus_style_selectors = [
            ':focus',
            '.focus',
            '[focus]',
            '.focused',
            ':focus-visible'
        ]
        
        # Naturally focusable elements that should show focus
        self.focusable_elements = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'select',
            'textarea',
            '[tabindex]:not([tabindex="-1"])',
            '[contenteditable="true"]'
        ]
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 2.4.7 criterion.
        
        This looks for elements that might hide focus indicators through CSS.
        Note: This is a limited static analysis that can't check the final
        rendered styles, so it may have false positives/negatives.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Check inline styles that might hide focus
        self._check_inline_styles(soup, issues, html_content)
        
        # Check style elements for focus hiding
        self._check_style_elements(soup, issues, html_content)
        
        # Check for custom focus styles without sufficient visibility
        self._check_custom_focus_styles(soup, issues, html_content)
        
        # Check focusable elements with no apparent focus styles
        self._check_focusable_without_focus_styles(soup, issues, html_content)
        
        return issues
    
    def _check_inline_styles(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check inline styles that might hide focus."""
        elements = soup.find_all(lambda tag: tag.has_attr('style'))
        
        for element in elements:
            style = element.get('style', '').lower()
            
            # Check if the style might be hiding the focus outline
            if any(focus_css in style for focus_css in self.focus_hiding_css):
                # Check if it's a focusable element
                if self._is_focusable(element):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description="Focusable element has inline styles that may hide the focus indicator",
                        impact="serious",
                        how_to_fix="Remove the outline:none or outline:0 style, or add a visible alternative focus style.",
                        code_solution=self._generate_focus_style_solution(element),
                        line_number=line_number
                    ))
    
    def _check_style_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check style elements for CSS that might hide focus."""
        style_elements = soup.find_all('style')
        
        for style_element in style_elements:
            style_content = style_element.string if style_element.string else ''
            
            # Check if the style might be hiding the focus outline
            if any(focus_css in style_content.lower() for focus_css in self.focus_hiding_css):
                element_path = self.get_element_path(style_element)
                element_html = str(style_element)
                line_number = self.get_line_number(style_element, html_content)
                
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Style element contains CSS that may hide focus indicators",
                    impact="serious",
                    how_to_fix="Ensure that all focusable elements have a visible focus indicator. Replace outline:none with a visible alternative.",
                    code_solution=self._generate_style_element_solution(style_element),
                    line_number=line_number
                ))
    
    def _check_custom_focus_styles(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check for potentially insufficient custom focus styles."""
        style_elements = soup.find_all('style')
        
        for style_element in style_elements:
            style_content = style_element.string if style_element.string else ''
            
            # Look for focus selectors
            for selector in self.focus_style_selectors:
                if selector in style_content:
                    # Check if the style seems sufficient (very basic check)
                    if not self._has_sufficient_focus_style(style_content, selector):
                        element_path = self.get_element_path(style_element)
                        element_html = str(style_element)
                        line_number = self.get_line_number(style_element, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Custom focus style using '{selector}' may not provide sufficient visibility",
                            impact="moderate",
                            how_to_fix="Ensure focus styles provide sufficient visibility. Use outline, border, background-color, or other properties to make focus clearly visible.",
                            code_solution=self._generate_sufficient_focus_style_solution(selector),
                            line_number=line_number
                        ))
    
    def _check_focusable_without_focus_styles(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """
        Check for focusable elements that don't appear to have focus styles.
        This is a heuristic since we can't know for sure without rendering.
        """
        # Find all focusable elements
        for selector in self.focusable_elements:
            elements = soup.select(selector)
            
            for element in elements:
                # Skip if it has an ID or class that suggests it might get focus styles
                if (element.has_attr('id') and any('focus' in id_name.lower() for id_name in element['id'].split())) or \
                   (element.has_attr('class') and any('focus' in class_name.lower() for class_name in element['class'])):
                    continue
                
                # Skip if it's a standard control that browsers style by default
                if element.name in ['input', 'textarea', 'select'] and not self._has_potential_focus_override(element):
                    continue
                
                # Check for custom elements or roles that may need explicit focus styling
                if (element.name in ['div', 'span'] or 
                    (element.has_attr('role') and element['role'] in ['button', 'link', 'menuitem', 'tab'])):
                    
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description="Interactive element may not have visible focus indicator",
                        impact="moderate",
                        how_to_fix="Add explicit focus styles to ensure keyboard focus is visible.",
                        code_solution=self._generate_focus_style_solution(element),
                        line_number=line_number
                    ))
    
    def _is_focusable(self, element: Tag) -> bool:
        """
        Check if an element is focusable.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if the element is focusable
        """
        # Check if it's a naturally focusable element
        if element.name in ['a', 'button', 'input', 'select', 'textarea'] and element.name != 'input' and element.get('type') != 'hidden':
            return True
        
        # Check for href attribute on anchors
        if element.name == 'a' and element.has_attr('href'):
            return True
        
        # Check for tabindex
        if element.has_attr('tabindex') and element['tabindex'] != '-1':
            return True
        
        # Check for contenteditable
        if element.has_attr('contenteditable') and element['contenteditable'] != 'false':
            return True
        
        # Check for WAI-ARIA roles that imply focusability
        if element.has_attr('role') and element['role'] in ['button', 'link', 'checkbox', 'radio', 'tab', 'menuitem']:
            return True
        
        return False
    
    def _has_potential_focus_override(self, element: Tag) -> bool:
        """
        Check if an element might have styles that override default focus.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if the element might override default focus
        """
        # Check for inline styles
        if element.has_attr('style'):
            style = element['style'].lower()
            if any(focus_css in style for focus_css in self.focus_hiding_css):
                return True
        
        # Check for classes that might indicate a framework that could override focus
        if element.has_attr('class'):
            class_str = ' '.join(element['class']).lower()
            framework_classes = ['btn', 'button', 'form-control', 'input-', 'select-', 'custom-']
            if any(framework_class in class_str for framework_class in framework_classes):
                return True
        
        return False
    
    def _has_sufficient_focus_style(self, style_content: str, selector: str) -> bool:
        """
        Check if a focus style seems sufficient (very basic heuristic).
        
        Args:
            style_content: CSS content as string
            selector: Focus selector to check
            
        Returns:
            True if the style seems sufficient
        """
        # Try to find the full selector and its declaration block
        pattern = rf'{selector}[^{{]*{{([^}}]*)}}'
        match = re.search(pattern, style_content, re.IGNORECASE | re.DOTALL)
        
        if not match:
            return False
        
        declarations = match.group(1).lower()
        
        # Check for properties that would make focus visible
        visible_properties = [
            'outline:',
            'border:',
            'background-color:',
            'background:',
            'box-shadow:',
            'text-decoration:',
            'color:',
            'font-weight:',
            'transform:'
        ]
        
        return any(prop in declarations for prop in visible_properties)
    
    def _generate_focus_style_solution(self, element: Tag) -> str:
        """
        Generate solution for an element missing focus styles.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            HTML string with solution
        """
        element_selector = self.get_element_path(element)
        
        return f"""/* Add this to your CSS */
{element_selector}:focus {{
  outline: 2px solid #4d90fe;  /* Blue focus ring */
  outline-offset: 2px;        /* Offset to make it stand out */
}}

/* If you must remove the default outline, always provide an alternative */
{element_selector}:focus {{
  outline: none;              /* Remove default if needed */
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);  /* Alternative visible focus style */
}}

/* For your HTML element */
{str(element)}
"""
    
    def _generate_style_element_solution(self, style_element: Tag) -> str:
        """
        Generate solution for problematic style element.
        
        Args:
            style_element: BeautifulSoup style element
            
        Returns:
            HTML string with solution
        """
        style_content = style_element.string if style_element.string else ''
        
        # Replace outline:none with a visible focus style
        for focus_css in self.focus_hiding_css:
            if focus_css in style_content.lower():
                improved_style = style_content.replace(
                    focus_css,
                    '/* Replace outline:none with visible focus styles */\n  outline: 2px solid #4d90fe; outline-offset: 2px;'
                )
                
                return f"""<style>
{improved_style}
</style>"""
        
        # Fallback if specific replacement couldn't be made
        return f"""<style>
/* Original style with problematic focus handling */
{style_content}

/* Add these improved focus styles */
a:focus, button:focus, input:focus, select:focus, textarea:focus, [tabindex]:focus {{
  outline: 2px solid #4d90fe;
  outline-offset: 2px;
}}
</style>"""
    
    def _generate_sufficient_focus_style_solution(self, selector: str) -> str:
        """
        Generate solution for insufficient focus styles.
        
        Args:
            selector: Focus selector
            
        Returns:
            CSS string with solution
        """
        return f"""/* Replace your current {selector} style with this improved version */
{selector} {{
  /* Clear visibility enhancements */
  outline: 2px solid #4d90fe;  /* Blue focus ring */
  outline-offset: 2px;         /* Offset to make it stand out */
  
  /* Optional additional enhancements */
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.5);
  transition: outline 0.1s ease-in-out;
}}

/* For high contrast mode support */
@media screen and (forced-colors: active) {{
  {selector} {{
    outline: 2px solid HighlightText;
    outline-offset: 2px;
  }}
}}
"""