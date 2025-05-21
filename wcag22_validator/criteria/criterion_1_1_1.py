"""
WCAG 2.2 - 1.1.1 Non-text Content (Level A)

All non-text content that is presented to the user has a text alternative
that serves the equivalent purpose.
"""

from typing import List, Set
import re
from bs4 import BeautifulSoup, Tag

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_1_1_1(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 1.1.1: Non-text Content.
    
    This criterion requires that all non-text content (images, icons, etc.)
    has appropriate text alternatives.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "1.1.1"
        self.name = "Non-text Content"
        self.level = "A"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/non-text-content.html"
        self.description = """
        All non-text content that is presented to the user has a text alternative
        that serves the equivalent purpose, except for the situations listed in the
        WCAG documentation.
        """
        
        # Common decorative class names
        self.decorative_classes = {
            'decorative', 'decoration', 'ornament', 'bg', 'background',
            'icon-decorative', 'visual-separator', 'separator',
        }
        
        # Placeholder alt texts that don't provide meaningful alternatives
        self.placeholder_alt_texts = {
            'image', 'photo', 'picture', 'pic', 'graphic', 'logo', 'icon',
            'img', 'photograph', 'photograph of', 'image of', 'picture of',
        }
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 1.1.1 criterion.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Check img elements
        self._check_img_elements(soup, issues, html_content)
        
        # Check svg elements
        self._check_svg_elements(soup, issues, html_content)
        
        # Check area elements (image maps)
        self._check_area_elements(soup, issues, html_content)
        
        # Check input type="image" elements
        self._check_input_image_elements(soup, issues, html_content)
        
        # Check objects, canvas, and other elements that might contain visual content
        self._check_other_visual_elements(soup, issues, html_content)
        
        return issues
    
    def _check_img_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check img elements for alternative text."""
        img_elements = soup.find_all('img')
        
        for img in img_elements:
            element_path = self.get_element_path(img)
            element_html = str(img)
            line_number = self.get_line_number(img, html_content)
            
            # Check if alt attribute exists
            if not img.has_attr('alt'):
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Image missing alt attribute",
                    impact="critical",
                    how_to_fix="Add an alt attribute to the image that describes its content and function.",
                    code_solution=self._generate_img_alt_solution(img),
                    line_number=line_number
                ))
                continue
            
            # Check if alt is empty but image isn't marked as decorative
            alt_text = img.get('alt', '')
            
            if alt_text == '' and not self._is_decorative(img):
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Image has empty alt text but doesn't appear to be decorative",
                    impact="moderate",
                    how_to_fix="Either add a descriptive alt text or mark the image as decorative with role='presentation'.",
                    code_solution=self._generate_img_alt_solution(img, decorative=False),
                    line_number=line_number
                ))
            
            # Check for placeholder alt text
            if alt_text.lower() in self.placeholder_alt_texts:
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description=f"Image has placeholder alt text: '{alt_text}'",
                    impact="serious",
                    how_to_fix="Replace the generic placeholder with a descriptive alt text that conveys the image's content and function.",
                    code_solution=self._generate_img_alt_solution(img),
                    line_number=line_number
                ))
            
            # Check for filename as alt text
            if self._is_likely_filename(alt_text):
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description=f"Image alt text appears to be a filename: '{alt_text}'",
                    impact="serious",
                    how_to_fix="Replace the filename with a descriptive alt text that conveys the image's content and function.",
                    code_solution=self._generate_img_alt_solution(img),
                    line_number=line_number
                ))
            
            # Check for very long alt text (possibly too verbose)
            if len(alt_text) > 100:
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description=f"Image alt text is very long ({len(alt_text)} characters)",
                    impact="minor",
                    how_to_fix="Consider using a more concise alt text and potentially use a figure with figcaption or aria-describedby for longer descriptions.",
                    code_solution=self._generate_longdesc_solution(img),
                    line_number=line_number
                ))
    
    def _check_svg_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check SVG elements for alternative text."""
        svg_elements = soup.find_all('svg')
        
        for svg in svg_elements:
            element_path = self.get_element_path(svg)
            element_html = str(svg)
            line_number = self.get_line_number(svg, html_content)
            
            # Check if SVG has accessible name
            has_title = svg.find('title') is not None
            has_aria_label = svg.has_attr('aria-label')
            has_aria_labelledby = svg.has_attr('aria-labelledby')
            has_role = svg.has_attr('role')
            
            # Skip if decorative
            if has_role and svg['role'] in ['presentation', 'none']:
                continue
            
            if not has_title and not has_aria_label and not has_aria_labelledby:
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="SVG element has no accessible name",
                    impact="serious",
                    how_to_fix="Add a title element, aria-label, or aria-labelledby attribute to provide an accessible name.",
                    code_solution=self._generate_svg_solution(svg),
                    line_number=line_number
                ))
    
    def _check_area_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check area elements (in image maps) for alternative text."""
        area_elements = soup.find_all('area')
        
        for area in area_elements:
            element_path = self.get_element_path(area)
            element_html = str(area)
            line_number = self.get_line_number(area, html_content)
            
            # Skip if no href (not interactive)
            if not area.has_attr('href'):
                continue
                
            # Check for alt attribute
            if not area.has_attr('alt'):
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Area element missing alt attribute",
                    impact="serious",
                    how_to_fix="Add an alt attribute that describes the function of this area.",
                    code_solution=self._generate_area_solution(area),
                    line_number=line_number
                ))
    
    def _check_input_image_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check input type="image" elements for alternative text."""
        input_images = soup.find_all('input', {'type': 'image'})
        
        for input_img in input_images:
            element_path = self.get_element_path(input_img)
            element_html = str(input_img)
            line_number = self.get_line_number(input_img, html_content)
            
            # Check for alt attribute
            if not input_img.has_attr('alt'):
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Input image missing alt attribute",
                    impact="serious",
                    how_to_fix="Add an alt attribute that describes the function of this image button.",
                    code_solution=self._generate_input_image_solution(input_img),
                    line_number=line_number
                ))
    
    def _check_other_visual_elements(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check other elements that might contain visual content (object, canvas, etc.)."""
        # Check canvas elements
        canvas_elements = soup.find_all('canvas')
        
        for canvas in canvas_elements:
            element_path = self.get_element_path(canvas)
            element_html = str(canvas)
            line_number = self.get_line_number(canvas, html_content)
            
            # Check if canvas has fallback content or accessible name
            fallback_content = canvas.text.strip()
            has_aria_label = canvas.has_attr('aria-label')
            has_aria_labelledby = canvas.has_attr('aria-labelledby')
            
            if not fallback_content and not has_aria_label and not has_aria_labelledby:
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Canvas element has no fallback content or accessible name",
                    impact="serious",
                    how_to_fix="Add fallback content inside the canvas element or provide an aria-label or aria-labelledby attribute.",
                    code_solution=self._generate_canvas_solution(canvas),
                    line_number=line_number
                ))
        
        # Check object elements
        object_elements = soup.find_all('object')
        
        for obj in object_elements:
            element_path = self.get_element_path(obj)
            element_html = str(obj)
            line_number = self.get_line_number(obj, html_content)
            
            # Check if object has fallback content
            fallback_content = obj.text.strip()
            
            if not fallback_content:
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description="Object element has no fallback content",
                    impact="serious",
                    how_to_fix="Add fallback content inside the object element to provide an alternative for users who cannot access the object.",
                    code_solution=self._generate_object_solution(obj),
                    line_number=line_number
                ))
    
    def _is_decorative(self, img: Tag) -> bool:
        """
        Check if an image is likely decorative.
        
        Args:
            img: BeautifulSoup img tag
            
        Returns:
            True if the image is likely decorative, False otherwise
        """
        # Check for role="presentation" or role="none"
        if img.has_attr('role') and img['role'] in ['presentation', 'none']:
            return True
        
        # Check for decorative classes
        if img.has_attr('class'):
            img_classes = set(img['class'])
            if img_classes.intersection(self.decorative_classes):
                return True
        
        # Check for aria-hidden="true"
        if img.has_attr('aria-hidden') and img['aria-hidden'] == 'true':
            return True
        
        # Check if it might be a spacer image
        if img.has_attr('width') and img.has_attr('height'):
            try:
                width = int(img['width'])
                height = int(img['height'])
                if (width <= 1 or height <= 1) and img.get('alt', '') == '':
                    return True
            except ValueError:
                pass
        
        return False
    
    def _is_likely_filename(self, text: str) -> bool:
        """
        Check if a string is likely a filename.
        
        Args:
            text: The string to check
            
        Returns:
            True if the string is likely a filename, False otherwise
        """
        # Check for common image file extensions
        if re.search(r'\.(jpe?g|png|gif|webp|svg|bmp|tiff?)$', text, re.IGNORECASE):
            return True
        
        # Check for underscores and hyphens common in filenames
        if re.search(r'^[a-zA-Z0-9_-]+$', text) and ('_' in text or '-' in text):
            return True
            
        return False
    
    def _generate_img_alt_solution(self, img: Tag, decorative: bool = None) -> str:
        """
        Generate solution code for an img element.
        
        Args:
            img: BeautifulSoup img tag
            decorative: Whether the image is decorative. If None, determined by _is_decorative
            
        Returns:
            HTML string with solution
        """
        if decorative is None:
            decorative = self._is_decorative(img)
            
        # Create a copy of the attributes
        attrs = {key: value for key, value in img.attrs.items() if key != 'alt'}
        
        if decorative:
            attrs['alt'] = ''
            attrs['role'] = 'presentation'
            
            return f'<img {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} alt="" role="presentation">'
        else:
            return f'<img {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} alt="[Descriptive text about the image]">'
    
    def _generate_longdesc_solution(self, img: Tag) -> str:
        """
        Generate solution code for an image with long description.
        
        Args:
            img: BeautifulSoup img tag
            
        Returns:
            HTML string with solution
        """
        # Create a copy of the attributes
        attrs = {key: value for key, value in img.attrs.items() if key != 'alt' and key != 'aria-describedby'}
        
        return f'''<figure>
  <img {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} alt="[Brief description]" aria-describedby="img-desc">
  <figcaption id="img-desc">[Detailed description of the image]</figcaption>
</figure>'''
    
    def _generate_svg_solution(self, svg: Tag) -> str:
        """
        Generate solution code for an SVG element.
        
        Args:
            svg: BeautifulSoup svg tag
            
        Returns:
            HTML string with solution
        """
        # Get first 50 chars of SVG content to preserve for example
        svg_content = str(svg)
        svg_start = svg_content[:50]
        if svg_content.count('\n') > 3:
            # Add just first few lines for readability
            svg_lines = svg_content.split('\n')[:4]
            svg_start = '\n'.join(svg_lines) + '\n  ...'
        
        return f'''<svg aria-label="[Descriptive text about the SVG]">
  <title>Descriptive text about the SVG</title>
  {svg_start}
</svg>'''
    
    def _generate_area_solution(self, area: Tag) -> str:
        """
        Generate solution code for an area element.
        
        Args:
            area: BeautifulSoup area tag
            
        Returns:
            HTML string with solution
        """
        # Create a copy of the attributes
        attrs = {key: value for key, value in area.attrs.items() if key != 'alt'}
        
        return f'<area {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} alt="[Descriptive text for this region]">'
    
    def _generate_input_image_solution(self, input_img: Tag) -> str:
        """
        Generate solution code for an input type=image element.
        
        Args:
            input_img: BeautifulSoup input tag
            
        Returns:
            HTML string with solution
        """
        # Create a copy of the attributes
        attrs = {key: value for key, value in input_img.attrs.items() if key != 'alt'}
        
        return f'<input {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} alt="[Descriptive text for button function]">'
    
    def _generate_canvas_solution(self, canvas: Tag) -> str:
        """
        Generate solution code for a canvas element.
        
        Args:
            canvas: BeautifulSoup canvas tag
            
        Returns:
            HTML string with solution
        """
        # Get attrs except aria-label
        attrs = {key: value for key, value in canvas.attrs.items() if key != 'aria-label'}
        
        return f'''<canvas {" ".join(f"{k}=\"{v}\"" for k, v in attrs.items())} aria-label="[Descriptive text for canvas content]">
  Your browser does not support the canvas element.
  [Alternative content or description of what the canvas displays]
</canvas>'''
    
    def _generate_object_solution(self, obj: Tag) -> str:
        """
        Generate solution code for an object element.
        
        Args:
            obj: BeautifulSoup object tag
            
        Returns:
            HTML string with solution
        """
        attrs_str = " ".join(f"{k}=\"{v}\"" for k, v in obj.attrs.items())
        
        return f'''<object {attrs_str}>
  [Alternative content for users who cannot access the object]
  <p>This content displays [description of what the object contains or does].</p>
</object>'''