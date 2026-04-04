#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function
from os import system as os_system
from os.path import exists
from re import sub, IGNORECASE, compile
from sys import version_info
from six import text_type
import math


try:
    from urllib.parse import quote_plus, unquote, quote
    from urllib.request import HTTPError, urlopen, Request
except ImportError:
    from urllib import quote_plus, unquote, quote
    from urllib2 import HTTPError, Request, urlopen


# Headers for TVBb or other
agents = {
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'
}

# Headers for JSON APIs (TMDB)
agents_json = {
    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)',
    'Accept': 'application/json'}


PY3 = version_info.major >= 3
tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
thetvdb_api = 'a99d487bb3426e5f3a60dea6d3d3c7ef'
# thetvdb_api = 'D19315B88B2DE21F'


if not PY3:
    import codecs
    text_type_type = text_type
    open_func = codecs.open
    str_type = text_type
else:
    text_type_type = str
    open_func = open
    str_type = str


def isDreamOS():
    isDreamOS = False
    if exists('/var/lib/dpkg/status'):
        isDreamOS = True
    return isDreamOS


def quoteEventName(eventName):
    try:
        text = eventName.decode('utf8').replace(
            u'\x86', u'').replace(
            u'\x87', u'').encode('utf8')
    except BaseException:
        text = eventName
    return quote_plus(text, safe="+")


def getDesktopSize():
    from enigma import getDesktop
    s = getDesktop(0).size()
    return (s.width(), s.height())


def isFHD():
    desktopSize = getDesktopSize()
    return desktopSize[0] == 1920


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes // p, 2)
    return "%s %s" % (s, size_name[i])


def OnclearMem():
    try:
        os_system('sync')
        os_system('echo 1 > /proc/sys/vm/drop_caches')
        os_system('echo 2 > /proc/sys/vm/drop_caches')
        os_system('echo 3 > /proc/sys/vm/drop_caches')
    except BaseException:
        pass


def threadGetPage(
        url=None,
        file=None,
        key=None,
        success=None,
        fail=None,
        custom_headers=None):
    print('[MovieBrowser][threadGetPage] url, file, key, success, fail: ',
          url, "   ", file, "   ", key, "   ", success, "   ", fail)
    from requests import get
    from requests.exceptions import Timeout, RequestException

    headers = custom_headers if custom_headers is not None else agents

    if isinstance(url, bytes):
        try:
            url = url.decode('utf-8')
        except BaseException:
            url = url.decode('latin-1')

    try:
        response = get(url, headers=headers, timeout=10)
        response.raise_for_status()

        if file is None:
            success(response.content)
        elif key is not None:
            success(response.content, file, key)
        else:
            success(response.content, file)

    except HTTPError as httperror:
        print(
            f'[MovieBrowser][threadGetPage] HTTP Error for {url}: {httperror}')
        if fail:
            fail(str(httperror))
    except Timeout as timeout:
        print(f'[MovieBrowser][threadGetPage] Timeout for {url}: {timeout}')
        if fail:
            fail(str(timeout))
    except RequestException as error:
        print(
            f'[MovieBrowser][threadGetPage] Request error for {url}: {error}')
        if fail:
            fail(str(error))
    except Exception as error:
        print(
            f'[MovieBrowser][threadGetPage] General error for {url}: {error}')
        if fail:
            fail(str(error))


"""
def fetch_url(url, custom_headers=None):
    headers = custom_headers if custom_headers is not None else agents
    if url.startswith("http://") or url.startswith("https://"):
        try:
            request = Request(url, headers=headers)
            response = urlopen(request)
            bytes_data = response.read()

            try:
                return bytes_data.decode("utf-8", "ignore")
            except UnicodeDecodeError:
                return bytes_data.decode("latin-1", "ignore")

        except Exception as e:
            print("Unexpected error: {}, url={}".format(str(e), url))
            return None

    elif exists(url):
        try:
            with open(url, "rb") as f:
                return f.read()
        except Exception as e:
            print("Error reading file {}: {}".format(url, e))
            return None
    else:
        raise ValueError("Invalid URL or file path: %s" % url)
"""


