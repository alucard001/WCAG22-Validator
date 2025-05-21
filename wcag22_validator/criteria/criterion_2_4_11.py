"""
WCAG 2.2 - 2.4.11 Focus Not Obscured (Minimum) (Level AA)

When a user interface component receives keyboard focus, the component is not
entirely hidden due to author-created content.
"""

from typing import List, Optional
import re
from bs4 import BeautifulSoup, Tag

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_2_4_11(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 2.4.11: Focus Not Obscured (Minimum).
    
    This criterion requires that when a component receives keyboard focus, 
    it is not entirely hidden due to author-created content.
    
    Note: This criterion is best validated with dynamic browser testing since it's about
    focus behavior which is difficult to check with static analysis. This implementation
    provides a best-effort static analysis looking for potential issues.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "2.4.11"
        self.name = "Focus Not Obscured (Minimum)"
        self.level = "AA"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html"
        self.description = """
        When a user interface component receives keyboard focus, the component is not
        entirely hidden due to author-created content.
        """
        
        # CSS properties that may cause elements to obscure focused elements
        self.potential_obscuring_properties = [
            'position: fixed', 
            'position: sticky',
            'position: absolute',
            'z-index',
            'transform: translate',
            'top: 0',
            'bottom: 0',
            'left: 0',
            'right: 0'
        ]
        
        # Classes commonly used for fixed position elements
        self.potential_obscuring_classes = [
            'header', 'navbar', 'nav-fixed', 'sticky', 'fixed', 'fixed-top',
            'sticky-top', 'navbar-fixed', 'fixed-bottom', 'modal', 'overlay',
            'tooltip', 'dropdown', 'popover'
        ]
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 2.4.11 criterion.
        
        This is a limited static analysis that identifies potential issues.
        Full validation requires dynamic browser testing.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Find potentially obscuring elements (fixed/sticky positioned)
        potentially_obscuring_elements = self._find_potentially_obscuring_elements(soup)
        
        # Find all focusable elements
        focusable_elements = self._find_focusable_elements(soup)
        
        # Check for potential issues where focusable elements could be obscured
        for focusable in focusable_elements:
            element_path = self.get_element_path(focusable)
            element_html = str(focusable)
            line_number = self.get_line_number(focusable, html_content)
            
            # Check for potentially conflicting elements
            for obscuring in potentially_obscuring_elements:
                # Skip self-comparison
                if obscuring is focusable:
                    continue
                    
                # Check if this is a potential issue based on element types and positions
                if self._could_potentially_obscure(obscuring, focusable):
                    obscuring_path = self.get_element_path(obscuring)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description=f"Focusable element could potentially be obscured by fixed/sticky element: {obscuring_path}",
                        impact="moderate",
                        how_to_fix="Ensure that when this element receives focus, it is not entirely hidden behind fixed or sticky content. Add code to adjust the position of fixed elements when this element receives focus.",
                        code_solution=self._generate_focus_solution(focusable, obscuring),
                        line_number=line_number
                    ))
        
        return issues
    
    def _find_potentially_obscuring_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Find elements that could potentially obscure focused elements.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of potentially obscuring elements
        """
        result = []
        
        # Find elements with inline styles that could cause obscuring
        for element in soup.find_all(lambda tag: tag.has_attr('style')):
            style = element.get('style', '').lower()
            
            if any(prop in style for prop in self.potential_obscuring_properties):
                result.append(element)
        
        # Find elements with classes commonly used for fixed/sticky elements
        for class_name in self.potential_obscuring_classes:
            elements = soup.find_all(class_=re.compile(class_name, re.IGNORECASE))
            result.extend(elements)
        
        # Find header, footer, navbar elements (commonly fixed or sticky)
        result.extend(soup.find_all(['header', 'nav']))
        result.extend(soup.find_all(id=re.compile(r'header|navbar|nav', re.IGNORECASE)))
        
        # Find potential modal or overlay elements
        result.extend(soup.find_all(id=re.compile(r'modal|overlay|dialog|popup', re.IGNORECASE)))
        
        return result
    
    def _find_focusable_elements(self, soup: BeautifulSoup) -> List[Tag]:
        """
        Find all potentially focusable elements.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            List of focusable elements
        """
        result = []
        
        # Naturally focusable elements
        result.extend(soup.find_all(['a', 'button', 'input', 'select', 'textarea']))
        
        # Elements with tabindex
        result.extend(soup.find_all(lambda tag: tag.has_attr('tabindex') and tag['tabindex'] != '-1'))
        
        # Elements with click handlers (might be keyboard focusable)
        result.extend(soup.find_all(lambda tag: any(attr for attr in tag.attrs if attr.startswith('on'))))
        
        # Elements with role that implies focusability
        focusable_roles = ['button', 'link', 'checkbox', 'radio', 'menuitem', 'tab']
        result.extend(soup.find_all(lambda tag: tag.has_attr('role') and tag['role'] in focusable_roles))
        
        return result
    
    def _could_potentially_obscure(self, obscuring: Tag, focusable: Tag) -> bool:
        """
        Determine if one element could potentially obscure another.
        
        This is a heuristic since we can't do real layout calculation
        in static analysis.
        
        Args:
            obscuring: Potentially obscuring element
            focusable: Focusable element that might be obscured
            
        Returns:
            True if there's a potential obscuring issue
        """
        # If the obscuring element is a parent of the focusable element, it's less likely to be an issue
        if focusable in obscuring.find_all():
            return False
        
        # Check for modals, tooltips, or overlays that might appear on focus/click
        if self._is_likely_modal_or_overlay(obscuring):
            return True
        
        # Check for fixed headers or navbars that could obscure elements near the top
        if self._is_likely_fixed_header(obscuring):
            # Heuristic: check if focusable element might be near the top
            return True
        
        # Check for fixed footers that could obscure elements near the bottom
        if self._is_likely_fixed_footer(obscuring):
            # Heuristic: check if focusable element might be near the bottom
            return True
        
        return False
    
    def _is_likely_modal_or_overlay(self, element: Tag) -> bool:
        """
        Check if an element is likely a modal, tooltip, or overlay.
        
        Args:
            element: Element to check
            
        Returns:
            True if element is likely a modal or overlay
        """
        # Check for modal-related properties
        if element.has_attr('class'):
            classes = ' '.join(element['class']).lower()
            if any(term in classes for term in ['modal', 'overlay', 'dialog', 'popup', 'tooltip', 'dropdown']):
                return True
        
        # Check for modal-related IDs
        if element.has_attr('id'):
            element_id = element['id'].lower()
            if any(term in element_id for term in ['modal', 'overlay', 'dialog', 'popup']):
                return True
        
        # Check for ARIA roles
        if element.has_attr('role') and element['role'] in ['dialog', 'alertdialog', 'tooltip']:
            return True
        
        # Check for common modal style properties
        if element.has_attr('style'):
            style = element['style'].lower()
            if 'position: fixed' in style and ('z-index' in style or 'opacity' in style):
                return True
        
        return False
    
    def _is_likely_fixed_header(self, element: Tag) -> bool:
        """
        Check if an element is likely a fixed header or navbar.
        
        Args:
            element: Element to check
            
        Returns:
            True if element is likely a fixed header
        """
        # Check element type
        if element.name in ['header', 'nav']:
            return True
        
        # Check for header-related classes
        if element.has_attr('class'):
            classes = ' '.join(element['class']).lower()
            if any(term in classes for term in ['header', 'navbar', 'nav', 'fixed-top', 'sticky-top']):
                return True
        
        # Check for header-related IDs
        if element.has_attr('id'):
            element_id = element['id'].lower()
            if any(term in element_id for term in ['header', 'navbar', 'nav']):
                return True
        
        # Check for fixed position styles
        if element.has_attr('style'):
            style = element['style'].lower()
            if ('position: fixed' in style or 'position: sticky' in style) and ('top: 0' in style or 'top:0' in style):
                return True
        
        return False
    
    def _is_likely_fixed_footer(self, element: Tag) -> bool:
        """
        Check if an element is likely a fixed footer.
        
        Args:
            element: Element to check
            
        Returns:
            True if element is likely a fixed footer
        """
        # Check element type
        if element.name == 'footer':
            return True
        
        # Check for footer-related classes
        if element.has_attr('class'):
            classes = ' '.join(element['class']).lower()
            if any(term in classes for term in ['footer', 'fixed-bottom']):
                return True
        
        # Check for footer-related IDs
        if element.has_attr('id'):
            element_id = element['id'].lower()
            if 'footer' in element_id:
                return True
        
        # Check for fixed position styles at bottom
        if element.has_attr('style'):
            style = element['style'].lower()
            if ('position: fixed' in style or 'position: sticky' in style) and ('bottom: 0' in style or 'bottom:0' in style):
                return True
        
        return False
    
    def _generate_focus_solution(self, focusable: Tag, obscuring: Tag) -> str:
        """
        Generate a solution for focus obscuring issue.
        
        Args:
            focusable: The focusable element
            obscuring: The potentially obscuring element
            
        Returns:
            Code solution as string
        """
        focusable_path = self.get_element_path(focusable)
        obscuring_path = self.get_element_path(obscuring)
        
        if self._is_likely_modal_or_overlay(obscuring):
            return f"""// JavaScript solution to prevent the modal/overlay from obscuring focused elements
