"""
Example script to demonstrate the WCAG 2.2 Validator.
"""

import os
import sys
import time

# Add the parent directory to the path for importing the library
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from wcag22_validator import WCAGValidator


def main():
    """Run a test validation on the example HTML file."""
    
    # Path to the test HTML file
    html_file_path = os.path.join(os.path.dirname(__file__), 'test_page.html')
    
    print(f"Validating file: {html_file_path}")
    print("=" * 80)
    
    # Initialize the validator
    validator = WCAGValidator(conformance_level="AA")
    
    # Start timing
    start_time = time.time()
    
    # Run validation
    reporter = validator.validate_file(html_file_path)
    
    # Record execution time
    reporter.execution_time = time.time() - start_time
    
    # Print summary
    print(reporter.summary())
    print("\n" + "=" * 80 + "\n")
    
    # Print detailed report
    print("DETAILED MARKDOWN REPORT:")
    print(reporter.to_markdown())
    
    # Generate HTML report
    html_report_path = os.path.join(os.path.dirname(__file__), 'report.html')
    with open(html_report_path, 'w', encoding='utf-8') as f:
        f.write(reporter.to_html())
    
    print(f"\nHTML report saved to: {html_report_path}")


if __name__ == "__main__":
    main()