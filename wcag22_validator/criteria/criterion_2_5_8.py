"""
WCAG 2.2 - 2.5.8 Target Size (Minimum) (Level AA)

The size of the target for pointer inputs is at least 24 by 24 CSS pixels.
"""

from typing import List, Dict, Optional, Set, Tuple
import re
from bs4 import BeautifulSoup, Tag

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_2_5_8(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 2.5.8: Target Size (Minimum).
    
    This criterion (new in WCAG 2.2) requires that interactive elements
    be large enough (at least 24x24 CSS pixels) to be easily activated
    by users with motor impairments.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "2.5.8"
        self.name = "Target Size (Minimum)"
        self.level = "AA"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html"
        self.description = """
        The size of the target for pointer inputs is at least 24 by 24 CSS pixels, except where:
        - Spacing: The target offset is at least 24 CSS pixels to every adjacent target.
        - Equivalent: The function can be achieved through an equivalent control that meets this criterion.
        - Inline: The target is in a sentence or its size is otherwise constrained by the line-height.
        - User Agent Control: The size of the target is determined by the user agent and is not modified by the author.
        - Essential: A particular presentation of the target is essential or is legally required for the information being conveyed.
        """
        
        # Minimum target size per criterion
        self.min_target_size = 24  # 24x24 CSS pixels
        
        # Elements that are commonly interactive and should meet the target size requirement
        self.interactive_elements = [
            'a[href]',
            'button',
            'input[type="button"]',
            'input[type="submit"]',
            'input[type="reset"]',
            'input[type="checkbox"]',
            'input[type="radio"]',
            'select',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="tab"]',
            '[role="menuitem"]',
            '[tabindex]:not([tabindex="-1"])',
            '[onclick]'
        ]
        
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 2.5.8 criterion.
        
        Note: Static analysis has limitations for this criterion since the actual
        rendered size depends on CSS. This implementation does its best to estimate
        target sizes based on inline styles and common patterns.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Find all potentially interactive elements
        for selector in self.interactive_elements:
            for element in soup.select(selector):
                # Skip elements that are likely to be exempt
                if self._is_likely_exempt(element):
                    continue
                
                # Check the element's dimensions from inline styles
                width, height = self._get_element_dimensions(element)
                
                if width is not None and height is not None:
                    # If we can determine exact dimensions, check if they're too small
                    if width < self.min_target_size or height < self.min_target_size:
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Interactive element has a target size smaller than {self.min_target_size}x{self.min_target_size} CSS pixels (found {width}x{height})",
                            impact="moderate",
                            how_to_fix=f"Increase the size of the interactive element to at least {self.min_target_size}x{self.min_target_size} CSS pixels, or ensure sufficient spacing around it.",
                            code_solution=self._generate_target_size_solution(element, width, height),
                            line_number=line_number
                        ))
                else:
                    # If we can't determine dimensions, check for potentially small targets
                    if self._is_potentially_small_target(element):
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Interactive element may have insufficient target size (cannot determine exact dimensions)",
                            impact="minor",
                            how_to_fix=f"Ensure the target size is at least {self.min_target_size}x{self.min_target_size} CSS pixels, or provide sufficient spacing around it.",
                            code_solution=self._generate_target_size_solution(element),
                            line_number=line_number
                        ))
        
        return issues
    
    def _is_likely_exempt(self, element: Tag) -> bool:
        """
        Check if an element is likely exempt from the target size requirement.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if the element is likely exempt
        """
        # Inline exemption: Check if the element is likely inline in text
        if element.parent and element.parent.name in ['p', 'li', 'td', 'span', 'div']:
            parent_text = element.parent.get_text()
            if len(parent_text) > len(element.get_text()) * 3:  # Rough heuristic for being in a block of text
                return True
        
        # User agent control exemption: Default form controls
        if element.name in ['input', 'select'] and not element.has_attr('style') and not element.has_attr('class'):
            return True
        
        # Check for ARIA attributes that might indicate an essential presentation
        if element.has_attr('aria-hidden') and element['aria-hidden'] == 'true':
            return True
            
        return False
    
    def _get_element_dimensions(self, element: Tag) -> Tuple[Optional[int], Optional[int]]:
        """
        Try to determine element dimensions from inline styles or attributes.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Tuple of (width, height) in CSS pixels, or (None, None) if can't determine
        """
        width = None
        height = None
        
        # Check inline style
        if element.has_attr('style'):
            style = element['style'].lower()
            
            # Try to extract width from inline style
            width_match = re.search(r'width\s*:\s*(\d+)px', style)
            if width_match:
                width = int(width_match.group(1))
            
            # Try to extract height from inline style
            height_match = re.search(r'height\s*:\s*(\d+)px', style)
            if height_match:
                height = int(height_match.group(1))
            
            # If we have min-width/min-height but not width/height
            if width is None:
                min_width_match = re.search(r'min-width\s*:\s*(\d+)px', style)
                if min_width_match:
                    width = int(min_width_match.group(1))
            
            if height is None:
                min_height_match = re.search(r'min-height\s*:\s*(\d+)px', style)
                if min_height_match:
                    height = int(min_height_match.group(1))
        
        # Check width/height attributes
        if width is None and element.has_attr('width'):
            try:
                width_value = element['width']
                if width_value.isdigit():
                    width = int(width_value)
                elif width_value.endswith('px'):
                    width = int(width_value[:-2])
            except (ValueError, IndexError):
                pass
        
        if height is None and element.has_attr('height'):
            try:
                height_value = element['height']
                if height_value.isdigit():
                    height = int(height_value)
                elif height_value.endswith('px'):
                    height = int(height_value[:-2])
            except (ValueError, IndexError):
                pass
        
        return width, height
    
    def _is_potentially_small_target(self, element: Tag) -> bool:
        """
        Check if an element is potentially too small based on heuristics.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if the element is potentially too small
        """
        # Check if this might be an icon-only button or link
        is_icon_only = False
        
        # Check for common icon classes
        if element.has_attr('class'):
            classes = ' '.join(element['class']).lower()
            icon_class_patterns = ['icon', 'fa-', 'material-icons', 'glyphicon', 'btn-sm', 'btn-xs', 'btn-icon']
            if any(pattern in classes for pattern in icon_class_patterns):
                is_icon_only = True
        
        # Check if the content is just a single character or entity
        element_text = element.get_text(strip=True)
        if len(element_text) == 1:
            is_icon_only = True
        
        # Check if it contains only an image and the image is likely small
        img = element.find('img')
        if img and not element_text:
            img_width, img_height = self._get_element_dimensions(img)
            if (img_width and img_width < self.min_target_size) or (img_height and img_height < self.min_target_size):
                is_icon_only = True
        
        # Check for SVG icon
        svg = element.find('svg')
        if svg and not element_text:
            svg_width, svg_height = self._get_element_dimensions(svg)
            if (svg_width and svg_width < self.min_target_size) or (svg_height and svg_height < self.min_target_size):
                is_icon_only = True
        
        return is_icon_only
    
    def _generate_target_size_solution(self, element: Tag, width: Optional[int] = None, height: Optional[int] = None) -> str:
        """
        Generate solution for a target size issue.
        
        Args:
            element: BeautifulSoup element
            width: Current width if known
            height: Current height if known
            
        Returns:
            HTML string with solution
        """
        element_path = self.get_element_path(element)
        
        if width is not None and height is not None:
            # We know the exact dimensions
            return f"""/* Add this to your CSS */
{element_path} {{
  /* Increase from {width}x{height}px to at least {self.min_target_size}x{self.min_target_size}px */
  min-width: {self.min_target_size}px;
  min-height: {self.min_target_size}px;
  
  /* If it's an inline element, make it block or inline-block */
  display: inline-block;
  
  /* Optional: Add padding to increase the clickable area */
  padding: 4px;
  
  /* Optional: Center contents if needed */
  text-align: center;
  line-height: {self.min_target_size}px;
}}

/* Alternative solution: Add sufficient spacing around the element */
{element_path} {{
  margin: 12px;  /* Half of the minimum target size on each side creates sufficient spacing */
}}

/* For your HTML element */
{str(element)}
"""
        else:
            # We don't know the exact dimensions
            return f"""/* Add this to your CSS */
{element_path} {{
  /* Ensure minimum target size */
  min-width: {self.min_target_size}px;
  min-height: {self.min_target_size}px;
  
  /* If it's an inline element, make it block or inline-block */
  display: inline-block;
  
  /* Optional: Add padding to increase the clickable area */
  padding: 4px;
}}

/* Alternative solution: Add sufficient spacing around small targets */
{element_path} {{
  margin: 12px;  /* Half of the minimum target size on each side creates sufficient spacing */
}}

/* For your HTML element */
{str(element)}
"""