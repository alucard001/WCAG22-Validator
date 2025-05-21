# WCAG 2.2 Analysis for HTML Validation Library

## 1. Main Principles, Guidelines, and Success Criteria

WCAG 2.2 is organized hierarchically around four fundamental principles:

### 1.1 Principles

1. **Perceivable** - Information and user interface components must be presentable to users in ways they can perceive
2. **Operable** - User interface components and navigation must be operable
3. **Understandable** - Information and the operation of the user interface must be understandable
4. **Robust** - Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies

### 1.2 Guidelines

Each principle contains multiple guidelines (13 in total):

- **Principle 1: Perceivable**
  - 1.1 Text Alternatives
  - 1.2 Time-based Media
  - 1.3 Adaptable
  - 1.4 Distinguishable

- **Principle 2: Operable**
  - 2.1 Keyboard Accessible
  - 2.2 Enough Time
  - 2.3 Seizures and Physical Reactions
  - 2.4 Navigable
  - 2.5 Input Modalities

- **Principle 3: Understandable**
  - 3.1 Readable
  - 3.2 Predictable
  - 3.3 Input Assistance

- **Principle 4: Robust**
  - 4.1 Compatible

### 1.3 Success Criteria

Each guideline contains testable success criteria. WCAG 2.2 contains a total of 78 success criteria.

## 2. Success Criteria Organization by Level

Success criteria are organized into three levels of conformance:

### 2.1 Level A (Minimum Level)
- Contains approximately 30 success criteria
- Represents the bare minimum required for basic accessibility
- Addresses critical barriers that would completely block certain user groups
- Examples include:
  - 1.1.1 Non-text Content (providing text alternatives for images)
  - 2.1.1 Keyboard (all functionality available from keyboard)
  - 3.1.1 Language of Page (identifying the default language)

### 2.2 Level AA (Standard Level)
- Contains approximately 20 success criteria
- Represents the industry standard level adopted by most organizations
- Addresses significant barriers for users with disabilities
- Examples include:
  - 1.4.3 Contrast (Minimum) (4.5:1 for normal text, 3:1 for large text)
  - 2.4.7 Focus Visible (visible keyboard focus indicator)
  - 3.2.3 Consistent Navigation (consistent navigation across pages)

### 2.3 Level AAA (Enhanced Level)
- Contains approximately 28 success criteria
- Represents the highest level of accessibility
- Addresses nuanced or specialized accessibility needs
- Examples include:
  - 1.4.6 Contrast (Enhanced) (7:1 for normal text, 4.5:1 for large text)
  - 2.2.3 No Timing (no time limits on user interactions)
  - 3.1.5 Reading Level (content written at lower secondary education level)

## 3. Examples of Success Criteria and Technical Requirements

### 3.1 1.1.1 Non-text Content (Level A)
- **Requirement**: All non-text content has text alternatives that serve the equivalent purpose
- **Technical Implementation**:
  - Images: Use `alt` attributes on `<img>` elements
  - SVG: Include descriptive text using `<title>` and `<desc>` elements
  - ARIA: Use `aria-label` or `aria-labelledby` for custom controls
  - Decorative images: Use `alt=""` or `role="presentation"`
- **Testing Methodologies**:
  - Check all images have non-empty alt text unless decorative
  - Verify form controls have accessible names
  - Ensure complex images have extended descriptions when needed

### 3.2 1.4.3 Contrast (Minimum) (Level AA)
- **Requirement**: 
  - Normal text: Contrast ratio of at least 4.5:1
  - Large text (18pt or 14pt bold): Contrast ratio of at least 3:1
  - UI components and graphical objects: Contrast ratio of at least 3:1
- **Technical Implementation**:
  - Use sufficient color contrast between text and background
  - Implement adequate contrast for UI component boundaries
  - Ensure visual indicators for states have sufficient contrast
- **Testing Methodologies**:
  - Calculate contrast ratios using color contrast analyzers
  - Test all text elements against their actual backgrounds
  - Check state indicators like focus and hover

