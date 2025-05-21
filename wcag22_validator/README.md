# WCAG 2.2 Validator

A Python library for validating HTML against Web Content Accessibility Guidelines (WCAG) 2.2 criteria. This tool helps developers identify accessibility issues and provides detailed reports with explanations of:

1. What's wrong
2. How to fix it
3. Code suggestions for remediation

## Features

- Validate HTML content, files, or URLs against WCAG 2.2 criteria
- Filter validation by conformance level (A, AA, AAA)
- Include or exclude specific criteria from validation
- Generate detailed reports in multiple formats (text, JSON, HTML, Markdown)
- Provide specific code examples for fixing identified issues
- Command-line interface for easy integration into workflows
- Optional Selenium integration for testing JavaScript-rendered content
- Performance optimizations for large websites:
    - Parallel processing for multiple files/pages
    - Caching of validation results
    - Website crawling capabilities
    - Batch processing for large numbers of files
- Improved HTML report visualization with tabs and code highlighting

## Installation

```bash
pip install wcag22-validator
```

For optional Selenium support:

```bash
pip install wcag22-validator[selenium]
```

## Command-Line Usage

```bash
# Validate a local HTML file
wcag22-validator path/to/file.html

# Validate a URL
wcag22-validator https://example.com

# Validate against a specific WCAG level
wcag22-validator https://example.com --level AA

# Output as HTML report
wcag22-validator https://example.com --format html --output report.html

# Include only specific criteria
wcag22-validator https://example.com --include 1.1.1 1.4.3

# Exclude specific criteria
wcag22-validator https://example.com --exclude 2.4.1

# Use Selenium for JavaScript-rendered content
wcag22-validator https://example.com --selenium

# Crawl a website and validate all pages
wcag22-validator https://example.com --crawl --max-pages 50

# Validate a directory of HTML files in parallel
wcag22-validator path/to/directory --parallel --workers 8
```

## Programmatic Usage

```python
from wcag22_validator import WCAGValidator
from wcag22_validator.performance import WebsiteCrawler, BatchProcessor

# Initialize validator
validator = WCAGValidator(conformance_level="AA")

# Validate HTML string
html_content = "<html><img src='image.jpg'></html>"
reporter = validator.validate_html(html_content)

# Validate URL
reporter = validator.validate_url("https://example.com")

# Validate file
reporter = validator.validate_file("path/to/file.html")

# Check results
if reporter.has_issues:
    print(f"Found {reporter.total_issues} issues")
    
    # Get issues by impact level
    critical_issues = reporter.get_issues_by_impact().get("critical", [])
    for issue in critical_issues:
        print(f"Critical issue: {issue.description}")
        print(f"How to fix: {issue.how_to_fix}")
        print(f"Code solution: {issue.code_solution}")
        
# Generate reports
html_report = reporter.to_html()
json_report = reporter.to_json()
markdown_report = reporter.to_markdown()
summary = reporter.summary()

# Crawl a website
crawler = WebsiteCrawler(validator, max_pages=50)
results = crawler.crawl("https://example.com")

# Process a directory of files
processor = BatchProcessor(validator)
results = processor.process_directory("path/to/html_files")
aggregated_report = processor.aggregate_results(results)
```

## Supported WCAG 2.2 Criteria

The library currently supports validation for the following WCAG 2.2 criteria:

- 1.1.1 Non-text Content (Level A)
- 1.4.3 Contrast (Minimum) (Level AA)
- 2.4.7 Focus Visible (Level AA)
- 2.4.11 Focus Not Obscured (Minimum) (Level AA) - New in WCAG 2.2
- 2.5.8 Target Size (Minimum) (Level AA) - New in WCAG 2.2
- 3.3.7 Redundant Entry (Level A) - New in WCAG 2.2
- 4.1.2 Name, Role, Value (Level A)

Additional criteria are being implemented in future releases.

## Limitations

- Some WCAG criteria require human evaluation and cannot be fully automated
- Static analysis has limitations compared to dynamic testing with real browsers
- JavaScript-heavy applications may require using the Selenium integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.