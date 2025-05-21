"""
WCAG 2.2 - 4.1.2 Name, Role, Value (Level A)

For all user interface components, the name and role can be programmatically determined; 
states, properties, and values can be programmatically set; and 
notification of changes to these items is available to user agents, including assistive technologies.
"""

from typing import List, Dict, Set, Optional
import re
from bs4 import BeautifulSoup, Tag

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_4_1_2(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 4.1.2: Name, Role, Value.
    
    This criterion requires that all UI components have appropriate 
    accessible names, roles, states, and properties that can be 
    detected by assistive technologies.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "4.1.2"
        self.name = "Name, Role, Value"
        self.level = "A"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/name-role-value.html"
        self.description = """
        For all user interface components, the name and role can be programmatically determined; 
        states, properties, and values can be programmatically set; and 
        notification of changes to these items is available to user agents, including assistive technologies.
        """
        
        # Interactive elements that need accessible names
        self.interactive_elements = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'select',
            'textarea',
            '[role="button"]',
            '[role="link"]',
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="combobox"]',
            '[role="listbox"]',
            '[role="menu"]',
            '[role="menuitem"]',
            '[role="menuitemcheckbox"]',
            '[role="menuitemradio"]',
            '[role="option"]',
            '[role="switch"]',
            '[role="tab"]',
            '[role="textbox"]',
            '[role="treeitem"]',
            '[tabindex]:not([tabindex="-1"])',
            '[aria-haspopup]',
            '[contenteditable="true"]'
        ]
        
        # Elements that should have defined roles
        self.elements_needing_roles = [
            'div[onclick]',
            'span[onclick]',
            'div[onkeydown]',
            'span[onkeydown]',
            'div[tabindex]:not([tabindex="-1"])',
            'span[tabindex]:not([tabindex="-1"])',
            '[aria-label]',
            '[aria-labelledby]'
        ]
        
        # Form controls that should have labels
        self.form_controls_needing_labels = [
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"])',
            'select',
            'textarea'
        ]
        
        # Custom controls that need ARIA states/properties
        self.custom_controls = [
            '[role="checkbox"]',
            '[role="radio"]',
            '[role="switch"]',
            '[role="combobox"]',
            '[role="listbox"]',
            '[role="menu"]',
            '[role="menubar"]',
            '[role="radiogroup"]',
            '[role="slider"]',
            '[role="tablist"]',
            '[role="tree"]'
        ]
        
        # Required states/properties for various roles
        self.required_states = {
            'checkbox': ['aria-checked'],
            'radio': ['aria-checked'],
            'switch': ['aria-checked'],
            'combobox': ['aria-expanded'],
            'listbox': [],
            'option': ['aria-selected'],
            'menu': [],
            'menuitem': [],
            'menuitemcheckbox': ['aria-checked'],
            'menuitemradio': ['aria-checked'],
            'radiogroup': [],
            'slider': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'tablist': [],
            'tab': ['aria-selected'],
            'tree': [],
            'treeitem': ['aria-expanded', 'aria-selected']
        }
        
        # Valid roles for common HTML elements
        self.valid_roles_for_elements = {
            'a': ['button', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 
                  'option', 'radio', 'switch', 'tab', 'treeitem', 'link'],
            'button': ['checkbox', 'link', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 
                      'option', 'radio', 'switch', 'tab', 'button'],
            'h1': ['tab', 'heading'],
            'h2': ['tab', 'heading'],
            'h3': ['tab', 'heading'],
            'h4': ['tab', 'heading'],
            'h5': ['tab', 'heading'],
            'h6': ['tab', 'heading'],
            'img': ['button', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 
                   'option', 'radio', 'switch', 'tab'],
            'input': ['button', 'checkbox', 'option', 'radio', 'switch', 'textbox', 'combobox'],
            'li': ['menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'tab', 'treeitem', 'listitem'],
            'select': ['combobox', 'listbox', 'menu'],
            'table': ['grid'],
            'td': ['gridcell'],
            'tr': ['row'],
            'ul': ['listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'tree', 'list'],
            'ol': ['listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'tree', 'list'],
            'div': ['*'],  # div can have any role
            'span': ['*']  # span can have any role
        }
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 4.1.2 criterion.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Check for interactive elements without accessible names
        self._check_accessible_names(soup, issues, html_content)
        
        # Check for elements with improper roles
        self._check_roles(soup, issues, html_content)
        
        # Check for form controls without proper labels
        self._check_form_labels(soup, issues, html_content)
        
        # Check custom controls for required ARIA states/properties
        self._check_custom_controls(soup, issues, html_content)
        
        # Check for invalid ARIA attributes
        self._check_invalid_aria(soup, issues, html_content)
        
        return issues
    
    def _check_accessible_names(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check interactive elements for accessible names."""
        for selector in self.interactive_elements:
            for element in soup.select(selector):
                # Skip elements that shouldn't need names (like decorative elements)
                if element.has_attr('aria-hidden') and element['aria-hidden'] == 'true':
                    continue
                    
                # Skip input elements that naturally don't need visible labels
                if element.name == 'input' and element.get('type') in ['submit', 'reset', 'button'] and element.has_attr('value'):
                    continue
                    
                # Check if element has an accessible name
                if not self._has_accessible_name(element):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description="Interactive element does not have an accessible name",
                        impact="critical",
                        how_to_fix="Add an accessible name using aria-label, aria-labelledby, or visible text content.",
                        code_solution=self._generate_accessible_name_solution(element),
                        line_number=line_number
                    ))
    
    def _check_roles(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check elements for proper roles."""
        # Check elements that need explicit roles
        for selector in self.elements_needing_roles:
            for element in soup.select(selector):
                # Skip if it already has a role attribute
                if element.has_attr('role'):
                    # Check if the role is valid for this element
                    if not self._is_valid_role_for_element(element, element['role']):
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Element has invalid role '{element['role']}' for element type '{element.name}'",
                            impact="serious",
                            how_to_fix=f"Use a valid role for this element type, or change the element type to match the desired role.",
                            code_solution=self._generate_valid_role_solution(element),
                            line_number=line_number
                        ))
                        
                    continue
                    
                # Check if this element is likely interactive
                if (element.has_attr('onclick') or element.has_attr('onkeydown') or 
                    (element.has_attr('tabindex') and element['tabindex'] != '-1')):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description="Interactive element does not have an explicit role",
                        impact="serious",
                        how_to_fix="Add an appropriate role attribute to indicate the element's function to assistive technologies.",
                        code_solution=self._generate_role_solution(element),
                        line_number=line_number
                    ))
        
        # Check elements that already have roles
        for element in soup.find_all(attrs={"role": True}):
            role = element['role']
            
            # Check if the role is valid for this element
            if not self._is_valid_role_for_element(element, role):
                element_path = self.get_element_path(element)
                element_html = str(element)
                line_number = self.get_line_number(element, html_content)
                
                issues.append(self.create_issue(
                    element_path=element_path,
                    element_html=element_html,
                    description=f"Element has invalid role '{role}' for element type '{element.name}'",
                    impact="serious",
                    how_to_fix=f"Use a valid role for this element type, or change the element type to match the desired role.",
                    code_solution=self._generate_valid_role_solution(element),
                    line_number=line_number
                ))
    
    def _check_form_labels(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check form controls for proper labels."""
        for selector in self.form_controls_needing_labels:
            for element in soup.select(selector):
                # Skip elements with built-in labels (e.g., button with text)
                if element.name == 'button' and element.get_text(strip=True):
                    continue
                    
                # Check if the element has some form of label
                if not self._has_label(element, soup):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    
                    issues.append(self.create_issue(
                        element_path=element_path,
                        element_html=element_html,
                        description="Form control does not have a proper label",
                        impact="critical",
                        how_to_fix="Add an associated label element, or use aria-label or aria-labelledby.",
                        code_solution=self._generate_label_solution(element),
                        line_number=line_number
                    ))
    
    def _check_custom_controls(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check custom controls for required ARIA states and properties."""
        for selector in self.custom_controls:
            for element in soup.select(selector):
                role = element.get('role')
                if not role:
                    continue
                    
                # Get required states for this role
                required_states = self.required_states.get(role, [])
                
                # Check if the element has the required states
                for state in required_states:
                    if not element.has_attr(state):
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Element with role='{role}' is missing required state attribute '{state}'",
                            impact="serious",
                            how_to_fix=f"Add the required '{state}' attribute to convey the element's state to assistive technologies.",
                            code_solution=self._generate_aria_state_solution(element, state),
                            line_number=line_number
                        ))
    
    def _check_invalid_aria(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        """Check for invalid ARIA attributes."""
        # Find all elements with aria attributes
        for element in soup.find_all(lambda tag: any(attr.startswith('aria-') for attr in tag.attrs)):
            for attr in list(element.attrs):
                if attr.startswith('aria-'):
                    # Check for invalid boolean values
                    if attr in ['aria-hidden', 'aria-checked', 'aria-selected', 'aria-expanded', 
                              'aria-disabled', 'aria-pressed', 'aria-busy', 'aria-required']:
                        value = element[attr].lower()
                        if value not in ['true', 'false']:
                            element_path = self.get_element_path(element)
                            element_html = str(element)
                            line_number = self.get_line_number(element, html_content)
                            
                            issues.append(self.create_issue(
                                element_path=element_path,
                                element_html=element_html,
                                description=f"ARIA attribute '{attr}' has invalid value '{value}'. It must be 'true' or 'false'.",
                                impact="serious",
                                how_to_fix=f"Correct the value of '{attr}' to be either 'true' or 'false'.",
                                code_solution=self._generate_aria_correction_solution(element, attr, value),
                                line_number=line_number
                            ))
    
    def _has_accessible_name(self, element: Tag) -> bool:
        """
        Check if an element has an accessible name.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            True if the element has an accessible name
        """
        # Check for aria-label
        if element.has_attr('aria-label') and element['aria-label'].strip():
            return True
        
        # Check for aria-labelledby
        if element.has_attr('aria-labelledby') and element['aria-labelledby'].strip():
            return True
        
        # Check for title attribute
        if element.has_attr('title') and element['title'].strip():
            return True
        
        # Check for alt text on images
        if element.name == 'img' and element.has_attr('alt') and element['alt'].strip():
            return True
        
        # Check for text content
        if element.get_text(strip=True):
            return True
        
        # Check for value on buttons
        if element.name == 'input' and element.get('type') in ['button', 'submit', 'reset'] and element.has_attr('value') and element['value'].strip():
            return True
        
        # Check for label association by ID
        if element.has_attr('id'):
            label = element.find_parent().find('label', attrs={'for': element['id']})
            if label and label.get_text(strip=True):
                return True
        
        # Check for wrapped label
        parent = element.parent
        if parent and parent.name == 'label' and parent.get_text(strip=True):
            return True
        
        return False
    
    def _has_label(self, element: Tag, soup: BeautifulSoup) -> bool:
        """
        Check if a form control has a proper label.
        
        Args:
            element: BeautifulSoup element
            soup: BeautifulSoup object
            
        Returns:
            True if the element has a label
        """
        # Check for aria-label
        if element.has_attr('aria-label') and element['aria-label'].strip():
            return True
        
        # Check for aria-labelledby
        if element.has_attr('aria-labelledby') and element['aria-labelledby'].strip():
            # Try to find the referenced element
            if any(soup.find(id=label_id) for label_id in element['aria-labelledby'].split()):
                return True
        
        # Check for title attribute
        if element.has_attr('title') and element['title'].strip():
            return True
        
        # Check for explicit label with for attribute
        if element.has_attr('id'):
            label = soup.find('label', attrs={'for': element['id']})
            if label and label.get_text(strip=True):
                return True
        
        # Check for implicit label (element wrapped in a label)
        parent = element.parent
        while parent and parent.name != 'body':
            if parent.name == 'label' and parent.get_text(strip=True):
                return True
            parent = parent.parent
        
        # Check for placeholder as a fallback (not a replacement for a label, but better than nothing)
        if element.has_attr('placeholder') and element['placeholder'].strip():
            return True
        
        return False
    
    def _is_valid_role_for_element(self, element: Tag, role: str) -> bool:
        """
        Check if a role is valid for an element type.
        
        Args:
            element: BeautifulSoup element
            role: ARIA role value
            
        Returns:
            True if the role is valid for this element type
        """
        if element.name not in self.valid_roles_for_elements:
            return True  # If we don't have specific rules for this element, assume it's valid
        
        valid_roles = self.valid_roles_for_elements[element.name]
        if '*' in valid_roles:
            return True  # This element can have any role
        
        return role in valid_roles
    
    def _generate_accessible_name_solution(self, element: Tag) -> str:
        """
        Generate solution for an element missing an accessible name.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            HTML string with solution
        """
        element_type = element.name
        
        # Generate different solutions based on element type
        if element_type == 'a' or element_type == 'button':
            return f"""<!-- Add visible text content -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>
    Link/Button Text
</{element_type}>

<!-- OR use aria-label for icon-only buttons -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-label')} aria-label="Descriptive label">
    <!-- Icon or empty content -->
</{element_type}>
"""
        elif element_type == 'input':
            input_type = element.get('type', 'text')
            
            if input_type in ['submit', 'button', 'reset']:
                # For button inputs
                return f"""<!-- Add value attribute for button text -->
<input {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'value')} value="Descriptive Button Text">

<!-- OR use aria-label if a non-text button is required -->
<input {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-label')} aria-label="Descriptive Button Text">
"""
            else:
                # For other form controls
                element_id = element.get('id', 'element-id')
                return f"""<!-- Add an associated label element -->
<label for="{element_id}">Descriptive Label</label>
<input {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>

<!-- OR use aria-label -->
<input {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-label')} aria-label="Descriptive Label">
"""
        else:
            # Generic solution
            return f"""<!-- Add an accessible name using one of these methods -->

<!-- Method 1: Add visible text content -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>
    Descriptive Text
</{element_type}>

<!-- Method 2: Use aria-label -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-label')} aria-label="Descriptive Label">
    <!-- Content -->
</{element_type}>

<!-- Method 3: Use aria-labelledby to reference another element -->
<div id="element-label">Descriptive Label</div>
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-labelledby')} aria-labelledby="element-label">
    <!-- Content -->
</{element_type}>
"""
    
    def _generate_role_solution(self, element: Tag) -> str:
        """
        Generate solution for an element missing a role.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            HTML string with solution
        """
        element_type = element.name
        suggested_roles = []
        
        # Suggest appropriate roles based on element type and attributes
        if element.has_attr('onclick') or element.has_attr('onkeydown'):
            suggested_roles = ['button']
        elif element_type == 'div' or element_type == 'span':
            if element.find('input', {'type': 'checkbox'}):
                suggested_roles = ['checkbox', 'switch']
            elif element.find('input', {'type': 'radio'}):
                suggested_roles = ['radio']
            elif element.has_attr('tabindex') and element['tabindex'] != '-1':
                suggested_roles = ['button', 'link']
        
        if not suggested_roles:
            suggested_roles = ['button', 'link', 'checkbox', 'menuitem']
        
        suggested_role = suggested_roles[0]
        
        return f"""<!-- Add an appropriate role attribute -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'role')} role="{suggested_role}">
    {element.decode_contents()}
</{element_type}>

<!-- Other appropriate roles for this element could be: {', '.join(suggested_roles[1:]) if len(suggested_roles) > 1 else 'none'} -->
"""
    
    def _generate_valid_role_solution(self, element: Tag) -> str:
        """
        Generate solution for an element with an invalid role.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            HTML string with solution
        """
        element_type = element.name
        current_role = element.get('role', '')
        
        # Get valid roles for this element type
        valid_roles = self.valid_roles_for_elements.get(element_type, ['button', 'link'])
        if '*' in valid_roles:
            valid_roles = ['button', 'link', 'checkbox', 'menuitem']
        
        if valid_roles:
            suggested_role = valid_roles[0]
            
            solution1 = f"""<!-- Option 1: Change the role to a valid one for this element type -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'role')} role="{suggested_role}">
    {element.decode_contents()}
</{element_type}>

<!-- Valid roles for {element_type} elements include: {', '.join(valid_roles)} -->
"""
            
            # Suggest an alternative element type for the desired role
            better_element = 'div'  # Default fallback
            for el_type, roles in self.valid_roles_for_elements.items():
                if current_role in roles or '*' in roles:
                    better_element = el_type
                    break
                    
            solution2 = f"""<!-- Option 2: Change the element type to one that supports the role '{current_role}' -->
<{better_element} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>
    {element.decode_contents()}
</{better_element}>
"""
            
            return solution1 + "\n" + solution2
        else:
            # If we don't have specific rules, suggest using a div or span
            return f"""<!-- Use a more generic element type that supports any role -->
<div {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>
    {element.decode_contents()}
</div>
"""
    
    def _generate_label_solution(self, element: Tag) -> str:
        """
        Generate solution for a form control without a label.
        
        Args:
            element: BeautifulSoup element
            
        Returns:
            HTML string with solution
        """
        element_type = element.name
        element_id = element.get('id', '')
        
        if not element_id:
            element_id = f"{element_type}-{hash(str(element)) % 1000}"
        
        return f"""<!-- Option 1: Add an explicit label with 'for' attribute -->
<label for="{element_id}">Descriptive Label</label>
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'id')} id="{element_id}">

<!-- Option 2: Wrap the input in a label -->
<label>
    Descriptive Label
    <{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items())}>
</label>

<!-- Option 3: Use aria-label when a visible label is not possible -->
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-label')} aria-label="Descriptive Label">

<!-- Option 4: Use aria-labelledby to reference another element -->
<div id="label-{element_id}">Descriptive Label</div>
<{element_type} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != 'aria-labelledby')} aria-labelledby="label-{element_id}">
"""
    
    def _generate_aria_state_solution(self, element: Tag, state: str) -> str:
        """
        Generate solution for an element missing a required ARIA state.
        
        Args:
            element: BeautifulSoup element
            state: Missing ARIA state attribute
            
        Returns:
            HTML string with solution
        """
        role = element.get('role', '')
        
        # Determine appropriate initial value based on the state
        if state == 'aria-checked':
            value = 'false'
        elif state == 'aria-selected':
            value = 'false'
        elif state == 'aria-expanded':
            value = 'false'
        elif state == 'aria-valuenow':
            value = '50'
            return f"""<!-- Add required ARIA state attributes for role='{role}' -->
<{element.name} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k not in ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'])} aria-valuenow="50" aria-valuemin="0" aria-valuemax="100">
    {element.decode_contents()}
</{element.name}>

<!-- Also add JavaScript to update these values dynamically -->
<script>
// Update the aria attributes when the control's value changes
document.querySelector('selector-for-element').addEventListener('input', function(event) {{
  const newValue = /* get the new value */;
  this.setAttribute('aria-valuenow', newValue);
}});
</script>
"""
        else:
            value = 'true'
        
        return f"""<!-- Add required ARIA state attribute -->
<{element.name} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != state)} {state}="{value}">
    {element.decode_contents()}
</{element.name}>

<!-- Also add JavaScript to update this attribute when the state changes -->
<script>
// Example: Toggle the {state} attribute when clicked
document.querySelector('selector-for-element').addEventListener('click', function() {{
  const currentState = this.getAttribute('{state}') === 'true';
  this.setAttribute('{state}', (!currentState).toString());
}});
</script>
"""
    
    def _generate_aria_correction_solution(self, element: Tag, attr: str, value: str) -> str:
        """
        Generate solution for an element with an invalid ARIA attribute value.
        
        Args:
            element: BeautifulSoup element
            attr: ARIA attribute with invalid value
            value: Current invalid value
            
        Returns:
            HTML string with solution
        """
        # Determine the correct value (typically 'true' or 'false')
        suggested_value = 'true'
        if value.lower() in ['0', 'no', 'n', 'off', 'disabled', 'none']:
            suggested_value = 'false'
        
        return f"""<!-- Correct the ARIA attribute value -->
<{element.name} {' '.join(f'{k}="{v}"' for k, v in element.attrs.items() if k != attr)} {attr}="{suggested_value}">
    {element.decode_contents()}
</{element.name}>

<!-- ARIA boolean attributes must use the string values "true" or "false" -->
"""