# Udmcorpus-wrapper

## Overview

The **Udmcorpus-wrapper** is a Python library designed to facilitate interaction with the Udmcorpus API. This library provides a simple and intuitive interface for searching words in the Udmurt dictionary and texts in the Udmurt corpus. It is particularly useful for researchers, linguists, and developers working with Udmurt language data.

## Features

- **Word Search**: Search for words in the Udmurt dictionary with options to replace tildes, return full JSON responses, and lemmatize words if not found.
- **Text Search**: Search for texts in the Udmurt corpus with customizable parameters such as result count, full text comparison, and pagination.
- **Error Handling**: Custom exceptions for handling API errors, word not found, and texts not found.
- **Caching**: Utilizes `lru_cache` for efficient word search requests.
- **Language Support**: Supports Udmurt (`udm`) and Russian (`rus`) languages.

## Usage

### Searching for a Word

```python
from udmurtwrapper import UdmcorpusWrapper

wrapper = UdmcorpusWrapper()

# Basic word search
result = wrapper.search_word('укно')
print(result)

# Word search with tilde replacement
result_with_tilde = wrapper.search_word('укно', replace_tilde=True)
print(result_with_tilde)

# Word search with full JSON response
full_json_result = wrapper.search_word('укно', return_full_json=True)
print(full_json_result)
```

### Searching for Texts

```python
# Basic text search
texts_result = wrapper.search_texts('аспӧртэм')
print(texts_result)

# Text search with parameters
params = {'count': 5, 'full_compare': True}
texts_with_params = wrapper.search_texts('аспӧртэм', params=params)
print(texts_with_params)
```

### Handling Errors

```python
try:
    wrapper.search_word('asdfqwerty123')
except WordNotFoundError as e:
    print(f"Error: {e}")

try:
    wrapper.search_texts('asdfqwerty123')
except TextsNotFoundError as e:
    print(f"Error: {e}")
```

## Testing

The library includes a suite of unit tests to ensure its functionality. You can run the tests using `unittest`:

```bash
python -m unittest test_udmcorpus.py
```

---

**Note**: This library is not officially affiliated with the Udmcorpus API. It is an independent project created to simplify interaction with the API.