def fetch_url_bytes(url, custom_headers=None):
    """Fetch URL e restituisci bytes (per immagini)"""
    # Stessa logica di fetch_url ma SENZA decode
    headers = custom_headers if custom_headers is not None else agents

    if url.startswith("http://") or url.startswith("https://"):
        try:
            request = Request(url, headers=headers)
            response = urlopen(request)
            return response.read()  # ← Restituisci bytes, non decodificare!
        except Exception as e:
            print("Error fetching bytes from {}: {}".format(str(url), str(e)))
            return None
    elif exists(url):
        try:
            with open(url, "rb") as f:
                return f.read()
        except Exception as e:
            print("Error reading file {}: {}".format(str(url), str(e)))
            return None
    else:
        print("Invalid URL or file path:", str(url))
        return None


def fetch_url(url, custom_headers=None):
    headers = custom_headers if custom_headers is not None else agents

    if url.startswith("http://") or url.startswith("https://"):
        try:
            request = Request(url, headers=headers)
            response = urlopen(request)
            bytes_data = response.read()

            # Gestione compatibilità Python 2/3
            if PY3:
                # Python 3: decodifica bytes
                try:
                    return bytes_data.decode("utf-8", "ignore")
                except UnicodeDecodeError:
                    return bytes_data.decode("latin-1", "ignore")
            else:
                # Python 2: se è già str, restituiscilo
                if isinstance(bytes_data, str):
                    return bytes_data
                # Altrimenti decodifica
                try:
                    return bytes_data.decode("utf-8", "ignore")
                except (UnicodeDecodeError, AttributeError):
                    try:
                        return bytes_data.decode("latin-1", "ignore")
                    except (UnicodeDecodeError, AttributeError):
                        # Fallback: restituisci come stringa
                        return str(bytes_data)

        except Exception as e:
            print("Unexpected error: {}, url={}".format(str(e), url))
            return None

    elif exists(url):
        try:
            with open(url, "rb") as f:
                data = f.read()

            # Per file locali, mantieni la logica originale
            # ma gestisci la compatibilità
            if PY3:
                # Python 3: restituisci bytes
                return data
            else:
                # Python 2: restituisci str
                return data

        except Exception as e:
            print("Error reading file {}: {}".format(url, e))
            return None
    else:
        raise ValueError("Invalid URL or file path: %s" % url)