### 3.3 2.4.7 Focus Visible (Level AA)
- **Requirement**: Keyboard focus indicator is visible on all interactive elements
- **Technical Implementation**:
  - Use browser default focus indicators
  - Implement custom focus styles with sufficient visibility
  - Avoid removing focus outlines without replacement
- **Testing Methodologies**:
  - Navigate through all interactive elements using keyboard
  - Verify visible focus indicator on all interactive elements
  - Check custom focus indicators have sufficient contrast

### 3.4 3.3.7 Redundant Entry (Level A, new in 2.2)
- **Requirement**: Information previously entered by the user that is required again must be either auto-populated or available for selection
- **Technical Implementation**:
  - Auto-fill form fields with previously entered information
  - Provide selection options for previously entered data
  - Implement browser autocomplete attributes appropriately
- **Testing Methodologies**:
  - Test multi-step processes requiring the same information
  - Verify that information isn't requested multiple times
  - Check that selection options are provided when appropriate

## 4. New Success Criteria in WCAG 2.2

WCAG 2.2 introduces 9 new success criteria that weren't in WCAG 2.1:

### 4.1 Focus-related criteria
- **2.4.11 Focus Not Obscured (Minimum)** (Level AA): Requires that when a component receives keyboard focus, it is not entirely hidden by author-created content
- **2.4.12 Focus Not Obscured (Enhanced)** (Level AAA): More stringent version requiring that no part of the focused component is hidden
- **2.4.13 Focus Appearance** (Level AAA): Specifies requirements for the visual characteristics of the keyboard focus indicator

### 4.2 Input modality criteria
- **2.5.7 Dragging Movements** (Level AA): All functionality using dragging movements must be achievable without dragging using a single pointer
- **2.5.8 Target Size (Minimum)** (Level AA): Pointer input targets must be at least 24x24 CSS pixels with specific exceptions

### 4.3 Usability and form criteria
- **3.2.6 Consistent Help** (Level A): Help mechanisms must appear in the same relative order when included on multiple pages
- **3.3.7 Redundant Entry** (Level A): Previously entered information must be either auto-populated or available for selection
- **3.3.8 Accessible Authentication (Minimum)** (Level AA): Prohibits cognitive function tests in authentication unless alternatives are provided
- **3.3.9 Accessible Authentication (Enhanced)** (Level AAA): More stringent version completely prohibiting cognitive function tests

## 5. Detailed Analysis of Representative Success Criteria

### 5.1 Principle 1 (Perceivable) - 1.3.5 Identify Input Purpose (AA)

#### Technical Requirement
The purpose of input fields collecting user information must be programmatically determinable, typically by using `autocomplete` attributes.

#### Testing Implementation
```python
def check_input_purpose(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    inputs = soup.find_all(['input', 'select', 'textarea'])
    user_info_fields = ['name', 'email', 'tel', 'address', 'cc-number']
    issues = []
    
    for input_field in inputs:
        field_type = input_field.get('type', '')
        field_name = input_field.get('name', '').lower()
        field_id = input_field.get('id', '').lower()
        
        # Check if field is likely collecting user information
        if any(info in field_name or info in field_id for info in user_info_fields):
            if not input_field.has_attr('autocomplete'):
                issues.append(f"Input field likely collecting user information missing autocomplete attribute: {input_field}")
    
    return issues
```

#### Common Failures
- Missing autocomplete attributes on user information fields
- Using incorrect values for autocomplete attributes
- Not identifying common input fields (name, address, etc.)

### 5.2 Principle 2 (Operable) - 2.4.11 Focus Not Obscured (Minimum) (AA, new in 2.2)

#### Technical Requirement
When a component receives keyboard focus, it must not be entirely hidden by author-created content such as sticky headers, footers, or modals.

