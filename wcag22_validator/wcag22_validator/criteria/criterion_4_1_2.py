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
        
        self.interactive_elements = [
            'a[href]', 'button', 'input:not([type="hidden"])', 'select', 'textarea',
            '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="radio"]',
            '[role="combobox"]', '[role="listbox"]', '[role="menu"]', '[role="menuitem"]',
            '[role="menuitemcheckbox"]', '[role="menuitemradio"]', '[role="option"]',
            '[role="switch"]', '[role="tab"]', '[role="textbox"]', '[role="treeitem"]',
            '[tabindex]:not([tabindex="-1"])', '[aria-haspopup]', '[contenteditable="true"]'
        ]
        self.elements_needing_roles = [
            'div[onclick]', 'span[onclick]', 'div[onkeydown]', 'span[onkeydown]',
            'div[tabindex]:not([tabindex="-1"])', 'span[tabindex]:not([tabindex="-1"])',
            '[aria-label]', '[aria-labelledby]' 
        ]
        self.form_controls_needing_labels = [
            'input:not([type="hidden"]):not([type="button"]):not([type="submit"]):not([type="reset"])',
            'select', 'textarea'
        ]
        self.custom_controls = [
            '[role="checkbox"]', '[role="radio"]', '[role="switch"]', '[role="combobox"]',
            '[role="listbox"]', '[role="menu"]', '[role="menubar"]', '[role="radiogroup"]',
            '[role="slider"]', '[role="tablist"]', '[role="tree"]'
        ]
        self.required_states = {
            'checkbox': ['aria-checked'], 'radio': ['aria-checked'], 'switch': ['aria-checked'],
            'combobox': ['aria-expanded'], 'listbox': [], 'option': ['aria-selected'],
            'menu': [], 'menuitem': [], 'menuitemcheckbox': ['aria-checked'],
            'menuitemradio': ['aria-checked'], 'radiogroup': [],
            'slider': ['aria-valuenow', 'aria-valuemin', 'aria-valuemax'],
            'tablist': [], 'tab': ['aria-selected'], 'tree': [],
            'treeitem': ['aria-expanded', 'aria-selected']
        }
        self.valid_roles_for_elements = {
            'a': ['button', 'checkbox', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 
                  'option', 'radio', 'switch', 'tab', 'treeitem', 'link', 'doc-backlink', 'doc-biblioref', 'doc-glossref', 'doc-noteref'],
            'button': ['checkbox', 'link', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 
                       'option', 'radio', 'switch', 'tab', 'button'],
            'img': ['button', 'checkbox', 'link', 'menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'switch', 'tab', 'none', 'presentation', 'img', 'figure', 'doc-cover', 'doc-screenshot'],
            'input': ['button', 'checkbox', 'option', 'radio', 'switch', 'textbox', 'combobox', 'searchbox', 'slider', 'spinbutton'],
            'li': ['menuitem', 'menuitemcheckbox', 'menuitemradio', 'option', 'radio', 'tab', 'treeitem', 'listitem', 'doc-biblioentry', 'doc-endnote'],
            'select': ['combobox', 'listbox', 'menu'], 
            'ul': ['listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'tree', 'list', 'directory', 'group', 'toolbar', 'doc-toc', 'doc-index'],
            'ol': ['listbox', 'menu', 'menubar', 'radiogroup', 'tablist', 'tree', 'list', 'directory', 'group', 'toolbar', 'doc-toc', 'doc-index'],
            'div': ['*'], 'span': ['*'], 'article': ['application', 'document', 'feed', 'main', 'presentation', 'region', 'doc-abstract', 'doc-chapter', 'doc-part'],
            'section': ['application', 'document', 'feed', 'main', 'presentation', 'region', 'alert', 'log', 'marquee', 'status', 'timer', 'doc-abstract', 'doc-chapter', 'doc-part', 'doc-acknowledgments', 'doc-afterword', 'doc-appendix', 'doc-bibliography', 'doc-colophon', 'doc-conclusion', 'doc-credits', 'doc-dedication', 'doc-epigraph', 'doc-epilogue', 'doc-errata', 'doc-example', 'doc-foreword', 'doc-glossary', 'doc-introduction', 'doc-notice', 'doc-preface', 'doc-prologue'],
            'h1': ['tab', 'heading'], 'h2': ['tab', 'heading'], 'h3': ['tab', 'heading'], 
            'h4': ['tab', 'heading'], 'h5': ['tab', 'heading'], 'h6': ['tab', 'heading'],
            'table': ['grid', 'treegrid', 'table', 'figure'], 'td': ['gridcell', 'cell', 'columnheader', 'rowheader'], 'th': ['columnheader', 'rowheader', 'gridcell', 'cell'],
            'tr': ['row', 'rowgroup']
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
        self._check_accessible_names(soup, issues, html_content)
        self._check_roles(soup, issues, html_content)
        self._check_form_labels(soup, issues, html_content)
        self._check_custom_controls(soup, issues, html_content)
        self._check_invalid_aria(soup, issues, html_content)
        return issues
    
    def _check_accessible_names(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        for selector in self.interactive_elements:
            for element in soup.select(selector):
                if element.has_attr('aria-hidden') and element['aria-hidden'].lower() == 'true': continue
                if element.name == 'input' and element.get('type') in ['submit', 'reset', 'button'] and element.has_attr('value') and element['value'].strip(): continue
                if element.name == 'input' and element.get('type') == 'image' and element.has_attr('alt') and element['alt'].strip(): continue

                if not self._has_accessible_name(element, soup):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    issues.append(self.create_issue(
                        element_path=element_path, element_html=element_html,
                        description="Interactive element does not have an accessible name.",
                        impact="critical",
                        how_to_fix="Provide an accessible name using visible text content, aria-label, aria-labelledby, or an associated <label> for form inputs.",
                        code_solution=self._generate_accessible_name_solution(element),
                        line_number=line_number
                    ))
    
    def _check_roles(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        for selector in self.elements_needing_roles:
            for element in soup.select(selector):
                current_role = element.get('role')
                if current_role:
                    if not self._is_valid_role_for_element(element, current_role):
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        issues.append(self.create_issue(
                            element_path=element_path, element_html=element_html,
                            description=f"Element <{element.name}> has a role='{current_role}' which may not be appropriate for this element type or is a redundant ARIA role.",
                            impact="serious",
                            how_to_fix=f"Ensure the role is valid and necessary for this element. Native HTML elements often do not need explicit ARIA roles. Refer to ARIA in HTML specification.",
                            code_solution=self._generate_valid_role_solution(element),
                            line_number=line_number
                        ))
                elif (element.name in ['div', 'span'] and (element.has_attr('onclick') or element.has_attr('onkeydown') or \
                     (element.has_attr('tabindex') and element['tabindex'] != '-1'))) or \
                     (element.has_attr('aria-label') or element.has_attr('aria-labelledby')):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    issues.append(self.create_issue(
                        element_path=element_path, element_html=element_html,
                        description=f"Generic element <{element.name}> is interactive or has an ARIA label but does not have an explicit ARIA role.",
                        impact="serious",
                        how_to_fix="Add an appropriate ARIA role (e.g., role='button', role='link') to define its purpose for assistive technologies.",
                        code_solution=self._generate_role_solution(element),
                        line_number=line_number
                    ))

        for element in soup.find_all(attrs={"role": True}):
            role = element['role']
            roles = role.split(' ')
            for r_val in roles:
                r_stripped = r_val.strip()
                if r_stripped and not self._is_valid_role_for_element(element, r_stripped):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    issues.append(self.create_issue(
                        element_path=element_path, element_html=element_html,
                        description=f"Element <{element.name}> has role='{r_stripped}' which is not a valid ARIA role or is not appropriate for this element.",
                        impact="serious",
                        how_to_fix=f"Use a valid ARIA role suitable for <{element.name}>, or remove the role if the element's native semantics are sufficient.",
                        code_solution=self._generate_valid_role_solution(element),
                        line_number=line_number
                    ))
                    break 

    def _check_form_labels(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        for selector in self.form_controls_needing_labels:
            for element in soup.select(selector):
                if element.get('type') == 'hidden': continue

                if not self._has_label(element, soup):
                    element_path = self.get_element_path(element)
                    element_html = str(element)
                    line_number = self.get_line_number(element, html_content)
                    issues.append(self.create_issue(
                        element_path=element_path, element_html=element_html,
                        description=f"Form control <{element.name}{(' type='+element.get('type','')) if element.name=='input' else ''}> does not have an accessible name or label.",
                        impact="critical",
                        how_to_fix="Associate a <label> with the form control using 'for' and 'id' attributes, or provide an accessible name via aria-label or aria-labelledby.",
                        code_solution=self._generate_label_solution(element),
                        line_number=line_number
                    ))

    def _check_custom_controls(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        for selector in self.custom_controls:
            for element in soup.select(selector):
                role = element.get('role')
                if not role: continue
                
                required_states_for_role = self.required_states.get(role, [])
                for state_attr in required_states_for_role:
                    if not element.has_attr(state_attr):
                        element_path = self.get_element_path(element)
                        element_html = str(element)
                        line_number = self.get_line_number(element, html_content)
                        issues.append(self.create_issue(
                            element_path=element_path, element_html=element_html,
                            description=f"Custom control with role='{role}' is missing the required ARIA attribute: {state_attr}.",
                            impact="serious",
                            how_to_fix=f"Add the '{state_attr}' attribute with an appropriate value to manage the state of this custom control.",
                            code_solution=self._generate_aria_state_solution(element, state_attr),
                            line_number=line_number
                        ))

    def _check_invalid_aria(self, soup: BeautifulSoup, issues: List[ValidationIssue], html_content: str):
        for element in soup.find_all(lambda tag: any(attr.startswith('aria-') for attr in tag.attrs)):
            for attr_name, attr_value_list in element.attrs.items():
                attr_value = " ".join(attr_value_list) if isinstance(attr_value_list, list) else attr_value_list
                if attr_name.startswith('aria-'):
                    boolean_aria_attrs = [
                        'aria-atomic', 'aria-busy', 'aria-checked', 'aria-current', 
                        'aria-disabled', 'aria-expanded', 'aria-haspopup', 'aria-hidden', 
                        'aria-invalid', 'aria-live', 'aria-modal', 'aria-multiline', 
                        'aria-multiselectable', 'aria-pressed', 'aria-readonly', 
                        'aria-required', 'aria-selected'
                    ]
                    if attr_name in boolean_aria_attrs:
                        # For aria-current, specific tokens are allowed beyond true/false
                        valid_current_tokens = ['page', 'step', 'location', 'date', 'time', 'true', 'false']
                        if attr_name == 'aria-current' and attr_value.lower() not in valid_current_tokens:
                             issues.append(self.create_issue(
                                element_path=self.get_element_path(element), element_html=str(element),
                                description=f"ARIA attribute '{attr_name}' has an invalid value '{attr_value}'. Valid values are: {', '.join(valid_current_tokens)}.",
                                impact="serious",
                                how_to_fix=f"Correct the value of '{attr_name}'.",
                                code_solution=self._generate_aria_correction_solution(element, attr_name, attr_value),
                                line_number=self.get_line_number(element, html_content)
                            ))
                        elif attr_name != 'aria-current' and attr_value.lower() not in ['true', 'false']:
                            # aria-checked can also have 'mixed'
                            if not (attr_name == 'aria-checked' and attr_value.lower() == 'mixed'):
                                issues.append(self.create_issue(
                                    element_path=self.get_element_path(element), element_html=str(element),
                                    description=f"ARIA attribute '{attr_name}' has invalid value '{attr_value}'. It must be 'true' or 'false' (or 'mixed' for aria-checked).",
                                    impact="serious",
                                    how_to_fix=f"Correct the value of '{attr_name}' to be either 'true' or 'false' (or 'mixed' if appropriate for aria-checked).",
                                    code_solution=self._generate_aria_correction_solution(element, attr_name, attr_value),
                                    line_number=self.get_line_number(element, html_content)
                                ))
    
    def _has_accessible_name(self, element: Tag, soup: BeautifulSoup) -> bool:
        if element.has_attr('aria-label') and element['aria-label'].strip(): return True
        if element.has_attr('aria-labelledby') and element['aria-labelledby'].strip():
            label_ids = element['aria-labelledby'].split()
            if any(soup.find(id=label_id) and soup.find(id=label_id).get_text(strip=True) for label_id in label_ids):
                return True
        
        if element.name == 'img' and element.has_attr('alt') and element['alt'].strip(): return True
        if element.name == 'input' and element.get('type') == 'image' and element.has_attr('alt') and element['alt'].strip(): return True
        
        if element.name in ['input', 'select', 'textarea'] and self._has_label(element, soup): return True
        if element.get_text(strip=True): return True
        if element.name == 'input' and element.get('type') in ['button', 'submit', 'reset'] and element.has_attr('value') and element['value'].strip(): return True
        if element.has_attr('title') and element['title'].strip(): return True
        return False
    
    def _has_label(self, element: Tag, soup: BeautifulSoup) -> bool:
        if element.has_attr('id'):
            label = soup.find('label', attrs={'for': element['id']})
            if label and label.get_text(strip=True): return True
        parent = element.parent
        if parent and parent.name == 'label':
            label_text = parent.get_text(strip=True)
            input_text = element.get_text(strip=True) 
            if label_text and (label_text != input_text or not input_text): return True
        if element.has_attr('aria-label') and element['aria-label'].strip(): return True
        if element.has_attr('aria-labelledby') and element['aria-labelledby'].strip(): return True
        if element.has_attr('title') and element['title'].strip(): return True
        return False

    def _is_valid_role_for_element(self, element: Tag, role: str) -> bool:
        if element.name in ['div', 'span']: return True 
        allowed_roles = self.valid_roles_for_elements.get(element.name)
        if allowed_roles:
            if '*' in allowed_roles: return True
            return role in allowed_roles
        return True 

    def _generate_accessible_name_solution(self, element: Tag) -> str:
        attrs_str = self._build_attrs_string(element.attrs)
        element_type = element.name
        
        if element_type == 'a' or element_type == 'button':
            return f"""<!-- Add visible text content -->
<{element_type} {attrs_str}>Accessible Name Here</{element_type}>
<!-- OR use aria-label for icon-only controls -->
<{element_type} {self._build_attrs_string({k:v for k,v in element.attrs.items() if k != 'aria-label'})} aria-label="Descriptive Label"> {element.decode_contents()} </{element_type}>"""
        elif element_type == 'input':
            input_type = element.get('type', 'text')
            if input_type in ['submit', 'button', 'reset']:
                return f"<input {self._build_attrs_string({k:v for k,v in element.attrs.items() if k != 'value'})} value=\"Descriptive Button Text\">"
            else:
                el_id = element.get('id', f"input-{hash(str(element))%1000}")
                current_attrs = dict(element.attrs)
                if 'id' not in current_attrs: current_attrs['id'] = el_id
                attrs_str_with_id = self._build_attrs_string(current_attrs)
                return f"""<label for="{el_id}">Descriptive Label:</label>
<{element_type} {attrs_str_with_id}>"""
        return f"<{element_type} {self._build_attrs_string({k:v for k,v in element.attrs.items() if k != 'aria-label'})} aria-label=\"Descriptive Label\">{element.decode_contents()}</{element_type}>"

    def _generate_role_solution(self, element: Tag) -> str:
        attrs_str = self._build_attrs_string(element.attrs, exclude_attrs=['role'])
        return f"<{element.name} {attrs_str} role=\"button\">{element.decode_contents()}</{element.name}>\n<!-- Or role=\"link\", etc., depending on function -->"

    def _generate_valid_role_solution(self, element: Tag) -> str:
        attrs_str = self._build_attrs_string(element.attrs, exclude_attrs=['role'])
        return f"<!-- Review role='{element.get('role', '[unknown]')}' on <{element.name}>. -->\n<!-- Option 1: Remove role if native semantics are sufficient. -->\n<{element.name} {attrs_str}>{element.decode_contents()}</{element.name}>\n<!-- Option 2: Use a more semantically appropriate HTML element. -->"

    def _generate_label_solution(self, element: Tag) -> str:
        el_id = element.get('id', f"{element.name}-{hash(str(element))%1000}")
        current_attrs = dict(element.attrs)
        if 'id' not in current_attrs : current_attrs['id'] = el_id
        attrs_str_with_id = self._build_attrs_string(current_attrs)
        
        return f"""<!-- Option 1: Explicit label -->
<label for="{el_id}">Label Text:</label>
<{element.name} {attrs_str_with_id}>

<!-- Option 2: Wrap the input in a label -->
<label>
    Label Text
    <{element.name} {self._build_attrs_string(element.attrs)}>
</label>

<!-- Option 3: Use aria-label -->
<{element.name} {self._build_attrs_string(element.attrs, exclude_attrs=['aria-label'])} aria-label="Label Text">

<!-- Option 4: Use aria-labelledby -->
<span id=\"label_for_{el_id}\">Label Text</span>
<{element.name} {self._build_attrs_string(element.attrs, exclude_attrs=['aria-labelledby'])} aria-labelledby=\"label_for_{el_id}\">"""

    def _generate_aria_state_solution(self, element: Tag, state: str) -> str:
        attrs_str = self._build_attrs_string(element.attrs, exclude_attrs=[state])
        value = 'false' if state in ['aria-checked', 'aria-expanded', 'aria-pressed', 'aria-selected'] else '0' 
        if state == 'aria-valuenow': value = '50'
        
        solution = f"<{element.name} {attrs_str} {state}=\"{value}\">{element.decode_contents()}</{element.name}>"
        if state in ['aria-valuenow', 'aria-valuemin', 'aria-valuemax', 'aria-checked', 'aria-pressed', 'aria-expanded', 'aria-selected']:
            solution += "\n<!-- Ensure this ARIA attribute is updated dynamically with JavaScript as the control\'s state changes. -->"
        return solution
        
    def _generate_aria_correction_solution(self, element: Tag, attr: str, value: str) -> str:
        attrs_str = self._build_attrs_string(element.attrs, exclude_attrs=[attr])
        suggested_value = 'true'
        if value.lower() in ['0', 'no', 'off', 'disabled', 'none', 'false']:
            suggested_value = 'false'
        elif attr == 'aria-current' and value.lower() not in ['page', 'step', 'location', 'date', 'time', 'true', 'false']:
            suggested_value = 'page'
        elif attr == 'aria-checked' and value.lower() == 'mixed':
            suggested_value = 'mixed' # Keep 'mixed' if it was the invalid value that triggered this (though it's valid for aria-checked)

        return f"<{element.name} {attrs_str} {attr}=\"{suggested_value}\">{element.decode_contents()}</{element.name}>\n<!-- Verify '{attr}' has a valid token value. Common boolean states are 'true' or 'false'. 'aria-checked' can also be 'mixed'. 'aria-current' has specific tokens like 'page'. -->"