def applySkinVars(skin, dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception as e:
            print(e, '@key=', key)
    return skin


REGEX = compile(
    r'([\(\[].*?[\)\]])|'                       # Text in brackets
    r'(: odc\.\d+)|'                            # Episode markers
    r'(\d+: odc\.\d+)|'                         # Season/episode markers
    r'(\d+ odc\.\d+)|'                          # Alternative episode markers
    r'(:)|'                                     # Colon
    r'( -.*?\.)|'                               # Text after dash
    r'(,)|'                                     # Comma
    r'!|'                                       # Exclamation
    r'\/.*|'                                    # Slash and following text
    r'\\\|\s[0-9]+\+|'                          # Backslash and numbers
    r'[0-9]+\+|'                                # Numbers with plus
    r'\s\d{4}\Z|'                               # 4-digit year at end
    r'([\(\[\|].*?[\)\]\|])|'                   # Various brackets
    r'(\.\s.+)|'                                # Dot followed by text
    r'(\"|\"\.|\"\,)|\s.+|'                     # Quotes and following text
    r'\"|'                                      # Quote
    r':|'                                       # Colon
    r'(\d{3,4}p|\d{3,4}x\d{3,4}|4K|UHD)|'       # Resolutions
    r'(WEBRip|WEB-DL|BluRay|BRRip|WEB|HDTV)|'   # Quality tags
    r'(x264|x265|H\.264|H\.265|HEVC)|'          # Codecs
    r'(AAC\d\.\d|AC3|DTS)|'                     # Audio formats
    r'(10bit|HDR|YTS|MX)|'                      # Other tags
    r'(FRENCH|GERMAN|SPANISH)',                 # Languages
    IGNORECASE
)


def cleanSeriesName(self, name, language='en'):
    """Cleans the series name by removing episode/season patterns"""

    # Multilingual patterns to remove
    patterns_to_remove = {
        'all': [  # Patterns valid for all languages
            r'[Ss][0-9]+[Ee][0-9]+.*',          # S01E01...
            r'[0-9]+x[0-9]+.*',                 # 1x08...
            r'\[.*?\]',                         # [something]
            r'\(.*?\)',                         # (something)
            r'\{.*?\}',                         # {something}
            r'\.\.\.',                          # ...
            r'\s+-\s+',                         # " - " separator
        ],
        'it': [  # Italian
            r'[Ss]tagione[ ._-]*[0-9]+.*',      # Stagione 1...
            r'[Ee]pisodio[ ._-]*[0-9]+.*',      # Episodio 8...
            r'[Pp]arte[ ._-]*[0-9]+.*',         # Parte 1...
        ],
        'en': [  # English
            r'[Ss]eason[ ._-]*[0-9]+.*',        # Season 1...
            r'[Ee]pisode[ ._-]*[0-9]+.*',       # Episode 8...
            r'[Pp]art[ ._-]*[0-9]+.*',          # Part 1...
        ],
        'fr': [  # French
            r'[Ss]aison[ ._-]*[0-9]+.*',        # Saison 1...
            r'[ÉéEe]pisode[ ._-]*[0-9]+.*',     # Épisode 8...
        ],
        'es': [  # Spanish
            r'[Tt]emporada[ ._-]*[0-9]+.*',     # Temporada 1...
            r'[Ee]pisodio[ ._-]*[0-9]+.*',      # Episodio 8...
        ],
        'de': [  # German
            r'[Ss]taffel[ ._-]*[0-9]+.*',       # Staffel 1...
            r'[Ff]olge[ ._-]*[0-9]+.*',         # Folge 8...
        ]
    }

    cleaned_name = name

    # 1. Remove universal patterns
    for pattern in patterns_to_remove['all']:
        cleaned_name = sub(pattern, '', cleaned_name, flags=IGNORECASE)

    # 2. Remove language-specific patterns
    if language in patterns_to_remove:
        for pattern in patterns_to_remove[language]:
            cleaned_name = sub(pattern, '', cleaned_name, flags=IGNORECASE)
    else:
        # Fallback to English
        for pattern in patterns_to_remove['en']:
            cleaned_name = sub(pattern, '', cleaned_name, flags=IGNORECASE)

    # 3. Final cleanup
    # Replace multiple spaces with a single one
    cleaned_name = sub(r'\s+', ' ', cleaned_name)
    # Remove leading/trailing spaces
    cleaned_name = cleaned_name.strip()
    # Remove trailing underscores or hyphens
    cleaned_name = sub(r'[_-]+$', '', cleaned_name)

    print("[DEBUG cleanSeriesName] From: '" + name + "'")
    print("[DEBUG] To: '" + cleaned_name + "' (Language: " + language + ")")

    return cleaned_name


def cleanSeriesFilename(filename):
    """Clean series filename for TVDB search"""
    name = str(filename)
    # Remove file extension
    name = sub(r'\.[a-zA-Z0-9]{2,4}$', '', name, flags=IGNORECASE)

    # Remove episode/season patterns (case insensitive, flexible spacing)
    patterns = [
        r'[Ss][0-9]+\s*[Ee][0-9]+.*',
        r'[0-9]+\s*[Xx]\s*[0-9]+.*',
        r'[Ss]tagione\s*[0-9]+.*',
        r'[Ee]pisodio\s*[0-9]+.*',
        r'[Ss]tagione\s*[0-9]+\s*[-–—]\s*[Ee]pisodio\s*[0-9]+.*',
        r'[Pp]arte\s*[0-9]+.*',
        r'[Ss]eason\s*[0-9]+.*',
        r'[Ee]pisode\s*[0-9]+.*',
    ]

    for pattern in patterns:
        name = sub(pattern, '', name, flags=IGNORECASE)

    # Clean up
    name = sub(r'\s+', ' ', name).strip()
    name = sub(r'^[\.\-_\s]+|[\.\-_\s]+$', '', name)

    return name


def clean_for_search(text, search_type='movie'):
    """
    Cleans any filename for TMDB/TVDB search.
    """

    if not text:
        return ""

    # 1. Remove path if present
    name = sub(r'.*[/\\]', '', str(text))

    # 2. Remove file extensions
    name = sub(
        r'\.(ts|avi|divx|flv|iso|m2ts|m4v|mov|mp4|mpg|mpeg|mkv|vob|srt|sub|idx)$',
        '',
        name,
        flags=IGNORECASE)

    # 3. Convert to lowercase
    name = name.lower()

    # 4. Different handling for movies vs series
    if search_type == 'series':
        # For series: remove season/episode patterns
        name = sub(r'[sse][0-9]+[e][0-9]+.*', '', name)
        name = sub(r'[0-9]+x[0-9]+.*', '', name)
        name = sub(r'season[\.\s]*[0-9]+.*', '', name, flags=IGNORECASE)
        name = sub(r'episode[\.\s]*[0-9]+.*', '', name, flags=IGNORECASE)

    # 5. Remove year in parentheses
    name = sub(r'[\(\[](19|20)[0-9]{2}[\)\]]', '', name)

    # 6. Use the existing REGEX for cleanup
    name = REGEX.sub(' ', name)

    # 7. Clean multiple spaces and trim
    name = sub(r'\s+', ' ', name).strip()

    return name


def clean_movie_title(filename):
    """Cleans the file name for TMDB search."""
    # Remove file extension
    name = sub(r'\.[a-z0-9]{2,4}$', '', filename, flags=IGNORECASE)

    # Apply regex to remove metadata
    name = REGEX.sub(' ', name)

    # Remove multiple spaces and trim
    name = sub(r'\s+', ' ', name).strip()

    # URL-encode (use quote instead of replacing with +)
    return quote(name)


def remove_accents(string):
    import unicodedata
    if not PY3:
        if type(string) is not text_type:
            string = text_type(string, encoding='utf-8')
    string = unicodedata.normalize('NFD', string)
    string = sub(r'[\u0300-\u036f]', '', string)
    return string


def cutName(eventName=""):
    if eventName:
        eventName = eventName.replace(
            '"',
            '').replace(
            'Х/Ф',
            '').replace(
            'М/Ф',
            '').replace(
                'Х/ф',
                '').replace(
                    '.',
                    '').replace(
                        ' | ',
            '')
        eventName = eventName.replace(
            '(18+)',
            '').replace(
            '18+',
            '').replace(
            '(16+)',
            '').replace(
                '16+',
                '').replace(
                    '(12+)',
            '')
        eventName = eventName.replace(
            '12+',
            '').replace(
            '(7+)',
            '').replace(
            '7+',
            '').replace(
                '(6+)',
                '').replace(
                    '6+',
            '')
        eventName = eventName.replace(
            '(0+)',
            '').replace(
            '0+',
            '').replace(
            '+',
            '')
        eventName = eventName.replace('episode', '')
        eventName = eventName.replace('مسلسل', '')
        eventName = eventName.replace('فيلم وثائقى', '')
        eventName = eventName.replace('حفل', '')
        return eventName
    return ""


def getCleanTitle(eventitle=""):
    save_name = eventitle.replace(' ^`^s', '').replace(' ^`^y', '')
    return save_name


def convtext(text=''):
    try:
        if text is None:
            print('Input text is None')
            return

        if text == '':
            print('text is an empty string')
        else:
            print('original text: ', text)
            text = text.lower()
            print('lowercased text: ', text)
            text = remove_accents(text)
            print('remove_accents text: ', text)
            text = cutName(text)
            text = getCleanTitle(text)
            if text.endswith("the"):
                text = "the " + text[:-4]
            text = text.replace(
                "\xe2\x80\x93",
                "").replace(
                '\xc2\x86',
                '').replace(
                '\xc2\x87',
                '')  # replace special
            text = transMOVIE(text)
            print('transMOVIE: ', text)
            text = quoteEventName(text)
            print('TEXT=', text)
        return unquote(text).capitalize()
    except Exception as e:
        print('convtext error: ', e)
        pass


def transMOVIE(text):
    """
    Fixed version of transMOVIE.
    Compatible with existing code, but uses new logic.
    """
    cleaned = clean_for_search(text, search_type='movie')
    return cleaned.replace(' ', '+')


def transSERIES(text):
    """
    Fixed version of transSERIES.
    Compatible with existing code, but uses new logic.
    """
    cleaned = clean_for_search(text, search_type='series')
    return cleaned.replace(' ', '+')


def _renewTMDb(text):
    """
    Simplified and corrected version of _renewTMDb.
    """
    return clean_for_search(text, search_type='movie')


def _renewTVDb(text):
    """
    Simplified and corrected version of _renewTVDb.
    """
    return clean_for_search(text, search_type='series')