#### Testing Implementation
```python
def check_focus_not_obscured(driver, url):
    driver.get(url)
    focusable_elements = driver.find_elements(By.CSS_SELECTOR, 
                                             'a, button, input, select, textarea, [tabindex]')
    issues = []
    
    for element in focusable_elements:
        # Skip elements not in the viewport
        if not is_in_viewport(driver, element):
            continue
            
        # Focus the element
        element.send_keys(Keys.NULL)
        
        # Check if the element is completely obscured
        is_visible = driver.execute_script('''
            const elem = arguments[0];
            const rect = elem.getBoundingClientRect();
            
            // Check if the element is completely obscured by fixed position elements
            const obscuringElements = document.elementsFromPoint(
                rect.left + rect.width/2, 
                rect.top + rect.height/2
            );
            
            // If the first element isn't our target element, check if it's fixed/sticky
            if (obscuringElements[0] !== elem) {
                const style = window.getComputedStyle(obscuringElements[0]);
                if (style.position === 'fixed' || style.position === 'sticky') {
                    return false;
                }
            }
            
            return true;
        ''', element)
        
        if not is_visible:
            issues.append(f"Element obscured when focused: {element.tag_name} - {element.text}")
    
    return issues
```

#### Common Failures
- Sticky headers completely covering focused elements
- Modals or tooltips obscuring the focused component
- Content scrolling under fixed elements

### 5.3 Principle 3 (Understandable) - 3.3.7 Redundant Entry (A, new in 2.2)

#### Technical Requirement
Information previously entered by the user that is required again must be either auto-populated or available for selection.

#### Testing Implementation
```python
def check_redundant_entry(driver, url):
    driver.get(url)
    issues = []
    
    # Find multi-page forms
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    for form in forms:
        # Check for next page/continue buttons
        next_buttons = form.find_elements(By.XPATH, 
                                          ".//button[contains(text(), 'Next') or contains(text(), 'Continue')]")
        
        if not next_buttons:
            continue
            
        # Track all input fields on first page
        first_page_inputs = {}
        inputs = form.find_elements(By.TAG_NAME, 'input')
        
        for input_field in inputs:
            field_name = input_field.get_attribute('name')
            field_id = input_field.get_attribute('id')
            field_label = get_field_label(driver, input_field)
            
            if field_name or field_id:
                first_page_inputs[field_name or field_id] = {
                    'element': input_field,
                    'label': field_label
                }
        
        # Go to next page
        next_buttons[0].click()
        WebDriverWait(driver, 10).until(EC.staleness_of(next_buttons[0]))
        
        # Check for redundant fields on second page
        second_page_inputs = form.find_elements(By.TAG_NAME, 'input')
        
        for input_field in second_page_inputs:
            field_name = input_field.get_attribute('name')
            field_id = input_field.get_attribute('id')
            field_label = get_field_label(driver, input_field)
            
            # Check if this field exists on first page
            if field_name in first_page_inputs or field_id in first_page_inputs:
                # Check if field is auto-populated
                value = input_field.get_attribute('value')
                has_autocomplete = input_field.get_attribute('autocomplete') != 'off'
                
                if not value and not has_autocomplete:
                    issues.append(f"Redundant entry required for field: {field_label or field_name or field_id}")
    
    return issues
```

#### Common Failures
- Forcing users to re-enter information in multi-step processes
- Not remembering previously entered data
- Failing to provide selection from previously entered information

### 5.4 Principle 4 (Robust) - 4.1.3 Status Messages (AA)

#### Technical Requirement
Status messages must be programmatically determinable through role or properties so they can be presented to users without receiving focus.

