"""
Data reader module for reading exported files from scraper.

Supports reading from TXT (JSONL), JSON, and CSV formats.
"""

import json
import csv
from typing import List, Dict, Optional
from pathlib import Path


class DataReader:
    """
    Reader for exported property data files.
    
    Supports three formats:
    - TXT: JSONL format (one JSON object per line)
    - JSON: Structured JSON with metadata and properties array
    - CSV: Tabular format with headers
    """
    
    @staticmethod
    def read_txt(file_path: str) -> List[Dict]:
        """
        Read TXT file in JSONL format.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            List of property dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        properties = []
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        prop = json.loads(line)
                        properties.append(prop)
                    except json.JSONDecodeError as e:
                        raise ValueError(
                            f"Invalid JSON on line {line_num} in {file_path}: {e}"
                        )
        except UnicodeDecodeError:
            raise ValueError(f"Encoding error in {file_path}. Expected UTF-8.")
        
        return properties
    
    @staticmethod
    def read_json(file_path: str) -> List[Dict]:
        """
        Read JSON file with structured format.
        
        Expected format:
        {
            "metadata": {...},
            "propiedades": [...]
        }
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            List of property dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except UnicodeDecodeError:
            raise ValueError(f"Encoding error in {file_path}. Expected UTF-8.")
        
        # Check if it's the structured format with "propiedades" key
        if 'propiedades' in data:
            return data['propiedades']
        
        # If it's a plain array, return it
        if isinstance(data, list):
            return data
        
        raise ValueError(
            f"Invalid JSON format in {file_path}. "
            "Expected 'propiedades' key or array."
        )
    
    @staticmethod
    def read_csv(file_path: str) -> List[Dict]:
        """
        Read CSV file with headers.
        
        Args:
            file_path: Path to CSV file
            
        Returns:
            List of property dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        properties = []
        
        try:
            with open(path, 'r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert empty strings to None
                    cleaned_row = {
                        k: (v if v != '' else None) 
                        for k, v in row.items()
                    }
                    properties.append(cleaned_row)
        except UnicodeDecodeError:
            raise ValueError(f"Encoding error in {file_path}. Expected UTF-8.")
        except csv.Error as e:
            raise ValueError(f"CSV error in {file_path}: {e}")
        
        return properties
    
    @staticmethod
    def read_file(file_path: str) -> List[Dict]:
        """
        Auto-detect format and read file.
        
        Args:
            file_path: Path to file
            
        Returns:
            List of property dictionaries
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix == '.txt':
            return DataReader.read_txt(file_path)
        elif suffix == '.json':
            return DataReader.read_json(file_path)
        elif suffix == '.csv':
            return DataReader.read_csv(file_path)
        else:
            raise ValueError(
                f"Unsupported file format: {suffix}. "
                "Supported formats: .txt, .json, .csv"
            )
    
    @staticmethod
    def read_directory(directory_path: str) -> Dict[str, List[Dict]]:
        """
        Read all supported files from a directory.
        
        Args:
            directory_path: Path to directory
            
        Returns:
            Dictionary mapping filenames to property lists
        """
        dir_path = Path(directory_path)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {directory_path}")
        
        results = {}
        supported_extensions = {'.txt', '.json', '.csv'}
        
        for file_path in dir_path.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    properties = DataReader.read_file(str(file_path))
                    results[file_path.name] = properties
                except (ValueError, json.JSONDecodeError, csv.Error) as e:
                    print(f"Warning: Skipping {file_path.name}: {e}")
        
        return results
