"""
WCAG 2.2 - 1.4.3 Contrast (Minimum) (Level AA)

The visual presentation of text and images of text has a contrast ratio
of at least 4.5:1, except for Large Text (at least 3:1), incidental text,
and logotypes.
"""

from typing import List, Tuple, Dict, Optional
import re
import math
from bs4 import BeautifulSoup, Tag
import colorsys

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_1_4_3(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 1.4.3: Contrast (Minimum).
    
    This criterion requires sufficient contrast between text and its background.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "1.4.3"
        self.name = "Contrast (Minimum)"
        self.level = "AA"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html"
        self.description = """
        The visual presentation of text and images of text has a contrast ratio
        of at least 4.5:1, except for Large Text (at least 3:1), incidental text,
        and logotypes.
        """
        
        # CSS properties that may specify colors
        self.color_properties = ['color', 'background-color', 'background']
        
        # Minimum contrast ratios
        self.min_contrast_normal = 4.5  # 4.5:1 for normal text
        self.min_contrast_large = 3.0   # 3:1 for large text (18pt or 14pt bold)
        
        # Common font size breakpoints (in pixels)
        self.large_text_size = 18  # 18px
        self.large_bold_text_size = 14  # 14px (if bold)
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 1.4.3 criterion.
        
        Note: This static analysis has limitations and may produce false positives/negatives
        since it cannot calculate actual computed styles. For complete accuracy,
        browser-based testing would be required.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Check text elements that commonly have content
        text_elements = soup.find_all(['p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                     'a', 'button', 'label', 'li', 'td', 'th'])
        
        for element in text_elements:
            # Skip elements with no text content
            if not element.get_text(strip=True):
                continue
            
            element_path = self.get_element_path(element)
            element_html = str(element)
            line_number = self.get_line_number(element, html_content)
            
            # Extract inline styles if present
            inline_styles = self._parse_inline_styles(element)
            
            # Extract foreground color
            fg_color = self._extract_color(inline_styles.get('color', ''))
            
            # Extract background color
            bg_color = None
            for prop in ['background-color', 'background']:
                if prop in inline_styles:
                    bg_color = self._extract_color(inline_styles[prop])
                    if bg_color:
                        break
            
            # If we have both colors, check contrast
            if fg_color and bg_color:
                # Determine font size from inline styles
                font_size = self._extract_font_size(inline_styles.get('font-size', ''))
                font_weight = inline_styles.get('font-weight', '')
                is_bold = font_weight in ['bold', 'bolder', '700', '800', '900']
                
                # Determine if text is "large" according to WCAG
                is_large = False
                if font_size:
                    if (font_size >= self.large_text_size or 
                        (font_size >= self.large_bold_text_size and is_bold)):
                        is_large = True
                
                # Calculate contrast ratio
                contrast_ratio = self._calculate_contrast_ratio(fg_color, bg_color)
                
                # Determine minimum required contrast
                min_contrast = self.min_contrast_large if is_large else self.min_contrast_normal
                
                # Check if contrast is sufficient
                if contrast_ratio < min_contrast:
                    threshold_name = "large text (3:1)" if is_large else "normal text (4.5:1)"
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description=f"Insufficient contrast ratio of {contrast_ratio:.2f}:1 (minimum should be {min_contrast}:1 for {threshold_name})",
                        impact="serious",
                        how_to_fix=f"Increase the contrast between the text ({self._rgb_to_hex(fg_color)}) and background ({self._rgb_to_hex(bg_color)}).",
                        code_solution=self._generate_contrast_solution(element, fg_color, bg_color, min_contrast),
                        line_number=line_number
                    ))
        
        return issues
    
    def _parse_inline_styles(self, element: Tag) -> Dict[str, str]:
        """
        Parse inline styles from an element.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            Dictionary of CSS properties
        """
        styles = {}
        
        if element.has_attr('style'):
            style_text = element['style']
            
            # Simple CSS parsing (doesn't handle all cases but works for basic styles)
            style_parts = style_text.split(';')
            
            for part in style_parts:
                if ':' in part:
                    prop, value = part.split(':', 1)
                    styles[prop.strip().lower()] = value.strip()
        
        return styles
    
    def _extract_color(self, color_value: str) -> Optional[Tuple[int, int, int]]:
        """
        Extract RGB color from CSS color value.
        
        Args:
            color_value: CSS color value (hex, rgb, or named color)
            
        Returns:
            Tuple of (R, G, B) values or None if extraction fails
        """
        if not color_value:
            return None
            
        # Handle rgb/rgba format
        rgb_match = re.search(r'rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
        if rgb_match:
            r = int(rgb_match.group(1))
            g = int(rgb_match.group(2))
            b = int(rgb_match.group(3))
            return (r, g, b)
            
        rgba_match = re.search(r'rgba\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*[\d.]+\s*\)', color_value)
        if rgba_match:
            r = int(rgba_match.group(1))
            g = int(rgba_match.group(2))
            b = int(rgba_match.group(3))
            return (r, g, b)
        
        # Handle hex format
        hex_match = re.search(r'#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})', color_value, re.IGNORECASE)
        if hex_match:
            r = int(hex_match.group(1), 16)
            g = int(hex_match.group(2), 16)
            b = int(hex_match.group(3), 16)
            return (r, g, b)
            
        # Handle short hex format
        short_hex_match = re.search(r'#([0-9a-f])([0-9a-f])([0-9a-f])', color_value, re.IGNORECASE)
        if short_hex_match:
            r = int(short_hex_match.group(1) + short_hex_match.group(1), 16)
            g = int(short_hex_match.group(2) + short_hex_match.group(2), 16)
            b = int(short_hex_match.group(3) + short_hex_match.group(3), 16)
            return (r, g, b)
        
        # Handle some common named colors
        named_colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'red': (255, 0, 0),
            'green': (0, 128, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0),
            'purple': (128, 0, 128),
            'gray': (128, 128, 128),
            'grey': (128, 128, 128),
            'orange': (255, 165, 0),
            'brown': (165, 42, 42),
            'cyan': (0, 255, 255),
            'magenta': (255, 0, 255),
        }
        
        color_value = color_value.lower().strip()
        if color_value in named_colors:
            return named_colors[color_value]
            
        return None
    
    def _extract_font_size(self, size_value: str) -> Optional[float]:
        """
        Extract font size in pixels from CSS font-size value.
        
        Args:
            size_value: CSS font-size value
            
        Returns:
            Font size in pixels or None if extraction fails
        """
        if not size_value:
            return None
            
        # Handle pixel values
        px_match = re.search(r'([\d.]+)px', size_value)
        if px_match:
            return float(px_match.group(1))
            
        # Handle point values (approximate conversion to pixels)
        pt_match = re.search(r'([\d.]+)pt', size_value)
        if pt_match:
            return float(pt_match.group(1)) * 1.333  # Approximate pt to px conversion
            
        # Handle em values (using a baseline assumption of 16px)
        em_match = re.search(r'([\d.]+)em', size_value)
        if em_match:
            return float(em_match.group(1)) * 16  # Assume 1em = 16px
            
        # Handle rem values (using a baseline assumption of 16px)
        rem_match = re.search(r'([\d.]+)rem', size_value)
        if rem_match:
            return float(rem_match.group(1)) * 16  # Assume 1rem = 16px
            
        # Handle percentage (using a baseline assumption of 16px)
        percent_match = re.search(r'([\d.]+)%', size_value)
        if percent_match:
            return float(percent_match.group(1)) * 0.16  # Assume 100% = 16px
            
        # Handle named sizes (approximate conversion to pixels)
        named_sizes = {
            'xx-small': 9,
            'x-small': 10,
            'small': 13,
            'medium': 16,
            'large': 18,
            'x-large': 24,
            'xx-large': 32,
        }
        
        size_value = size_value.lower().strip()
        if size_value in named_sizes:
            return named_sizes[size_value]
            
        return None
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """
        Calculate contrast ratio between two colors using WCAG formula.
        
        Args:
            color1: RGB tuple (R, G, B)
            color2: RGB tuple (R, G, B)
            
        Returns:
            Contrast ratio as a float
        """
        # Calculate relative luminance for each color
        luminance1 = self._relative_luminance(color1)
        luminance2 = self._relative_luminance(color2)
        
        # Calculate contrast ratio
        if luminance1 > luminance2:
            return (luminance1 + 0.05) / (luminance2 + 0.05)
        else:
            return (luminance2 + 0.05) / (luminance1 + 0.05)
    
    def _relative_luminance(self, color: Tuple[int, int, int]) -> float:
        """
        Calculate relative luminance of a color using WCAG formula.
        
        Args:
            color: RGB tuple (R, G, B)
            
        Returns:
            Relative luminance value
        """
        r, g, b = color
        
        # Convert RGB values to sRGB
        r_srgb = r / 255.0
        g_srgb = g / 255.0
        b_srgb = b / 255.0
        
        # Apply transformation
        r_linear = self._srgb_to_linear(r_srgb)
        g_linear = self._srgb_to_linear(g_srgb)
        b_linear = self._srgb_to_linear(b_srgb)
        
        # Calculate luminance
        return 0.2126 * r_linear + 0.7152 * g_linear + 0.0722 * b_linear
    
    def _srgb_to_linear(self, value: float) -> float:
        """
        Convert sRGB value to linear RGB value.
        
        Args:
            value: sRGB value (0-1)
            
        Returns:
            Linear RGB value
        """
        if value <= 0.03928:
            return value / 12.92
        else:
            return ((value + 0.055) / 1.055) ** 2.4
    
    def _rgb_to_hex(self, color: Tuple[int, int, int]) -> str:
        """
        Convert RGB color to hex representation.
        
        Args:
            color: RGB tuple (R, G, B)
            
        Returns:
            Hex color string
        """
        r, g, b = color
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _adjust_color_for_contrast(self, 
                                  fg_color: Tuple[int, int, int], 
                                  bg_color: Tuple[int, int, int], 
                                  target_ratio: float) -> Tuple[int, int, int]:
        """
        Adjust foreground color to achieve target contrast ratio with background.
        
        Args:
            fg_color: RGB tuple for foreground color
            bg_color: RGB tuple for background color
            target_ratio: Target contrast ratio
            
        Returns:
            Adjusted RGB tuple for foreground color
        """
        # Convert RGB to HSL for more intuitive adjustment
        r, g, b = fg_color
        h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
        
        # Calculate current contrast ratio
        current_ratio = self._calculate_contrast_ratio(fg_color, bg_color)
        
        # Determine if we need to lighten or darken the foreground
        bg_luminance = self._relative_luminance(bg_color)
        fg_luminance = self._relative_luminance(fg_color)
        
        # Adjust lightness to increase contrast
        adjust_up = bg_luminance < 0.5
        
        # Binary search to find the right lightness value
        min_l = 0.0
        max_l = 1.0
        
        for _ in range(10):  # 10 iterations should be sufficient
            if adjust_up:
                new_l = (max_l + l) / 2
            else:
                new_l = (min_l + l) / 2
                
            # Convert back to RGB and calculate new contrast
            r_new, g_new, b_new = colorsys.hls_to_rgb(h, new_l, s)
            new_fg_color = (int(r_new * 255), int(g_new * 255), int(b_new * 255))
            new_ratio = self._calculate_contrast_ratio(new_fg_color, bg_color)
            
            # Check if we've reached our target
            if new_ratio >= target_ratio:
                if adjust_up:
                    max_l = new_l
                else:
                    min_l = new_l
            else:
                if adjust_up:
                    l = new_l
                else:
                    l = new_l
            
            # If we're close enough, return the result
            if abs(new_ratio - target_ratio) < 0.1:
                break
        
        # Convert final values to RGB
        r_final, g_final, b_final = colorsys.hls_to_rgb(h, new_l, s)
        return (int(r_final * 255), int(g_final * 255), int(b_final * 255))
    
    def _generate_contrast_solution(self, 
                                   element: Tag, 
                                   fg_color: Tuple[int, int, int], 
                                   bg_color: Tuple[int, int, int], 
                                   min_contrast: float) -> str:
        """
        Generate solution code for a contrast issue.
        
        Args:
            element: BeautifulSoup element
            fg_color: RGB tuple for foreground color
            bg_color: RGB tuple for background color
            min_contrast: Minimum required contrast ratio
            
        Returns:
            HTML string with solution
        """
        # Adjust the foreground color to meet contrast requirements
        adjusted_fg = self._adjust_color_for_contrast(fg_color, bg_color, min_contrast)
        
        # Create the CSS property to update
        fg_hex = self._rgb_to_hex(fg_color)
        adjusted_fg_hex = self._rgb_to_hex(adjusted_fg)
        bg_hex = self._rgb_to_hex(bg_color)
        
        # Create inline style solution
        if element.has_attr('style'):
            original_style = element['style']
            # Replace color property in style
            new_style = re.sub(r'color\s*:\s*[^;]+', f'color: {adjusted_fg_hex}', original_style)
            if new_style == original_style:  # Color wasn't in the style attribute
                new_style = original_style + f'; color: {adjusted_fg_hex}'
                
            attributes = ' '.join([f'{k}="{v}"' for k, v in element.attrs.items() if k != 'style'])
            return f'<{element.name} {attributes} style="{new_style}">{element.get_text()}</{element.name}>'
        else:
            # Add new style attribute
            attributes = ' '.join([f'{k}="{v}"' for k, v in element.attrs.items()])
            return f'<{element.name} {attributes} style="color: {adjusted_fg_hex}">{element.get_text()}</{element.name}>'
        
        # Alternative: provide a CSS class solution
        css_class_solution = f"""/* Add this to your CSS file */
.accessible-text {{
  color: {adjusted_fg_hex};
  /* Alternatively, you could darken/lighten the background instead */
}}

/* Then apply the class to your element */
<{element.name} class="accessible-text">Your text</{element.name}>"""
        
        return css_class_solution