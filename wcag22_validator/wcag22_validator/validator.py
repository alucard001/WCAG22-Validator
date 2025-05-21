"""
Main validator module for WCAG 2.2 validation.
"""

import logging
from typing import Dict, List, Optional, Union, Set
import importlib
import os
from pathlib import Path
import re
import inspect

from bs4 import BeautifulSoup
from .reporter import WCAGReporter, ValidationIssue
from .criteria import BaseCriterion


class WCAGValidator:
    """
    Main validator class for WCAG 2.2 validation.
    
    This class provides methods to validate HTML content against WCAG 2.2 criteria.
    It loads all criteria modules and runs validation checks against the provided HTML.
    """
    
    def __init__(self, 
                 conformance_level: str = "AA", 
                 criteria_to_include: Optional[List[str]] = None,
                 criteria_to_exclude: Optional[List[str]] = None,
                 log_level: int = logging.INFO):
        """
        Initialize the WCAG validator.
        
        Args:
            conformance_level: WCAG conformance level ('A', 'AA', or 'AAA').
            criteria_to_include: List of specific criteria to include (e.g., ['1.1.1', '1.3.5']).
            criteria_to_exclude: List of specific criteria to exclude.
            log_level: Logging level.
        """
        self.conformance_level = conformance_level.upper()
        self.criteria_to_include = criteria_to_include
        self.criteria_to_exclude = criteria_to_exclude
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Initialize reporter
        self.reporter = WCAGReporter()
        
        # Load criteria
        self.criteria = self._load_criteria()
        
    def _load_criteria(self) -> List[BaseCriterion]:
        """
        Load all criteria modules based on the specified conformance level.
        
        Returns:
            List of initialized criteria objects.
        """
        criteria = []
        
        # Get the directory where criteria modules are located
        criteria_dir = Path(__file__).parent / "criteria"
        
        # Define which levels to include based on conformance level
        levels_to_include = []
        if self.conformance_level == "A":
            levels_to_include = ["A"]
        elif self.conformance_level == "AA":
            levels_to_include = ["A", "AA"]
        elif self.conformance_level == "AAA":
            levels_to_include = ["A", "AA", "AAA"]
        else:
            self.logger.warning(f"Invalid conformance level: {self.conformance_level}. Defaulting to AA.")
            levels_to_include = ["A", "AA"]
        
        # Walk through criteria modules and import them
        module_pattern = re.compile(r'criterion_(\d+)_(\d+)_(\d+)\.py$')
        
        for module_file in criteria_dir.glob("*.py"):
            if module_file.name == "__init__.py" or module_file.name == "base.py":
                continue
                
            # Extract criterion identifier (e.g., 1.1.1) from filename
            match = module_pattern.match(module_file.name)
            if not match:
                continue
                
            criterion_id = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
            
            # Check if we should include this criterion
            if self.criteria_to_include and criterion_id not in self.criteria_to_include:
                continue
                
            if self.criteria_to_exclude and criterion_id in self.criteria_to_exclude:
                continue
            
            # Import the module
            module_name = f".criteria.{module_file.stem}"
            try:
                module = importlib.import_module(module_name, package="wcag22_validator")
                
                # Find and instantiate criterion classes
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and issubclass(obj, BaseCriterion) and
                            obj.__name__ != 'BaseCriterion'):
                        
                        criterion = obj()
                        
                        # Check if this criterion's level is included in our target conformance level
                        if criterion.level in levels_to_include:
                            criteria.append(criterion)
                            self.logger.debug(f"Loaded criterion: {criterion.id} ({criterion.level})")
                        
            except (ImportError, AttributeError) as e:
                self.logger.error(f"Error loading criterion module {module_name}: {e}")
        
        self.logger.info(f"Loaded {len(criteria)} criteria for conformance level {self.conformance_level}")
        return criteria
    
    def validate_html(self, html_content: str, page_url: Optional[str] = None) -> WCAGReporter:
        """
        Validate HTML content against WCAG 2.2 criteria.
        
        Args:
            html_content: HTML content to validate.
            page_url: URL of the page being validated (optional, for reporting).
            
        Returns:
            Reporter object containing validation results.
        """
        self.reporter.clear()
        self.reporter.url = page_url
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Run each criterion's validation
        for criterion in self.criteria:
            try:
                self.logger.debug(f"Validating criterion {criterion.id}: {criterion.name}")
                issues = criterion.validate(soup, html_content)
                
                for issue in issues:
                    self.reporter.add_issue(issue)
                    
            except Exception as e:
                self.logger.error(f"Error validating criterion {criterion.id}: {e}")
                self.reporter.add_error(criterion.id, str(e))
        
        return self.reporter
    
    def validate_file(self, file_path: str) -> WCAGReporter:
        """
        Validate HTML from a file.
        
        Args:
            file_path: Path to HTML file.
            
        Returns:
            Reporter object containing validation results.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        return self.validate_html(html_content, page_url=f"file://{os.path.abspath(file_path)}")
    
    def validate_url(self, url: str, use_selenium: bool = False) -> WCAGReporter:
        """
        Validate HTML from a URL.
        
        Args:
            url: URL to validate.
            use_selenium: Whether to use Selenium for rendering (for JavaScript-rendered content).
            
        Returns:
            Reporter object containing validation results.
        """
        import requests
        
        if use_selenium:
            try:
                from selenium import webdriver
                from selenium.webdriver.chrome.options import Options
                
                options = Options()
                options.add_argument('--headless')
                options.add_argument('--disable-gpu')
                
                driver = webdriver.Chrome(options=options)
                driver.get(url)
                
                # Wait for page to load
                import time
                time.sleep(2)
                
                html_content = driver.page_source
                driver.quit()
                
            except ImportError:
                self.logger.error("Selenium not installed. Please install selenium to use this feature.")
                return self.reporter
                
        else:
            response = requests.get(url)
            response.raise_for_status()
            html_content = response.text
            
        return self.validate_html(html_content, page_url=url)