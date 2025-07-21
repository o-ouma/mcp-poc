import unittest
from unittest.mock import patch, MagicMock
from pr_analyzer import GithubOps

class TestGithubOps(unittest.TestCase):
    @patch('pr_analyzer.FastMCP')
    @patch('pr_analyzer.Client')
    @patch('pr_analyzer.Confluence')
    @patch('pr_analyzer.load_dotenv')
    def test_init(self, mock_dotenv, mock_confluence, mock_client, mock_fastmcp):
        # Mock environment variables
        with patch('os.getenv') as mock_getenv:
            mock_getenv.side_effect = lambda k: {
                'NOTION_API_KEY': 'fake_notion_key',
                'NOTION_PAGE_ID': 'fake_page_id',
                'CONFLUENCE_URL': 'http://confluence',
                'CONFLUENCE_USERNAME': 'user',
                'CONFLUENCE_API_TOKEN': 'token',
                'CONFLUENCE_SPACE_KEY': 'space',
                'GITHUB_TOKEN': 'gh_token',
            }.get(k)
            # Should not raise
            ops = GithubOps()
            self.assertIsNotNone(ops.mcp)
            self.assertIsNotNone(ops.notion)
            self.assertIsNotNone(ops.confluence)
            self.assertEqual(ops.github_token, 'gh_token')

    @patch('pr_analyzer.FastMCP')
    @patch('pr_analyzer.Client')
    @patch('pr_analyzer.Confluence')
    @patch('pr_analyzer.load_dotenv')
    def test_missing_env_vars(self, mock_dotenv, mock_confluence, mock_client, mock_fastmcp):
        # Missing NOTION_API_KEY should cause sys.exit
        with patch('os.getenv', return_value=None), self.assertRaises(SystemExit):
            GithubOps()

if __name__ == '__main__':
    unittest.main() 