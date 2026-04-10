"""
Unit tests for data_reader module.
"""

import pytest
import json
import csv
import tempfile
import os
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.data_reader import DataReader


class TestDataReader:
    """Test cases for DataReader class."""
    
    def test_read_txt_file(self):
        """Test reading TXT file in JSONL format."""
        # Create temporary TXT file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('{"id": "MLC-1", "titulo": "Prop 1"}\n')
            f.write('{"id": "MLC-2", "titulo": "Prop 2"}\n')
            temp_path = f.name
        
        try:
            properties = DataReader.read_txt(temp_path)
            
            assert len(properties) == 2
            assert properties[0]['id'] == 'MLC-1'
            assert properties[1]['id'] == 'MLC-2'
        finally:
            os.unlink(temp_path)
    
    def test_read_json_structured(self):
        """Test reading JSON file with structured format."""
        data = {
            "metadata": {"operacion": "venta", "tipo": "departamento"},
            "propiedades": [
                {"id": "MLC-1", "titulo": "Prop 1"},
                {"id": "MLC-2", "titulo": "Prop 2"}
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            properties = DataReader.read_json(temp_path)
            
            assert len(properties) == 2
            assert properties[0]['id'] == 'MLC-1'
            assert properties[1]['id'] == 'MLC-2'
        finally:
            os.unlink(temp_path)
    
    def test_read_json_array(self):
        """Test reading JSON file as plain array."""
        data = [
            {"id": "MLC-1", "titulo": "Prop 1"},
            {"id": "MLC-2", "titulo": "Prop 2"}
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            properties = DataReader.read_json(temp_path)
            
            assert len(properties) == 2
            assert properties[0]['id'] == 'MLC-1'
        finally:
            os.unlink(temp_path)
    
    def test_read_csv(self):
        """Test reading CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            writer = csv.DictWriter(f, fieldnames=['id', 'titulo', 'precio'])
            writer.writeheader()
            writer.writerow({'id': 'MLC-1', 'titulo': 'Prop 1', 'precio': 'UF 3.000'})
            writer.writerow({'id': 'MLC-2', 'titulo': 'Prop 2', 'precio': 'UF 4.000'})
            temp_path = f.name
        
        try:
            properties = DataReader.read_csv(temp_path)
            
            assert len(properties) == 2
            assert properties[0]['id'] == 'MLC-1'
            assert properties[1]['titulo'] == 'Prop 2'
        finally:
            os.unlink(temp_path)
    
    def test_read_file_auto_detect_txt(self):
        """Test auto-detection of TXT format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('{"id": "MLC-1", "titulo": "Prop 1"}\n')
            temp_path = f.name
        
        try:
            properties = DataReader.read_file(temp_path)
            assert len(properties) == 1
        finally:
            os.unlink(temp_path)
    
    def test_read_file_auto_detect_json(self):
        """Test auto-detection of JSON format."""
        data = {"propiedades": [{"id": "MLC-1", "titulo": "Prop 1"}]}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            properties = DataReader.read_file(temp_path)
            assert len(properties) == 1
        finally:
            os.unlink(temp_path)
    
    def test_read_file_not_found(self):
        """Test error handling when file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            DataReader.read_file('/nonexistent/file.txt')
    
    def test_read_file_invalid_format(self):
        """Test error handling for unsupported format."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.xyz') as f:
            f.write('some content')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported file format"):
                DataReader.read_file(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_read_json_invalid_format(self):
        """Test error handling for invalid JSON structure."""
        data = {"invalid_key": "value"}
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            json.dump(data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON format"):
                DataReader.read_json(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_read_txt_invalid_json(self):
        """Test error handling for invalid JSON in TXT file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('invalid json\n')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                DataReader.read_txt(temp_path)
        finally:
            os.unlink(temp_path)
    
    def test_read_directory(self):
        """Test reading all files from directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create TXT file
            txt_path = os.path.join(temp_dir, 'data.txt')
            with open(txt_path, 'w') as f:
                f.write('{"id": "MLC-1", "titulo": "Prop 1"}\n')
            
            # Create JSON file
            json_path = os.path.join(temp_dir, 'data.json')
            with open(json_path, 'w') as f:
                json.dump({"propiedades": [{"id": "MLC-2", "titulo": "Prop 2"}]}, f)
            
            results = DataReader.read_directory(temp_dir)
            
            assert len(results) == 2
            assert 'data.txt' in results
            assert 'data.json' in results
            assert len(results['data.txt']) == 1
            assert len(results['data.json']) == 1
    
    def test_read_directory_not_found(self):
        """Test error handling when directory doesn't exist."""
        with pytest.raises(FileNotFoundError):
            DataReader.read_directory('/nonexistent/directory')
    
    def test_read_directory_not_directory(self):
        """Test error handling when path is not a directory."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write('content')
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Not a directory"):
                DataReader.read_directory(temp_path)
        finally:
            os.unlink(temp_path)
