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
        
        self.personal_info_fields = {
            'name', 'fullname', 'firstname', 'lastname', 'fname', 'lname',
            'email', 'emailaddress', 'phone', 'phonenumber', 'mobile', 'tel',
            'address', 'streetaddress', 'street', 'city', 'state', 'zip', 'zipcode',
            'postal', 'postalcode', 'country', 'username', 'password', 'birth',
            'birthday', 'birthdate', 'dob', 'age', 'gender', 'credit', 'creditcard',
            'cc', 'card', 'cardnumber', 'expiry', 'expiration', 'cvc', 'cvv',
            'ssn', 'social', 'passport', 'license', 'payment',
        }
        
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
    
    def _build_attrs_string(self, attrs_dict: dict, exclude_attrs: Optional[List[str]] = None) -> str:
        if exclude_attrs is None:
            exclude_attrs = []
        attr_list = []
        for k_item, v_item_list in attrs_dict.items():
            if k_item.lower() in exclude_attrs:
                continue
            v_str = " ".join(v_item_list) if isinstance(v_item_list, list) else v_item_list
            v_str_escaped = v_str.replace('"', '&quot;')
            attr_list.append(f'{k_item}="{v_str_escaped}"')
        return " ".join(attr_list)

    def validate(self, soup: BeautifulSoup, html_content: str) -> List[ValidationIssue]:
        issues = []
        forms = soup.find_all('form')
        
        for form in forms:
            if self._is_likely_multi_step_form(form):
                input_fields = self._get_form_input_fields(form)
                for field_name, field in input_fields.items():
                    if self._looks_like_personal_info_field(field_name, field):
                        if not self._has_proper_autocomplete(field):
                            element_path = self.get_element_path(field)
                            element_html = str(field)
                            line_number = self.get_line_number(field, html_content)
                            issues.append(self.create_issue(
                                element_path=element_path, element_html=element_html,
                                description="Input field likely collecting personal information in multi-step form process lacks proper autocomplete attribute.",
                                impact="serious",
                                how_to_fix="Add appropriate autocomplete attribute to ensure users don't need to re-enter information they've already provided in earlier steps.",
                                code_solution=self._generate_autocomplete_solution(field),
                                line_number=line_number
                            ))
        
        all_forms = soup.find_all('form')
        if len(all_forms) > 1:
            all_input_fields = {}
            for form in all_forms:
                input_fields = self._get_form_input_fields(form)
                all_input_fields.update(input_fields)
            
            field_names = [self._normalize_field_name(name) for name in all_input_fields.keys()]
            seen_fields = set()
            duplicate_fields = set()
            
            for name in field_names:
                if name in seen_fields:
                    duplicate_fields.add(name)
                seen_fields.add(name)
            
            for field_name, field in all_input_fields.items():
                normalized_name = self._normalize_field_name(field_name)
                if normalized_name in duplicate_fields and self._looks_like_personal_info_field(field_name, field):
                    if not self._has_proper_autocomplete(field):
                        element_path = self.get_element_path(field)
                        element_html = str(field)
                        line_number = self.get_line_number(field, html_content)
                        issues.append(self.create_issue(
                            element_path=element_path, element_html=element_html,
                            description=f"Duplicate input field '{field_name}' across multiple forms lacks proper autocomplete attribute.",
                            impact="serious",
                            how_to_fix="Add appropriate autocomplete attribute to duplicate fields to meet the redundant entry requirement.",
                            code_solution=self._generate_autocomplete_solution(field),
                            line_number=line_number
                        ))
        return issues
    
    def _is_likely_multi_step_form(self, form: Tag) -> bool:
        if form.select('.pagination, .steps, .wizard-steps, .progress-indicator'): return True
        if form.find_all(['button', 'input'], string=re.compile(r'next|continue|proceed|forward|back|previous', re.IGNORECASE)): return True
        if form.find_all(['button', 'input'], class_=re.compile(r'next|continue|proceed|forward|back|previous', re.IGNORECASE)): return True
        if form.has_attr('class') and re.search(r'step|wizard|multi|page', ' '.join(form['class']), re.IGNORECASE): return True
        if form.has_attr('id') and re.search(r'step|wizard|multi|page', form['id'], re.IGNORECASE): return True
        hidden_fieldsets = form.find_all('fieldset', style=re.compile(r'display:\s*none', re.IGNORECASE))
        visible_fieldsets = form.find_all('fieldset')
        if hidden_fieldsets and len(visible_fieldsets) > len(hidden_fieldsets): return True
        return False
    
    def _get_form_input_fields(self, form: Tag) -> Dict[str, Tag]:
        result = {}
        input_elements = form.find_all(['input', 'select', 'textarea'])
        for input_el in input_elements:
            if input_el.name == 'input' and input_el.get('type') in ['button', 'submit', 'reset', 'hidden']:
                continue
            if input_el.has_attr('name') and input_el['name']:
                result[input_el['name']] = input_el
            elif input_el.has_attr('id') and input_el['id']:
                result[input_el['id']] = input_el
        return result
    
    def _normalize_field_name(self, name: str) -> str:
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    def _looks_like_personal_info_field(self, field_name: str, field: Tag) -> bool:
        normalized_name = self._normalize_field_name(field_name)
        if any(info_field in normalized_name for info_field in self.personal_info_fields): return True
        if field.has_attr('id'):
            label = field.find_parent().find('label', attrs={'for': field['id']})
            if label and label.get_text():
                label_text = label.get_text().lower()
                if any(info_field in label_text for info_field in self.personal_info_fields): return True
        if field.has_attr('placeholder'):
            placeholder = field['placeholder'].lower()
            if any(info_field in placeholder for info_field in self.personal_info_fields): return True
        if field.name == 'input' and field.has_attr('type') and field['type'] in ['email', 'tel', 'number', 'date']:
            return True
        return False
    
    def _has_proper_autocomplete(self, field: Tag) -> bool:
        if field.has_attr('autocomplete'):
            autocomplete_value = field['autocomplete'].lower()
            if autocomplete_value != 'off':
                parts = autocomplete_value.split()
                if any(part in self.valid_autocomplete_values for part in parts):
                    return True
                return True 
        return False
    
    def _generate_autocomplete_solution(self, field: Tag) -> str:
        field_name_attr = field.get('name', field.get('id', ''))
        normalized_name = self._normalize_field_name(field_name_attr)
        autocomplete_value = 'on'
        mapping = {
            'name': 'name', 'fullname': 'name', 'firstname': 'given-name',
            'lastname': 'family-name', 'fname': 'given-name', 'lname': 'family-name',
            'email': 'email', 'phone': 'tel', 'tel': 'tel', 'mobile': 'tel',
            'address': 'street-address', 'streetaddress': 'street-address',
            'city': 'address-level2', 'state': 'address-level1',
            'zip': 'postal-code', 'zipcode': 'postal-code', 'postalcode': 'postal-code',
            'country': 'country', 'username': 'username', 'password': 'new-password',
            'birth': 'bday', 'birthday': 'bday', 'birthdate': 'bday',
            'creditcard': 'cc-number', 'cardnumber': 'cc-number',
        }
        for key, value in mapping.items():
            if key in normalized_name:
                autocomplete_value = value
                break
        if field.name == 'input' and field.get('type') == 'email':
            autocomplete_value = 'email'
        elif field.name == 'input' and field.get('type') == 'tel':
            autocomplete_value = 'tel'
        
        attrs_str = self._build_attrs_string(field.attrs, exclude_attrs=['autocomplete'])
        return f'<{field.name} {attrs_str} autocomplete="{autocomplete_value}">'
