"""
Performance optimization module for WCAG 2.2 Validator.

This module provides tools to optimize validation performance for large websites,
including parallel processing, caching, and batch processing.
"""

import os
import time
import concurrent.futures
import hashlib
import pickle
import logging
import queue
import threading
import requests
from typing import List, Dict, Tuple, Optional, Set, Callable, Any
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .validator import WCAGValidator
from .reporter import ValidationIssue, WCAGReporter


class ValidationCache:
    """
    Cache for validation results to avoid redundant processing.
    """
    
    def __init__(self, cache_dir: str = ".wcag_cache", ttl: int = 86400):
        """
        Initialize the validation cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl: Time to live for cache entries in seconds (default: 24 hours)
        """
        self.cache_dir = cache_dir
        self.ttl = ttl
        self.logger = logging.getLogger(__name__)
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_key(self, html_content: str, criteria_ids: List[str]) -> str:
        """
        Generate a cache key for HTML content and criteria.
        
        Args:
            html_content: HTML content to validate
            criteria_ids: List of criteria IDs to check
            
        Returns:
            Cache key as a string
        """
        # Create a hash of the HTML content and criteria
        criteria_str = ','.join(sorted(criteria_ids))
        hash_input = f"{html_content}{criteria_str}"
        
        return hashlib.md5(hash_input.encode('utf-8')).hexdigest()
    
    def get_cache_path(self, key: str) -> str:
        """
        Get the file path for a cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            File path for the cache entry
        """
        return os.path.join(self.cache_dir, f"{key}.pickle")
    
    def get(self, html_content: str, criteria_ids: List[str]) -> Optional[WCAGReporter]:
        """
        Get validation results from cache if available and not expired.
        
        Args:
            html_content: HTML content to validate
            criteria_ids: List of criteria IDs to check
            
        Returns:
            WCAGReporter object if cache hit, None if cache miss
        """
        key = self.get_cache_key(html_content, criteria_ids)
        cache_path = self.get_cache_path(key)
        
        try:
            # Check if cache file exists and is not expired
            if os.path.exists(cache_path):
                cache_time = os.path.getmtime(cache_path)
                if time.time() - cache_time <= self.ttl:
                    with open(cache_path, 'rb') as f:
                        reporter = pickle.load(f)
                        self.logger.debug(f"Cache hit for key {key}")
                        return reporter
                else:
                    # Cache expired
                    os.remove(cache_path)
                    self.logger.debug(f"Cache expired for key {key}")
        except Exception as e:
            self.logger.warning(f"Error reading cache: {e}")
        
        return None
    
    def set(self, html_content: str, criteria_ids: List[str], reporter: WCAGReporter) -> None:
        """
        Store validation results in cache.
        
        Args:
            html_content: HTML content that was validated
            criteria_ids: List of criteria IDs that were checked
            reporter: WCAGReporter object with validation results
        """
        key = self.get_cache_key(html_content, criteria_ids)
        cache_path = self.get_cache_path(key)
        
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(reporter, f)
                self.logger.debug(f"Cached results for key {key}")
        except Exception as e:
            self.logger.warning(f"Error writing to cache: {e}")
    
    def clear(self, max_age: Optional[int] = None) -> int:
        """
        Clear all cache entries or those older than max_age.
        
        Args:
            max_age: Maximum age of cache entries to keep (in seconds)
            
        Returns:
            Number of cache entries removed
        """
        removed = 0
        current_time = time.time()
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.pickle'):
                file_path = os.path.join(self.cache_dir, filename)
                
                if max_age is None or (current_time - os.path.getmtime(file_path) > max_age):
                    try:
                        os.remove(file_path)
                        removed += 1
                    except Exception as e:
                        self.logger.warning(f"Error removing cache file {file_path}: {e}")
        
        return removed


