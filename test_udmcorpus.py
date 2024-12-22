import unittest
from udmurtwrapper import UdmcorpusWrapper, WordNotFoundError, TextsNotFoundError

class TestUdmcorpusWrapper(unittest.TestCase):
    def setUp(self):
        self.wrapper = UdmcorpusWrapper()

    def test_search_word_basic(self):
        """Test basic word search functionality"""
        result = self.wrapper.search_word('укно')
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        self.assertIn('окно', result[0])

    def test_search_word_with_tilde(self):
        """Test word search with tilde replacement"""
        result = self.wrapper.search_word('укно', replace_tilde=True)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        self.assertNotIn('~', result[0])

    def test_search_word_full_json(self):
        """Test word search with full JSON response"""
        result = self.wrapper.search_word('укно', return_full_json=True)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

    def test_search_word_invalid_language(self):
        """Test word search with invalid language"""
        with self.assertRaises(ValueError):
            self.wrapper.search_word('укно', lang='invalid')

    def test_search_word_not_found(self):
        """Test word search with non-existent word"""
        with self.assertRaises(WordNotFoundError):
            self.wrapper.search_word('asdfqwerty123')

    def test_search_texts_basic(self):
        """Test basic texts search functionality"""
        result = self.wrapper.search_texts('аспӧртэм')
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)
        self.assertIn('аспӧртэм', result[0])

    def test_search_texts_with_params(self):
        """Test texts search with parameters"""
        params = {'count': 5, 'full_compare': True}
        result = self.wrapper.search_texts('аспӧртэм', params=params)
        self.assertIsInstance(result, list)
        self.assertTrue(len(result) <= 5)

    def test_search_texts_not_found(self):
        """Test texts search with non-existent text"""
        with self.assertRaises(TextsNotFoundError):
            self.wrapper.search_texts('asdfqwerty123')

if __name__ == '__main__':
    unittest.main()