from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Union, Tuple
import requests
from bs4 import BeautifulSoup
from functools import lru_cache
import logging
from uniparser_udmurt import UdmurtAnalyzer

# Custom exceptions
class UdmCorpusError(Exception):
    """Base exception for UdmCorpus errors."""
    pass

class APIError(UdmCorpusError):
    """Raised when API request fails."""
    pass

class WordNotFoundError(UdmCorpusError):
    """Raised when word is not found in dictionary."""
    pass

class TextsNotFoundError(UdmCorpusError):
    """Raised when texts are not found in corpus."""
    pass

@dataclass
class Language:
    """Data class representing a language."""
    id: int
    code: str

class BaseCorpusAPI(ABC):
    """Abstract base class for corpus API implementations."""
    
    def __init__(self, headers: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize API client.

        Args:
            headers: Optional HTTP headers for requests
        """
        self.headers: Dict[str, str] = headers or {}
        self.logger: logging.Logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def make_request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make API request to specified endpoint.
        
        Args:
            endpoint: API endpoint
            payload: Request payload
            
        Returns:
            API response as dictionary
            
        Raises:
            APIError: If request fails
        """
        pass

class UdmcorpusWrapper:
    """Facade pattern implementation for UdmCorpus API."""

    def __init__(self) -> None:
        """Initialize wrapper with dictionary and corpus services."""
        self.dictionary = UdmurtDictionary()
        self.corpus = UdmurtCorpus()

    def search_word(self, word: str, lang: str = 'udm',
                    replace_tilde: bool = False, return_full_json: bool = False,
                    lemmatize_if_not_found: bool = False) -> Union[List[str], Dict[str, Any]]:
        """
        Search word in dictionary.

        Args:
            word: Word to search
            lang: Language code ('udm' or 'rus')
            replace_tilde: Whether to replace tildes with source words
            return_full_json: Whether to return full API response
            lemmatize_if_not_found: Lemmatize word if not found
        Returns:
            List of translations or full API response
        """
        return self.dictionary.get_word(word, lang, replace_tilde,
                                        return_full_json, lemmatize_if_not_found)

    def search_texts(self, text: str, 
                    params: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Search texts in corpus.

        Args:
            text: Text to search
            params: Additional search parameters

        Returns:
            List of found texts
        """
        return self.corpus.get_texts(text, params)

class UdmurtDictionary(BaseCorpusAPI):
    """Dictionary service implementation."""

    # Supported languages configuration
    LANGUAGES: Dict[str, Language] = {
        'udm': Language(1, 'udm'),
        'rus': Language(2, 'rus')
    }

    udmurt_analyzer = UdmurtAnalyzer(mode='strict')

    def make_request(self, endpoint: str, 
                    payload: Dict[str, Any]) -> Dict[str, Any]:
        """Implementation of abstract method for making API requests."""
        response = requests.post(
            f'https://udmcorpus.udman.ru/api/public/{endpoint}',
            json=payload,
            headers=self.headers
        )

        if response.status_code != 200:
            raise APIError(f'HTTP {response.status_code}: {response.text}')

        return response.json()

    @lru_cache(maxsize=128)
    def get_word(self, word: str, lang: str = 'udm',
                replace_tilde: bool = False,
                return_full_json: bool = False, 
                lemmatize_if_not_found: bool = False) -> Union[List[str], Dict[str, Any]]:
        """
        Get word translation.

        Args:
            word: Word to search
            lang: Language code
            replace_tilde: Whether to replace tildes with source words
            return_full_json: Whether to return full API response
            lemmatize_if_not_found: Lemmatize word if not found

        Returns:
            List of translations or full API response

        Raises:
            ValueError: If language is not supported
            WordNotFoundError: If word is not found
        """
        try:
            response = self.make_request('dictionary/search', {
                "word": word,
                "lang": {"id": self.LANGUAGES[lang].id}
            })
        except KeyError:
            raise ValueError(f"Unsupported language: {lang}")

        if not response:
            if lemmatize_if_not_found:
                new_word = self.udmurt_analyzer.analyze_words(word)[0].lemma
                if new_word != '':
                    response = self.make_request('dictionary/search', {
                        "word": new_word,
                        "lang": {"id": self.LANGUAGES[lang].id}
                    })

                    if not response:
                        raise WordNotFoundError(f"Word '{word}' not found")
                else:
                    raise WordNotFoundError(f"Word '{word}' not found")
            else:
                raise WordNotFoundError(f"Word '{word}' not found")

            word = new_word

        if return_full_json:
            return response

        return self._process_response(response, word, replace_tilde)

    def _process_response(self, response: List[Dict[str, Any]], 
                         word: str,
                         replace_tilde: bool) -> List[str]:
        """
        Process API response.

        Args:
            response: API response
            word: Original search word
            replace_tilde: Whether to replace tildes

        Returns:
            List of processed translations
        """
        results = []
        for item in response:
            text = BeautifulSoup(item['body'], "lxml").text
            if replace_tilde:
                text = text.replace('~', item['srcWord'])
            results.append(text)
        return results

class UdmurtCorpus(BaseCorpusAPI):
    """
    Implementation of Udmurt corpus API client.
    
    Provides methods for searching texts in the Udmurt corpus with various parameters.
    
    Attributes:
        DEFAULT_PARAMS (Dict[str, Union[int, bool]]): Default search parameters
    """

    DEFAULT_PARAMS: Dict[str, Union[int, bool]] = {
        'count': 10,  # Number of results to return
        'all_texts': False,  # Whether to return all found texts
        'return_full_json': False,  # Whether to return raw API response
        'full_compare': False,  # Enable full text comparison
        'full_text_mode': False,  # Enable full text search mode
        'page': 1,  # Starting page number
        'per_page': 10,  # Results per page
        'rows_count': 0  # Total rows count
    }

    def __init__(self, headers: Optional[Dict[str, str]] = None) -> None:
        """
        Initialize Udmurt corpus client.

        Args:
            headers: Optional HTTP headers for requests
        """
        super().__init__(headers)

    def make_request(self, endpoint: str, 
                    payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make HTTP request to corpus API endpoint.

        Args:
            endpoint: API endpoint path
            payload: Request payload

        Returns:
            API response as dictionary

        Raises:
            APIError: If request fails
        """
        response = requests.post(
            f'https://udmcorpus.udman.ru/api/public/{endpoint}',
            json=payload,
            headers=self.headers
        )

        if response.status_code != 200:
            raise APIError(f'HTTP {response.status_code}: {response.text}')

        return response.json()

    def get_texts(self, text: str, 
                 params: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Search texts in corpus.

        Args:
            text: Text to search for
            params: Optional search parameters to override defaults

        Returns:
            List of found texts or full API response if return_full_json=True

        Raises:
            TextsNotFoundError: If no texts found
        """
        # Merge default params with provided params
        search_params = self.DEFAULT_PARAMS.copy()
        if params:
            search_params.update(params)

        # Fetch texts from API
        results, new_count = self._fetch_texts(text, search_params)

        if len(results) == 0:
            raise TextsNotFoundError(f"Text: '{text}' not found")

        # Return raw results if requested
        if search_params['return_full_json']:
            return results
            
        # Extract and return text bodies
        return [item['body'] 
                for page in results 
                for item in page['content']][:new_count]

    def _fetch_texts(self, text: str, 
                    params: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], int]:
        """
        Fetch texts from API with pagination support.

        Args:
            text: Search text
            params: Search parameters

        Returns:
            Tuple of (list of results, count of results)
        """
        # Get first page of results
        first_res = self.make_request('search', self._build_search_payload(
            text, 
            full_compare=params['full_compare'],
            full_text_mode=params['full_text_mode']
        ))
        
        # Extract pagination info
        total_elements = first_res['totalElements']
        is_last_page = first_res['last']
        number_of_elements = first_res['numberOfElements']
        is_empty = first_res['empty']
        curr_elements = number_of_elements
        count = params['count']

        # Handle empty results
        if is_empty:
            return [], count

        # Handle single page results
        if is_last_page:
            return [first_res], count

        # Adjust count if all texts requested
        if params['all_texts']:
            count = total_elements

        # Fetch remaining pages
        results = [first_res]
        curr_page = 2

        while curr_elements < count:
            curr_res = self.make_request('search', self._build_search_payload(
                text,
                full_compare=params['full_compare'],
                full_text_mode=params['full_text_mode'],
                page=curr_page,
                rows_count=total_elements
            ))

            curr_elements += curr_res['numberOfElements']
            is_last_page = curr_res['last']
            results.append(curr_res)

            if is_last_page:
                break
            curr_page += 1

        return results, count

    def _build_search_payload(self, text: str, **kwargs: Any) -> Dict[str, Any]:
        """
        Build search request payload.

        Args:
            text: Search text
            **kwargs: Additional payload parameters

        Returns:
            Request payload dictionary
        """
        # Determine search mode and word/text parameters
        search_mode = 0
        word = text
        if kwargs.get('full_text_mode'):
            word = None
            search_mode = 1
            text_param = text
        else:
            text_param = None

        # Construct and return payload
        return {
            "searchMode": search_mode,
            "word": word,
            "page": kwargs.get('page', 1),
            "perPage": kwargs.get('per_page', 10),
            "fullcompare": kwargs.get('full_compare', False),
            "text": text_param,
            "title": "",
            "gr": {
                "partOfSpeech": [],
                "lexicalClasses": [],
                "attributivizers": [],
                "numerals": [],
                "number": [],
                "coreCases": [],
                "spatialCases": [],
                "spatialCases2": [],
                "possessiveness": [],
                "tense_mood": [],
                "verbalDerivation": [],
                "nonFiniteForms": [],
                "imperatives": []
            },
            "gloss": [],
            "startYear": None,
            "endYear": None,
            "theme": None,
            "type": {
                "value": 0,
                "title": "Корпус литературных текстов",
                "name": "CORPUS"
            },
            "authors": None,
            "rows": kwargs.get('rows_count', 0),
            "compiledgr": "Грамматика не выбрана",
            "compiledgloss": "Глоссы не выбраны"
        }