#### Testing Implementation
```python
def check_status_messages(driver, url):
    driver.get(url)
    issues = []
    
    # Find forms to trigger status messages
    forms = driver.find_elements(By.TAG_NAME, 'form')
    
    for form in forms:
        # Submit the form to potentially trigger status messages
        submit_buttons = form.find_elements(By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]')
        
        if not submit_buttons:
            continue
            
        # Record DOM state before submission
        dom_before = driver.execute_script('return document.documentElement.outerHTML')
        
        # Submit the form
        submit_buttons[0].click()
        
        # Wait for potential status messages
        time.sleep(2)
        
        # Find all new elements that appeared after submission
        new_elements = driver.execute_script('''
            const domBefore = arguments[0];
            const parser = new DOMParser();
            const docBefore = parser.parseFromString(domBefore, 'text/html');
            
            // Get all current elements that might be status messages
            const currentElements = Array.from(document.querySelectorAll('.status, .message, .alert, .notification'));
            
            // Filter to only elements that weren't present before
            return currentElements.filter(el => {
                // Check if this element or similar existed before
                const selector = el.tagName + (el.id ? '#' + el.id : '') + 
                                (el.className ? '.' + el.className.split(' ').join('.') : '');
                return !docBefore.querySelector(selector);
            }).map(el => ({
                outerHTML: el.outerHTML,
                role: el.getAttribute('role'),
                ariaLive: el.getAttribute('aria-live')
            }));
        ''', dom_before)
        
        for element in new_elements:
            # Check if the element has appropriate ARIA roles/attributes
            has_proper_role = element['role'] in ['status', 'alert', 'log', 'progressbar']
            has_aria_live = element['ariaLive'] in ['polite', 'assertive']
            
            if not has_proper_role and not has_aria_live:
                issues.append(f"Status message without proper ARIA role or live region: {element['outerHTML']}")
    
    return issues
```

#### Common Failures
- Creating status messages that are only visually apparent
- Using visual-only indicators for errors or submissions
- Implementing dynamic content updates without appropriate live region attributes

## 6. Implementation Considerations for Python Library

### 6.1 Core Components for WCAG 2.2 Validation

1. **HTML Parser Module**
   - Use BeautifulSoup or lxml for static HTML analysis
   - Implement Selenium/Playwright for dynamic content testing

2. **Success Criteria Test Modules**
   - Organize tests by WCAG principle and guideline
   - Implement severity levels (A, AA, AAA)
   - Create test functions for each success criterion

3. **Reporting System**
   - Generate detailed reports of issues found
   - Include references to WCAG success criteria
   - Provide remediation suggestions

4. **Configuration System**
   - Allow enabling/disabling specific tests
   - Configure conformance level target (A, AA, AAA)
   - Set custom thresholds for certain tests

### 6.2 Key Testing Methodologies

1. **Static Analysis**
   - HTML structure validation (headings, landmarks)
   - Alternative text for images
   - Form field labels and associations
   - Proper use of semantic HTML

2. **Color and Contrast Analysis**
   - Text contrast ratios
   - UI component contrast
   - Focus indicator visibility

3. **Dynamic Testing**
   - Keyboard navigation and focus management
   - ARIA attributes and dynamic updates
   - Status message announcements
   - Timeout and timing function behavior

4. **User Input Testing**
   - Form validation and error handling
   - Autocomplete functionality
   - Redundant entry prevention
   - Accessible authentication methods

### 6.3 Implementation Priorities

For a Python library implementing WCAG 2.2 validation, focus first on:

1. **Level A Criteria** - Fundamental accessibility requirements
2. **New WCAG 2.2 Criteria** - To provide value over existing tools
3. **Programmatically Testable Criteria** - Those that can be reliably automated
4. **Most Common Issues** - Focus on high-impact problems like:
   - Missing alternative text
   - Keyboard accessibility
   - Color contrast
   - Form labeling
   - Focus management

## 7. Conclusion

WCAG 2.2 builds upon previous versions with important additions particularly focused on:
- Keyboard accessibility improvements
- Target size requirements
- Reducing cognitive load
- Making authentication more accessible

A Python library for WCAG 2.2 validation should implement a comprehensive set of tests covering all four principles while prioritizing Level A and AA success criteria, with particular attention to the new criteria introduced in version 2.2.