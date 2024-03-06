import pytest
from unittest.mock import patch
import start

@patch('requests.get')
def test_get_stops(mock_get):
    mock_get.return_value.json.return_value = {
        'data': [
            {'id': '1', 'attributes': {'name': 'Stop 1'}},
            {'id': '2', 'attributes': {'name': 'Stop 2'}},
        ]
    }
    expected_stops = [
        {'id': '1', 'name': 'Stop 1'},
        {'id': '2', 'name': 'Stop 2'},
    ]
    assert start.get_stops() == expected_stops

@patch('requests.get')
def test_get_location(mock_get):
    mock_get.return_value.json.return_value = {
        'data': {'attributes': {'name': 'Location 1'}}
    }
    expected_location = 'Location 1'
    assert start.get_location('1') == expected_location