class ParallelValidator:
    """
    Validator that processes multiple HTML documents in parallel.
    """
    
    def __init__(self, 
                 max_workers: int = 4, 
                 use_cache: bool = True,
                 cache_dir: str = ".wcag_cache",
                 cache_ttl: int = 86400,
                 conformance_level: str = "AA"):
        """
        Initialize the parallel validator.
        
        Args:
            max_workers: Maximum number of worker threads
            use_cache: Whether to use caching
            cache_dir: Directory for cache files
            cache_ttl: Time to live for cache entries in seconds
            conformance_level: WCAG conformance level
        """
        self.max_workers = max_workers
        self.use_cache = use_cache
        self.logger = logging.getLogger(__name__)
        
        # Initialize the cache if enabled
        self.cache = ValidationCache(cache_dir, cache_ttl) if use_cache else None
        
        # Create a base validator instance
        self.validator = WCAGValidator(conformance_level=conformance_level)
        
        # Extract criteria IDs for cache key generation
        self.criteria_ids = [criterion.id for criterion in self.validator.criteria]
    
    def validate_pages(self, pages: List[Dict]) -> Dict[str, WCAGReporter]:
        """
        Validate multiple pages in parallel.
        
        Args:
            pages: List of page dictionaries with 'html' and 'url' keys
            
        Returns:
            Dictionary mapping URLs to WCAGReporter objects
        """
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all pages for validation
            future_to_url = {
                executor.submit(self._validate_page, page['html'], page.get('url')): page.get('url', f"page_{i}")
                for i, page in enumerate(pages)
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    reporter = future.result()
                    results[url] = reporter
                    self.logger.info(f"Completed validation for {url} - {reporter.total_issues} issues found")
                except Exception as e:
                    self.logger.error(f"Error validating {url}: {e}")
                    # Create a reporter with the error
                    reporter = WCAGReporter()
                    reporter.url = url
                    reporter.add_error("N/A", str(e))
                    results[url] = reporter
        
        return results
    
    def _validate_page(self, html_content: str, url: Optional[str] = None) -> WCAGReporter:
        """
        Validate a single page, using cache if enabled.
        
        Args:
            html_content: HTML content to validate
            url: URL of the page (for reporting)
            
        Returns:
            WCAGReporter object with validation results
        """
        # Try to get from cache first
        if self.use_cache and self.cache:
            cached_reporter = self.cache.get(html_content, self.criteria_ids)
            if cached_reporter:
                # Update the URL if it's different
                if url:
                    cached_reporter.url = url
                return cached_reporter
        
        # Perform validation
        start_time = time.time()
        reporter = self.validator.validate_html(html_content, url)
        reporter.execution_time = time.time() - start_time
        
        # Cache the result if enabled
        if self.use_cache and self.cache:
            self.cache.set(html_content, self.criteria_ids, reporter)
        
        return reporter


class WebsiteCrawler:
    """
    Crawler for validating an entire website.
    """
    
    def __init__(self, 
                 validator: WCAGValidator,
                 max_pages: int = 100,
                 max_depth: int = 3,
                 concurrency: int = 4,
                 include_patterns: Optional[List[str]] = None,
                 exclude_patterns: Optional[List[str]] = None,
                 use_cache: bool = True):
        """
        Initialize the website crawler.
        
        Args:
            validator: WCAGValidator instance
            max_pages: Maximum number of pages to crawl
            max_depth: Maximum crawl depth
            concurrency: Number of concurrent requests
            include_patterns: URL patterns to include (regex strings)
            exclude_patterns: URL patterns to exclude (regex strings)
            use_cache: Whether to use caching
        """
        self.validator = validator
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.concurrency = concurrency
        self.include_patterns = [re.compile(p) for p in include_patterns] if include_patterns else []
        self.exclude_patterns = [re.compile(p) for p in exclude_patterns] if exclude_patterns else []
        self.use_cache = use_cache
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize the parallel validator
        self.parallel_validator = ParallelValidator(
            max_workers=concurrency,
            use_cache=use_cache,
            conformance_level=validator.conformance_level
        )
        
        # Initialize crawl state
        self.visited_urls = set()
        self.queue = queue.Queue()
        self.results = {}
    
    def crawl(self, start_url: str) -> Dict[str, WCAGReporter]:
        """
        Crawl a website and validate all pages.
        
        Args:
            start_url: URL to start crawling from
            
        Returns:
            Dictionary mapping URLs to WCAGReporter objects
        """
        self.visited_urls = set()
        self.queue = queue.Queue()
        self.results = {}
        
        # Parse the start URL to get the domain
        parsed_url = urlparse(start_url)
        self.domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Add the start URL to the queue with depth 0
        self.queue.put((start_url, 0))
        
        # Create worker threads
        workers = []
        for _ in range(self.concurrency):
            t = threading.Thread(target=self._crawl_worker)
            t.daemon = True
            workers.append(t)
            t.start()
        
        # Wait for the queue to be processed
        self.queue.join()
        
        # Stop worker threads
        for _ in range(self.concurrency):
            self.queue.put((None, None))  # Signal threads to exit
        
        for t in workers:
            t.join()
        
        return self.results
    
    def _crawl_worker(self) -> None:
        """
        Worker thread for crawling pages.
        """
        while True:
            # Get a URL from the queue
            url, depth = self.queue.get()
            
            # Check for exit signal
            if url is None:
                self.queue.task_done()
                break
            
            try:
                # Skip if we've already visited this URL or reached max pages
                if url in self.visited_urls or len(self.visited_urls) >= self.max_pages:
                    self.queue.task_done()
                    continue
                
                # Mark as visited
                self.visited_urls.add(url)
                
                # Fetch and validate the page
                self.logger.info(f"Crawling {url} (depth {depth})")
                
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                html_content = response.text
                
                # Validate the page
                reporter = self.validator.validate_html(html_content, url)
                
                # Store the result
                with threading.Lock():
                    self.results[url] = reporter
                
                # If we haven't reached max depth, extract links and add to queue
                if depth < self.max_depth:
                    self._extract_links(url, html_content, depth + 1)
                
            except Exception as e:
                self.logger.error(f"Error processing {url}: {e}")
                
                # Create a reporter with the error
                reporter = WCAGReporter()
                reporter.url = url
                reporter.add_error("N/A", str(e))
                
                with threading.Lock():
                    self.results[url] = reporter
            
            finally:
                self.queue.task_done()
    
    def _extract_links(self, base_url: str, html_content: str, next_depth: int) -> None:
        """
        Extract links from a page and add them to the crawl queue.
        
        Args:
            base_url: Base URL for resolving relative links
            html_content: HTML content to extract links from
            next_depth: Depth for the extracted links
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        links = soup.find_all('a', href=True)
        
        for link in links:
            href = link['href']
            
            # Skip empty links, anchors, and non-HTTP(S) protocols
            if not href or href.startswith('#') or href.startswith('javascript:') or href.startswith('mailto:'):
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(base_url, href)
            
            # Skip URLs from other domains
            parsed_url = urlparse(absolute_url)
            if f"{parsed_url.scheme}://{parsed_url.netloc}" != self.domain:
                continue
            
            # Skip URLs that don't match include patterns
            if self.include_patterns and not any(pattern.search(absolute_url) for pattern in self.include_patterns):
                continue
            
            # Skip URLs that match exclude patterns
            if self.exclude_patterns and any(pattern.search(absolute_url) for pattern in self.exclude_patterns):
                continue
            
            # Skip URLs we've already visited or queued
            if absolute_url in self.visited_urls:
                continue
            
            # Add the URL to the queue
            self.queue.put((absolute_url, next_depth))


class BatchProcessor:
    """
    Processor for batch validation of large numbers of HTML files.
    """
    
    def __init__(self, 
                 validator: WCAGValidator,
                 batch_size: int = 20,
                 max_workers: int = 4,
                 use_cache: bool = True):
        """
        Initialize the batch processor.
        
        Args:
            validator: WCAGValidator instance
            batch_size: Size of batches for processing
            max_workers: Maximum number of worker threads
            use_cache: Whether to use caching
        """
        self.validator = validator
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.use_cache = use_cache
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize the parallel validator
        self.parallel_validator = ParallelValidator(
            max_workers=max_workers,
            use_cache=use_cache,
            conformance_level=validator.conformance_level
        )
    
    def process_directory(self, directory: str, pattern: str = "*.html") -> Dict[str, WCAGReporter]:
        """
        Process all HTML files in a directory.
        
        Args:
            directory: Directory to process
            pattern: File pattern to match
            
        Returns:
            Dictionary mapping file paths to WCAGReporter objects
        """
        # Find all HTML files
        import glob
        html_files = glob.glob(os.path.join(directory, pattern))
        
        return self.process_files(html_files)
    
    def process_files(self, file_paths: List[str]) -> Dict[str, WCAGReporter]:
        """
        Process a list of HTML files in batches.
        
        Args:
            file_paths: List of file paths to process
            
        Returns:
            Dictionary mapping file paths to WCAGReporter objects
        """
        results = {}
        total_files = len(file_paths)
        
        self.logger.info(f"Processing {total_files} files in batches of {self.batch_size}")
        
        # Process files in batches
        for i in range(0, total_files, self.batch_size):
            batch = file_paths[i:i + self.batch_size]
            self.logger.info(f"Processing batch {i // self.batch_size + 1}/{(total_files + self.batch_size - 1) // self.batch_size}")
            
            # Load HTML content for all files in the batch
            pages = []
            for file_path in batch:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        html_content = f.read()
                        pages.append({
                            'html': html_content,
                            'url': f"file://{os.path.abspath(file_path)}"
                        })
                except Exception as e:
                    self.logger.error(f"Error reading file {file_path}: {e}")
                    # Create a reporter with the error
                    reporter = WCAGReporter()
                    reporter.url = f"file://{os.path.abspath(file_path)}"
                    reporter.add_error("N/A", f"Error reading file: {e}")
                    results[file_path] = reporter
            
            # Validate the batch
            batch_results = self.parallel_validator.validate_pages(pages)
            
            # Map URLs back to file paths
            for file_path in batch:
                url = f"file://{os.path.abspath(file_path)}"
                if url in batch_results:
                    results[file_path] = batch_results[url]
        
        return results
    
    def aggregate_results(self, results: Dict[str, WCAGReporter]) -> WCAGReporter:
        """
        Aggregate results from multiple files into a single reporter.
        
        Args:
            results: Dictionary mapping file paths to WCAGReporter objects
            
        Returns:
            Aggregated WCAGReporter
        """
        aggregated = WCAGReporter()
        
        for url, reporter in results.items():
            # Add all issues from this reporter
            for issue in reporter.issues:
                # Add a note about which file this came from
                augmented_issue = ValidationIssue(
                    criterion_id=issue.criterion_id,
                    criterion_name=issue.criterion_name,
                    level=issue.level,
                    element_path=issue.element_path,
                    element_html=issue.element_html,
                    line_number=issue.line_number,
                    column_number=issue.column_number,
                    issue_type=issue.issue_type,
                    description=f"[{url}] {issue.description}",
                    impact=issue.impact,
                    how_to_fix=issue.how_to_fix,
                    code_solution=issue.code_solution,
                    ref_url=issue.ref_url
                )
                aggregated.add_issue(augmented_issue)
            
            # Add all errors from this reporter
            for criterion_id, error_message in reporter.errors.items():
                aggregated.add_error(criterion_id, f"[{url}] {error_message}")
        
        return aggregated