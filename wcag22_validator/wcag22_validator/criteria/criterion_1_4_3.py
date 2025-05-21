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
        
        self.color_properties = ['color', 'background-color', 'background']
        self.min_contrast_normal = 4.5
        self.min_contrast_large = 3.0
        # WCAG defines large text as 18pt (24px) or 14pt (18.66px) bold.
        # Using common browser default of 1pt = 1.333px (96dpi/72dpi)
        self.large_text_size_px = 18 * (4/3) 
        self.large_bold_text_size_px = 14 * (4/3)

    def _build_attrs_string(self, attrs_dict: dict) -> str:
        # This helper should ideally be in BaseCriterion or a utility module
        # For now, keeping it here for self-containment of this specific correction.
        attr_list = []
        for k_item, v_item_list in attrs_dict.items():
            v_str = " ".join(v_item_list) if isinstance(v_item_list, list) else v_item_list
            v_str_escaped = v_str.replace('"', '&quot;') # Basic HTML escaping for quotes
            attr_list.append(f'{k_item}="{v_str_escaped}"')
        return " ".join(attr_list)

    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        issues = []
        # More comprehensive list of elements that can contain text
        text_elements = soup.find_all(lambda tag: tag.string and tag.string.strip() and tag.name not in ['script', 'style', 'noscript', 'head', 'meta', 'title'])

        for element in text_elements:
            # Check if the element itself or its direct text nodes are visible
            # This is a very basic check; true visibility requires computed styles
            if not element.get_text(strip=True):
                continue
            
            element_path = self.get_element_path(element)
            # Create a snippet that's more likely to be unique for line number finding
            element_html_snippet = str(element.name) + "".join([f' {k}="{v}"' for k,v in element.attrs.items() if k in ['id', 'class']])


            line_number = self.get_line_number(element, html_content)
            
            inline_styles = self._parse_inline_styles(element)
            
            # Simplified: only checking inline styles directly on the element
            # A full solution would need to traverse up the DOM and consider CSS rules.
            fg_color_str = inline_styles.get('color')
            bg_color_str = inline_styles.get('background-color')
            # Crude check for 'background' property if 'background-color' is not set
            if not bg_color_str and 'background' in inline_styles:
                # This is very basic, assumes 'background' sets a plain color
                # A proper parser for 'background' shorthand is needed for accuracy
                bg_match = re.search(r'(#[0-9a-fA-F]{3,6}\\b|rgb\\([^\)]+\\)|[a-zA-Z]+)', inline_styles['background'])
                if bg_match:
                    bg_color_str = bg_match.group(0)

            if fg_color_str and bg_color_str:
                fg_color = self._extract_color(fg_color_str)
                # For background, if it's an image, we can't determine contrast here.
                # This simplified check assumes bg_color_str is a color.
                bg_color = self._extract_color(bg_color_str)


                if fg_color and bg_color:
                    font_size_str = inline_styles.get('font-size', '')
                    font_weight_str = inline_styles.get('font-weight', '')
                    
                    font_size_px = self._extract_font_size_px(font_size_str, soup) # Pass soup for context
                    is_bold = font_weight_str.lower() in ['bold', 'bolder'] or \
                              (font_weight_str.isdigit() and int(font_weight_str) >= 700)

                    is_large_text = False
                    if font_size_px:
                        if is_bold and font_size_px >= self.large_bold_text_size_px:
                            is_large_text = True
                        elif not is_bold and font_size_px >= self.large_text_size_px:
                            is_large_text = True
                    
                    contrast_ratio = self._calculate_contrast_ratio(fg_color, bg_color)
                    min_required_contrast = self.min_contrast_large if is_large_text else self.min_contrast_normal
                    
                    if contrast_ratio < min_required_contrast:
                        threshold_name = f"large text ({self.min_contrast_large}:1)" if is_large_text else f"normal text ({self.min_contrast_normal}:1)"
                        issues.append(self.create_issue(
                            element_path=element_path, element_html=str(element), # Use full element for context
                            description=f"Insufficient contrast ratio of {contrast_ratio:.2f}:1. Minimum for {threshold_name} is {min_required_contrast}:1. (Text: {self._rgb_to_hex(fg_color)}, Background: {self._rgb_to_hex(bg_color)})",
                            impact="serious",
                            how_to_fix=f"Adjust text color or background color to meet the minimum contrast ratio. For example, change text to a darker/lighter shade or modify the background.",
                            code_solution=self._generate_contrast_solution(element, fg_color, bg_color, min_required_contrast),
                            line_number=line_number
                        ))
        return issues
    
    def _parse_inline_styles(self, element: Tag) -> Dict[str, str]:
        styles = {}
        if element.has_attr('style'):
            style_text = element['style']
            # Handle cases where style might be a list (though unusual for style attr)
            if isinstance(style_text, list): style_text = " ".join(style_text)
            style_parts = style_text.split(';')
            for part in style_parts:
                if ':' in part:
                    prop, value = part.split(':', 1)
                    styles[prop.strip().lower()] = value.strip()
        return styles
    
    def _extract_color(self, color_value: str) -> Optional[Tuple[int, int, int]]:
        if not color_value: return None
        color_value = color_value.lower().strip()

        if color_value == 'transparent': return None # Cannot determine contrast with transparent

        # rgb/rgba
        match = re.search(r'rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})(?:\s*,\s*[\d.]+)?\s*\)', color_value)
        if match: 
            return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
        
        # hex
        if color_value.startswith('#'):
            hex_color = color_value[1:]
            if len(hex_color) == 6:
                try: return (int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16))
                except ValueError: pass
            if len(hex_color) == 3:
                try: return (int(hex_color[0]*2, 16), int(hex_color[1]*2, 16), int(hex_color[2]*2, 16))
                except ValueError: pass

        named_colors = {
            'black': (0,0,0), 'white': (255,255,255), 'red': (255,0,0), 'green': (0,128,0), 
            'blue': (0,0,255), 'yellow': (255,255,0), 'silver': (192,192,192), 'gray': (128,128,128),
            'maroon': (128,0,0), 'olive': (128,128,0), 'purple': (128,0,128), 'fuchsia':(255,0,255),
            'lime':(0,255,0), 'teal': (0,128,128), 'aqua': (0,255,255), 'navy': (0,0,128)
            # Add more common named colors if necessary
        }
        return named_colors.get(color_value)

    def _extract_font_size_px(self, size_value: str, soup: Optional[BeautifulSoup]=None, base_font_size_px: float = 16.0) -> Optional[float]:
        # Parameter `soup` is added for potential future use (e.g., getting parent\'s font size for em units)
        # but not used in this simplified version.
        if not size_value: return None
        size_value = size_value.lower().strip()
        
        val_match = re.match(r'([\\d.]+)\\s*(px|pt|em|rem|%)?', size_value)
        if not val_match: 
            # Handle named sizes (approximate, could vary by browser default settings)
            named_sizes = {
                \'xx-small\': base_font_size_px * 0.6, \'x-small\': base_font_size_px * 0.75,
                \'small\': base_font_size_px * 0.89, \'medium\': base_font_size_px, 
                \'large\': base_font_size_px * 1.2, \'x-large\': base_font_size_px * 1.5,
                \'xx-large\': base_font_size_px * 2.0, \'smaller\': base_font_size_px * 0.83, 
                \'larger\': base_font_size_px * 1.2 
            }
            return named_sizes.get(size_value)
        
        val = float(val_match.group(1))
        unit = val_match.group(2)

        if unit == \'px\': return val
        if unit == \'pt\': return val * (96/72) 
        if unit == \'em\' or unit == \'rem\': return val * base_font_size_px # Simplified: assumes base_font_size_px for both
        if unit == \'%\': return (val / 100) * base_font_size_px # Simplified: assumes percentage of base_font_size_px
        if not unit and val > 0: return val # Assume px if no unit

        return None # Fallback

    def _relative_luminance(self, color: Tuple[int, int, int]) -> float:
        srgb = [x / 255.0 for x in color]
        linear_rgb = []
        for val in srgb:
            if val <= 0.04045: # Corrected threshold from 0.03928
                linear_rgb.append(val / 12.92)
            else:
                linear_rgb.append(((val + 0.055) / 1.055) ** 2.4)
        return 0.2126 * linear_rgb[0] + 0.7152 * linear_rgb[1] + 0.0722 * linear_rgb[2]

    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        lum1 = self._relative_luminance(color1)
        lum2 = self._relative_luminance(color2)
        if lum1 > lum2:
            return (lum1 + 0.05) / (lum2 + 0.05)
        return (lum2 + 0.05) / (lum1 + 0.05)

    def _rgb_to_hex(self, color: Tuple[int, int, int]) -> str:
        return f\'#{color[0]:02x}{color[1]:02x}{color[2]:02x}\'\n\n    def _adjust_color_for_contrast(self, \n                                  fg_color_tuple: Tuple[int, int, int], \n                                  bg_color_tuple: Tuple[int, int, int], \n                                  target_ratio: float) -> Tuple[int, int, int]:\n        # This is a simplified heuristic and might not always find the best color.\n        # It tries to adjust the lightness of the foreground color.\n        current_ratio = self._calculate_contrast_ratio(fg_color_tuple, bg_color_tuple)\n        if current_ratio >= target_ratio:\n            return fg_color_tuple\n\n        r, g, b = [x / 255.0 for x in fg_color_tuple]\n        h, l, s = colorsys.rgb_to_hls(r, g, b)\n\n        # Determine if background is dark or light\n        bg_lum = self._relative_luminance(bg_color_tuple)\n        \n        best_l = l\n        final_color = fg_color_tuple\n\n        # Try 10 steps in either direction\n        for i in range(1, 11): \n            # Option 1: Adjust lightness towards white/black\n            if bg_lum < 0.5: # Dark background, try lighter foreground\n                test_l = min(1.0, l + i * 0.05)\n            else: # Light background, try darker foreground\n                test_l = max(0.0, l - i * 0.05)\n\n            r_adj, g_adj, b_adj = colorsys.hls_to_rgb(h, test_l, s)\n            adjusted_color = (int(r_adj*255), int(g_adj*255), int(b_adj*255))\n            \n            # Clamp values to 0-255\n            adjusted_color = tuple(max(0, min(255, c)) for c in adjusted_color)\n\n            new_ratio = self._calculate_contrast_ratio(adjusted_color, bg_color_tuple)\n\n            if new_ratio >= target_ratio:\n                return adjusted_color # Found a suitable color\n        \n        return fg_color_tuple # Return original if no better color found within simple heuristic\n\n\n    def _generate_contrast_solution(self,\n                                   element: Tag,\n                                   fg_color: Tuple[int, int, int],\n                                   bg_color: Tuple[int, int, int],\n                                   min_contrast: float) -> str:\n        adjusted_fg = self._adjust_color_for_contrast(fg_color, bg_color, min_contrast)\n        adjusted_fg_hex = self._rgb_to_hex(adjusted_fg)\n\n        attr_parts = []\n        original_style_value = \"\"\n        \n        # Use list(element.attrs.items()) for stable iteration if needed, though attrs is a dict\n        for k, v_val_list in element.attrs.items():\n            # BeautifulSoup attribute values can be a list (e.g. class) or a string.\n            v_str = \" \".join(v_val_list) if isinstance(v_val_list, list) else v_val_list\n            if k.lower() == \'style\':\n                original_style_value = v_str\n                continue \n            attr_parts.append(f\'{k}=\"{v_str.replace(\"\\\"\", \"&quot;\")}\"\') # Basic HTML escaping for quotes\n        \n        attributes_str = \" \".join(attr_parts)\n\n        # Prepare the new style declaration for color\n        new_color_declaration = f\"color: {adjusted_fg_hex};\"\n        processed_style = \"\"\n\n        if original_style_value:\n            # Try to replace existing color property\n            # Regex to find \'color: value;\' possibly with spaces and no semi-colon at the end for the last rule\n            style_rules = [rule.strip() for rule in original_style_value.split(\';\') if rule.strip()]\n            color_found_and_replaced = False\n            for i, rule in enumerate(style_rules):\n                if rule.lower().startswith(\"color:\"):\n                    style_rules[i] = new_color_declaration.rstrip(\';\') \n                    color_found_and_replaced = True\n                    break\n            if not color_found_and_replaced:\n                style_rules.append(new_color_declaration.rstrip(\';\'))\n            \n            processed_style = \"; \".join(rule for rule in style_rules if rule)\n            if processed_style and not processed_style.endswith(\';\'): # Ensure it ends with a semicolon\n                 processed_style += \';\'\n        else:\n            processed_style = new_color_declaration # If no original style, just use the new color\n        \n        element_tag = element.name\n        element_text_content = element.get_text(strip=True)\n\n        # Ensure attributes_str is not empty before adding a space\n        solution_html_attrs = f\" {attributes_str}\" if attributes_str else \"\"\n        solution_html = f\'<{element_tag}{solution_html_attrs} style=\"{processed_style.strip()}\">{element_text_content}</{element_tag}>\'\n        \n        css_class_attributes_str = attributes_str # Use the same non-style attributes\n\n        # Create a more unique class name\n        unique_class_suffix = hash(f\"{element_tag}{element_text_content}{adjusted_fg_hex}\") % 100000\n        css_class_name = f\"accessible-text-{unique_class_suffix}\"\n\n        css_class_solution = f\"\"\"\\\n/* Add this to your CSS file */\n.{css_class_name} {{\n  color: {adjusted_fg_hex};\n  /* Consider adjusting background if this doesn\'t suffice: background-color: {self._rgb_to_hex(bg_color)}; */\n}}\n\n/* Then apply the class to your element */\n<{element_tag}{solution_html_attrs} class=\"{css_class_name}\">{element_text_content}</{element_tag}>\"\"\"\n\n        return f\"Suggested inline style fix:\\n{solution_html}\\n\\nAlternative CSS class fix:\\n{css_class_solution}\"\n