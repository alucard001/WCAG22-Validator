"""
WCAG 2.2 - 3.3.7 Redundant Entry (Level A)

Information previously entered by or provided to the user that is required
to be entered again in the same process is either:
- auto-populated, or
- available for the user to select.
"""

from typing import List, Dict, Set, Tuple, Optional
from bs4 import BeautifulSoup, Tag
import re

from .base import BaseCriterion
from ..reporter import ValidationIssue


class Criterion_3_3_7(BaseCriterion):
    """
    Implements WCAG 2.2 Success Criterion 3.3.7: Redundant Entry.
    
    This criterion requires that when users are asked for information they've
    already provided, it should be either auto-populated or available for selection.
    
    Note: This criterion is challenging to validate with static analysis since
    it involves multi-step processes and form data handling which typically
    requires JavaScript evaluation. This implementation provides a best-effort
    static analysis looking for potential issues.
    """
    
    def __init__(self):
        super().__init__()
        self.id = "3.3.7"
        self.name = "Redundant Entry"
        self.level = "A"
        self.url = "https://www.w3.org/WAI/WCAG22/Understanding/redundant-entry.html"
        self.description = """
        Information previously entered by or provided to the user that is required
        to be entered again in the same process is either auto-populated or available
        for the user to select.
        """
        
        # Common form field types that should use autocomplete
        self.personal_info_fields = {
            'name', 'fullname', 'firstname', 'lastname', 'fname', 'lname',
            'email', 'emailaddress', 'phone', 'phonenumber', 'mobile', 'tel',
            'address', 'streetaddress', 'street', 'city', 'state', 'zip', 'zipcode',
            'postal', 'postalcode', 'country', 'username', 'password', 'birth',
            'birthday', 'birthdate', 'dob', 'age', 'gender', 'credit', 'creditcard',
            'cc', 'card', 'cardnumber', 'expiry', 'expiration', 'cvc', 'cvv',
            'ssn', 'social', 'passport', 'license', 'payment',
        }
        
        # Valid autocomplete attribute values from HTML spec
        self.valid_autocomplete_values = {
            'off', 'on', 'name', 'honorific-prefix', 'given-name', 'additional-name',
            'family-name', 'honorific-suffix', 'nickname', 'email', 'username',
            'new-password', 'current-password', 'one-time-code', 'organization-title',
            'organization', 'street-address', 'address-line1', 'address-line2',
            'address-line3', 'address-level4', 'address-level3', 'address-level2',
            'address-level1', 'country', 'country-name', 'postal-code', 'cc-name',
            'cc-given-name', 'cc-additional-name', 'cc-family-name', 'cc-number',
            'cc-exp', 'cc-exp-month', 'cc-exp-year', 'cc-csc', 'cc-type',
            'transaction-currency', 'transaction-amount', 'language', 'bday',
            'bday-day', 'bday-month', 'bday-year', 'sex', 'tel', 'tel-country-code',
            'tel-national', 'tel-area-code', 'tel-local', 'tel-extension',
            'impp', 'url', 'photo',
        }
    
    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        """
        Validate HTML content against 3.3.7 criterion.
        
        This is a limited static analysis that identifies potential issues.
        Full validation requires dynamic browser testing of the complete user flow.
        
        Args:
            soup: BeautifulSoup object of the HTML content
            html_content: Original HTML content as string
            
        Returns:
            List of ValidationIssue objects
        """
        issues = []
        
        # Check for forms with potential multi-step processes
        forms = soup.find_all('form')
        
        for form in forms:
            # Look for indicators of multi-step forms
            if self._is_likely_multi_step_form(form):
                input_fields = self._get_form_input_fields(form)
                
                # Check for proper autocomplete on fields likely to request personal info
                for field_name, field in input_fields.items():
                    if self._looks_like_personal_info_field(field_name, field):
                        if not self._has_proper_autocomplete(field):
                            element_path = self.get_element_path(field)
                            element_html = str(field)
                            line_number = self.get_line_number(field, html_content)
                            
                            issues.append(self.create_issue(
                                element_path=element_path,
                                element_html=element_html,
                                description=f"Input field likely collecting personal information in multi-step form process lacks proper autocomplete attribute.",
                                impact="serious",
                                how_to_fix="Add appropriate autocomplete attribute to ensure users don't need to re-enter information they've already provided in earlier steps.",
                                code_solution=self._generate_autocomplete_solution(field),
                                line_number=line_number
                            ))
        
        # Check for multi-form processes on the same page
        # This could indicate a multi-step process that shows/hides different forms
        all_forms = soup.find_all('form')
        if len(all_forms) > 1:
            all_input_fields = {}
            
            # Collect all input fields across forms
            for form in all_forms:
                input_fields = self._get_form_input_fields(form)
                all_input_fields.update(input_fields)
            
            # Find duplicate fields across forms
            field_names = [self._normalize_field_name(name) for name in all_input_fields.keys()]
            seen_fields = set()
            duplicate_fields = set()
            
            for name in field_names:
                if name in seen_fields:
                    duplicate_fields.add(name)
                seen_fields.add(name)
            
            # Check duplicate fields for proper autocomplete
            for field_name, field in all_input_fields.items():
                normalized_name = self._normalize_field_name(field_name)
                
                if normalized_name in duplicate_fields and self._looks_like_personal_info_field(field_name, field):
                    if not self._has_proper_autocomplete(field):
                        element_path = self.get_element_path(field)
                        element_html = str(field)
                        line_number = self.get_line_number(field, html_content)
                        
                        issues.append(self.create_issue(
                            element_path=element_path,
                            element_html=element_html,
                            description=f"Duplicate input field '{field_name}' across multiple forms lacks proper autocomplete attribute.",
                            impact="serious",
                            how_to_fix="Add appropriate autocomplete attribute to duplicate fields to meet the redundant entry requirement.",
                            code_solution=self._generate_autocomplete_solution(field),
                            line_number=line_number
                        ))
        
        return issues
    
    def _is_likely_multi_step_form(self, form: Tag) -> bool:
        """
        Check if a form is likely part of a multi-step process.
        
        Args:
            form: BeautifulSoup form tag
            
        Returns:
            True if the form appears to be part of a multi-step process
        """
        # Check for pagination indicators
        pagination_elements = form.select('.pagination, .steps, .wizard-steps, .progress-indicator')
        if pagination_elements:
            return True
        
        # Check for next/prev buttons
        navigation_buttons = form.find_all(['button', 'input'], 
                                        string=re.compile(r'next|continue|proceed|forward|back|previous', re.IGNORECASE))
        if navigation_buttons:
            return True
            
        # Check for buttons with navigation classes
        nav_class_buttons = form.find_all(['button', 'input'], 
                                       class_=re.compile(r'next|continue|proceed|forward|back|previous', re.IGNORECASE))
        if nav_class_buttons:
            return True
        
        # Check for step indicators in form classes or ID
        if form.has_attr('class') and re.search(r'step|wizard|multi|page', ' '.join(form['class']), re.IGNORECASE):
            return True
            
        if form.has_attr('id') and re.search(r'step|wizard|multi|page', form['id'], re.IGNORECASE):
            return True
        
        # Check for hidden fieldsets (often used in multi-step forms)
        hidden_fieldsets = form.find_all('fieldset', style=re.compile(r'display:\s*none', re.IGNORECASE))
        visible_fieldsets = form.find_all('fieldset')
        if hidden_fieldsets and len(visible_fieldsets) > len(hidden_fieldsets):
            return True
        
        return False
    
    def _get_form_input_fields(self, form: Tag) -> Dict[str, Tag]:
        """
        Get all input fields in a form with their names as keys.
        
        Args:
            form: BeautifulSoup form tag
            
        Returns:
            Dictionary mapping field names to input elements
        """
        result = {}
        
        # Check various input types
        input_elements = form.find_all(['input', 'select', 'textarea'])
        
        for input_el in input_elements:
            # Skip buttons, submit inputs, and hidden fields
            if input_el.name == 'input' and input_el.get('type') in ['button', 'submit', 'reset', 'hidden']:
                continue
                
            if input_el.has_attr('name') and input_el['name']:
                result[input_el['name']] = input_el
            elif input_el.has_attr('id') and input_el['id']:
                result[input_el['id']] = input_el
        
        return result
    
    def _normalize_field_name(self, name: str) -> str:
        """
        Normalize field name for comparison (ignore case, remove non-alphanumeric).
        
        Args:
            name: Field name to normalize
            
        Returns:
            Normalized field name
        """
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    def _looks_like_personal_info_field(self, field_name: str, field: Tag) -> bool:
        """
        Check if a field appears to collect personal information.
        
        Args:
            field_name: Name or ID of the field
            field: BeautifulSoup tag for the field
            
        Returns:
            True if field appears to collect personal information
        """
        # Normalize the field name to check against common patterns
        normalized_name = self._normalize_field_name(field_name)
        
        # Check against common personal info field names
        for info_field in self.personal_info_fields:
            if info_field in normalized_name:
                return True
        
        # Check field labels if available
        if field.has_attr('id'):
            # Find label that references this field
            label = field.find_parent().find('label', attrs={'for': field['id']})
            if label and label.get_text():
                label_text = label.get_text().lower()
                for info_field in self.personal_info_fields:
                    if info_field in label_text:
                        return True
        
        # Check placeholder text
        if field.has_attr('placeholder'):
            placeholder = field['placeholder'].lower()
            for info_field in self.personal_info_fields:
                if info_field in placeholder:
                    return True
        
        # Check for specific input types
        if field.name == 'input' and field.has_attr('type'):
            if field['type'] in ['email', 'tel', 'number', 'date']:
                return True
        
        return False
    
    def _has_proper_autocomplete(self, field: Tag) -> bool:
        """
        Check if a field has proper autocomplete attributes.
        
        Args:
            field: BeautifulSoup tag for the field
            
        Returns:
            True if field has proper autocomplete attributes
        """
        # Check if autocomplete attribute exists and is not set to 'off'
        if field.has_attr('autocomplete'):
            autocomplete_value = field['autocomplete'].lower()
            
            # Check if it's a valid value
            if autocomplete_value != 'off':
                # Check if it's one of the standard values
                parts = autocomplete_value.split()
                for part in parts:
                    if part in self.valid_autocomplete_values:
                        return True
                
                # If it's not 'off' and has some other value, consider it valid
                # (could be a custom value for site-specific autocomplete)
                return True
        
        return False
    
    def _generate_autocomplete_solution(self, field: Tag) -> str:
        """
        Generate a solution with appropriate autocomplete attribute.
        
        Args:
            field: BeautifulSoup tag for the field
            
        Returns:
            HTML string with solution
        """
        # Get the field name or id
        field_name = field.get('name', field.get('id', ''))
        normalized_name = self._normalize_field_name(field_name)
        
        # Try to determine the most appropriate autocomplete value
        autocomplete_value = 'on'  # Default
        
        # Map common field types to appropriate autocomplete values
        mapping = {
            'name': 'name',
            'fullname': 'name',
            'firstname': 'given-name',
            'lastname': 'family-name',
            'fname': 'given-name',
            'lname': 'family-name',
            'email': 'email',
            'phone': 'tel',
            'tel': 'tel',
            'mobile': 'tel',
            'address': 'street-address',
            'streetaddress': 'street-address',
            'city': 'address-level2',
            'state': 'address-level1',
            'zip': 'postal-code',
            'zipcode': 'postal-code',
            'postalcode': 'postal-code',
            'country': 'country',
            'username': 'username',
            'password': 'new-password',
            'birth': 'bday',
            'birthday': 'bday',
            'birthdate': 'bday',
            'creditcard': 'cc-number',
            'cardnumber': 'cc-number',
        }
        
        # Find the best match
        for key, value in mapping.items():
            if key in normalized_name:
                autocomplete_value = value
                break
                
        # Check if it's an input type="email" without explicit autocomplete
        if field.name == 'input' and field.get('type') == 'email':
            autocomplete_value = 'email'
        elif field.name == 'input' and field.get('type') == 'tel':
            autocomplete_value = 'tel'
        
        # Generate the solution
        attrs = " ".join([f'{k}="{v}"' for k, v in field.attrs.items() if k != 'autocomplete'])
        return f'<{field.name} {attrs} autocomplete="{autocomplete_value}">'