document.querySelector('{focusable_path}').addEventListener('focus', function() {{
  // Option 1: If the overlay is shown by default but should be hidden on focus
  document.querySelector('{obscuring_path}').style.display = 'none';
  
  // Option 2: If the overlay is positioned, adjust its position or z-index
  // document.querySelector('{obscuring_path}').style.zIndex = '0';
  
  // Option 3: Scroll the focused element into view ensuring it's not obscured
  this.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
}});"""
        
        if self._is_likely_fixed_header(obscuring) or self._is_likely_fixed_footer(obscuring):
            return f"""// CSS solution using :focus-within to adjust fixed header/footer when child elements are focused
{obscuring_path} {{
  position: fixed;
  /* other styles */
}}

/* When an element within the document receives focus, adjust the fixed element */
body:focus-within {obscuring_path} {{
  /* Option 1: Temporarily make it position:absolute instead of fixed */
  position: absolute;
  
  /* Option 2: Add padding to ensure the focused element is visible */
  /* padding-top: 40px; */
  
  /* Option 3: Adjust z-index to ensure focused elements appear above */
  /* z-index: 0; */
}}

// Alternative JavaScript solution
document.querySelector('{focusable_path}').addEventListener('focus', function() {{
  // When this element is focused, adjust the header/footer to ensure it's visible
  const headerEl = document.querySelector('{obscuring_path}');
  
  // Save original position to restore later
  const originalPosition = headerEl.style.position;
  
  // Temporarily adjust position
  headerEl.style.position = 'absolute';  // or adjust z-index, opacity, etc.
  
  // When focus leaves, restore original position
  this.addEventListener('blur', function() {{
    headerEl.style.position = originalPosition;
  }}, {{ once: true }});  // Use once:true to clean up the event listener
  
  // Ensure the focused element is fully visible
  this.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
}});"""
        
        # Generic solution
        return f"""// Generic solution to prevent elements from being obscured during focus
// Add this JavaScript to your site

document.querySelector('{focusable_path}').addEventListener('focus', function() {{
  // Get the potentially obscuring element
  const obscuringElement = document.querySelector('{obscuring_path}');
  
  // Get bounding rectangles to determine if there's overlap
  const focusedRect = this.getBoundingClientRect();
  const obscuringRect = obscuringElement.getBoundingClientRect();
  
  // Check if the focused element is completely covered
  const isCompletelyObscured = 
    focusedRect.top >= obscuringRect.top &&
    focusedRect.bottom <= obscuringRect.bottom &&
    focusedRect.left >= obscuringRect.left &&
    focusedRect.right <= obscuringRect.right;
  
  if (isCompletelyObscured) {{
    // Option 1: Temporarily adjust the obscuring element's styles
    obscuringElement.style.setProperty('z-index', '-1', 'important');
    
    // Option 2: Scroll the focused element into view
    this.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    
    // Option 3: If it's a modal/overlay, temporarily hide it
    // obscuringElement.style.display = 'none';
    
    // Restore original state when focus leaves
    this.addEventListener('blur', function() {{
      obscuringElement.style.removeProperty('z-index');
      // If using option 3: obscuringElement.style.display = '';
    }}, {{ once: true }});
  }}
}});"""