"""
Command-line interface for WCAG 2.2 Validator.
"""

import argparse
import logging
import os
import sys
import time
import re
from typing import Optional, List, Dict
from urllib.parse import urlparse

from .validator import WCAGValidator
from .performance import ParallelValidator, WebsiteCrawler, BatchProcessor


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="WCAG 2.2 Validator - Validate HTML against WCAG 2.2 criteria"
    )
    
    parser.add_argument(
        "input",
        help="HTML file path, directory path, or URL to validate",
    )
    
    parser.add_argument(
        "--level",
        choices=["A", "AA", "AAA"],
        default="AA",
        help="WCAG conformance level to validate against (default: AA)",
    )
    
    parser.add_argument(
        "--output",
        "-o",
        help="Output file for the report (default: stdout)",
    )
    
    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "html", "markdown"],
        default="text",
        help="Output format for the report (default: text)",
    )
    
    parser.add_argument(
        "--include",
        "-i",
        nargs="+",
        help="Include only specific criteria (e.g., 1.1.1 1.4.3)",
    )
    
    parser.add_argument(
        "--exclude",
        "-e",
        nargs="+",
        help="Exclude specific criteria (e.g., 1.1.1 1.4.3)",
    )
    
    parser.add_argument(
        "--selenium",
        action="store_true",
        help="Use Selenium for JavaScript-rendered content",
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output",
    )
    
    # Performance options
    parser.add_argument(
        "--parallel",
        "-p",
        action="store_true",
        help="Enable parallel processing for multiple files/pages",
    )
    
    parser.add_argument(
        "--workers",
        "-w",
        type=int,
        default=4,
        help="Number of worker threads for parallel processing (default: 4)",
    )
    
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Disable caching of validation results",
    )
    
    parser.add_argument(
        "--batch-size",
        type=int,
        default=20,
        help="Batch size for processing multiple files (default: 20)",
    )
    
    # Website crawling options
    parser.add_argument(
        "--crawl",
        action="store_true",
        help="Crawl website starting from the input URL",
    )
    
    parser.add_argument(
        "--max-pages",
        type=int,
        default=100,
        help="Maximum number of pages to crawl (default: 100)",
    )
    
    parser.add_argument(
        "--max-depth",
        type=int,
        default=3,
        help="Maximum crawl depth (default: 3)",
    )
    
    parser.add_argument(
        "--include-urls",
        nargs="+",
        help="Regex patterns for URLs to include in crawling",
    )
    
    parser.add_argument(
        "--exclude-urls",
        nargs="+",
        help="Regex patterns for URLs to exclude from crawling",
    )
    
    return parser.parse_args()


def main():
    """Main entry point for the command-line interface."""
    args = parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s - %(message)s",
    )
    
    # Initialize validator
    validator = WCAGValidator(
        conformance_level=args.level,
        criteria_to_include=args.include,
        criteria_to_exclude=args.exclude,
        log_level=log_level,
    )
    
    # Check if input is a URL
    is_url = args.input.startswith(("http://", "https://"))
    
    # Start timing
    start_time = time.time()
    
    # Run validation
    if is_url:
        if args.crawl:
            # Crawl website and validate all pages
            logger = logging.getLogger(__name__)
            logger.info(f"Crawling website starting from {args.input}")
            
            crawler = WebsiteCrawler(
                validator=validator,
                max_pages=args.max_pages,
                max_depth=args.max_depth,
                concurrency=args.workers,
                include_patterns=args.include_urls,
                exclude_patterns=args.exclude_urls,
                use_cache=not args.no_cache
            )
            
            results = crawler.crawl(args.input)
            
            # Create an aggregated reporter for all pages
            from .reporter import WCAGReporter
            reporter = WCAGReporter()
            reporter.url = args.input
            
            # Add issues and errors from all pages
            for url, page_reporter in results.items():
                for issue in page_reporter.issues:
                    # Add URL to the description
                    issue.description = f"[{url}] {issue.description}"
                    reporter.add_issue(issue)
                for criterion_id, error in page_reporter.errors.items():
                    reporter.add_error(criterion_id, f"[{url}] {error}")
                    
            logger.info(f"Finished crawling. Validated {len(results)} pages with a total of {reporter.total_issues} issues.")
        else:
            # Validate single URL
            reporter = validator.validate_url(args.input, use_selenium=args.selenium)
    else:
        if os.path.isdir(args.input):
            # Validate directory of HTML files
            logger = logging.getLogger(__name__)
            logger.info(f"Processing directory: {args.input}")
            
            if args.parallel:
                # Use batch processor for parallel validation
                processor = BatchProcessor(
                    validator=validator,
                    batch_size=args.batch_size,
                    max_workers=args.workers,
                    use_cache=not args.no_cache
                )
                
                # Process all HTML files in the directory
                results = processor.process_directory(args.input, "**/*.htm*")
                
                # Aggregate results
                reporter = processor.aggregate_results(results)
                logger.info(f"Validated {len(results)} files with {reporter.total_issues} total issues")
            else:
                # Sequential processing (original implementation)
                reporter = None
                html_files = []
                
                for root, _, files in os.walk(args.input):
                    for file in files:
                        if file.lower().endswith((".html", ".htm")):
                            html_files.append(os.path.join(root, file))
                
                if not html_files:
                    logger.error(f"No HTML files found in directory: {args.input}")
                    sys.exit(1)
                    
                # Validate first file
                reporter = validator.validate_file(html_files[0])
                
                # Validate other files and aggregate results
                for file in html_files[1:]:
                    file_reporter = validator.validate_file(file)
                    for issue in file_reporter.issues:
                        reporter.add_issue(issue)
                    for criterion_id, error in file_reporter.errors.items():
                        reporter.add_error(criterion_id, error)
        else:
            # Validate single file
            reporter = validator.validate_file(args.input)
    
    # Record execution time
    reporter.execution_time = time.time() - start_time
    
    # Generate report
    if args.format == "text":
        report = reporter.summary()
    elif args.format == "json":
        report = reporter.to_json()
    elif args.format == "html":
        report = reporter.to_html()
    elif args.format == "markdown":
        report = reporter.to_markdown()
    
    # Output report
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"Report saved to {args.output}")
    else:
        print(report)
    
    # Exit with error code if issues were found
    if reporter.has_issues:
        sys.exit(1)


if __name__ == "__main__":
    main()