import unittest
from unittest.mock import patch, Mock
from ghub_integration import fetch_pr_changes

class TestFetchPRChanges(unittest.TestCase):
    @patch('ghub_integration.requests.get')
    def test_fetch_pr_changes_success(self, mock_get):
        # Mock PR metadata response
        pr_metadata = {
            'title': 'Test PR',
            'body': 'This is a test PR',
            'user': {'login': 'testuser'},
            'created_at': '2024-01-01T00:00:00Z',
            'updated_at': '2024-01-02T00:00:00Z',
            'state': 'open'
        }
        pr_files = [
            {
                'filename': 'file1.py',
                'status': 'modified',
                'additions': 10,
                'deletions': 2,
                'changes': 12,
                'patch': 'patch content',
                'raw_url': 'http://example.com/raw',
                'contents_url': 'http://example.com/contents'
            }
        ]
        # Setup side effects for requests.get
        mock_get.side_effect = [
            Mock(status_code=200, json=Mock(return_value=pr_metadata), raise_for_status=Mock()),
            Mock(status_code=200, json=Mock(return_value=pr_files), raise_for_status=Mock())
        ]
        result = fetch_pr_changes('owner', 'repo', 1)
        self.assertIsInstance(result, dict)
        self.assertEqual(result['title'], 'Test PR')
        self.assertEqual(result['author'], 'testuser')
        self.assertEqual(result['total_changes'], 1)
        self.assertEqual(result['changes'][0]['filename'], 'file1.py')

    @patch('ghub_integration.requests.get')
    def test_fetch_pr_changes_failure(self, mock_get):
        # Simulate an exception in requests.get
        mock_get.side_effect = Exception('API error')
        result = fetch_pr_changes('owner', 'repo', 1)
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main() 