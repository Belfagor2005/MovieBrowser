#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import print_function

# 20221004 Kiddac edit: python 3 support et al
# 20221204 Lululla edit & add: language, config, major fix
# 20221208 Twol add callInThread getMountDefault
# 20221222 Lululla recoded, major fix
# 20240920 Lululla recoded - clean unnecessary code
# 20250516 Lululla refactoryzed all Cls and clean unnecessary all code

from __future__ import print_function

# Built-in modules
import datetime
import math
from shutil import copytree, copy2, rmtree
from os.path import exists, join, getsize, getmtime, isdir, normpath, dirname
from os import statvfs, remove, rename, system as os_system, popen, walk, makedirs, listdir
from re import sub, search, findall, IGNORECASE, S, escape
from io import open
import sys

# Third-party modules
from requests import get
from urllib.error import HTTPError, URLError
from twisted.internet.reactor import callInThread

# Enigma2 imports
from enigma import (
    RT_VALIGN_CENTER,
    RT_HALIGN_LEFT,
    eConsoleAppContainer,
    eListboxPythonMultiContent,
    ePoint,
    eServiceReference,
    eTimer,
    getDesktop,
    gFont,
    iPlayableService,
    iServiceInformation,
    loadPNG,
)

# Components imports
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.config import (
    ConfigSelection,
    ConfigText,
    ConfigYesNo,
    ConfigDirectory,
    ConfigSlider,
    ConfigEnableDisable,
    ConfigSubsection,
    ConfigOnOff,
    config,
    configfile,
    ConfigClock,
    NoSave,
    getConfigListEntry,
)
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest, MultiContentEntryText
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.Sources.StaticText import StaticText

# Screens imports
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard

from Plugins.Plugin import PluginDescriptor
from Tools.Directories import fileExists

# Localization import (from current package)
from . import _, isDreambox, PY3


try:
    from urllib2 import Request, urlopen
except:
    from urllib.request import Request, urlopen


def getDesktopSize():
    from enigma import getDesktop
    s = getDesktop(0).size()
    return (s.width(), s.height())


def isFHD():
    desktopSize = getDesktopSize()
    return desktopSize[0] >= 1920


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
        os_system("sync")
        os_system("echo 1 > /proc/sys/vm/drop_caches")
        os_system("echo 2 > /proc/sys/vm/drop_caches")
        os_system("echo 3 > /proc/sys/vm/drop_caches")
    except OSError:
        pass


class ItemList(MenuList):

    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        if isFHD():
            self.l.setItemHeight(50)
            self.l.setFont(36, gFont('Regular', 36))
            self.l.setFont(32, gFont('Regular', 32))
            self.l.setFont(30, gFont('Regular', 30))
        else:
            self.l.setItemHeight(35)
            self.l.setFont(26, gFont('Regular', 26))
            self.l.setFont(24, gFont('Regular', 24))


def threadGetPage(url=None, file=None, key=None, success=None, fail=None):

    try:
        print("[MovieBrowser][threadGetPage] url=%s, file=%s, key=%s", url, file, key)
        response = get(url, timeout=10)
        response.raise_for_status()

        if success:
            if file is None:
                success(response.content)
            elif key is not None:
                success(response.content, file, key)
            else:
                success(response.content, file)
    except HTTPError as httperror:
        print("[MovieBrowser][threadGetPage] HTTP error: %s", httperror)
        if fail:
            fail(httperror)
    except Exception as error:
        print("[MovieBrowser][threadGetPage] Unexpected error: %s", error)
        if fail:
            fail(error)


""" constants """
version = '3.9-rc0'

screenwidth = getDesktop(0).size()

dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser"
db_dir = join(dir_plugins, "db")
log_dir = join(dir_plugins, "log")

DATABASE_PATH = join(db_dir, "database")
DATABASE_RESET = join(db_dir, "reset")
DATABASE_CACHE = join(db_dir, "cache")

DATABASE_CACHE_HDD = join('/media/hdd', "moviebrowser/cache")
DATABASE_CACHE_USB = join('/media/hdd', "moviebrowser/cache")
DATABASE_CACHE_NET = join('/media/hdd', "moviebrowser/cache")

BLACKLIST_PATH = join(db_dir, "blacklist")
FILTER_PATH = join(db_dir, "filter")
LAST_PATH = join(db_dir, "last")

UPDATE_LOG_PATH = join(log_dir, "update.log")
TIMER_LOG_PATH = join(log_dir, "timer.log")
CLEANUP_LOG_PATH = join(log_dir, "cleanup.log")

infobarsession = None

skin_directory = "/".join([dir_plugins, "skin", "hd", ""])
if isFHD():
    skin_directory = "/".join([dir_plugins, "skin", "fhd", ""])

default_backdrop = "/".join([skin_directory, "pic", "setup", "default_backdrop.png"])
default_folder = "/".join([skin_directory, "pic", "browser", "default_folder.png"])
default_poster = "/".join([skin_directory, "pic", "browser", "default_poster.png"])
default_banner = "/".join([skin_directory, "pic", "browser", "default_banner.png"])
default_backdropm1v = "/".join([skin_directory, "pic", "browser", "default_backdrop.m1v"])
infoBackPNG = "/".join([skin_directory, "pic", "browser", "info_small_back.png"])
infosmallBackPNG = infoBackPNG  # duplicate
no_m1v = "/".join([skin_directory, "pic", "browser", "no.m1v"])
wiki_png = "/".join([skin_directory, "pic", "browser", "wiki.png"])
agents = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1'}

folders = listdir(skin_directory)
if "pic" in folders:
    folders.remove("pic")


tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
thetvdb_api = 'a99d487bb3426e5f3a60dea6d3d3c7ef'
# thetvdb_api = 'D19315B88B2DE21F'

""" init config """
config.plugins.moviebrowser = ConfigSubsection()
lang = language.getLanguage()[:2]
config.plugins.moviebrowser.language = ConfigSelection(default=lang, choices=[
    ('de', 'German'),
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('it', 'Italian'),
    ('ru', 'Russian')
])

config.plugins.moviebrowser.filter = ConfigSelection(default=':::Movie:Top:::', choices=[
    (':::Movie:Top:::', _('Movies')),
    (':::Series:Top:::', _('Series')),
    (':Top:::', _('Movies & Series'))
])
config.plugins.moviebrowser.sortorder = ConfigSelection(default='date_reverse', choices=[
    ('date_reverse', _('Movie Creation Date Descending')),
    ('date', _('Movie Creation Date Ascending')),
    ('name', _('Movie Title A-Z')),
    ('name_reverse', _('Movie Title Z-A')),
    ('rating_reverse', _('Movie Rating 10-0')),
    ('rating', _('Movie Rating 0-10')),
    ('year_reverse', _('Movie Release Date Descending')),
    ('year', _('Movie Release Date Ascending')),
    ('runtime_reverse', _('Movie Runtime Descending')),
    ('runtime', _('Movie Runtime Ascending')),
    ('folder', _('Movie Folder Ascending')),
    ('folder_reverse', _('Movie Folder Descending'))
])

config.plugins.moviebrowser.backdrops = ConfigSelection(default='auto', choices=[
    ('info', _('Info Button')),
    ('auto', _('Automatic')),
    ('hide', _('Hide'))
])
config.plugins.moviebrowser.download = ConfigSelection(default='update', choices=[
    ('access', _('On First Access')),
    ('update', _('On Database Update'))
])
config.plugins.moviebrowser.m1v = ConfigOnOff(default=False)

if config.plugins.moviebrowser.m1v.value is True:
    config.plugins.moviebrowser.showtv = ConfigSelection(default='hide', choices=[
        ('show', _('Show')),
        ('hide', _('Hide'))
    ])
else:
    config.plugins.moviebrowser.showtv = ConfigSelection(default='show', choices=[
        ('show', _('Show')),
        ('hide', _('Hide'))
    ])

config.plugins.moviebrowser.showswitch = ConfigOnOff(default=False)
config.plugins.moviebrowser.showmenu = ConfigOnOff(default=False)
config.plugins.moviebrowser.videobutton = ConfigOnOff(default=False)
config.plugins.moviebrowser.lastmovie = ConfigSelection(default='yes', choices=[
    ('yes', _('Yes')),
    ('no', _('No')),
    ('folder', _('Folder Selection'))
])
config.plugins.moviebrowser.lastfilter = ConfigOnOff(default=False)
config.plugins.moviebrowser.showfolder = ConfigOnOff(default=False)
config.plugins.moviebrowser.skin = ConfigSelection(default='default', choices=folders)
skin_path = "%s%s/" % (skin_directory, config.plugins.moviebrowser.skin.value)
config.plugins.moviebrowser.plotfull = ConfigSelection(default='show', choices=[
    ('hide', _('Info Button')),
    ('show', _('Automatic'))
])
config.plugins.moviebrowser.timerupdate = ConfigEnableDisable(default=False)
config.plugins.moviebrowser.timer = ConfigClock(default=6 * 3600)
config.plugins.moviebrowser.hideupdate = ConfigOnOff(default=False)
config.plugins.moviebrowser.reset = ConfigYesNo(default=False)
config.plugins.moviebrowser.style = ConfigSelection(default='backdrop', choices=[
    ('metrix', 'Metrix'),
    ('backdrop', 'Backdrop'),
    ('posterwall', 'Posterwall')
])
config.plugins.moviebrowser.seriesstyle = ConfigSelection(default='backdrop', choices=[
    ('metrix', 'Metrix'),
    ('backdrop', 'Backdrop'),
    ('posterwall', 'Posterwall')
])
config.plugins.moviebrowser.api = NoSave(ConfigSelection(['-> Ok']))
config.plugins.moviebrowser.txtapi = ConfigText(default=tmdb_api, visible_width=60, fixed_size=False)
config.plugins.moviebrowser.tvdbapi = NoSave(ConfigSelection(['-> Ok']))
config.plugins.moviebrowser.txttvdbapi = ConfigText(default=thetvdb_api, visible_width=60, fixed_size=False)
config.plugins.moviebrowser.moviefolder = ConfigDirectory("/media/hdd/movie")

try:
    from Components.UsageConfig import defaultMoviePath
    downloadpath = defaultMoviePath()
    config.plugins.moviebrowser.moviefolder = ConfigDirectory(default=downloadpath)
except:
    if isDreambox:
        config.plugins.moviebrowser.moviefolder = ConfigDirectory(default='/media/hdd/movie/')

config.plugins.moviebrowser.cachefolder = ConfigSelection(default=DATABASE_CACHE, choices=[
    (DATABASE_CACHE, 'Default'),
    (DATABASE_CACHE_HDD, '/media/hdd'),
    (DATABASE_CACHE_USB, '/media/usb'),
    (DATABASE_CACHE_NET, '/media/net'),
])

cache_path = config.plugins.moviebrowser.cachefolder.value
cache_dir = dirname(cache_path)

try:
    if not exists(cache_dir):
        makedirs(cache_dir)
except OSError as e:
    if not exists(cache_dir):
        print("Failed to create cache folder:", e)


config.plugins.moviebrowser.cleanup = ConfigYesNo(default=False)
config.plugins.moviebrowser.backup = ConfigYesNo(default=False)
config.plugins.moviebrowser.restore = ConfigYesNo(default=False)
config.plugins.moviebrowser.transparency = ConfigSlider(default=255, limits=(100, 255))

config.plugins.moviebrowser.metrixcolor = ConfigSelection(default='0x00000000', choices=[
    ('0x00000000', 'Skin Default'),
    ('0x00F0A30A', 'Amber'),
    ('0x007895BC', 'Blue'),
    ('0x00825A2C', 'Brown'),
    ('0x000050EF', 'Cobalt'),
    ('0x00911D10', 'Crimson'),
    ('0x001BA1E2', 'Cyan'),
    ('0x00008A00', 'Emerald'),
    ('0x0070AD11', 'Green'),
    ('0x006A00FF', 'Indigo'),
    ('0x00BB0048', 'Magenta'),
    ('0x0076608A', 'Mauve'),
    ('0x006D8764', 'Olive'),
    ('0x00C3461B', 'Orange'),
    ('0x00F472D0', 'Pink'),
    ('0x00E51400', 'Red'),
    ('0x007A3B3F', 'Sienna'),
    ('0x00647687', 'Steel'),
    ('0x00149BAF', 'Teal'),
    ('0x004176B6', 'Tufts'),
    ('0x006C0AAB', 'Violet'),
    ('0x00BF9217', 'Yellow')
])

""" end config """


def applySkinVars(skin, dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception as e:
            print(e, '@key=', key)
    return skin


def transHTML(text):
    if PY3:
        import html
        text = html.unescape(text)
    else:
        from six.moves import html_parser
        h = html_parser.HTMLParser()
        text = h.unescape(text.decode("utf8")).encode("utf8")

    charlist = [
        ("&#034;", '"'), ("&#038;", '&'), ("&#039;", "'"), ("&#060;", ' '),
        ("&#062;", ' '), ("&#160;", ' '), ("&#174;", ''), ("&#192;", 'À'),
        ("&#193;", 'Á'), ("&#194;", 'Â'), ("&#196;", 'Ä'), ("&#204;", 'Ì'),
        ("&#205;", 'Í'), ("&#206;", 'Î'), ("&#207;", 'Ï'), ("&#210;", 'Ò'),
        ("&#211;", 'Ó'), ("&#212;", 'Ô'), ("&#214;", 'Ö'), ("&#217;", 'Ù'),
        ("&#218;", 'Ú'), ("&#219;", 'Û'), ("&#220;", 'Ü'), ("&#223;", 'ß'),
        ("&#224;", 'à'), ("&#225;", 'á'), ("&#226;", 'â'), ("&#228;", 'ä'),
        ("&#232;", 'è'), ("&#233;", 'é'), ("&#234;", 'ê'), ("&#235;", 'ë'),
        ("&#236;", 'ì'), ("&#237;", 'í'), ("&#238;", 'î'), ("&#239;", 'ï'),
        ("&#242;", 'ò'), ("&#243;", 'ó'), ("&#244;", 'ô'), ("&#246;", 'ö'),
        ("&#249;", 'ù'), ("&#250;", 'ú'), ("&#251;", 'û'), ("&#252;", 'ü'),
        ("&#8203;", ''), ("&#8211;", '-'), ("&#8212;", '—'), ("&#8216;", "'"),
        ("&#8217;", "'"), ("&#8220;", '"'), ("&#8221;", '"'), ("&#8222;", ','),
        ("&#8230;", '...'), ("&#x21;", '!'), ("&#x26;", '&'), ("&#x27;", "'"),
        ("&#x3f;", '?'), ("&#xB7;", '·'), ("&#xC4;", 'Ä'), ("&#xD6;", 'Ö'),
        ("&#xDC;", 'Ü'), ("&#xDF;", 'ß'), ("&#xE4;", 'ä'), ("&#xE9;", 'é'),
        ("&#xF6;", 'ö'), ("&#xF8;", 'ø'), ("&#xFB;", 'û'), ("&#xFC;", 'ü'),
        ("&8221;", '”'), ("&8482;", '™'), ("&Aacute;", 'Á'), ("&Acirc;", 'Â'),
        ("&Agrave;", 'À'), ("&Auml;", 'Ä'), ("&Iacute;", 'Í'), ("&Icirc;", 'Î'),
        ("&Igrave;", 'Ì'), ("&Iuml;", 'Ï'), ("&Oacute;", 'Ó'), ("&Ocirc;", 'Ô'),
        ("&Ograve;", 'Ò'), ("&Ouml;", 'Ö'), ("&Uacute;", 'Ú'), ("&Ucirc;", 'Û'),
        ("&Ugrave;", 'Ù'), ("&Uuml;", 'Ü'), ("&aacute;", 'á'), ("&acirc;", 'â'),
        ("&acute;", "'"), ("&agrave;", 'à'), ("&amp;", '&'), ("&apos;", "'"),
        ("&auml;", 'ä'), ("&bdquo;", '"'), ("&eacute;", 'é'), ("&ecirc;", 'ê'),
        ("&egrave;", 'è'), ("&euml;", 'ë'), ("&gt;", '>'), ("&hellip;", '...'),
        ("&iacute;", 'í'), ("&icirc;", 'î'), ("&igrave;", 'ì'), ("&iuml;", 'ï'),
        ("&laquo;", '"'), ("&ldquo;", '"'), ("&lsquo;", "'"), ("&lt;", '<'),
        ("&mdash;", '—'), ("&nbsp;", ' '), ("&ndash;", '-'), ("&oacute;", 'ó'),
        ("&ocirc;", 'ô'), ("&ograve;", 'ò'), ("&ouml;", 'ö'), ("&quot;", '"'),
        ("&raquo;", '"'), ("&rsquo;", "'"), ("&szlig;", 'ß'), ("&uacute;", 'ú'),
        ("&ucirc;", 'û'), ("&ugrave;", 'ù'), ("&uuml;", 'ü'), ("&ntilde;", '~'),
        ("&equals;", '='), ("&quest;", '?'), ("&comma;", ','), ("&period;", '.'),
        ("&colon;", ':'), ("&lpar;", '('), ("&rpar;", ')'), ("&excl;", '!'),
        ("&dollar;", '$'), ("&num;", '#'), ("&ast;", '*'), ("&lowbar;", '_'),
        ("&lsqb;", '['), ("&rsqb;", ']'), ("&half;", '1/2'),
        ("&DiacriticalTilde;", '~'), ("&OpenCurlyDoubleQuote;", '"'),
        ("&CloseCurlyDoubleQuote;", '"'),
    ]

    for old, new in charlist:
        text = text.replace(old, new)
    text = sub("<[^>]+>", "", text)
    return text.strip()


def _renewTMDb(text):
    name = sub('.*?[/]', '', text)
    if name.endswith('.ts'):
        name = sub('_', ' ', name)
        name = sub('^.*? - .*? - ', '', name)
        name = sub('^[0-9]+ [0-9]+ - ', '', name)
        name = sub('^[0-9]+ - ', '', name)
        text = sub('[.]ts', '', name)
    else:
        text = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)

    return text


def _renewTVDb(text):
    name = sub('.*?[/]', '', text)
    if name.endswith('.ts'):
        name = sub('_', ' ', name)
        name = sub('^.*? - .*? - ', '', name)
        name = sub('^[0-9]+ [0-9]+ - ', '', name)
        name = sub('^[0-9]+ - ', '', name)
        text = sub('[.]ts', '', name)
    else:
        text = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
    return text


def transMOVIE(text):
    text = text.lower() + '+FIN'
    text = text.replace('  ', '+').replace(' ', '+').replace('&', '+') \
        .replace(':', '+').replace('_', '+').replace('.', '+') \
        .replace('"', '+').replace('(', '+').replace(')', '+') \
        .replace('[', '+').replace(']', '+').replace('!', '+') \
        .replace('++++', '+').replace('+++', '+').replace('++', '+')
    text = text.replace('+720p+', '++').replace('+1080i+', '+') \
        .replace('+1080p+', '++').replace('+dtshd+', '++') \
        .replace('+dtsrd+', '++').replace('+dtsd+', '++') \
        .replace('+dts+', '++').replace('+dd5+', '++') \
        .replace('+5+1+', '++').replace('+3d+', '++') \
        .replace('+ac3d+', '++').replace('+ac3+', '++') \
        .replace('+avchd+', '++').replace('+avc+', '++') \
        .replace('+dubbed+', '++').replace('+subbed+', '++') \
        .replace('+stereo+', '++')
    text = text.replace('+x264+', '++').replace('+mpeg2+', '++') \
        .replace('+avi+', '++').replace('+xvid+', '++') \
        .replace('+blu+', '++').replace('+ray+', '++') \
        .replace('+bluray+', '++').replace('+3dbd+', '++') \
        .replace('+bd+', '++').replace('+bdrip+', '++') \
        .replace('+dvdrip+', '++').replace('+rip+', '++') \
        .replace('+hdtv+', '++').replace('+hddvd+', '++')
    text = text.replace('+german+', '++').replace('+ger+', '++') \
        .replace('+english+', '++').replace('+eng+', '++') \
        .replace('+spanish+', '++').replace('+spa+', '++') \
        .replace('+italian+', '++').replace('+ita+', '++') \
        .replace('+russian+', '++').replace('+rus+', '++') \
        .replace('+dl+', '++').replace('+dc+', '++') \
        .replace('+sbs+', '++').replace('+se+', '++') \
        .replace('+ws+', '++').replace('+cee+', '++')
    text = text.replace('+remux+', '++').replace('+directors+', '++') \
        .replace('+cut+', '++').replace('+uncut+', '++') \
        .replace('+extended+', '++').replace('+repack+', '++') \
        .replace('+unrated+', '++').replace('+rated+', '++') \
        .replace('+retail+', '++').replace('+remastered+', '++') \
        .replace('+edition+', '++').replace('+version+', '++')

    text = sub('\\+tt[0-9]+\\+', '++', text)
    text = sub(
        r'(720p|1080p|1080i|4k|WEBRip|WEB-DL|BluRay|BRRip|HDRip|DVDRip|DVDScr|'
        r'x264|x265|HEVC|AAC[0-9]*\.?[0-9]*|10bits|10bit|DTS|DD5\.1|H\.264|H264|'
        r'XviD|HDTV|HD|HDR|Remux|Extended|Unrated|Director.?s Cut|Dual Audio|SUBBED|'
        r'DUBBED|TRUEHD|Atmos|5\.1|7\.1|HE-AAC|WEB|HDR10|Blu-ray|BDRip|BluRayRip|'
        r'HDCAM|CAM|TS|SCR|SD|HDTC|DVDRip|WEB-DL|PROPER|REPACK|RARBG|YTS)+',
        '', text, flags=IGNORECASE)
    text = sub('\\+\\+\\+\\+.*?FIN', '', text)
    text = sub('\\+FIN', '', text)
    return text


def transSERIES(text):
    # Lowercase and append sentinel
    text = text.lower() + "+FIN"

    # Replace multiple punctuation and symbols with '+'
    replacements = {
        '  ': '+', ' ': '+', '&': '+', ':': '+', '_': '+', 'u.s.': 'us', 'l.a.': 'la',
        '.': '+', '"': '+', '(': '+', ')': '+', '[': '+', ']': '+', '!': '+',
        '++++': '+', '+++': '+', '++': '+'
    }
    for k, v in replacements.items():
        text = text.replace(k, v)

    # Groups of tags that get replaced with '++'
    tags_plusplus = [
        '720p', '1080i', '1080p', 'dtshd', 'dtsrd', 'dtsd', 'dts', 'dd5', '5+1',
        '3d', 'ac3d', 'ac3', 'avchd', 'avc', 'dubbed', 'subbed', 'stereo',
        'x264', 'mpeg2', 'avi', 'xvid', 'blu', 'ray', 'bluray', '3dbd', 'bd', 'bdrip',
        'dvdrip', 'rip', 'hdtv', 'hddvd',
        'german', 'ger', 'english', 'eng', 'spanish', 'spa', 'italian', 'ita', 'russian', 'rus',
        'dl', 'dc', 'sbs', 'se', 'ws', 'cee',
        'remux', 'directors', 'cut', 'uncut', 'extended', 'repack', 'unrated', 'rated',
        'retail', 'remastered', 'edition', 'version'
    ]
    for tag in tags_plusplus:
        text = text.replace("+" + tag + "+", "++")

    # Replace special characters with URL encoding
    specials = {
        '\xc3\x9f': '%C3%9F', '\xc3\xa4': '%C3%A4', '\xc3\xb6': '%C3%B6', '\xc3\xbc': '%C3%BC'
    }
    for k, v in specials.items():
        text = text.replace(k, v)

    # Regex substitutions
    text = sub(r'\+tt[0-9]+\+', '++', text)
    text = sub(r'\+\+\+\+.*?FIN', '', text)
    text = sub(r'\+FIN', '', text)

    return text


def fetch_url(url):
    if url.startswith("http://") or url.startswith("https://"):
        try:
            request = Request(url, headers=agents)
            response = urlopen(request)
            return response.read()
        except HTTPError as e:
            print("HTTPError: code={}, reason={}, url={}".format(e.code, e.reason, url))
            return None
        except URLError as e:
            print("URLError: reason={}, url={}".format(e.reason, url))
            return None
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


class movieBrowserMetrix(Screen):

    def __init__(self, session, index, content, filter):

        skin = join(skin_path + "movieBrowserMetrix.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.seenEOF})
        self.toogleHelp = self.session.instantiateDialog(helpScreen)
        self.index = index
        self.hideflag = True
        self.ready = False
        self.startupdate = False
        self.reset = False
        self.tmdbposter = False
        self.topseries = False
        self.filterseen = False
        self.showhelp = False
        self.back = False
        self.content = content
        self.filter = filter
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value
        self.showfolder = config.plugins.moviebrowser.showfolder.getValue()
        self.ABC = 'ABC'
        self.namelist = []
        self.movielist = []
        self.datelist = []
        self.infolist = []
        self.plotlist = []
        self.posterlist = []
        self.backdroplist = []
        self.contentlist = []
        self.seenlist = []
        self.medialist = []
        self.dddlist = []
        self['name'] = Label()
        self['Director'] = Label(_('Director:'))
        self['Actors'] = Label(_('Actors:'))
        self['Year'] = Label(_('Years:'))
        self['Runtime'] = Label(_('Runtime:'))
        self['Country'] = Label(_('Country:'))
        self['text1'] = Label(_('Update'))
        self['text2'] = Label(_('Style'))
        self['text3'] = Label(_('Help'))
        self['Genres'] = Label(_('Genres:'))
        self['director'] = Label()
        self['actors'] = Label()
        self['year'] = Label()
        self['runtime'] = Label()
        self['country'] = Label()
        self['genres'] = Label()
        self['ratings'] = ProgressBar()
        self['ratings'].hide()
        self['ddd'] = Pixmap()
        self['ddd'].hide()
        self['ddd2'] = Pixmap()
        self['ddd2'].hide()
        self['seen'] = Pixmap()
        self['seen'].hide()
        self['ratingsback'] = Pixmap()
        self['ratingsback'].hide()
        # self['metrixback'] = Pixmap()
        # self['metrixback2'] = Pixmap()
        # self['metrixback2'].hide()
        self['menu'] = Pixmap()
        self['info'] = Pixmap()
        self['help'] = Pixmap()
        self['pvr'] = Pixmap()
        self['text'] = Pixmap()
        self['yellow'] = Pixmap()
        self['red'] = Pixmap()
        self['green'] = Pixmap()
        self['backdrop'] = Pixmap()
        self.oldbackdropurl = ''
        self.backdrops = config.plugins.moviebrowser.backdrops.getValue()
        if content == ':::Series:Top:::':
            self.episodes = True
        else:
            self.episodes = False
        self.control = False
        self.toggleCount = 0
        self['plotname'] = Label()
        self['plotfull'] = ScrollLabel()
        self['plotfull'].hide()
        self['poster'] = Pixmap()
        self['posterback'] = Pixmap()
        self['eposter'] = Pixmap()
        self['eposter'].hide()
        self['banner'] = Pixmap()
        self['banner'].hide()
        self['label'] = Label()
        self['label2'] = Label()
        self['label3'] = Label()
        self['list'] = ItemList([])
        self['episodes'] = ItemList([])
        self['episodes'].hide()
        self['seasons'] = MenuList([])
        self['seasons'].hide()
        self['audiotype'] = MultiPixmap()
        self['videomode'] = MultiPixmap()
        self['videocodec'] = MultiPixmap()
        self['aspectratio'] = MultiPixmap()
        self['actions'] = ActionMap([
            'OkCancelActions',
            'DirectionActions',
            'ColorActions',
            'ChannelSelectBaseActions',
            'HelpActions',
            'InfobarActions',
            'InfobarTeletextActions',
            'MovieSelectionActions',
            'MoviePlayerActions',
            'InfobarEPGActions',
            'NumberActions'
        ], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.up,
            'prevBouquet': self.down,
            'nextMarker': self.gotoABC,
            'prevMarker': self.gotoXYZ,
            'red': self.switchStyle,
            'yellow': self.updateDatabase,
            'blue': self.hideScreen,
            'green': self.showHelp,
            'contextMenu': self.config,
            'showEventInfo': self.toggleInfo,
            'EPGPressed': self.toggleInfo,
            'startTeletext': self.editDatabase,
            'showMovies': self.updateDatabase,
            'showRadio': self.deleteMovie,
            'leavePlayer': self.markSeen,
            '1': self.controlMovies,
            '2': self.renewTMDb,
            '3': self.renewTVDb,
            '4': self.filterSeen,
            '5': self.toogleContent,
            '6': self.filterFolder,
            '7': self.filterDirector,
            '8': self.filterActor,
            '9': self.filterGenre,
            '0': self.gotoEnd,
            'bluelong': self.showHelp,
            'displayHelp': self.showHelp
        }, -1)

        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        # BLACKLIST_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        # self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        # self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(DATABASE_PATH):
            size = getsize(DATABASE_PATH)
            if size < 10:
                remove(DATABASE_PATH)

        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)

        self['posterback'].hide()
        self['yellow'].hide()
        self['red'].hide()
        self['green'].hide()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
            self.session.nav.stopService()

        if fileExists(DATABASE_PATH):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value is True:
                    self.filter = open(FILTER_PATH).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(LAST_PATH).read()
                    if movie.endswith('...'):
                        self.index = -1
                    else:
                        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                        data = open(DATABASE_PATH).read()
                        count = 0
                        for line in data.split('\n'):
                            if self.content in line and self.filter in line:
                                if search(movie, line) is not None:
                                    self.index = count
                                    break
                                count += 1
                elif config.plugins.moviebrowser.lastmovie.value == 'folder' and self.showfolder is True:
                    self.index = -1
            self.makeMovieBrowserTimer = eTimer()
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)
        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(self.reset_return, MessageBox, 'The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?', MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(DATABASE_RESET, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.close, movieBrowserConfig)
        else:
            OnclearMem()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(DATABASE_RESET):
                remove(DATABASE_RESET)
            if fileExists(BLACKLIST_PATH):
                remove(BLACKLIST_PATH)
            open(DATABASE_PATH, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            self.close()

    def makeMovies(self, filter):
        if filter is not None:
            self.namelist = []
            self.movielist = []
            self.datelist = []
            self.infolist = []
            self.plotlist = []
            self.posterlist = []
            self.backdroplist = []
            self.contentlist = []
            self.seenlist = []
            self.medialist = []
            self.dddlist = []
            self.filter = filter
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        if self.content in line and filter in line:
                            name = ""
                            filename = ""
                            date = ""
                            runtime = ""
                            rating = ""
                            director = ""
                            actors = ""
                            genres = ""
                            year = ""
                            country = ""
                            plotfull = ""
                            poster = str(default_poster)
                            backdrop = str(default_backdrop)
                            seen = 'unseen'
                            content = 'Movie:Top'
                            media = '\n'
                            movieline = line.split(':::')
                            try:
                                name = movieline[0]
                                name = sub(r'[Ss][0]+[Ee]', 'Special ', name)
                                filename = movieline[1]
                                date = movieline[2]
                                runtime = movieline[3]
                                rating = movieline[4]
                                director = movieline[5]
                                actors = movieline[6]
                                genres = movieline[7]
                                year = movieline[8]
                                country = movieline[9]
                                plotfull = movieline[10]
                                poster = movieline[11]
                                backdrop = movieline[12]
                                content = movieline[13]
                                seen = movieline[14]
                                media = movieline[15]
                            except IndexError:
                                pass
                            self.namelist.append(name)
                            self.movielist.append(filename)
                            self.dddlist.append('yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director, actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)
                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(config.plugins.moviebrowser.moviefolder.value + '...')
                    self.datelist.append('')
                    res = []
                    res.append('')
                    res.append('0.0')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    self.infolist.append(res)
                    self.plotlist.append('')
                    self.posterlist.append(str(default_folder))
                    self.backdroplist.append(str(default_backdrop))
                    self.contentlist.append(':Top')
                    self.seenlist.append('unseen')
                    self.medialist.append('\n')
                self.maxentry = len(self.namelist)
                self.makeList()
                if self.backdrops != 'hide':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass

                else:
                    self.showDefaultBackdrop()
                self.ready = True
        OnclearMem()
        return

    def makeList(self):
        movies = []
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if self.content in line and self.filter in line:
                    movieline = line.split(":::")
                    try:
                        res = [""]
                        if self.content == ":::Series:::":
                            movie = sub(".*? - \\(", "", movieline[0])
                            movie = sub("\\) ", " ", movie)
                            movie = sub("S00E00 - ", "", movie)
                            movie = sub("[Ss][0]+[Ee]", "Special ", movie)
                        else:
                            movie = movieline[0]

                        if screenwidth.width() == 1920:
                            size = (810, 50)
                            font = 30
                            pos = (10, 0)
                        else:
                            size = (540, 40)
                            font = 26
                            pos = (5, 0)

                        kwargs = {
                            "pos": pos,
                            "size": size,
                            "font": font,
                            "color": 16777215,
                            "color_sel": 16777215,
                            "flags": RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            "text": movie
                        }

                        if self.backcolor is True:
                            kwargs["backcolor_sel"] = self.back_color

                        res.append(MultiContentEntryText(**kwargs))
                        movies.append(res)
                    except IndexError:
                        pass

        if self.content == ':::Series:::':
            movies.sort()
        if self.showfolder is True:
            res = ['']
            if screenwidth.width() == 1920:
                if self.backcolor is True:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(810, 50), font=30, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
                else:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(810, 50), font=30, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            else:
                if self.backcolor is True:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
                else:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            movies.append(res)
        self['list'].l.setList(movies)
        try:
            self['list'].moveToIndex(self.index)
        except IndexError:
            pass

        try:
            content = self.contentlist[self.index]
            if self.toggleCount == 0:
                if content == 'Series:Top':
                    self.hideInfo()
                    self.makeEpisodes()
                    if self.back is True:
                        self.back = False
                        self['list'].selectionEnabled(0)
                        self['episodes'].selectionEnabled(1)
                        self.control = True
                else:
                    self.hideEpisodes()
                    self.makePoster()
                    self.makeName(self.index)
                    self.makeInfo(self.index)
            else:
                if content != 'Series':
                    self.makePoster()
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                else:
                    self.makeName(self.index)
                    self.hideInfo()
                    self.makeEPoster()
                plot = self.plotlist[self.index]
                self['plotfull'].setText(plot)
                self.showPlot()
        except IndexError:
            pass

        self.ready = True
        self.totalMovies = len(movies)
        self.totalItem = len(movies)
        if self.showfolder is True:
            self.totalMovies -= 1
        free = _('Free Space')
        folder = _('Movie Folder')
        movies = _('MOVIES')
        series = _('SERIES')
        episodes = _('EPISODES')
        if exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = statvfs(config.plugins.moviebrowser.moviefolder.value)
            try:
                stat = movieFolder
                freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
            except Exception as e:
                print(e)
                freeSize = "-?-"

            if self.content == ':::Movie:Top:::':
                titel = '%s %s' % (str(self.totalMovies), movies)
                titel2 = '(%s: %s %s)' % (folder, str(freeSize), free)
            elif self.content == ':::Series:Top:::':
                titel = '%s %s' % (str(self.totalMovies), series)
                titel2 = '(%s: %s %s)' % (folder, str(freeSize), free)
            elif self.content == ':::Series:::':
                titel = '%s %s' % (str(self.totalMovies), episodes)
                titel2 = '(%s: %s %s)' % (folder, str(freeSize), free)
            else:
                titel = '%s %s & %s' % (str(self.totalMovies), movies, series)
                titel2 = '(%s: %s %s)' % (folder, str(freeSize), free)
            self['label'].setText(titel)
            self['label2'].setText(titel2)
            self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
        else:
            if self.content == ':::Movie:Top:::':
                titel = '%s %s' % (str(self.totalMovies), movies)
                titel2 = '(%s offline)' % folder
            elif self.content == ':::Series:Top:::':
                titel = '%s %s' % (str(self.totalMovies), series)
                titel2 = '(%s offline)' % folder
            elif self.content == ':::Series:::':
                titel = '%s %s' % (str(self.totalMovies), episodes)
                titel2 = '(%s offline)' % folder
            else:
                titel = '%s %s & %s' % (str(self.totalMovies), movies, series)
                titel2 = '(%s offline)' % folder
            self['label'].setText(titel)
            self['label2'].setText(titel2)
            self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))

    def updateDatabase(self):
        if self.ready is True:
            if exists(config.plugins.moviebrowser.moviefolder.value) and exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, '\nUpdate Movie Browser Database?', MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, "w") as f:
                    f.write(movie)
            except IndexError:
                pass

            if fileExists(DATABASE_PATH):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)
        OnclearMem()

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value is True:
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()
        movie = open(LAST_PATH).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(DATABASE_PATH).read()
        count = 0
        self.index = 0
        for line in data.split('\n'):
            if self.content in line and self.filter in line:
                if search(movie, line) is not None:
                    self.index = count
                    break
                count += 1

        self.topseries = False
        self.toggleCount = 0
        if self.content == ':::Series:Top:::':
            self.episodes = True
        else:
            self.episodes = False
        self.control = False
        if self.startupdate is True:
            self.startupdate = False
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.') % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                else:
                    self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        OnclearMem()
        return

    def ok(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    if self.toggleCount == 1:
                        self.toggleCount = 0
                        self.hidePlot()
                        self.hideInfo()
                        self.makeEpisodes()
                        if len(self.seasons) != 0:
                            self['list'].selectionEnabled(0)
                            self['episodes'].selectionEnabled(1)
                            self.control = True
                    elif self.control is False and len(self.seasons) != 0:
                        self['list'].selectionEnabled(0)
                        self['episodes'].selectionEnabled(1)
                        self.control = True
                    elif len(self.seasons) != 0:
                        self.topseries = True
                        self.episodes = False
                        self.control = False
                        self.toggleCount = 0
                        self.hideEpisodes()
                        self.oldcontent = self.content
                        self.oldfilter = self.filter
                        self.topindex = self.index
                        self.index = 0
                        self.content = ':::Series:::'
                        current = self['seasons'].getCurrent()
                        if current is not None:
                            current = sub('Specials', '(S00', current)
                            current = sub('specials', '(s00', current)
                            current = sub('Season ', '(S', current)
                            current = sub('season ', '(s', current)
                        else:
                            current = self.namelist[self.index]
                        self.makeMovies(current)
                else:
                    filename = self.movielist[self.index]
                    if self.showfolder is True and filename.endswith('...'):
                        self.filterFolder()
                        return
                    if filename.endswith('.ts'):
                        if fileExists(filename):
                            sref = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(self.getMediaInfo)
                    self.makeMovieBrowserTimer.start(2000, True)
            except IndexError:
                pass

        return

    def getMediaInfo(self):
        service = self.session.nav.getCurrentService()
        if service is not None:
            audiotype = ''
            videomode = ''
            videocodec = ''
            aspectratio = ''
            audio = service.audioTracks()
            if audio:
                try:
                    audioTrack = audio.getCurrentTrack()
                    if audioTrack is not None:
                        info = audio.getTrackInfo(audioTrack)
                        description = info.getDescription()
                        if 'AC3+' in description or 'Dolby Digital+' in description:
                            audiotype = 'dolbyplus'
                        elif 'AC3' in description or 'AC-3' in description or 'Dolby Digital' in description:
                            audiotype = 'dolby'
                        elif 'DTS-HD' in description:
                            audiotype = 'dtshd'
                        elif 'DTS' in description:
                            audiotype = 'dts'
                        else:
                            audiotype = 'mp2'
                except OverflowError:
                    audiotype = 'mp2'

            info = service and service.info()
            if info:
                height = info and info.getInfo(iServiceInformation.sVideoHeight)
                if str(height) == '1080':
                    videomode = '1080'
                elif str(height) == '720':
                    videomode = '720'
                else:
                    videomode = '480'
                aspect = info and info.getInfo(iServiceInformation.sAspect)
                if aspect in (3, 4, 7, 8, 11, 12, 15, 16):
                    aspectratio = '16_9'
                else:
                    aspectratio = '4_3'
            filename = self.movielist[self.index]
            if filename.endswith('.iso') or filename.endswith('.ISO'):
                videocodec = 'dvd'
            elif filename.endswith('.flv'):
                videocodec = 'flv'
            elif filename.endswith('.divx'):
                videocodec = 'divx'
            elif videomode == '480':
                videocodec = 'mpeg2'
            else:
                videocodec = 'h264'
            media = audiotype + ':' + videomode + ':' + videocodec + ':' + aspectratio
            self.medialist[self.index] = media
            info = media.split(':')
            try:
                if info[0] == 'dolby':
                    self['audiotype'].setPixmapNum(0)
                elif info[0] == 'mp2':
                    self['audiotype'].setPixmapNum(4)
                elif info[0] == 'dts':
                    self['audiotype'].setPixmapNum(2)
                elif info[0] == 'dolbyplus':
                    self['audiotype'].setPixmapNum(1)
                else:
                    self['audiotype'].setPixmapNum(3)
            except IndexError:
                self['audiotype'].setPixmapNum(4)

            try:
                if info[1] == '1080':
                    self['videomode'].setPixmapNum(0)
                elif info[1] == '720':
                    self['videomode'].setPixmapNum(1)
                else:
                    self['videomode'].setPixmapNum(2)
            except IndexError:
                self['videomode'].setPixmapNum(2)

            try:
                if info[2] == 'h264':
                    self['videocodec'].setPixmapNum(0)
                elif info[2] == 'mpeg2':
                    self['videocodec'].setPixmapNum(1)
                elif info[2] == 'divx':
                    self['videocodec'].setPixmapNum(2)
                elif info[2] == 'flv':
                    self['videocodec'].setPixmapNum(3)
                else:
                    self['videocodec'].setPixmapNum(4)
            except IndexError:
                self['videocodec'].setPixmapNum(1)

            try:
                if info[3] == '16_9':
                    self['aspectratio'].setPixmapNum(0)
                else:
                    self['aspectratio'].setPixmapNum(1)
            except IndexError:
                self['aspectratio'].setPixmapNum(1)

            self['audiotype'].show()
            self['videomode'].show()
            self['videocodec'].show()
            self['aspectratio'].show()
            if '3d' in filename.lower():
                self['ddd'].hide()
                self['ddd2'].show()
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            f = open(DATABASE_PATH + '.new', 'w')
            f.write(database)
            f.close()
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, _('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (str(tmdb_api), name, self.language)
                print('url tmdb=', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        try:
            output = fetch_url(url)
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")
        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w185', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = findall('"vote_average":(.*?),', output)
        year = findall('"release_date":"(.*?)"', output)
        titles = findall('"title":"(.*?)"', output)
        poster = findall('"poster_path":"(.*?)"', output)
        id = findall('"id":(.*?),', output)
        country = findall('"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            print("newwwwwwwwww ", new)
            if select == "movie":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = "https://api.themoviedb.org/3/movie/%s?api_key=%s" % (new + self.language, str(tmdb_api))
                print("url sls ", url)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select in ("poster", "backdrop"):
                if select == "poster":
                    old = self.posterlist[self.index]
                else:
                    old = self.backdroplist[self.index]
                new_val = new

                with open(DATABASE_PATH, "r") as f:
                    database = f.read()

                database = database.replace(old, new_val)

                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(database)

                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                # self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (name, self.language)
                print('renewTVDb url tmdb=', url)
                self.getTVDbMovies(url)
            except IndexError:
                pass

    def getTVDbMovies(self, url):
        rating = []
        year = []
        titles = []
        poster = []
        id = []
        country = []
        try:
            output = fetch_url(url)
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")
        # Extract series IDs
        seriesid = findall('<seriesid>(.*?)</seriesid>', output)

        for x in range(len(seriesid)):
            url = ('https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
            print('getTVDbMovies url=', url)
            output = fetch_url(url)
            # Fix poster URL base path
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            output = output.decode("utf-8", "ignore")

            output = sub('<poster>', '<poster>https://artworks.thetvdb.com/banners/_cache/', output)

            # Rebuild URL (looks redundant, but kept to match original code)
            url = ('https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)

            # Replace empty ratings with default 0.0
            output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
            output = output.replace('&amp;', '&')

            Rating = findall('<Rating>(.*?)</Rating>', output)
            Year = findall('<FirstAired>([0-9]+)-', output)
            Added = findall('<added>([0-9]+)-', output)
            Titles = findall('<SeriesName>(.*?)</SeriesName>', output)
            Poster = findall('<poster>(.*?)</poster>', output)
            TVDbid = findall('<id>(.*?)</id>', output)
            Country = findall('<Status>(.*?)</Status>', output)

            try:
                rating.append(Rating[0])
            except IndexError:
                rating.append('0.0')

            try:
                year.append(Year[0])
            except IndexError:
                try:
                    year.append(Added[0])
                except IndexError:
                    year.append(' ')

            try:
                titles.append(Titles[0])
            except IndexError:
                titles.append(' ')

            try:
                poster.append(Poster[0])
            except IndexError:
                poster.append(wiki_png)  # fallback poster image

            try:
                id.append(TVDbid[0])
            except IndexError:
                id.append('0')

            try:
                country.append(Country[0])
            except IndexError:
                country.append(' ')

        titel = _('TheTVDb Results')

        if not titles:
            self.session.open(MessageBox, _('\nNo TheTVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, True)
            else:
                self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, False)

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == "series":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ("https://www.thetvdb.com/api/%s/series/" + new + "/" + config.plugins.moviebrowser.language.value + ".xml") % str(thetvdb_api)
                print("makeTVDbUpdate url=", url)
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == "banner":
                banner = self.posterlist[self.index].split("<episode>")
                try:
                    banner = banner[1]
                except IndexError:
                    return

                bannernew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(banner, bannernew)
                f = open(DATABASE_PATH + ".new", "w")
                f.write(database)
                f.close()
                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            elif select == "backdrop":
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                f = open(DATABASE_PATH + ".new", "w")
                f.write(database)
                f.close()
                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.renewFinished()
        return

    def renewFinished(self):
        self.topseries = False
        self.toggleCount = 0
        if self.content == ':::Series:Top:::':
            self.episodes = True
        else:
            self.episodes = False
        self.control = False
        self.renew = False
        self.makeMovies(self.filter)

    def deleteMovie(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                    self.session.open(MessageBox, _('\nThe List of Movie Folder can not be deleted.'), MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def delete_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if fileExists(movie):
                    remove(movie)
                movie = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
                if search("[.]ts", movie) is not None:
                    eitfile = sub("[.]ts", ".eit", movie)
                    if fileExists(eitfile):
                        remove(eitfile)
                    if fileExists(movie + ".ap"):
                        remove(movie + ".ap")
                    if fileExists(movie + ".cuts"):
                        remove(movie + ".cuts")
                    if fileExists(movie + ".meta"):
                        remove(movie + ".meta")
                    if fileExists(movie + ".sc"):
                        remove(movie + ".sc")
                    if fileExists(movie + "_mp.jpg"):
                        remove(movie + "_mp.jpg")
                else:
                    subfile = sub(movie[-4:], ".sub", movie)
                    if fileExists(subfile):
                        remove(subfile)
                    srtfile = sub(movie[-4:], ".srt", movie)
                    if fileExists(srtfile):
                        remove(srtfile)
                data = open(DATABASE_PATH).read()
                if content == "Series:Top":
                    for line in data.split("\n"):
                        if search(movie + ".*?:::Series:", line) is not None:
                            data = data.replace(line + "\n", "")
                else:
                    for line in data.split("\n"):
                        if search(movie, line) is not None:
                            data = data.replace(line + "\n", "")

                name = name + "FIN"
                name = sub(" - [(][Ss][0-9]+[Ee][0-9]+.*?FIN", "", name)
                name = sub("FIN", "", name)
                episode = name + " - .*?:::Series:::"
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split("\n"):
                        if search(name, line) is not None and search(":::Series:Top:::", line) is not None:
                            data = data.replace(line + "\n", "")

                f = open(DATABASE_PATH, "w")
                f.write(data)
                f.close()
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            except IndexError:
                pass

            self.ready = True
        else:
            self.blacklistMovie()
        return

    def blacklistMovie(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            try:
                name = self.namelist[self.index]
                self.session.openWithCallback(self.blacklist_return, MessageBox, _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                movie = sub(r"\(|\)|\[|\]|\+|\?", ".", movie)

                mode = "a" if fileExists(BLACKLIST_PATH) else "w"
                with open(BLACKLIST_PATH, mode) as fremove, open(DATABASE_PATH, "r") as fdb:
                    data = fdb.read()
                    lines = data.split("\n")

                    new_lines = []
                    for line in lines:
                        if search(movie, line) is not None:
                            fremove.write(line + "\n")
                        else:
                            new_lines.append(line)

                    data = "\n".join(new_lines)

                name = name + "FIN"
                name = sub(r" - [(][Ss][0-9]+[Ee][0-9]+.*?FIN", "", name)
                name = sub(r"FIN", "", name)

                episode = name + " - .*?:::Series:::"
                if search(episode, data) is None and search(name, data) is not None:
                    lines = data.split("\n")
                    data_lines = []
                    for line in lines:
                        if not (search(name, line) and search(":::Series:Top:::", line)):
                            data_lines.append(line)
                    data = "\n".join(data_lines)

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)

                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)

            except IndexError:
                pass

            self.ready = True
        return

    def markSeen(self):
        if self.ready is True and self.content != ":::Series:Top:::":
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub(r"\(|\)|\[|\]|\+|\?", ".", movie)

            with open(DATABASE_PATH, "r") as f:
                database = f.read()

            lines = database.split("\n")
            updated = False

            for i, line in enumerate(lines):
                if search(movie, line) is not None:
                    if search(":::unseen:::", line) is not None:
                        newline = line.replace(":::unseen:::", ":::seen:::")
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, "seen")
                        self["seen"].show()
                    else:
                        newline = line.replace(":::seen:::", ":::unseen:::")
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, "unseen")
                        self["seen"].hide()
                    lines[i] = newline
                    updated = True

            if updated:
                new_database = "\n".join(lines)
                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(new_database)
                rename(DATABASE_PATH + ".new", DATABASE_PATH)

            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ":::Series:Top:::":
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub(r"\(|\)|\[|\]|\+|\?", ".", movie)
            with open(DATABASE_PATH, "r") as f:
                database = f.read()

            lines = database.split("\n")
            updated = False

            for i, line in enumerate(lines):
                if search(movie, line) is not None:
                    if search(":::unseen:::", line) is not None:
                        newline = line.replace(":::unseen:::", ":::seen:::")
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, "seen")
                        self["seen"].show()
                        lines[i] = newline
                        updated = True

            if updated:
                new_database = "\n".join(lines)
                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(new_database)
                rename(DATABASE_PATH + ".new", DATABASE_PATH)

            self.ready = True
        return

    def toggleInfo(self):
        if self.ready is True:
            if self.toggleCount == 0:
                self.toggleCount = 1
                self.showPlot()
                content = self.contentlist[self.index]
                if self.backdrops == 'info':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass

                if content == 'Series:Top':
                    self.hideEpisodes()
                    try:
                        self.makePoster()
                        self.makeName(self.index)
                        self.makeInfo(self.index)
                    except IndexError:
                        self.showInfo()

                elif content == 'Series':
                    self.hideInfo()
                    self.makeEPoster()
                try:
                    plot = self.plotlist[self.index]
                    self['plotfull'].setText(plot)
                except IndexError:
                    pass

            elif self.toggleCount == 1:
                self.toggleCount = 0
                self.hidePlot()
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.hideInfo()
                    self.makeEpisodes()
                elif content == 'Series':
                    self['eposter'].hide()
                    try:
                        self.makePoster()
                        self.makeName(self.index)
                        self.makeInfo(self.index)
                    except IndexError:
                        self.showInfo()

    def showPlot(self):
        # self['list'].hide()
        # self['label'].hide()
        # self['label2'].hide()
        # self['label3'].hide()
        self['help'].hide()
        self['pvr'].hide()
        self['text'].hide()
        self['plotfull'].show()
        self['plotname'].show()
        self['yellow'].show()
        self['green'].show()
        self['red'].show()
        self['text1'].setText('Update')
        self['text2'].setText('Style')
        self['text3'].setText('Help')

    def showInfo(self):
        self['poster'].show()
        self['posterback'].show()
        self['name'].show()
        self['ratings'].show()
        self['ratingsback'].show()
        self['Director'].show()
        self['director'].show()
        self['Country'].show()
        self['country'].show()
        self['Actors'].show()
        self['actors'].show()
        self['Year'].show()
        self['year'].show()
        self['Runtime'].show()
        self['runtime'].show()
        self['Genres'].show()
        self['genres'].show()

    def hidePlot(self):
        self['plotname'].hide()
        self['plotfull'].hide()
        self['yellow'].hide()
        self['green'].hide()
        self['red'].hide()
        self['list'].show()
        self['label'].show()
        self['label2'].show()
        self['label3'].show()
        self['help'].show()
        self['pvr'].show()
        self['text'].show()
        self['text1'].setText('Update')
        self['text2'].setText('Style')
        self['text3'].setText('Help')

    def hideInfo(self):
        self['poster'].hide()
        self['posterback'].hide()
        self['seen'].hide()
        self['name'].hide()
        self['ratings'].hide()
        self['ratingsback'].hide()
        self['Director'].hide()
        self['director'].hide()
        self['Country'].hide()
        self['country'].hide()
        self['Actors'].hide()
        self['actors'].hide()
        self['Year'].hide()
        self['year'].hide()
        self['Runtime'].hide()
        self['runtime'].hide()
        self['Genres'].hide()
        self['genres'].hide()

    def hideEpisodes(self):
        self.control = False
        self['banner'].hide()
        self['episodes'].hide()
        self['episodes'].selectionEnabled(0)
        self['list'].selectionEnabled(1)

    def makeName(self, count):
        try:
            name = self.namelist[count]
            if len(name) > 63:
                if name[62:63] == ' ':
                    name = name[0:62]
                else:
                    name = name[0:63] + 'FIN'
                    name = sub(' \\S+FIN', '', name)
                name = name + ' ...'
            self['name'].setText(str(name))
            self['name'].show()
            self.setTitle(str(name))
            if self.content == ':::Series:::':
                name = sub('.*? - \\(', '', name)
                name = sub('\\) ', ' ', name)
                name = sub('S00E00 - ', '', name)
            if len(name) > 50:
                if name[49:50] == ' ':
                    name = name[0:49]
                else:
                    name = name[0:50] + 'FIN'
                    name = sub(' \\S+FIN', '', name)
                name = name + ' ...'
            self['plotname'].setText(name)
            self['plotname'].hide()
        except IndexError:
            self['name'].hide()

        try:
            seen = self.seenlist[count]
            if seen == 'seen':
                self['seen'].show()
            else:
                self['seen'].hide()
        except IndexError:
            self['seen'].hide()

    def makeInfo(self, count):
        try:
            runtime = self.infolist[count][0]
            if self.showfolder is True and runtime == '':
                self['Runtime'].hide()
                self['runtime'].hide()
                self['ratings'].hide()
                self['ratingsback'].hide()
                self['Director'].hide()
                self['director'].hide()
                self['Actors'].hide()
                self['actors'].hide()
                self['Genres'].hide()
                self['genres'].hide()
                self['Year'].hide()
                self['year'].hide()
                self['Country'].hide()
                self['country'].hide()
                self['ddd'].hide()
                self['ddd2'].hide()
                self['audiotype'].hide()
                self['videomode'].hide()
                self['videocodec'].hide()
                self['aspectratio'].hide()
                return
            self['Runtime'].show()
            self['runtime'].setText(runtime)
            self['runtime'].show()
        except IndexError:
            self['Runtime'].hide()
            self['runtime'].hide()

        try:
            ratings = self.infolist[count][1]
            try:
                rating = int(10 * round(float(ratings), 1))
            except ValueError:
                ratings = '0.0'
                rating = int(10 * round(float(ratings), 1))

            self['ratings'].setValue(rating)
            self['ratings'].show()
            self['ratingsback'].show()
        except IndexError:
            self['ratings'].hide()

        try:
            director = self.infolist[count][2]
            self['Director'].show()
            self['director'].setText(director)
            self['director'].show()
        except IndexError:
            self['Director'].hide()
            self['director'].hide()

        try:
            actors = self.infolist[count][3]
            self['Actors'].show()
            self['actors'].setText(actors)
            self['actors'].show()
        except IndexError:
            self['Actors'].hide()
            self['actors'].hide()

        try:
            genres = self.infolist[count][4]
            self['Genres'].show()
            self['genres'].setText(genres)
            self['genres'].show()
        except IndexError:
            self['Genres'].hide()
            self['genres'].hide()

        try:
            year = self.infolist[count][5]
            self['Year'].show()
            self['year'].setText(year)
            self['year'].show()
        except IndexError:
            self['Year'].hide()
            self['year'].hide()

        try:
            country = self.infolist[count][6]
            self['Country'].show()
            self['country'].setText(country)
            self['country'].show()
        except IndexError:
            self['Country'].hide()
            self['country'].hide()

        ddd = self.dddlist[self.index]
        media = self.medialist[self.index]
        if media != '\n':
            info = media.split(':')
            try:
                if info[0] == 'dolby':
                    self['audiotype'].setPixmapNum(0)
                elif info[0] == 'mp2':
                    self['audiotype'].setPixmapNum(4)
                elif info[0] == 'dts':
                    self['audiotype'].setPixmapNum(2)
                elif info[0] == 'dolbyplus':
                    self['audiotype'].setPixmapNum(1)
                else:
                    self['audiotype'].setPixmapNum(3)
            except IndexError:
                self['audiotype'].setPixmapNum(4)

            try:
                if info[1] == '1080':
                    self['videomode'].setPixmapNum(0)
                elif info[1] == '720':
                    self['videomode'].setPixmapNum(1)
                else:
                    self['videomode'].setPixmapNum(2)
            except IndexError:
                self['videomode'].setPixmapNum(2)

            try:
                if info[2] == 'h264':
                    self['videocodec'].setPixmapNum(0)
                elif info[2] == 'mpeg2':
                    self['videocodec'].setPixmapNum(1)
                elif info[2] == 'divx':
                    self['videocodec'].setPixmapNum(2)
                elif info[2] == 'flv':
                    self['videocodec'].setPixmapNum(3)
                else:
                    self['videocodec'].setPixmapNum(4)
            except IndexError:
                self['videocodec'].setPixmapNum(1)

            try:
                if info[3] == '16_9':
                    self['aspectratio'].setPixmapNum(0)
                else:
                    self['aspectratio'].setPixmapNum(1)
            except IndexError:
                self['aspectratio'].setPixmapNum(1)

            self['audiotype'].show()
            self['videomode'].show()
            self['videocodec'].show()
            self['aspectratio'].show()
            if ddd == 'yes':
                self['ddd'].hide()
                self['ddd2'].show()
            else:
                self['ddd'].hide()
                self['ddd2'].hide()
        else:
            if ddd == 'yes':
                self['ddd'].show()
                self['ddd2'].hide()
            else:
                self['ddd'].hide()
                self['ddd2'].hide()
            self['audiotype'].hide()
            self['videomode'].hide()
            self['videocodec'].hide()
            self['aspectratio'].hide()

    def makeEpisodes(self):
        try:
            posterurl = self.posterlist[self.index]
            if search('<episode>', posterurl) is not None:
                bannerurl = search('<episode>(.*?)<episode>', posterurl)
                bannerurl = bannerurl.group(1)
                banner = sub('.*?[/]', '', bannerurl)
                banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                if fileExists(banner):
                    self["banner"].instance.setPixmapFromFile(banner)
                    self['banner'].show()
                else:
                    if PY3:
                        bannerurl = bannerurl.encode()
                    callInThread(threadGetPage, url=bannerurl, file=banner, key=None, success=self.getBanner, fail=self.downloadError)
            else:
                self['banner'].hide()
        except IndexError:
            pass

        self.episodes = True
        self.filterSeasons()
        self['ddd'].hide()
        self['ddd2'].hide()
        self['audiotype'].hide()
        self['videomode'].hide()
        self['videocodec'].hide()
        self['aspectratio'].hide()
        return

    def getBanner(self, output, banner):
        try:
            open(banner, 'wb').write(output)
            if fileExists(banner):
                self["banner"].instance.setPixmapFromFile(banner)
                self['banner'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
            self['banner'].hide()
        return

    def makeEPoster(self):
        try:
            posterurl = self.posterlist[self.index]
            if search('<episode>', posterurl) is not None:
                eposterurl = search('<episode>(.*?)<episode>', posterurl)
                eposterurl = eposterurl.group(1)
                eposter = sub('.*?[/]', '', eposterurl)
                eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                if fileExists(eposter):
                    self["eposter"].instance.setPixmapFromFile(eposter)
                    self['eposter'].show()
                else:
                    if PY3:
                        eposterurl = eposterurl.encode()
                    callInThread(threadGetPage, url=eposterurl, file=eposter, key=None, success=self.getEPoster, fail=self.downloadError)
        except IndexError:
            pass

        return

    def getEPoster(self, output, eposter):
        try:
            open(eposter, 'wb').write(output)
            if fileExists(eposter):
                self["eposter"].instance.setPixmapFromFile(eposter)
                self['eposter'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
            self['eposter'].hide()
        return

    def makePoster(self, poster=None):
        try:
            posterurl = self.posterlist[self.index]
            posterurl = sub('<episode>.*?<episode>', '', posterurl)
            poster = sub('.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                self["poster"].instance.setPixmapFromFile(poster)
                self['posterback'].show()
                self['poster'].show()
            else:
                if PY3:
                    posterurl = posterurl.encode()
                callInThread(threadGetPage, url=posterurl, file=poster, key=None, success=self.getPoster, fail=self.downloadError)
        except IndexError:
            self['posterback'].hide()
            self['poster'].hide()

        return

    def getPoster(self, output, poster):
        try:
            open(poster, 'wb').write(output)
            self['posterback'].show()
            self["poster"].instance.setPixmapFromFile(poster)
            self['poster'].show()
        except Exception as e:
            print('error ', str(e))
            self['posterback'].hide()
            self['poster'].hide()
        return

    def showBackdrops(self, index):
        try:
            backdropurl = self.backdroplist[index]
            if backdropurl != self.oldbackdropurl:
                self.oldbackdropurl = backdropurl
                backdrop = sub('.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        if PY3:
                            backdropurl = backdropurl.encode()
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        popen('/usr/bin/showiframe %s') % no_m1v
                elif fileExists(backdrop):
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
                else:
                    if PY3:
                        backdropurl = backdropurl.encode()
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            open(backdrop, 'wb').write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        backdrop = default_backdrop  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = default_backdropm1v  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def _update_display(self):
        self['label3'].setText("Item %s/%s" % (str(self.index + 1), str(self.totalItem)))
        try:
            if self.backdrops == "auto":
                self.showBackdrops(self.index)
            content = self.contentlist[self.index]
            if self.toggleCount == 0:
                if content == "Series:Top":
                    self.hideInfo()
                    self.makeEpisodes()
                else:
                    self.hideEpisodes()
                    self.makePoster()
                    self.makeName(self.index)
                    self.makeInfo(self.index)
            else:
                if content != "Series":
                    self.makePoster()
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                else:
                    self.makeName(self.index)
                    self.hideInfo()
                    self.makeEPoster()
                plot = self.plotlist[self.index]
                self['plotfull'].setText(plot)
                self.showPlot()
        except IndexError:
            pass

    def down(self):
        if not self.ready:
            return
        if self.control:
            self['episodes'].down()
            self['seasons'].down()
        else:
            self['list'].down()
            self.index = self['list'].getSelectedIndex()
            self._update_display()

    def up(self):
        if not self.ready:
            return
        if self.control:
            self['episodes'].up()
            self['seasons'].up()
        else:
            self['list'].up()
            self.index = self['list'].getSelectedIndex()
            self._update_display()

    def rightDown(self):
        if not self.ready:
            return
        if self.toggleCount == 1:
            self['plotfull'].pageDown()
            return

        content = self.contentlist[self.index]
        self.episodes = content == "Series:Top"

        if not self.control and self.episodes:
            self['list'].selectionEnabled(0)
            self['episodes'].selectionEnabled(1)
            self.control = True
        elif self.control:
            self['episodes'].pageDown()
            index = self['episodes'].getSelectedIndex()
            self['seasons'].moveToIndex(index)
        else:
            self['list'].pageDown()
            self.index = self['list'].getSelectedIndex()
            self._update_display()

    def leftUp(self):
        if not self.ready:
            return
        if self.toggleCount == 1:
            self['plotfull'].pageUp()
            return
        if self.control:
            self['episodes'].selectionEnabled(0)
            self['list'].selectionEnabled(1)
            self.control = False
        else:
            self['list'].pageUp()
            self.index = self['list'].getSelectedIndex()
            self._update_display()

    def gotoEnd(self):
        if not self.ready:
            return
        self.index = self.maxentry - 1
        self['list'].moveToIndex(self.index)
        self['list'].selectionEnabled(1)
        self['episodes'].selectionEnabled(0)
        self.control = False
        self._update_display()

    def controlMovies(self):
        if self.ready is True:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.open(MessageBox, _('Series Folder: No Info possible'), MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, "r") as f:
                    for line in f:
                        if self.content in line and self.filter in line:
                            movieline = line.split(":::")
                            try:
                                self.movies.append((movieline[0], movieline[1], movieline[12]))
                            except IndexError:
                                pass

                if self.showfolder is True:
                    self.movies.append((_("<List of Movie Folder>"), config.plugins.moviebrowser.moviefolder.value + "...", str(default_backdrop)))

                self.session.openWithCallback(self.gotoMovie, movieControlList, self.movies, self.index, self.content)

    def gotoMovie(self, index, rebuild):
        if index is not None:
            self.index = index
            if rebuild is True:
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            else:
                self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                try:
                    self['list'].moveToIndex(self.index)
                    self['list'].selectionEnabled(1)
                    self['episodes'].selectionEnabled(0)
                    self.control = False
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    content = self.contentlist[self.index]
                    if self.toggleCount == 0:
                        if content == 'Series:Top':
                            self.hideInfo()
                            self.makeEpisodes()
                        else:
                            self.hideEpisodes()
                            self.makePoster()
                            self.makeName(self.index)
                            self.makeInfo(self.index)
                    else:
                        if content != 'Series':
                            self.makePoster()
                            self.makeName(self.index)
                            self.makeInfo(self.index)
                        else:
                            self.makeName(self.index)
                            self.hideInfo()
                            self.makeEPoster()
                        plot = self.plotlist[self.index]
                        self['plotfull'].setText(plot)
                        self.showPlot()
                except IndexError:
                    pass

        return

    def gotoABC(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, False)

    def gotoXYZ(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, True)

    def enterABC(self, ABC):
        if ABC is None:
            pass
        else:
            self.ABC = ABC
            ABC = ABC[0].lower()
            try:
                self.index = next((index for index, value in enumerate(self.namelist) if value.lower().replace('der ', '').replace('die ', '').replace('das ', '').replace('the ', '').startswith(ABC)))
                try:
                    self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                    self['list'].moveToIndex(self.index)
                    self['list'].selectionEnabled(1)
                    self['episodes'].selectionEnabled(0)
                    self.control = False
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    content = self.contentlist[self.index]
                    if self.toggleCount == 0:
                        if content == 'Series:Top':
                            self.hideInfo()
                            self.makeEpisodes()
                        else:
                            self.hideEpisodes()
                            self.makePoster()
                            self.makeName(self.index)
                            self.makeInfo(self.index)
                    else:
                        if content != 'Series':
                            self.makePoster()
                            self.makeName(self.index)
                            self.makeInfo(self.index)
                        else:
                            self.makeName(self.index)
                            self.hideInfo()
                            self.makeEPoster()
                        plot = self.plotlist[self.index]
                        self['plotfull'].setText(plot)
                        self.showPlot()
                except IndexError:
                    pass

            except StopIteration:
                pass

        return

    def filterSeen(self):
        if self.ready is True:
            if self.filterseen is False:
                self.filterseen = True
                self.filter = ':::unseen:::'
                self.index = 0
                self.toggleCount = 0
                self.makeMovies(self.filter)
            else:
                self.filterseen = False
                self.filter = self.content
                self.index = 0
                self.toggleCount = 0
                self.makeMovies(self.filter)

    def filterFolder(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _('Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            genres = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            genre = movieline[7]
                        except IndexError:
                            genre = ' '

                        if genre != ' ':
                            genres = genres + genre + ', '
                self.genres = [i for i in genres.split(', ')]
                self.genres.sort()
                self.genres.pop(0)
                try:
                    last = self.genres[-1]
                    for i in range(len(self.genres) - 2, -1, -1):
                        if last == self.genres[i]:
                            del self.genres[i]
                        else:
                            last = self.genres[i]
                            if len(last) > max:
                                max = len(last)

                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _('Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            actors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            actor = movieline[6]
                        except IndexError:
                            actor = ' '

                        if actor != ' ':
                            actors = actors + actor + ', '
                self.actors = [i for i in actors.split(', ')]
                self.actors.sort()
                self.actors.pop(0)
                try:
                    last = self.actors[-1]
                    for i in range(len(self.actors) - 2, -1, -1):
                        if last == self.actors[i]:
                            del self.actors[i]
                        else:
                            last = self.actors[i]
                            if len(last) > max:
                                max = len(last)
                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _('Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            directors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        if director != ' ':
                            directors = directors + director + ', '
                self.directors = [i for i in directors.split(', ')]
                self.directors.sort()
                self.directors.pop(0)
                try:
                    last = self.directors[-1]
                    for i in range(len(self.directors) - 2, -1, -1):
                        if last == self.directors[i]:
                            del self.directors[i]
                        else:
                            last = self.directors[i]
                            if len(last) > max:
                                max = len(last)
                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _('Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
                filter = sub('FIN', '', filter)
            content = ':::Series:::'
            seasons = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                for line in f:
                    if line.startswith(filter) and content in line:
                        movieline = line.split(':::')
                        try:
                            season = movieline[0]
                            season = season + 'FIN'
                            season = sub('[(]S00', 'Specials', season)
                            season = sub('[(]s00', 'specials', season)
                            season = sub('[(]S', 'Season ', season)
                            season = sub('[(]s', 'season ', season)
                            season = sub('[Ee][0-9]+[)].*?FIN', '', season)
                            season = sub('FIN', '', season)
                            season = sub(',', '', season)
                        except IndexError:
                            season = ' '
                        if season != ' ':
                            seasons = seasons + season + ', '
                self.seasons = [i for i in seasons.split(', ')]
                self.seasons.sort()
                self.seasons.pop(0)
                try:
                    last = self.seasons[-1]
                    for i in range(len(self.seasons) - 2, -1, -1):
                        if last == self.seasons[i]:
                            del self.seasons[i]
                        else:
                            last = self.seasons[i]

                except IndexError:
                    pass

                self['seasons'].l.setList(self.seasons)
            if self.episodes is True or self.content == ':::Series:::':
                self.hideInfo()
                list = []
                for i in range(len(self.seasons)):
                    res = ['']
                    if screenwidth.width() == 1920:
                        res.append(MultiContentEntryText(pos=(10, 0), size=(810, 40), font=30, flags=RT_HALIGN_LEFT, text=self.seasons[i]))
                    else:
                        res.append(MultiContentEntryText(pos=(5, 0), size=(540, 30), font=26, flags=RT_HALIGN_LEFT, text=self.seasons[i]))
                    list.append(res)

                self['episodes'].l.setList(list)
                self['episodes'].selectionEnabled(0)
                self['episodes'].show()
            else:
                self.session.openWithCallback(self.filter_return, filterSeasonList, self.seasons, self.content)

    def filter_return(self, filter):
        if filter and filter is not None:
            self.index = 0
            if screenwidth.width() >= 1280:
                self.posterindex = 6
            else:
                self.posterindex = 5
            self.makeMovies(filter)
        return

    def switchStyle(self):
        if self.ready is True:
            self.ready = False
            self.session.openWithCallback(self.returnStyle, switchScreen, 2, 'style')

    def returnStyle(self, number):
        if number is None or number == 1:
            self.ready = True
        elif number == 2:
            if config.plugins.moviebrowser.lastmovie.value == "yes":
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == "hide" or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserBackdrop, self.index, self.content, self.filter)

        elif number == 3:
            if config.plugins.moviebrowser.lastmovie.value == "yes":
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserPosterwall, self.index, self.content, self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(self.returnContent, switchScreen, 3, 'content')

    def returnContent(self, number):
        if number is None:
            self.ready = True
        elif number == 1 and self.content != ':::Movie:Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.filter = ':::Movie:Top:::'
                self.content = ':::Movie:Top:::'
                self.index = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.episodes = True
                else:
                    self.episodes = False
                self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Movie:Top:::', ':::Movie:Top:::')
        elif number == 2 and self.content != ':::Series:Top:::':
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.filter = ':::Series:Top:::'
                self.content = ':::Series:Top:::'
                self.index = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.episodes = True
                else:
                    self.episodes = False
                self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif number == 3 and self.content != ':Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.filter = '::Top:::'
                self.content = ':Top:::'
                self.index = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.episodes = True
                else:
                    self.episodes = False
                self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':Top:::', ':Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':Top:::', ':Top:::')
        else:
            self.ready = True
        return

    def editDatabase(self):
        if self.ready is True:
            try:
                movie = self.movielist[self.index]
            except IndexError:
                movie = 'None'
            self.session.openWithCallback(self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
            self.sortDatabase()
            count = 0
            with open(DATABASE_PATH, "r") as f:
                for line in f:
                    if self.content in line and self.filter in line:
                        if movie in line:
                            self.index = count
                            break
                        count += 1
            self.makeMovies(self.filter)

    def sortDatabase(self):
        series = ''
        with open(DATABASE_PATH, 'r') as f:
            for line in f:
                if ':::Series:::' in line:
                    series += line

        with open(DATABASE_PATH + '.series', 'w') as fseries:
            fseries.write(series)

        with open(DATABASE_PATH + '.series', 'r') as fseries:
            series_lines = fseries.readlines()

        series_lines.sort(key=lambda line: line.split(':::')[0])

        with open(DATABASE_PATH + '.series', 'w') as fseries:
            fseries.writelines(series_lines)

        movies = ''
        with open(DATABASE_PATH, 'r') as f:
            for line in f:
                if ':::Series:::' not in line:
                    movies += line

        with open(DATABASE_PATH + '.movies', 'w') as fmovies:
            fmovies.write(movies)

        with open(DATABASE_PATH + '.movies', 'r') as fmovies:
            lines = fmovies.readlines()

        self.sortorder = config.plugins.moviebrowser.sortorder.value
        try:
            if self.sortorder == 'name':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower())
            elif self.sortorder == 'name_reverse':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower(), reverse=True)
            elif self.sortorder == 'rating':
                lines.sort(key=lambda line: line.split(':::')[4])
            elif self.sortorder == 'rating_reverse':
                lines.sort(key=lambda line: line.split(':::')[4], reverse=True)
            elif self.sortorder == 'year':
                lines.sort(key=lambda line: line.split(':::')[8])
            elif self.sortorder == 'year_reverse':
                lines.sort(key=lambda line: line.split(':::')[8], reverse=True)
            elif self.sortorder == 'date':
                lines.sort(key=lambda line: line.split(':::')[2])
            elif self.sortorder == 'date_reverse':
                lines.sort(key=lambda line: line.split(':::')[2], reverse=True)
            elif self.sortorder == 'folder':
                lines.sort(key=lambda line: line.split(':::')[1])
            elif self.sortorder == 'folder_reverse':
                lines.sort(key=lambda line: line.split(':::')[1], reverse=True)
            elif self.sortorder == 'runtime':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')))
            elif self.sortorder == 'runtime_reverse':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')), reverse=True)
        except IndexError:
            pass
        except ValueError:
            self.session.open(MessageBox, _('\nDatabase Error: Entry without runtime'), MessageBox.TYPE_ERROR)

        with open(DATABASE_PATH + ".movies", "w") as f:
            f.writelines(lines)
        files = [DATABASE_PATH + '.movies', DATABASE_PATH + '.series']
        with open(DATABASE_PATH + '.sorted', 'w') as outfile:
            for name in files:
                with open(name, 'r') as infile:
                    outfile.write(infile.read())

        if fileExists(DATABASE_PATH + '.movies'):
            remove(DATABASE_PATH + '.movies')
        if fileExists(DATABASE_PATH + '.series'):
            remove(DATABASE_PATH + '.series')
        rename(DATABASE_PATH + '.sorted', DATABASE_PATH)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if PY3:
            link = link.encode()
        callInThread(threadGetPage, url=link, file=None, key=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.exit, movieBrowserConfig)

    def zap(self):
        if self.ready is True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)

    def showHelp(self):
        if self.showhelp is False:
            self.showhelp = True
            self.toogleHelp.show()
        else:
            self.showhelp = False
            self.toogleHelp.hide()

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        if self.showhelp is True:
            self.showhelp = False
            self.toogleHelp.hide()
        elif self.toggleCount != 0:
            self.toggleCount = 0
            self.hidePlot()
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.hideInfo()
                    self.makeEpisodes()
                elif content == 'Series':
                    self['eposter'].hide()
                    self.makePoster()
                    self.makeName(self.index)
                    self.makeInfo(self.index)
            except IndexError:
                self['eposter'].hide()
                self.hideInfo()

        elif self.topseries is True:
            self.topseries = False
            self.episodes = True
            self.control = True
            self.back = True
            self.toggleCount = 0
            self.content = self.oldcontent
            self.filter = self.oldfilter
            self.index = self.topindex
            self.hideInfo()
            self.hidePlot()
            self['eposter'].hide()
            self.makeMovies(self.filter)
        else:
            if config.plugins.moviebrowser.lastmovie.value == "yes":
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value is True:
                with open(FILTER_PATH, "w") as f:
                    f.write(self.filter)
            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            self.session.deleteDialog(self.toogleHelp)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            # self.close()
        self.close()


class movieBrowserBackdrop(Screen):

    def __init__(self, session, index, content, filter):
        skin = join(skin_path + "movieBrowserBackdrop.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.seenEOF})
        self.toogleHelp = self.session.instantiateDialog(helpScreen)
        self.hideflag = True
        self.ready = False
        self.renew = False
        self.startupdate = False
        self.reset = False
        self.tmdbposter = False
        self.topseries = False
        self.filterseen = False
        self.showhelp = False
        self.control = False
        self.content = content
        self.filter = filter
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value
        self.showfolder = config.plugins.moviebrowser.showfolder.getValue()
        self.ABC = 'ABC'
        self.namelist = []
        self.movielist = []
        self.datelist = []
        self.infolist = []
        self.plotlist = []
        self.posterlist = []
        self.backdroplist = []
        self.contentlist = []
        self.seenlist = []
        self.medialist = []
        self.dddlist = []
        self['name'] = Label()
        self['seen'] = Pixmap()
        self['seen'].hide()
        self['Director'] = Label(_('Director:'))
        self['Actors'] = Label(_('Actors:'))
        self['Year'] = Label(_('Years:'))
        self['Runtime'] = Label(_('Runtime:'))
        self['Country'] = Label(_('Country:'))
        self['Genres'] = Label(_('Genres:'))
        self['Rating'] = Label(_('Rating:'))
        self['director'] = Label()
        self['actors'] = Label()
        self['year'] = Label()
        self['runtime'] = Label()
        self['country'] = Label()
        self['genres'] = Label()
        self['ratings'] = ProgressBar()
        self['ratings'].hide()
        self['ratingsback'] = Pixmap()
        self['ratingsback'].hide()
        self['infoback'] = Pixmap()
        self['backdrop'] = Pixmap()
        self.oldbackdropurl = ''
        self.backdrops = config.plugins.moviebrowser.backdrops.getValue()
        if content == ':::Series:Top:::':
            self.plotfull = True
            self.episodes = True
            self.toggleCount = 1
        elif config.plugins.moviebrowser.plotfull.value == 'show':
            self.plotfull = True
            self.episodes = False
            self.toggleCount = 0
        else:
            self.plotfull = False
            self.episodes = False
            self.toggleCount = 0
        self['plotfull'] = ScrollLabel()
        self['plotfull'].hide()
        self['plotfullback'] = Pixmap()
        self['plotfullback'].hide()
        self['poster0'] = Pixmap()
        self['poster1'] = Pixmap()
        self['poster2'] = Pixmap()
        self['poster3'] = Pixmap()
        self['poster4'] = Pixmap()
        self['poster5'] = Pixmap()
        self['poster6'] = Pixmap()
        self['poster7'] = Pixmap()
        self['poster8'] = Pixmap()
        self['poster9'] = Pixmap()
        self['poster10'] = Pixmap()
        self.index = index
        if screenwidth.width() >= 1280:
            self.posterindex = 6
            self.posterALL = 13
            self['poster11'] = Pixmap()
            self['poster12'] = Pixmap()
        else:
            self.posterindex = 5
            self.posterALL = 11
        self['eposter'] = Pixmap()
        self['eposter'].hide()
        self['banner'] = Pixmap()
        self['banner'].hide()
        self['episodes'] = ItemList([])
        self['episodes'].hide()
        self['ddd'] = Pixmap()
        self['ddd'].hide()
        self['ddd2'] = Pixmap()
        self['ddd2'].hide()
        self['audiotype'] = MultiPixmap()
        self['videomode'] = MultiPixmap()
        self['videocodec'] = MultiPixmap()
        self['aspectratio'] = MultiPixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'InfobarActions', 'InfobarTeletextActions', 'MovieSelectionActions', 'MoviePlayerActions', 'InfobarEPGActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.up,
            'prevBouquet': self.down,
            'nextMarker': self.gotoABC,
            'prevMarker': self.gotoXYZ,
            'red': self.switchStyle,
            'yellow': self.updateDatabase,
            'blue': self.hideScreen,
            'contextMenu': self.config,
            'showEventInfo': self.togglePlot,
            'EPGPressed': self.togglePlot,
            'startTeletext': self.editDatabase,
            'showMovies': self.updateDatabase,
            'showRadio': self.deleteMovie,
            'leavePlayer': self.markSeen,
            '1': self.controlMovies,
            '2': self.renewTMDb,
            '3': self.renewTVDb,
            '4': self.filterSeen,
            '5': self.toogleContent,
            '6': self.filterFolder,
            '7': self.filterDirector,
            '8': self.filterActor,
            '9': self.filterGenre,
            '0': self.gotoEnd,
            'bluelong': self.showHelp,
            'displayHelp': self.showHelp
        }, -1)

        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        # BLACKLIST_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        # self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        # self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(DATABASE_PATH):
            size = getsize(DATABASE_PATH)
            if size < 10:
                remove(DATABASE_PATH)

        if fileExists(infosmallBackPNG):
            if self["infoback"].instance:
                self["infoback"].instance.setPixmapFromFile(infosmallBackPNG)
                self['infoback'].show()

        if fileExists(infoBackPNG):
            if self["plotfullback"].instance:
                self["plotfullback"].instance.setPixmapFromFile(infoBackPNG)
                self['plotfullback'].hide()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
            self.session.nav.stopService()

        if fileExists(DATABASE_PATH):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value is True:
                    self.filter = open(FILTER_PATH).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(LAST_PATH).read()
                    if movie.endswith('...'):
                        self.index = -1
                    else:
                        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                        data = open(DATABASE_PATH).read()
                        count = 0
                        for line in data.split('\n'):
                            if self.content in line and self.filter in line:
                                if search(movie, line) is not None:
                                    self.index = count
                                    break
                                count += 1

                elif config.plugins.moviebrowser.lastmovie.value == 'folder' and self.showfolder is True:
                    self.index = -1
            self.makeMovieBrowserTimer = eTimer()
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)
        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(DATABASE_RESET, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.exit, movieBrowserConfig)
        else:
            OnclearMem()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(DATABASE_RESET):
                remove(DATABASE_RESET)
            if fileExists(BLACKLIST_PATH):
                remove(BLACKLIST_PATH)
            open(DATABASE_PATH, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            self.close()

    def makeMovies(self, filter):
        if filter is not None:
            self.namelist = []
            self.movielist = []
            self.datelist = []
            self.infolist = []
            self.plotlist = []
            self.posterlist = []
            self.backdroplist = []
            self.contentlist = []
            self.seenlist = []
            self.medialist = []
            self.dddlist = []
            self.filter = filter
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        if self.content in line and filter in line:
                            name = ""
                            filename = ""
                            date = ""
                            runtime = ""
                            rating = ""
                            director = ""
                            actors = ""
                            genres = ""
                            year = ""
                            country = ""
                            plotfull = ""
                            poster = str(default_poster)
                            backdrop = str(default_backdrop)
                            seen = 'unseen'
                            content = 'Movie:Top'
                            media = '\n'
                            movieline = line.split(':::')
                            try:
                                name = movieline[0]
                                name = sub(r'[Ss][0]+[Ee]', 'Special ', name)
                                filename = movieline[1]
                                date = movieline[2]
                                runtime = movieline[3]
                                rating = movieline[4]
                                director = movieline[5]
                                actors = movieline[6]
                                genres = movieline[7]
                                year = movieline[8]
                                country = movieline[9]
                                plotfull = movieline[10]
                                poster = movieline[11]
                                backdrop = movieline[12]
                                content = movieline[13]
                                seen = movieline[14]
                                media = movieline[15]
                            except IndexError:
                                pass
                            self.namelist.append(name)
                            self.movielist.append(filename)
                            self.dddlist.append('yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director, actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)
                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(config.plugins.moviebrowser.moviefolder.value + '...')
                    self.datelist.append('')
                    res = []
                    res.append('')
                    res.append('0.0')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    self.infolist.append(res)
                    self.plotlist.append('')
                    self.posterlist.append(str(default_folder))
                    self.backdroplist.append(str(default_backdrop))
                    self.contentlist.append(':Top')
                    self.seenlist.append('unseen')
                    self.medialist.append('\n')
                self.maxentry = len(self.namelist)
                self.makePoster()
                if self.backdrops != 'hide':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass

                else:
                    self.showDefaultBackdrop()
                try:
                    self.makeName(self.index)
                except IndexError:
                    pass

                try:
                    self.makeInfo(self.index)
                except IndexError:
                    pass

                try:
                    content = self.contentlist[self.index]
                    if content == 'Series:Top':
                        self.plotfull = True
                        self.episodes = True
                        self.toggleCount = 1
                        self.makePlot(self.index)
                    elif self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

                self.ready = True
        OnclearMem()
        return

    def updateDatabase(self):
        if self.ready is True:
            if exists(config.plugins.moviebrowser.moviefolder.value) and exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, '\nUpdate Movie Browser Database?', MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, "w") as f:
                    f.write(movie)
            except IndexError:
                pass

            if fileExists(DATABASE_PATH):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)
        OnclearMem()

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value is True:
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()
        movie = open(LAST_PATH).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(DATABASE_PATH).read()
        count = 0
        self.index = 0
        for line in data.split('\n'):
            if self.content in line and self.filter in line:
                if search(movie, line) is not None:
                    self.index = count
                    break
                count += 1

        if self.startupdate is True:
            self.startupdate = False
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.') % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                else:
                    self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        OnclearMem()
        return

    def ok(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    if self.plotfull is False:
                        self.plotfull = True
                        self.makePlot(self.index)
                    elif len(self.seasons) != 0:
                        self.topseries = True
                        self.episodes = False
                        self.control = False
                        self.toggleCount = 1
                        self.oldcontent = self.content
                        self.oldfilter = self.filter
                        self.topindex = self.index
                        self.index = 5
                        if screenwidth.width() >= 1280:
                            self.posterindex = 6
                        else:
                            self.posterindex = 5
                        self.content = ':::Series:::'
                        index = self['episodes'].getSelectedIndex()
                        current = self.seasons[index]
                        if current is not None:
                            current = sub('Specials', '(S00', current)
                            current = sub('specials', '(s00', current)
                            current = sub('Season ', '(S', current)
                            current = sub('season ', '(s', current)
                        else:
                            current = self.namelist[self.index]
                        self.makeMovies(current)
                else:
                    filename = self.movielist[self.index]
                    if self.showfolder is True and filename.endswith('...'):
                        self.filterFolder()
                        return
                    if filename.endswith('.ts'):
                        if fileExists(filename):
                            sref = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(self.getMediaInfo)
                    self.makeMovieBrowserTimer.start(2000, True)
            except IndexError:
                pass

        return

    def getMediaInfo(self):
        service = self.session.nav.getCurrentService()
        if service is not None:
            audiotype = ''
            videomode = ''
            videocodec = ''
            aspectratio = ''
            audio = service.audioTracks()
            if audio:
                try:
                    audioTrack = audio.getCurrentTrack()
                    if audioTrack is not None:
                        info = audio.getTrackInfo(audioTrack)
                        description = info.getDescription()
                        if 'AC3+' in description or 'Dolby Digital+' in description:
                            audiotype = 'dolbyplus'
                        elif 'AC3' in description or 'AC-3' in description or 'Dolby Digital' in description:
                            audiotype = 'dolby'
                        elif 'DTS-HD' in description:
                            audiotype = 'dtshd'
                        elif 'DTS' in description:
                            audiotype = 'dts'
                        else:
                            audiotype = 'mp2'
                except OverflowError:
                    audiotype = 'mp2'

            info = service and service.info()
            if info:
                height = info and info.getInfo(iServiceInformation.sVideoHeight)
                if str(height) == '1080':
                    videomode = '1080'
                elif str(height) == '720':
                    videomode = '720'
                else:
                    videomode = '480'
                aspect = info and info.getInfo(iServiceInformation.sAspect)
                if aspect in (3, 4, 7, 8, 11, 12, 15, 16):
                    aspectratio = '16_9'
                else:
                    aspectratio = '4_3'
            filename = self.movielist[self.index]
            if filename.endswith('.iso') or filename.endswith('.ISO'):
                videocodec = 'dvd'
            elif filename.endswith('.flv'):
                videocodec = 'flv'
            elif filename.endswith('.divx'):
                videocodec = 'divx'
            elif videomode == '480':
                videocodec = 'mpeg2'
            else:
                videocodec = 'h264'
            media = audiotype + ':' + videomode + ':' + videocodec + ':' + aspectratio
            self.medialist[self.index] = media
            info = media.split(':')
            try:
                if info[0] == 'dolby':
                    self['audiotype'].setPixmapNum(0)
                elif info[0] == 'mp2':
                    self['audiotype'].setPixmapNum(4)
                elif info[0] == 'dts':
                    self['audiotype'].setPixmapNum(2)
                elif info[0] == 'dolbyplus':
                    self['audiotype'].setPixmapNum(1)
                else:
                    self['audiotype'].setPixmapNum(3)
            except IndexError:
                self['audiotype'].setPixmapNum(4)

            try:
                if info[1] == '1080':
                    self['videomode'].setPixmapNum(0)
                elif info[1] == '720':
                    self['videomode'].setPixmapNum(1)
                else:
                    self['videomode'].setPixmapNum(2)
            except IndexError:
                self['videomode'].setPixmapNum(2)

            try:
                if info[2] == 'h264':
                    self['videocodec'].setPixmapNum(0)
                elif info[2] == 'mpeg2':
                    self['videocodec'].setPixmapNum(1)
                elif info[2] == 'divx':
                    self['videocodec'].setPixmapNum(2)
                elif info[2] == 'flv':
                    self['videocodec'].setPixmapNum(3)
                else:
                    self['videocodec'].setPixmapNum(4)
            except IndexError:
                self['videocodec'].setPixmapNum(1)

            try:
                if info[3] == '16_9':
                    self['aspectratio'].setPixmapNum(0)
                else:
                    self['aspectratio'].setPixmapNum(1)
            except IndexError:
                self['aspectratio'].setPixmapNum(1)

            self['audiotype'].show()
            self['videomode'].show()
            self['videocodec'].show()
            self['aspectratio'].show()
            if '3d' in filename.lower():
                self['ddd'].hide()
                self['ddd2'].show()
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + '.new', 'w') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, _('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                # self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (str(tmdb_api), name, self.language)
                print('renewTMDb url tmdb=', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if PY3:
                output = urlopen(request, timeout=10).read().decode('utf-8')
            else:
                output = urlopen(request, timeout=10).read()
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w185', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = findall('"vote_average":(.*?),', output)
        year = findall('"release_date":"(.*?)"', output)
        titles = findall('"title":"(.*?)"', output)
        poster = findall('"poster_path":"(.*?)"', output)
        id = findall('"id":(.*?),', output)
        country = findall('"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == 'movie':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (new + self.language, str(tmdb_api))
                print('makeTMDbUpdate url tmdb=', url)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select == 'poster':
                poster = self.posterlist[self.index]
                posternew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(poster, posternew)
                with open(DATABASE_PATH + '.new', 'w') as f:
                    f.write(database)
                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                with open(DATABASE_PATH + '.new', 'w') as f:
                    f.write(database)
                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                # self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (name, self.language)
                print('renewTVDb url  =', url)
                self.getTVDbMovies(url)
            except IndexError:
                pass

    def getTVDbMovies(self, url):
        rating = []
        year = []
        titles = []
        poster = []
        id = []
        country = []
        request = Request(url, headers=agents)
        try:
            if PY3:
                output = urlopen(request, timeout=10).read().decode('utf-8')
            else:
                output = urlopen(request, timeout=10).read()
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        try:
            output = output.replace('&amp;', '&')
            seriesid = findall('<seriesid>(.*?)</seriesid>', output)
            for x in range(len(seriesid)):
                url = ('https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('getTVDbMovies url tmdb=', url)
                request = Request(url, headers=agents)
                try:
                    if PY3:
                        output = urlopen(request, timeout=10).read().decode('utf-8')
                    else:
                        output = urlopen(request, timeout=10).read()
                except Exception:
                    output = ''

                output = sub('<poster>', '<poster>https://www.thetvdb.com/banners/_cache/', output)
                output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>' + wiki_png + '</poster>', output)
                output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
                output = sub('&amp;', '&', output)
                Rating = findall('<Rating>(.*?)</Rating>', output)
                Year = findall('<FirstAired>([0-9]+)-', output)
                Added = findall('<added>([0-9]+)-', output)
                Titles = findall('<SeriesName>(.*?)</SeriesName>', output)
                Poster = findall('<poster>(.*?)</poster>', output)
                TVDbid = findall('<id>(.*?)</id>', output)
                Country = findall('<Status>(.*?)</Status>', output)
                try:
                    rating.append(Rating[0])
                except IndexError:
                    rating.append('0.0')

                try:
                    year.append(Year[0])
                except IndexError:
                    try:
                        year.append(Added[0])
                    except IndexError:
                        year.append(' ')
                try:
                    titles.append(Titles[0])
                except IndexError:
                    titles.append(' ')

                try:
                    poster.append(Poster[0])
                except IndexError:
                    poster.append(wiki_png)

                try:
                    id.append(TVDbid[0])
                except IndexError:
                    id.append('0')
                try:
                    country.append(Country[0])
                except IndexError:
                    country.append(' ')
            titel = _('TheTVDb Results')
            if not titles:
                self.session.open(MessageBox, _('\nNo TheTVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            else:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, True)
                else:
                    self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, False)
        except Exception as e:
            print('error get ', str(e))

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ('https://www.thetvdb.com/api/%s/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('makeTVDbUpdate url tmdb=', url)
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return
                bannernew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(banner, bannernew)
                with open(DATABASE_PATH + '.new', 'w') as f:
                    f.write(database)
                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                with open(DATABASE_PATH + '.new', 'w') as f:
                    f.write(database)

                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.renewFinished()
        return

    def renewFinished(self):
        self.renew = False
        self.makeMovies(self.filter)

    def deleteMovie(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                    self.session.open(MessageBox, _('\nThe List of Movie Folder can not be deleted.'), MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def delete_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if fileExists(movie):
                    remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        remove(eitfile)
                    if fileExists(movie + '.ap'):
                        remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        remove(srtfile)
                data = open(DATABASE_PATH).read()
                if content == 'Series:Top':
                    for line in data.split('\n'):
                        if search(movie + '.*?:::Series:', line) is not None:
                            data = data.replace(line + '\n', '')

                else:
                    for line in data.split('\n'):
                        if search(movie, line) is not None:
                            data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            except IndexError:
                pass

            self.ready = True
        else:
            self.blacklistMovie()
        return

    def blacklistMovie(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            try:
                name = self.namelist[self.index]
                self.session.openWithCallback(self.blacklist_return, MessageBox, _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(BLACKLIST_PATH):
                    fremove = open(BLACKLIST_PATH, 'a')
                else:
                    fremove = open(BLACKLIST_PATH, 'w')
                data = open(DATABASE_PATH).read()
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        fremove.write(line + '\n')
                        fremove.close()
                        data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            except IndexError:
                pass

            self.ready = True
        return

    def markSeen(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                    else:
                        newline = line.replace(':::seen:::', ':::unseen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'unseen')
                        self['seen'].hide()
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + ".new", "w") as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        database = database.replace(line, newline)

            with open(DATABASE_PATH + ".new", "w") as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def togglePlot(self):
        if self.ready is True:
            if self.toggleCount == 0:
                self.plotfull = True
                self.toggleCount = 1
                self['ddd'].hide()
                self['ddd2'].hide()
                self['audiotype'].hide()
                self['videomode'].hide()
                self['videocodec'].hide()
                self['aspectratio'].hide()
                if self.backdrops == 'info':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass
                try:
                    self.makePlot(self.index)
                except IndexError:
                    pass

            elif self.toggleCount == 1:
                self.toggleCount = 2
                self.control = False
                self.hideEPoster()
                self['plotfull'].show()
            elif self.toggleCount == 2:
                self.toggleCount = 0
                self.plotfull = False
                self.hidePlot()
                self.hideEPoster()
                ddd = self.dddlist[self.index]
                media = self.medialist[self.index]
                if media != '\n':
                    self['audiotype'].show()
                    self['videomode'].show()
                    self['videocodec'].show()
                    self['aspectratio'].show()
                    if ddd == 'yes':
                        self['ddd2'].show()
                elif ddd == 'yes':
                    self['ddd'].show()

    def showPlot(self):
        self['plotfull'].show()
        self['plotfullback'].show()

    def showEPoster(self):
        self['eposter'].show()
        self['banner'].show()
        self['episodes'].show()
        self['plotfull'].hide()

    def hidePlot(self):
        self['plotfull'].hide()
        self['plotfullback'].hide()

    def hideEPoster(self):
        self['eposter'].hide()
        self['banner'].hide()
        self['episodes'].hide()

    def makeName(self, count):
        try:
            name = self.namelist[count]
            if screenwidth.width() >= 1280:
                if len(name) > 63:
                    if name[62:63] == ' ':
                        name = name[0:62]
                    else:
                        name = name[0:63] + 'FIN'
                        name = sub(' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 66:
                if name[65:66] == ' ':
                    name = name[0:65]
                else:
                    name = name[0:66] + 'FIN'
                    name = sub(' \\S+FIN', '', name)
                name = name + ' ...'
            self['name'].setText(str(name))
            self['name'].show()
            self.setTitle(str(name))
        except IndexError:
            self['name'].hide()

        try:
            seen = self.seenlist[count]
            if seen == 'seen':
                self['seen'].show()
            else:
                self['seen'].hide()
        except IndexError:
            self['seen'].hide()

    def makeInfo(self, count):
        try:
            runtime = self.infolist[count][0]
            if self.showfolder is True and runtime == '':
                self['Runtime'].hide()
                self['runtime'].hide()
                self['Rating'].hide()
                self['ratings'].hide()
                self['ratingsback'].hide()
                self['Director'].hide()
                self['director'].hide()
                self['Actors'].hide()
                self['actors'].hide()
                self['Genres'].hide()
                self['genres'].hide()
                self['Year'].hide()
                self['year'].hide()
                self['Country'].hide()
                self['country'].hide()
                self['ddd'].hide()
                self['ddd2'].hide()
                self['audiotype'].hide()
                self['videomode'].hide()
                self['videocodec'].hide()
                self['aspectratio'].hide()
                return
            self['Runtime'].show()
            self['runtime'].setText(runtime)
            self['runtime'].show()
        except IndexError:
            self['Runtime'].hide()
            self['runtime'].hide()

        try:
            ratings = self.infolist[count][1]
            try:
                rating = int(10 * round(float(ratings), 1))
            except ValueError:
                ratings = '0.0'
                rating = int(10 * round(float(ratings), 1))

            self['Rating'].show()
            self['ratings'].setValue(rating)
            self['ratings'].show()
            self['ratingsback'].show()
        except IndexError:
            self['Rating'].hide()
            self['ratings'].hide()

        try:
            director = self.infolist[count][2]
            self['Director'].show()
            self['director'].setText(director)
            self['director'].show()
        except IndexError:
            self['Director'].hide()
            self['director'].hide()

        try:
            actors = self.infolist[count][3]
            self['Actors'].show()
            self['actors'].setText(actors)
            self['actors'].show()
        except IndexError:
            self['Actors'].hide()
            self['actors'].hide()

        try:
            genres = self.infolist[count][4]
            self['Genres'].show()
            self['genres'].setText(genres)
            self['genres'].show()
        except IndexError:
            self['Genres'].hide()
            self['genres'].hide()

        try:
            year = self.infolist[count][5]
            self['Year'].show()
            self['year'].setText(year)
            self['year'].show()
        except IndexError:
            self['Year'].hide()
            self['year'].hide()

        try:
            country = self.infolist[count][6]
            self['Country'].show()
            self['country'].setText(country)
            self['country'].show()
        except IndexError:
            self['Country'].hide()
            self['country'].hide()

        if self.plotfull is False:
            ddd = self.dddlist[self.index]
            media = self.medialist[self.index]
            if media != '\n':
                info = media.split(':')
                try:
                    if info[0] == 'dolby':
                        self['audiotype'].setPixmapNum(0)
                    elif info[0] == 'mp2':
                        self['audiotype'].setPixmapNum(4)
                    elif info[0] == 'dts':
                        self['audiotype'].setPixmapNum(2)
                    elif info[0] == 'dolbyplus':
                        self['audiotype'].setPixmapNum(1)
                    else:
                        self['audiotype'].setPixmapNum(3)
                except IndexError:
                    self['audiotype'].setPixmapNum(4)

                try:
                    if info[1] == '1080':
                        self['videomode'].setPixmapNum(0)
                    elif info[1] == '720':
                        self['videomode'].setPixmapNum(1)
                    else:
                        self['videomode'].setPixmapNum(2)
                except IndexError:
                    self['videomode'].setPixmapNum(2)

                try:
                    if info[2] == 'h264':
                        self['videocodec'].setPixmapNum(0)
                    elif info[2] == 'mpeg2':
                        self['videocodec'].setPixmapNum(1)
                    elif info[2] == 'divx':
                        self['videocodec'].setPixmapNum(2)
                    elif info[2] == 'flv':
                        self['videocodec'].setPixmapNum(3)
                    else:
                        self['videocodec'].setPixmapNum(4)
                except IndexError:
                    self['videocodec'].setPixmapNum(1)

                try:
                    if info[3] == '16_9':
                        self['aspectratio'].setPixmapNum(0)
                    else:
                        self['aspectratio'].setPixmapNum(1)
                except IndexError:
                    self['aspectratio'].setPixmapNum(1)

                self['audiotype'].show()
                self['videomode'].show()
                self['videocodec'].show()
                self['aspectratio'].show()
                if ddd == 'yes':
                    self['ddd'].hide()
                    self['ddd2'].show()
                else:
                    self['ddd'].hide()
                    self['ddd2'].hide()
            else:
                self['audiotype'].hide()
                self['videomode'].hide()
                self['videocodec'].hide()
                self['aspectratio'].hide()
                if ddd == 'yes':
                    self['ddd'].show()
                    self['ddd2'].hide()
                else:
                    self['ddd'].hide()
                    self['ddd2'].hide()
        else:
            self['ddd'].hide()
            self['ddd2'].hide()
            self['audiotype'].hide()
            self['videomode'].hide()
            self['videocodec'].hide()
            self['aspectratio'].hide()

    def makePlot(self, index):
        self['plotfullback'].show()
        try:
            plot = self.plotlist[self.index]
            self['plotfull'].setText(plot)
        except IndexError:
            pass

        self['plotfull'].hide()
        self.makeEPoster()

    def makeEPoster(self):
        if self.content == ':::Movie:Top:::':
            self.toggleCount = 2
            self['eposter'].hide()
            self['banner'].hide()
            self['episodes'].hide()
            self['plotfull'].show()
        elif self.content == ':::Series:Top:::':
            self.toggleCount = 1
            try:
                posterurl = self.posterlist[self.index]
                if search('<episode>', posterurl) is not None:
                    bannerurl = search('<episode>(.*?)<episode>', posterurl)
                    bannerurl = bannerurl.group(1)
                    banner = sub('.*?[/]', '', bannerurl)
                    banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                    if fileExists(banner):
                        self["banner"].instance.setPixmapFromFile(banner)
                        self['banner'].show()
                    else:
                        if PY3:
                            bannerurl = bannerurl.encode()
                        callInThread(threadGetPage, url=bannerurl, file=banner, key=None, success=self.getBanner, fail=self.downloadError)
                else:
                    self['banner'].hide()
            except IndexError:
                pass

            self.filterSeasons()
        elif self.content == ':Top:::':
            try:
                content = self.contentlist[self.index]
                if content == 'Movie:Top':
                    self.toggleCount = 2
                    self.episodes = False
                    self.control = False
                    self['eposter'].hide()
                    self['banner'].hide()
                    self['episodes'].hide()
                    self['plotfull'].show()
                else:
                    self.toggleCount = 1
                    self.episodes = True
                    posterurl = self.posterlist[self.index]
                    if search('<episode>', posterurl) is not None:
                        bannerurl = search('<episode>(.*?)<episode>', posterurl)
                        bannerurl = bannerurl.group(1)
                        banner = sub('.*?[/]', '', bannerurl)
                        banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                        if fileExists(banner):
                            self["banner"].instance.setPixmapFromFile(banner)
                            self['banner'].show()
                        else:
                            if PY3:
                                bannerurl = bannerurl.encode()
                            callInThread(threadGetPage, url=bannerurl, file=banner, key=None, success=self.getBanner, fail=self.downloadError)
                    else:
                        self['banner'].hide()
                    self.filterSeasons()
            except IndexError:
                pass

        else:
            self.toggleCount = 1
            self['banner'].hide()
            self['episodes'].hide()
            self['plotfull'].hide()
            try:
                posterurl = self.posterlist[self.index]
                if search('<episode>', posterurl) is not None:
                    eposterurl = search('<episode>(.*?)<episode>', posterurl)
                    eposterurl = eposterurl.group(1)
                    eposter = sub('.*?[/]', '', eposterurl)
                    eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                    if fileExists(eposter):
                        self["eposter"].instance.setPixmapFromFile(eposter)
                        self['eposter'].show()
                    else:
                        if PY3:
                            eposterurl = eposterurl.encode()
                        callInThread(threadGetPage, url=eposterurl, file=eposter, key=None, success=self.getEPoster, fail=self.downloadError)
                else:
                    self.toggleCount = 2
                    self['eposter'].hide()
                    self['plotfull'].show()
            except IndexError:
                pass

        return

    def getEPoster(self, output, eposter):
        try:
            open(eposter, 'wb').write(output)
            if fileExists(eposter):
                self["eposter"].instance.setPixmapFromFile(eposter)
                self['eposter'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
            self['eposter'].hide()
        return

    def getBanner(self, output, banner):
        try:
            open(banner, 'wb').write(output)
            if fileExists(banner):
                self['plotfull'].hide()
                self["banner"].instance.setPixmapFromFile(banner)
                self['banner'].show()
        except Exception as e:
            print('error ', str(e))
            self['banner'].hide()
        return

    def makePoster(self):
        for x in range(self.posterALL):
            try:
                index = self.index - self.posterindex + x
                if index >= self.maxentry:
                    index = index - self.maxentry
                elif index < 0:
                    index = self.maxentry + index
                posterurl = self.posterlist[index]
                posterurl = sub('<episode>.*?<episode>', '', posterurl)
                poster = sub('.*?[/]', '', posterurl)
                poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
                if fileExists(poster):
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
                else:
                    if PY3:
                        posterurl = posterurl.encode()
                    callInThread(threadGetPage, url=posterurl, file=poster, key=x, success=self.getPoster, fail=self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        return

    def getPoster(self, output, poster, x):  # success(response.content, file, key
        try:
            open(poster, 'wb').write(output)
            if fileExists(poster):
                if self['poster' + str(x)].instance:
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
        except Exception as e:
            print('error ', str(e))
            self['poster' + str(x)].hide()
        return

    def showBackdrops(self, index):
        try:
            backdropurl = self.backdroplist[index]
            if backdropurl != self.oldbackdropurl:
                self.oldbackdropurl = backdropurl
                backdrop = sub('.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        if PY3:
                            backdropurl = backdropurl.encode()
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        popen('/usr/bin/showiframe %s') % no_m1v
                elif fileExists(backdrop):
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
                else:
                    if PY3:
                        backdropurl = backdropurl.encode()
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            open(backdrop, 'wb').write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        backdrop = default_backdrop  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = default_backdropm1v  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
                popen('/usr/bin/showiframe %s') % no_m1v
        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def down(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].down()
            elif self.toggleCount == 2:
                self['plotfull'].pageDown()
            else:
                self.index -= self.posterALL - 2
                if self.index < 0:
                    self.index = self.maxentry + self.index
                    if self.index < 0:
                        self.index = 0
                try:
                    self.makePoster()
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

    def up(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].up()
            elif self.toggleCount == 2:
                self['plotfull'].pageUp()
            else:
                self.index += self.posterALL - 2
                if self.index >= self.maxentry:
                    self.index = self.index - self.maxentry
                    if self.index >= self.maxentry:
                        self.index = self.maxentry - 1
                try:
                    self.makePoster()
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

    def rightDown(self):
        if self.ready is True:
            self.index += 1
            if self.index == self.maxentry:
                self.index = 0
            try:
                self.makePoster()
                if self.backdrops == 'auto':
                    self.showBackdrops(self.index)
                self.makeName(self.index)
                self.makeInfo(self.index)
                if self.plotfull is True:
                    self.makePlot(self.index)
            except IndexError:
                pass

    def leftUp(self):
        if self.ready is True:
            self.index -= 1
            if self.index < 0:
                self.index = self.maxentry - 1
            try:
                self.makePoster()
                if self.backdrops == 'auto':
                    self.showBackdrops(self.index)
                self.makeName(self.index)
                self.makeInfo(self.index)
                if self.plotfull is True:
                    self.makePlot(self.index)
            except IndexError:
                pass

    def gotoEnd(self):
        if self.ready is True:
            self.index = self.maxentry - 1
            try:
                self.makePoster()
                if self.backdrops == 'auto':
                    self.showBackdrops(self.index)
                self.makeName(self.index)
                self.makeInfo(self.index)
                if self.plotfull is True:
                    self.makePlot(self.index)
            except IndexError:
                pass

    def controlMovies(self):
        if self.ready is True:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.open(MessageBox, _('Series Folder: No Info possible'), MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                for line in f:
                    if self.content in line and self.filter in line:
                        movieline = line.split(':::')
                        try:
                            self.movies.append((movieline[0], movieline[1], movieline[12]))
                        except IndexError:
                            pass

                if self.showfolder is True:
                    self.movies.append(_('<List of Movie Folder>'), config.plugins.moviebrowser.moviefolder.value + '...', str(default_backdrop))
                f.close()
                self.session.openWithCallback(self.gotoMovie, movieControlList, self.movies, self.index, self.content)

    def gotoMovie(self, index, rebuild):
        if index is not None:
            self.index = index
            if rebuild is True:
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            else:
                try:
                    self.makePoster()
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

        return

    def gotoABC(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, False)

    def gotoXYZ(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, True)

    def enterABC(self, ABC):
        if ABC is None:
            pass
        else:
            self.ABC = ABC
            ABC = ABC[0].lower()
            try:
                self.index = next((index for index, value in enumerate(self.namelist) if value.lower().replace('der ', '').replace('die ', '').replace('das ', '').replace('the ', '').startswith(ABC)))
                try:
                    self.makePoster()
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

            except StopIteration:
                pass
        return

    def filterSeen(self):
        if self.ready is True:
            if self.filterseen is False:
                self.filterseen = True
                self.filter = ':::unseen:::'
                self.index = 0
                self.toggleCount = 0
                if screenwidth.width() >= 1280:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.makeMovies(self.filter)
            else:
                self.filterseen = False
                self.filter = self.content
                self.index = 0
                self.toggleCount = 0
                if screenwidth.width() >= 1280:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.makeMovies(self.filter)

    def filterFolder(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _('Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            genres = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            genre = movieline[7]
                        except IndexError:
                            genre = ' '

                        if genre != ' ':
                            genres = genres + genre + ', '

                self.genres = [i for i in genres.split(', ')]
                self.genres.sort()
                self.genres.pop(0)
                try:
                    last = self.genres[-1]
                    for i in range(len(self.genres) - 2, -1, -1):
                        if last == self.genres[i]:
                            del self.genres[i]
                        else:
                            last = self.genres[i]
                            if len(last) > max:
                                max = len(last)

                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _('Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            actors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            actor = movieline[6]
                        except IndexError:
                            actor = ' '

                        if actor != ' ':
                            actors = actors + actor + ', '

                self.actors = [i for i in actors.split(', ')]
                self.actors.sort()
                self.actors.pop(0)
                try:
                    last = self.actors[-1]
                    for i in range(len(self.actors) - 2, -1, -1):
                        if last == self.actors[i]:
                            del self.actors[i]
                        else:
                            last = self.actors[i]
                            if len(last) > max:
                                max = len(last)

                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _('Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            directors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        if director != ' ':
                            directors = directors + director + ', '

                self.directors = [i for i in directors.split(', ')]
                self.directors.sort()
                self.directors.pop(0)
                try:
                    last = self.directors[-1]
                    for i in range(len(self.directors) - 2, -1, -1):
                        if last == self.directors[i]:
                            del self.directors[i]
                        else:
                            last = self.directors[i]
                            if len(last) > max:
                                max = len(last)

                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _('Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
                filter = sub('FIN', '', filter)
            content = ':::Series:::'
            seasons = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                for line in f:
                    if line.startswith(filter) and content in line:
                        movieline = line.split(':::')
                        try:
                            season = movieline[0]
                            season = season + 'FIN'
                            season = sub('[(]S00', 'Specials', season)
                            season = sub('[(]s00', 'specials', season)
                            season = sub('[(]S', 'Season ', season)
                            season = sub('[(]s', 'season ', season)
                            season = sub('[Ee][0-9]+[)].*?FIN', '', season)
                            season = sub('FIN', '', season)
                            season = sub(',', '', season)
                        except IndexError:
                            season = ' '

                        if season != ' ':
                            seasons = seasons + season + ', '

                self.seasons = [i for i in seasons.split(', ')]
                self.seasons.sort()
                self.seasons.pop(0)
                try:
                    last = self.seasons[-1]
                    for i in range(len(self.seasons) - 2, -1, -1):
                        if last == self.seasons[i]:
                            del self.seasons[i]
                        else:
                            last = self.seasons[i]

                except IndexError:
                    pass

            if self.episodes is True or self.content == ':::Series:::':
                self.control = True
                self['eposter'].hide()
                self['plotfull'].hide()
                self['plotfullback'].show()
                self['banner'].show()
                self.entries = []
                if config.plugins.moviebrowser.metrixcolor.value != '0x00000000':
                    backcolor = True
                    back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
                else:
                    backcolor = False
                if screenwidth.width() == 1920:
                    listwidth = 760
                elif screenwidth.width() == 1280:
                    listwidth = 500
                else:
                    listwidth = 440
                idx = 0
                for x in self.seasons:
                    idx += 1

                for i in range(idx):
                    try:
                        res = ['']
                        if screenwidth.width() == 1920:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(10, 0), size=(listwidth, 40), font=30, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(10, 0), size=(listwidth, 30), font=30, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(5, 0), size=(listwidth, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(5, 0), size=(listwidth, 3), font=26, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                        self.entries.append(res)
                    except IndexError:
                        pass

                self['episodes'].l.setList(self.entries)
                self['episodes'].show()
            else:
                self.session.openWithCallback(self.filter_return, filterSeasonList, self.seasons, self.content)

    def filter_return(self, filter):
        if filter and filter is not None:
            self.index = 0
            if screenwidth.width() >= 1280:
                self.posterindex = 6
            else:
                self.posterindex = 5
            self.makeMovies(filter)
        return

    def switchStyle(self):
        if self.ready is True:
            self.ready = False
            self.session.openWithCallback(self.returnStyle, switchScreen, 3, 'style')

    def returnStyle(self, number):
        if number is None or number == 2:
            self.ready = True
        elif number == 3:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserPosterwall, self.index, self.content, self.filter)
        elif number == 1:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserMetrix, self.index, self.content, self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(self.returnContent, switchScreen, 3, 'content')

    def returnContent(self, number):
        if number is None:
            self.ready = True
        elif number == 1 and self.content != ':::Movie:Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.filter = ':::Movie:Top:::'
                self.content = ':::Movie:Top:::'
                self.index = 0
                if screenwidth.width() >= 1280:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.plotfull = True
                    self.episodes = True
                    self.toggleCount = 1
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.plotfull = True
                    self.episodes = False
                    self.toggleCount = 0
                else:
                    self.plotfull = False
                    self.episodes = False
                    self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Movie:Top:::', ':::Movie:Top:::')
        elif number == 2 and self.content != ':::Series:Top:::':
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.filter = ':::Series:Top:::'
                self.content = ':::Series:Top:::'
                self.index = 0
                if screenwidth.width() >= 1280:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.plotfull = True
                    self.episodes = True
                    self.toggleCount = 1
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.plotfull = True
                    self.episodes = False
                    self.toggleCount = 0
                else:
                    self.plotfull = False
                    self.episodes = False
                    self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif number == 3 and self.content != ':Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':Top:::', ':Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.filter = ':Top:::'
                self.content = ':Top:::'
                self.index = 0
                if screenwidth.width() >= 1280:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.plotfull = True
                    self.episodes = True
                    self.toggleCount = 1
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.plotfull = True
                    self.episodes = False
                    self.toggleCount = 0
                else:
                    self.plotfull = False
                    self.episodes = False
                    self.toggleCount = 0
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':Top:::', ':Top:::')
        else:
            self.ready = True
        return

    def editDatabase(self):
        if self.ready is True:
            try:
                movie = self.movielist[self.index]
            except IndexError:
                movie = 'None'

            self.session.openWithCallback(self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            self.sortDatabase()
            f = open(DATABASE_PATH, 'r')
            count = 0
            for line in f:
                if self.content in line and self.filter in line:
                    if movie in line:
                        self.index = count
                        break
                    count += 1

            f.close()
            self.makeMovies(self.filter)

    def sortDatabase(self):
        with open(DATABASE_PATH, "r") as f:
            series_lines = [line for line in f if ":::Series:::" in line]

        with open(DATABASE_PATH + ".series", "w") as fseries:
            fseries.writelines(series_lines)

        with open(DATABASE_PATH + ".series", "r") as fseries:
            series = fseries.readlines()
        series.sort(key=lambda line: line.split(":::")[0])
        with open(DATABASE_PATH + ".series", "w") as fseries:
            fseries.writelines(series)

        with open(DATABASE_PATH, "r") as f:
            movies_lines = [line for line in f if ":::Series:::" not in line]

        with open(DATABASE_PATH + ".movies", "w") as fmovies:
            fmovies.writelines(movies_lines)

        with open(DATABASE_PATH + ".movies", "r") as fmovies:
            lines = fmovies.readlines()

        self.sortorder = config.plugins.moviebrowser.sortorder.value
        try:
            if self.sortorder == 'name':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower())
            elif self.sortorder == 'name_reverse':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower(), reverse=True)
            elif self.sortorder == 'rating':
                lines.sort(key=lambda line: line.split(':::')[4])
            elif self.sortorder == 'rating_reverse':
                lines.sort(key=lambda line: line.split(':::')[4], reverse=True)
            elif self.sortorder == 'year':
                lines.sort(key=lambda line: line.split(':::')[8])
            elif self.sortorder == 'year_reverse':
                lines.sort(key=lambda line: line.split(':::')[8], reverse=True)
            elif self.sortorder == 'date':
                lines.sort(key=lambda line: line.split(':::')[2])
            elif self.sortorder == 'date_reverse':
                lines.sort(key=lambda line: line.split(':::')[2], reverse=True)
            elif self.sortorder == 'folder':
                lines.sort(key=lambda line: line.split(':::')[1])
            elif self.sortorder == 'folder_reverse':
                lines.sort(key=lambda line: line.split(':::')[1], reverse=True)
            elif self.sortorder == 'runtime':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')))
            elif self.sortorder == 'runtime_reverse':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')), reverse=True)
        except IndexError:
            pass
        except ValueError:
            self.session.open(MessageBox, _('\nDatabase Error: Entry without runtime'), MessageBox.TYPE_ERROR)

        f = open(DATABASE_PATH + '.movies', 'w')
        f.writelines(lines)
        f.close()
        files = [DATABASE_PATH + '.movies', DATABASE_PATH + '.series']
        with open(DATABASE_PATH + '.sorted', 'w') as outfile:
            for name in files:
                with open(name, 'r') as infile:
                    outfile.write(infile.read())

        if fileExists(DATABASE_PATH + '.movies'):
            remove(DATABASE_PATH + '.movies')
        if fileExists(DATABASE_PATH + '.series'):
            remove(DATABASE_PATH + '.series')
        rename(DATABASE_PATH + '.sorted', DATABASE_PATH)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if PY3:
            link = link.encode()
        callInThread(threadGetPage, url=link, file=None, key=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.exit, movieBrowserConfig)

    def zap(self):
        if self.ready is True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)

    def showHelp(self):
        if self.showhelp is False:
            self.showhelp = True
            self.toogleHelp.show()
        else:
            self.showhelp = False
            self.toogleHelp.hide()

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        # Hide help if it's currently visible
        if self.showhelp:
            self.showhelp = False
            self.toogleHelp.hide()

        # Exit from full plot view
        elif config.plugins.moviebrowser.plotfull.value == 'hide' and not self.topseries and self.plotfull:
            self.toggleCount = 0
            try:
                content = self.contentlist[self.index]
                self.episodes = content == 'Series:Top'
            except IndexError:
                self.episodes = False
            self.plotfull = False
            self.control = False
            self.hidePlot()
            self.hideEPoster()

        # Exit from top series view
        elif self.topseries:
            self.topseries = False
            self.episodes = True
            self.plotfull = True
            self.control = True
            self.toggleCount = 1
            self.content = self.oldcontent
            self.filter = self.oldfilter
            self.index = self.topindex
            self.makeMovies(self.filter)

        # Final exit
        else:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, 'w') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value is True:
                with open(FILTER_PATH, 'w') as f:
                    f.write(self.filter)

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)

            self.session.deleteDialog(self.toogleHelp)

            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof

            self.close()


class movieBrowserPosterwall(Screen):

    def __init__(self, session, index, content, filter):
        skincontent = ''
        if screenwidth.width() >= 1920:
            self.xd = False
            self.spaceTop = 0
            self.spaceLeft = 16
            self.spaceX = 5
            self.spaceY = 5
            self.picX = 225
            self.picY = 338
            self.posterX = 8
            self.posterY = 3
            self.posterALL = 24
            self.posterREST = 0

            skincontent += '<screen name="movieBrowserPosterwall" position="center,center" size="1920,1080" flags="wfNoBorder" title="  ">'
            skincontent += ' <ePixmap pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/setup/default_backdrop.png" position="0,0" size="1920,1080" transparent="0" zPosition="-4"/>'
            skincontent += ' <widget name="backdrop" position="0,0" size="1920,1080" scale="1" alphatest="on" transparent="0" zPosition="-5"/>'
            skincontent += ' <!-- Titolo e Visto -->'
            skincontent += ' <widget name="name" position="503,930" size="915,143" font="Regular; 48" halign="center" valign="center" foregroundColor="yellow" backgroundColor="#000000" transparent="1" zPosition="3"/>'
            skincontent += ' <widget name="seen" position="1425,965" size="60,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/seen.png" transparent="1" alphatest="on" scale="1" zPosition="3"/>'
            skincontent += ' <!-- Info -->'
            skincontent += ' <widget name="ratings" position="98,986" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings.png" orientation="orHorizontal" alphatest="blend" zPosition="6"/>'
            skincontent += ' <widget name="ratingsback" position="98,986" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings_back.png" alphatest="blend" zPosition="5"/>'
            skincontent += ' <widget name="runtime" position="1500,930" size="180,143" font="Regular;30" halign="right" foregroundColor="yellow" transparent="1" zPosition="17"/>'
            skincontent += ' <widget name="country" position="1688,930" size="90,143" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="11"/>'
            skincontent += ' <widget name="year" position="1785,930" size="98,143" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="15"/>'
            skincontent += ' <widget name="plotfull" position="1116,130" size="746,500" font="Regular;28" foregroundColor="yellow" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="eposter" position="1113,80" size="750,563" alphatest="on" transparent="1" scale="1" zPosition="5"/>'
            skincontent += ' <widget name="banner" position="1113,80" size="750,138" alphatest="on" transparent="1" scale="1" zPosition="5"/>'
            skincontent += ' <widget name="episodes" position="1113,227" size="750,405" scrollbarMode="showNever" transparent="1" zPosition="5"/>'
            skincontent += ' <widget name="audiotype" position="124,795" size="120,57" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="videomode" position="259,795" size="75,57" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="videocodec" position="348,795" size="120,57" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="aspectratio" position="480,795" size="75,57" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="ddd" position="569,795" size="75,57" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="ddd2" position="37,795" size="75,57" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="9"/>'
            skincontent += ' <widget name="ratings_up" position="98,947" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings.png" orientation="orHorizontal" alphatest="blend" zPosition="6"/>'
            skincontent += ' <widget name="ratingsback_up" position="98,947" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings_back.png" alphatest="blend" zPosition="5"/>'
            skincontent += ' <widget name="2name" position="60,45" size="683,105" font="Regular;30" foregroundColor="yellow" valign="center" transparent="1" zPosition="13"/>'
            skincontent += ' <widget name="2seen" position="743,45" size="60,60" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="13"/>'
            skincontent += ' <widget name="2Rating" position="60,150" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="14"/>'
            skincontent += ' <widget name="2ratings" position="60,195" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings.png" orientation="orHorizontal" alphatest="blend" zPosition="6"/>'
            skincontent += ' <widget name="2ratingsback" position="60,195" size="315,32" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/pic/browser/ratings_back.png" alphatest="blend" zPosition="5"/>'
            skincontent += ' <widget name="2Director" position="60,255" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="18"/>'
            skincontent += ' <widget name="2director" position="60,300" size="480,42" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="19"/>'
            skincontent += ' <widget name="2Country" position="555,255" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="20"/>'
            skincontent += ' <widget name="2country" position="555,300" size="188,42" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="5"/>'
            skincontent += ' <widget name="2Actors" position="60,360" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="22"/>'
            skincontent += ' <widget name="2actors" position="60,405" size="480,153" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="23"/>'
            skincontent += ' <widget name="2Year" position="555,360" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="24"/>'
            skincontent += ' <widget name="2year" position="555,405" size="188,42" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="25"/>'
            skincontent += ' <widget name="2Runtime" position="555,465" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="26"/>'
            skincontent += ' <widget name="2runtime" position="555,510" size="188,42" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="27"/>'
            skincontent += ' <widget name="2Genres" position="60,570" size="188,42" font="Regular;30" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="28"/>'
            skincontent += ' <widget name="2genres" position="60,615" size="750,42" font="Regular;30" foregroundColor="yellow" transparent="1" zPosition="29"/>'
            skincontent += ' <widget name="2infoback" position="38,38" size="788,645" scale="1" alphatest="blend" transparent="1" zPosition="-1"/>'
            skincontent += ' <widget name="plotfullback" position="1095,38" size="788,645" scale="1" alphatest="blend" transparent="1" zPosition="-1"/>'
            skincontent += ' <widget name="infoback" position="0,780" size="1920,300" alphatest="blend" transparent="1" zPosition="2"/>'
            skincontent += ' <widget name="frame" position="0,0" size="225,338" zPosition="-2" alphatest="on"/>'

        else:
            # screenwidth.width() == 1280:
            self.xd = False
            self.spaceTop = 0
            self.spaceLeft = 16
            self.spaceX = 5
            self.spaceY = 5
            self.picX = 133
            self.picY = 200
            self.posterX = 9
            self.posterY = 3
            self.posterALL = 27
            self.posterREST = 0
            skincontent += ' <screen name="movieBrowserPosterwall" position="center,center" size="1280,720" flags="wfNoBorder" title="  ">'
            skincontent += ' <widget name="backdrop" position="0,0" size="1280,720" scale="1" alphatest="on" transparent="0" zPosition="-5"/>'
            skincontent += ' <widget name="infoback" position="5,620" size="1270,95" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/overlay.png" scale="1" alphatest="blend" transparent="1" zPosition="2"/>'
            skincontent += ' <widget name="plotfullback" position="730,25" size="525,430" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/overlay.png" scale="1" alphatest="blend" transparent="1" zPosition="-1"/>'
            skincontent += ' <widget name="episodes" position="742,151" size="500,270" scrollbarMode="showOnDemand" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="plotfull" position="745,40" size="500,393" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="ratings_up" position="65,641" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>'
            skincontent += ' <widget name="ratingsback_up" position="65,641" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>'
            skincontent += ' <widget name="audiotype" position="25,672" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="videomode" position="115,672" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="videocodec" position="175,672" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="aspectratio" position="265,672" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="ddd" position="25,672" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="ddd2" position="325,672" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>'
            skincontent += ' <widget name="ratings" position="65,657" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>'
            skincontent += ' <widget name="ratingsback" position="65,657" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>'
            skincontent += ' <widget name="name" position="335,620" size="610,95" font="Regular;28" foregroundColor="#FFFFFF" valign="center" halign="center" transparent="1" zPosition="5"/>'
            skincontent += ' <widget name="seen" position="950,643" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="6"/>'
            skincontent += ' <widget name="runtime" position="1000,620" size="120,95" font="Regular;26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="7"/>'
            skincontent += ' <widget name="country" position="1125,620" size="60,95" font="Regular;26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="8"/>'
            skincontent += ' <widget name="year" position="1190,620" size="65,95" font="Regular;26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="9"/>'
            skincontent += ' <widget name="2infoback" position="25,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1"/>'
            skincontent += ' <widget name="2name" position="40,30" size="455,70" font="Regular;28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="13"/>'
            skincontent += ' <widget name="2seen" position="495,30" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="13"/>'
            skincontent += ' <widget name="2Rating" position="40,100" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="14"/>'
            skincontent += ' <widget name="2ratings" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="15"/>'
            skincontent += ' <widget name="2ratingsback" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings_back.png" alphatest="on" zPosition="16"/>'
            skincontent += ' <widget name="2Director" position="40,170" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="18"/>'
            skincontent += ' <widget name="2director" position="40,200" size="320,28" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>'
            skincontent += ' <widget name="2Country" position="370,170" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="20"/>'
            skincontent += ' <widget name="2country" position="370,200" size="125,28" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="21"/>'
            skincontent += ' <widget name="2Actors" position="40,240" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="22"/>'
            skincontent += ' <widget name="2actors" position="40,270" size="320,102" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="23"/>'
            skincontent += ' <widget name="2Year" position="370,240" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="24"/>'
            skincontent += ' <widget name="2year" position="370,270" size="125,28" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="25"/>'
            skincontent += ' <widget name="2Runtime" position="370,310" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="26"/>'
            skincontent += ' <widget name="2runtime" position="370,340" size="125,28" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="27"/>'
            skincontent += ' <widget name="2Genres" position="40,380" size="125,28" font="Regular;22" halign="left" foregroundColor="{color}" transparent="1" zPosition="28"/>'
            skincontent += ' <widget name="2genres" position="40,410" size="500,28" font="Regular;22" foregroundColor="#FFFFFF" transparent="1" zPosition="29"/>'
            skincontent += ' <widget name="eposter" position="742,53" size="500,375" scale="1" alphatest="on" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="banner" position="742,53" size="500,92" scale="1" alphatest="on" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="frame" position="7,-9" size="160,230" scale="1" zPosition="-2" alphatest="on"/>'
        # else:
            # self.xd = True
            # self.spaceTop = 0
            # self.spaceLeft = 10
            # self.spaceX = 5
            # self.spaceY = 5
            # self.picX = 106
            # self.picY = 160
            # self.posterX = 9
            # self.posterY = 3
            # self.posterALL = 27
            # self.posterREST = 0
        self.positionlist = []
        numX = -1
        for x in range(self.posterALL):
            numY = x // self.posterX
            numX += 1
            if numX >= self.posterX:
                numX = 0
            posX = self.spaceLeft + self.spaceX + numX * (self.spaceX + self.picX)
            posY = self.spaceTop + self.spaceY + numY * (self.spaceY + self.picY)

            if screenwidth.width() >= 1920:
                self.positionlist.append((posX - 16, posY - 18))

            elif screenwidth.width() == 1280:
                self.positionlist.append((posX - 13, posY - 15))
            else:
                self.positionlist.append((posX - 8, posY - 10))
            skincontent += '<widget name="poster' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-54" transparent="1" alphatest="on" />'
            skincontent += '<widget name="poster_back' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-53" transparent="1" alphatest="blend" pixmap="%spic/browser/default_poster.png" />' % skin_directory
        skincontent += '\n</screen>'
        '''
        # skin_file = join(skin_path + "movieBrowserPosterwall.xml")
        # with open(skin_file, "r") as f:
            # self.skin = f.read()
        '''
        self.skin = skincontent
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.seenEOF})
        self.toogleHelp = self.session.instantiateDialog(helpScreen)
        self.hideflag = True
        self.ready = False
        self.renew = False
        self.startupdate = False
        self.reset = False
        self.tmdbposter = False
        self.topseries = False
        self.filterseen = False
        self.showhelp = False
        self.control = False
        self.index = index
        self.wallindex = self.index % self.posterALL
        self.pagecount = self.index // self.posterALL + 1
        self.oldwallindex = 0
        self.pagemax = 1
        self.content = content
        self.filter = filter
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value
        self.showfolder = config.plugins.moviebrowser.showfolder.getValue()
        self.backdrops = config.plugins.moviebrowser.backdrops.getValue()
        if content == ':::Series:Top:::':
            self.infofull = True
            self.plotfull = True
            self.episodes = True
        elif config.plugins.moviebrowser.plotfull.value == 'show':
            self.infofull = True
            self.plotfull = True
            self.episodes = False
        else:
            self.infofull = False
            self.plotfull = False
            self.episodes = False
        self.toggleCount = 0
        self.ABC = 'ABC'
        self.namelist = []
        self.movielist = []
        self.datelist = []
        self.infolist = []
        self.plotlist = []
        self.posterlist = []
        self.backdroplist = []
        self.contentlist = []
        self.seenlist = []
        self.medialist = []
        self.dddlist = []
        self['name'] = Label()
        self['runtime'] = Label()
        self['country'] = Label()
        # self['Country'] = Label()
        self['year'] = Label()
        self['seen'] = Pixmap()
        self['seen'].hide()
        self['ratings'] = ProgressBar()
        self['ratings'].hide()
        self['ratingsback'] = Pixmap()
        self['ratingsback'].hide()
        self['ratings_up'] = ProgressBar()
        self['ratings_up'].hide()
        self['ratingsback_up'] = Pixmap()
        self['ratingsback_up'].hide()
        self['infoback'] = Pixmap()
        self['frame'] = Pixmap()
        self['backdrop'] = Pixmap()
        self.oldbackdropurl = ''
        for x in range(self.posterALL):
            self['poster' + str(x)] = Pixmap()
            self['poster_back' + str(x)] = Pixmap()
        self['2name'] = Label()
        self['2seen'] = Pixmap()
        self['2seen'].hide()
        self['2Director'] = Label(_('Director:'))
        self['2Actors'] = Label(_('Actors:'))
        self['2Year'] = Label(_('Years:'))
        self['2Runtime'] = Label(_('Runtime:'))
        self['2Country'] = Label(_('Country:'))
        self['2Genres'] = Label(_('Genres:'))
        self['2Rating'] = Label(_('Rating:'))
        self['2Director'].hide()
        self['2Actors'].hide()
        self['2Year'].hide()
        self['2Runtime'].hide()
        self['2Country'].hide()
        self['2Genres'].hide()
        self['2Rating'].hide()
        self['2director'] = Label()
        self['2actors'] = Label()
        self['2year'] = Label()
        self['2runtime'] = Label()
        self['2country'] = Label()
        self['2genres'] = Label()
        self['2ratings'] = ProgressBar()
        self['2ratings'].hide()
        self['2ratingsback'] = Pixmap()
        self['2ratingsback'].hide()
        self['2infoback'] = Pixmap()
        self['2infoback'].hide()
        self['plotfull'] = ScrollLabel()
        self['plotfull'].hide()
        self['plotfullback'] = Pixmap()
        self['plotfullback'].hide()
        self['eposter'] = Pixmap()
        self['eposter'].hide()
        self['banner'] = Pixmap()
        self['banner'].hide()
        self['episodes'] = ItemList([])
        self['episodes'].hide()
        self['ddd'] = Pixmap()
        self['ddd'].hide()
        self['ddd2'] = Pixmap()
        self['ddd2'].hide()
        self['audiotype'] = MultiPixmap()
        self['videomode'] = MultiPixmap()
        self['videocodec'] = MultiPixmap()
        self['aspectratio'] = MultiPixmap()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'InfobarActions', 'InfobarTeletextActions', 'MovieSelectionActions', 'MoviePlayerActions', 'InfobarEPGActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.PageUp,
            'prevBouquet': self.PageDown,
            'nextMarker': self.gotoABC,
            'prevMarker': self.gotoXYZ,
            'red': self.switchStyle,
            'yellow': self.updateDatabase,
            'blue': self.hideScreen,
            'contextMenu': self.config,
            'showEventInfo': self.toggleInfo,
            'EPGPressed': self.toggleInfo,
            'startTeletext': self.editDatabase,
            'showMovies': self.updateDatabase,
            'showRadio': self.deleteMovie,
            'leavePlayer': self.markSeen,
            '1': self.controlMovies,
            '2': self.renewTMDb,
            '3': self.renewTVDb,
            '4': self.filterSeen,
            '5': self.toogleContent,
            '6': self.filterFolder,
            '7': self.filterDirector,
            '8': self.filterActor,
            '9': self.filterGenre,
            '0': self.gotoEnd,
            'bluelong': self.showHelp,
            'displayHelp': self.showHelp
        }, -1)

        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        # BLACKLIST_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        # self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        # self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(DATABASE_PATH):
            size = getsize(DATABASE_PATH)
            if size < 10:
                remove(DATABASE_PATH)

        if fileExists(infosmallBackPNG):
            if self["infoback"].instance:
                self["infoback"].instance.setPixmapFromFile(infosmallBackPNG)
                self['infoback'].show()

        if fileExists(infoBackPNG):
            if self["2infoback"].instance:
                self["2infoback"].instance.setPixmapFromFile(infoBackPNG)
                self['2infoback'].hide()

        if fileExists(infoBackPNG):
            if self["plotfullback"].instance:
                self["plotfullback"].instance.setPixmapFromFile(infoBackPNG)
                self['plotfullback'].hide()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
            self.session.nav.stopService()

        if fileExists(DATABASE_PATH):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value is True:
                    self.filter = open(FILTER_PATH).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(LAST_PATH).read()
                    movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                    data = open(DATABASE_PATH).read()
                    count = 0
                    for line in data.split('\n'):
                        if self.content in line and self.filter in line:
                            if search(movie, line) is not None:
                                self.index = count
                                break
                            count += 1

                    if movie.endswith('...'):
                        self.index = count
                    self.wallindex = self.index % self.posterALL
                    self.pagecount = self.index // self.posterALL + 1
                elif config.plugins.moviebrowser.lastmovie.value == 'folder' and self.showfolder is True:
                    self.index = sum((1 for line in open(DATABASE_PATH)))
                    self.wallindex = self.index % self.posterALL
                    self.pagecount = self.index // self.posterALL + 1
            self.makeMovieBrowserTimer = eTimer()
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)

        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(DATABASE_RESET, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.exit, movieBrowserConfig)
        else:
            OnclearMem()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(DATABASE_RESET):
                remove(DATABASE_RESET)
            if fileExists(BLACKLIST_PATH):
                remove(BLACKLIST_PATH)
            open(DATABASE_PATH, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            self.close()

    def makeMovies(self, filter):
        if filter is not None:
            self.namelist = []
            self.movielist = []
            self.datelist = []
            self.infolist = []
            self.plotlist = []
            self.posterlist = []
            self.backdroplist = []
            self.contentlist = []
            self.seenlist = []
            self.medialist = []
            self.dddlist = []
            self.filter = filter
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        if self.content in line and filter in line:
                            name = ""
                            filename = ""
                            date = ""
                            runtime = ""
                            rating = ""
                            director = ""
                            actors = ""
                            genres = ""
                            year = ""
                            country = ""
                            plotfull = ""
                            poster = str(default_poster)
                            backdrop = str(default_backdrop)
                            seen = 'unseen'
                            content = 'Movie:Top'
                            media = '\n'
                            movieline = line.split(':::')
                            try:
                                name = movieline[0]
                                name = sub(r'[Ss][0]+[Ee]', 'Special ', name)
                                filename = movieline[1]
                                date = movieline[2]
                                runtime = movieline[3]
                                rating = movieline[4]
                                director = movieline[5]
                                actors = movieline[6]
                                genres = movieline[7]
                                year = movieline[8]
                                country = movieline[9]
                                plotfull = movieline[10]
                                poster = movieline[11]
                                backdrop = movieline[12]
                                content = movieline[13]
                                seen = movieline[14]
                                media = movieline[15]
                            except IndexError:
                                pass
                            self.namelist.append(name)
                            self.movielist.append(filename)
                            self.dddlist.append('yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director, actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)
                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(config.plugins.moviebrowser.moviefolder.value + '...')
                    self.datelist.append('')
                    res = []
                    res.append('')
                    res.append('0.0')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    res.append('')
                    self.infolist.append(res)
                    self.plotlist.append('')
                    self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser/default_folder.png')
                    self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png')
                    self.contentlist.append(':Top')
                    self.seenlist.append('unseen')
                    self.medialist.append('\n')
                self.maxentry = len(self.namelist)
                self.posterREST = self.maxentry % self.posterALL
                if self.posterREST == 0:
                    self.posterREST = self.posterALL
                self.pagemax = self.maxentry // self.posterALL
                if self.maxentry % self.posterALL > 0:
                    self.pagemax += 1
                self.makePoster(self.pagecount - 1)
                self.paintFrame()
                if self.backdrops != 'hide':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass

                else:
                    self.showDefaultBackdrop()
                try:
                    self.makeName(self.index)
                except IndexError:
                    pass

                try:
                    self.makeInfo(self.index)
                except IndexError:
                    pass

                try:
                    content = self.contentlist[self.index]
                    if content == 'Series:Top':
                        self.infofull = True
                        self.plotfull = True
                        self.episodes = True
                    if self.infofull is True:
                        self.makeInfo2(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                except IndexError:
                    pass

                self.ready = True
        OnclearMem()
        return

    def updateDatabase(self):
        if self.ready is True:
            if exists(config.plugins.moviebrowser.moviefolder.value) and exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, _('\nUpdate Movie Browser Database?'), MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, "w") as f:
                    f.write(movie)
            except IndexError:
                pass

            if fileExists(DATABASE_PATH):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)
        OnclearMem()

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value is True:
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()
        movie = open(LAST_PATH).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(DATABASE_PATH).read()
        count = 0
        self.index = 0
        for line in data.split('\n'):
            if self.content in line and self.filter in line:
                if search(movie, line) is not None:
                    self.index = count
                    break
                count += 1

        self.wallindex = self.index % self.posterALL
        self.pagecount = self.index // self.posterALL + 1
        self.oldwallindex = 0
        self.pagemax = 1
        if self.startupdate is True:
            self.startupdate = False
            self.makeMovieBrowserTimer.callback.append(self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.') % str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.') % str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.') % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                else:
                    self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(MessageBox, _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(MessageBox, _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        OnclearMem()
        return

    def ok(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    if self.infofull is False or self.plotfull is False:
                        self.infofull = True
                        self.plotfull = True
                        self.makeInfo2(self.index)
                        self.makePlot(self.index)
                    elif self.toggleCount == 1:
                        self.toggleCount = 0
                        self['plotfull'].hide()
                        self['banner'].show()
                        self['episodes'].show()
                        if len(self.seasons) != 0:
                            self.control = True
                    elif len(self.seasons) != 0:
                        self.topseries = True
                        self.episodes = False
                        self.control = False
                        self.toggleCount = 0
                        self.topwallindex = self.oldwallindex
                        self.oldcontent = self.content
                        self.oldfilter = self.filter
                        self.topindex = self.index
                        self.index = 0
                        self.oldwallindex = 0
                        self.pagemax = 1
                        self.wallindex = self.index % self.posterALL
                        self.pagecount = self.index // self.posterALL + 1
                        self.content = ':::Series:::'
                        index = self['episodes'].getSelectedIndex()
                        current = self.seasons[index]
                        if current is not None:
                            current = sub('Specials', '(S00', current)
                            current = sub('specials', '(s00', current)
                            current = sub('Season ', '(S', current)
                            current = sub('season ', '(s', current)
                        else:
                            current = self.namelist[self.index]
                        self.makeMovies(current)
                else:
                    filename = self.movielist[self.index]
                    if self.showfolder is True and filename.endswith('...'):
                        self.filterFolder()
                        return
                    if filename.endswith('.ts'):
                        if fileExists(filename):
                            sref = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(self.getMediaInfo)
                    self.makeMovieBrowserTimer.start(2000, True)
            except IndexError:
                pass

        return

    def getMediaInfo(self):
        service = self.session.nav.getCurrentService()
        if service is not None:
            audiotype = ''
            videomode = ''
            videocodec = ''
            aspectratio = ''
            audio = service.audioTracks()
            if audio:
                try:
                    audioTrack = audio.getCurrentTrack()
                    if audioTrack is not None:
                        info = audio.getTrackInfo(audioTrack)
                        description = info.getDescription()
                        if 'AC3+' in description or 'Dolby Digital+' in description:
                            audiotype = 'dolbyplus'
                        elif 'AC3' in description or 'AC-3' in description or 'Dolby Digital' in description:
                            audiotype = 'dolby'
                        elif 'DTS-HD' in description:
                            audiotype = 'dtshd'
                        elif 'DTS' in description:
                            audiotype = 'dts'
                        else:
                            audiotype = 'mp2'
                except OverflowError:
                    audiotype = 'mp2'

            info = service and service.info()
            if info:
                height = info and info.getInfo(iServiceInformation.sVideoHeight)
                if str(height) == '1080':
                    videomode = '1080'
                elif str(height) == '720':
                    videomode = '720'
                else:
                    videomode = '480'
                aspect = info and info.getInfo(iServiceInformation.sAspect)
                if aspect in (3, 4, 7, 8, 11, 12, 15, 16):
                    aspectratio = '16_9'
                else:
                    aspectratio = '4_3'
            filename = self.movielist[self.index]
            if filename.endswith('.iso') or filename.endswith('.ISO'):
                videocodec = 'dvd'
            elif filename.endswith('.flv'):
                videocodec = 'flv'
            elif filename.endswith('.divx'):
                videocodec = 'divx'
            elif videomode == '480':
                videocodec = 'mpeg2'
            else:
                videocodec = 'h264'
            media = audiotype + ':' + videomode + ':' + videocodec + ':' + aspectratio
            self.medialist[self.index] = media
            info = media.split(':')
            try:
                if info[0] == 'dolby':
                    self['audiotype'].setPixmapNum(0)
                elif info[0] == 'mp2':
                    self['audiotype'].setPixmapNum(4)
                elif info[0] == 'dts':
                    self['audiotype'].setPixmapNum(2)
                elif info[0] == 'dolbyplus':
                    self['audiotype'].setPixmapNum(1)
                else:
                    self['audiotype'].setPixmapNum(3)
            except IndexError:
                self['audiotype'].setPixmapNum(4)

            try:
                if info[1] == '1080':
                    self['videomode'].setPixmapNum(0)
                elif info[1] == '720':
                    self['videomode'].setPixmapNum(1)
                else:
                    self['videomode'].setPixmapNum(2)
            except IndexError:
                self['videomode'].setPixmapNum(2)

            try:
                if info[2] == 'h264':
                    self['videocodec'].setPixmapNum(0)
                elif info[2] == 'mpeg2':
                    self['videocodec'].setPixmapNum(1)
                elif info[2] == 'divx':
                    self['videocodec'].setPixmapNum(2)
                elif info[2] == 'flv':
                    self['videocodec'].setPixmapNum(3)
                else:
                    self['videocodec'].setPixmapNum(4)
            except IndexError:
                self['videocodec'].setPixmapNum(1)

            try:
                if info[3] == '16_9':
                    self['aspectratio'].setPixmapNum(0)
                else:
                    self['aspectratio'].setPixmapNum(1)
            except IndexError:
                self['aspectratio'].setPixmapNum(1)

            self['audiotype'].show()
            self['videomode'].show()
            self['videocodec'].show()
            self['aspectratio'].show()
            self['ratings'].hide()
            self['ratingsback'].hide()
            try:
                ratings = self.infolist[self.index][1]
                try:
                    rating = int(10 * round(float(ratings), 1))
                except ValueError:
                    ratings = '0.0'
                    rating = int(10 * round(float(ratings), 1))

                self['ratings_up'].setValue(rating)
                self['ratings_up'].show()
                self['ratingsback_up'].show()
            except IndexError:
                self['ratings_up'].hide()

            if '3d' in filename.lower():
                self['ddd'].hide()
                self['ddd2'].show()
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + '.new', 'w') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, _('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                # self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (str(tmdb_api), name, self.language)
                print('renewTMDb  url tmdb =', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if PY3:
                output = urlopen(request, timeout=10).read().decode('utf-8')
            else:
                output = urlopen(request, timeout=10).read()
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w185', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = findall('"vote_average":(.*?),', output)
        year = findall('"release_date":"(.*?)"', output)
        titles = findall('"title":"(.*?)"', output)
        poster = findall('"poster_path":"(.*?)"', output)
        id = findall('"id":(.*?),', output)
        country = findall('"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == "movie":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = "https://api.themoviedb.org/3/movie/%s?api_key=%s" % (new, str(tmdb_api))
                print("makeTMDbUpdate  url tmdb =", url)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select in ("poster", "backdrop"):
                if select == "poster":
                    old_value = self.posterlist[self.index]
                else:
                    old_value = self.backdroplist[self.index]
                new_value = new
                database = open(DATABASE_PATH).read()
                database = database.replace(old_value, new_value)
                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(database)
                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                # self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (name, self.language)
                print('renewTVDb url =', url)
                self.getTVDbMovies(url)
            except IndexError:
                pass

    def getTVDbMovies(self, url):
        rating = []
        year = []
        titles = []
        poster = []
        id = []
        country = []
        request = Request(url, headers=agents)
        try:
            if PY3:
                output = urlopen(request, timeout=10).read().decode('utf-8')
            else:
                output = urlopen(request, timeout=10).read()
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        try:
            output = output.replace('&amp;', '&')
            seriesid = findall('<seriesid>(.*?)</seriesid>', output)
            for x in range(len(seriesid)):
                url = ('https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('getTVDbMovies  url tmdb =', url)
                request = Request(url, headers=agents)
                try:
                    if PY3:
                        output = urlopen(request, timeout=10).read().decode('utf-8')
                    else:
                        output = urlopen(request, timeout=10).read()
                except Exception:
                    output = ''

                output = sub('<poster>', '<poster>https://www.thetvdb.com/banners/_cache/', output)
                output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>' + wiki_png + '</poster>', output)
                output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
                output = sub('&amp;', '&', output)
                Rating = findall('<Rating>(.*?)</Rating>', output)
                Year = findall('<FirstAired>([0-9]+)-', output)
                Added = findall('<added>([0-9]+)-', output)
                Titles = findall('<SeriesName>(.*?)</SeriesName>', output)
                Poster = findall('<poster>(.*?)</poster>', output)
                TVDbid = findall('<id>(.*?)</id>', output)
                Country = findall('<Status>(.*?)</Status>', output)
                try:
                    rating.append(Rating[0])
                except IndexError:
                    rating.append('0.0')

                try:
                    year.append(Year[0])
                except IndexError:
                    try:
                        year.append(Added[0])
                    except IndexError:
                        year.append(' ')

                try:
                    titles.append(Titles[0])
                except IndexError:
                    titles.append(' ')

                try:
                    poster.append(Poster[0])
                except IndexError:
                    poster.append(str(wiki_png))

                try:
                    id.append(TVDbid[0])
                except IndexError:
                    id.append('0')
                try:
                    country.append(Country[0])
                except IndexError:
                    country.append(' ')
            titel = _('TheTVDb Results')
            if not titles:
                self.session.open(MessageBox, _('\nNo TheTVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            else:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, True)
                else:
                    self.session.openWithCallback(self.makeTVDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, False, False)
        except Exception as e:
            print('error get ', str(e))

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ('https://www.thetvdb.com/api/%s/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('makeTVDbUpdate  url tmdb =', url)
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return

                bannernew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(banner, bannernew)
                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(database)
                rename(DATABASE_PATH + ".new", DATABASE_PATH)

            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                with open(DATABASE_PATH + ".new", "w") as f:
                    f.write(database)
                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.renewFinished()
        return

    def renewFinished(self):
        self.wallindex = self.index % self.posterALL
        self.pagecount = self.index // self.posterALL + 1
        self.oldwallindex = 0
        self.pagemax = 1
        self.renew = False
        self.makeMovies(self.filter)

    def deleteMovie(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                    self.session.open(MessageBox, _('\nThe List of Movie Folder can not be deleted.'), MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def delete_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                content = self.contentlist[self.index]
                if fileExists(movie):
                    remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        remove(eitfile)
                    if fileExists(movie + '.ap'):
                        remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        remove(srtfile)
                data = open(DATABASE_PATH).read()
                if content == 'Series:Top':
                    for line in data.split('\n'):
                        if search(movie + '.*?:::Series:', line) is not None:
                            data = data.replace(line + '\n', '')

                else:
                    for line in data.split('\n'):
                        if search(movie, line) is not None:
                            data = data.replace(line + '\n', '')
                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)

                if self.index == self.maxentry - 1:
                    self.index = 0
                    self.oldwallindex = self.wallindex
                    self.wallindex = 0
                    self.pagecount = 1
                self.makeMovies(self.filter)
            except IndexError:
                pass

            self.ready = True
        else:
            self.blacklistMovie()
        return

    def blacklistMovie(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            try:
                name = self.namelist[self.index]
                self.session.openWithCallback(self.blacklist_return, MessageBox, _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(BLACKLIST_PATH):
                    fremove = open(BLACKLIST_PATH, 'a')
                else:
                    fremove = open(BLACKLIST_PATH, 'w')
                data = open(DATABASE_PATH).read()
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        fremove.write(line + '\n')
                        fremove.close()
                        data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)

                if self.index == self.maxentry - 1:
                    self.index = 0
                    self.oldwallindex = self.wallindex
                    self.wallindex = 0
                    self.pagecount = 1
                self.makeMovies(self.filter)
            except IndexError:
                pass

            self.ready = True
        return

    def markSeen(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        if self.infofull is True:
                            self['2seen'].show()
                    else:
                        newline = line.replace(':::seen:::', ':::unseen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'unseen')
                        self['seen'].hide()
                        if self.infofull is True:
                            self['2seen'].hide()
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + ".new", "w") as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        if self.infofull is True:
                            self['2seen'].show()
                        database = database.replace(line, newline)

            with open(DATABASE_PATH + ".new", "w") as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def toggleInfo(self):
        if self.ready is True:
            if self.infofull is False and self.plotfull is False:
                self.infofull = True
                if self.backdrops == 'info':
                    try:
                        self.showBackdrops(self.index)
                    except IndexError:
                        pass

                try:
                    self.makeInfo2(self.index)
                except IndexError:
                    self.showInfo2()

            elif self.infofull is True and self.plotfull is False:
                self.plotfull = True
                try:
                    self.makePlot(self.index)
                except IndexError:
                    pass

            elif self.infofull is True and self.plotfull is True and self.toggleCount == 0:
                self.toggleCount = 1
                self.control = False
                self['banner'].hide()
                self['episodes'].hide()
                self['eposter'].hide()
                self['plotfull'].show()

            elif self.infofull is True and self.plotfull is True and self.toggleCount == 1:
                self.toggleCount = 0
                self.infofull = False
                self.plotfull = False
                self.hideInfo2()
                self.hidePlot()

    def showInfo2(self):
        self['2name'].show()
        try:
            seen = self.seenlist[self.index]
            if seen == 'seen':
                self['2seen'].show()
            else:
                self['2seen'].hide()
        except IndexError:
            self['2seen'].hide()
        self['2runtime'].show()
        self['2Runtime'].show()
        self['2ratings'].show()
        self['2ratingsback'].show()
        self['2Rating'].show()
        self['2director'].show()
        self['2Director'].show()
        self['2actors'].show()
        self['2Actors'].show()
        self['2genres'].show()
        self['2Genres'].show()
        self['2year'].show()
        self['2Year'].show()
        self['2country'].show()
        self['2Country'].show()
        self['2infoback'].show()

    def hideInfo2(self):
        self['2name'].hide()
        self['2seen'].hide()
        self['2runtime'].hide()
        self['2Runtime'].hide()
        self['2ratings'].hide()
        self['2ratingsback'].hide()
        self['2Rating'].hide()
        self['2director'].hide()
        self['2Director'].hide()
        self['2actors'].hide()
        self['2Actors'].hide()
        self['2genres'].hide()
        self['2Genres'].hide()
        self['2year'].hide()
        self['2Year'].hide()
        self['2country'].hide()
        self['2Country'].hide()
        self['2infoback'].hide()

    def hidePlot(self):
        self['eposter'].hide()
        self['plotfull'].hide()
        self['plotfullback'].hide()

    def makeName(self, count):
        try:
            name = self.namelist[count]
            if screenwidth.width() >= 1280:
                if len(name) > 137:
                    if name[136:137] == ' ':
                        name = name[0:136]
                    else:
                        name = name[0:137] + 'FIN'
                        name = sub(' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 64:
                if name[63:64] == ' ':
                    name = name[0:63]
                else:
                    name = name[0:64] + 'FIN'
                    name = sub(' \\S+FIN', '', name)
                name = name + ' ...'
            self['name'].setText(str(name))
            self['name'].show()
            self.setTitle(str(name))
        except IndexError:
            self['name'].hide()

        try:
            seen = self.seenlist[count]
            if seen == 'seen':
                self['seen'].show()
            else:
                self['seen'].hide()
        except IndexError:
            self['seen'].hide()

    def makeInfo(self, count):
        try:
            runtime = self.infolist[count][0]
            if self.showfolder is True and runtime == '':
                self['runtime'].hide()
                self['year'].hide()
                self['country'].hide()
                # self['Country'].hide()
                self['ddd'].hide()
                self['ddd2'].hide()
                self['audiotype'].hide()
                self['videomode'].hide()
                self['videocodec'].hide()
                self['aspectratio'].hide()
                self['ratings_up'].hide()
                self['ratingsback_up'].hide()
                return
            runtime = '(' + runtime + ')'
            self['runtime'].setText(runtime)
            self['runtime'].show()
        except IndexError:
            self['runtime'].hide()

        try:
            year = self.infolist[count][5]
            self['year'].setText(year)
            self['year'].show()
        except IndexError:
            self['year'].hide()

        try:
            country = self.infolist[count][6]
            self['country'].setText(country)
            self['country'].show()
        except IndexError:
            self['country'].hide()

        ddd = self.dddlist[self.index]
        media = self.medialist[self.index]
        if media != '\n':
            self['ratings'].hide()
            self['ratingsback'].hide()

            try:
                ratings = self.infolist[count][1]
                try:
                    rating = int(10 * round(float(ratings), 1))
                except ValueError:
                    ratings = '0.0'
                    rating = int(10 * round(float(ratings), 1))

                self['ratings_up'].setValue(rating)
                self['ratings_up'].show()
                self['ratingsback_up'].show()
            except IndexError:
                self['ratings_up'].hide()

            info = media.split(':')

            try:
                if info[0] == 'dolby':
                    self['audiotype'].setPixmapNum(0)
                elif info[0] == 'mp2':
                    self['audiotype'].setPixmapNum(4)
                elif info[0] == 'dts':
                    self['audiotype'].setPixmapNum(2)
                elif info[0] == 'dolbyplus':
                    self['audiotype'].setPixmapNum(1)
                else:
                    self['audiotype'].setPixmapNum(3)
            except IndexError:
                self['audiotype'].setPixmapNum(4)

            try:
                if info[1] == '1080':
                    self['videomode'].setPixmapNum(0)
                elif info[1] == '720':
                    self['videomode'].setPixmapNum(1)
                else:
                    self['videomode'].setPixmapNum(2)
            except IndexError:
                self['videomode'].setPixmapNum(2)

            try:
                if info[2] == 'h264':
                    self['videocodec'].setPixmapNum(0)
                elif info[2] == 'mpeg2':
                    self['videocodec'].setPixmapNum(1)
                elif info[2] == 'divx':
                    self['videocodec'].setPixmapNum(2)
                elif info[2] == 'flv':
                    self['videocodec'].setPixmapNum(3)
                else:
                    self['videocodec'].setPixmapNum(4)
            except IndexError:
                self['videocodec'].setPixmapNum(1)

            try:
                if info[3] == '16_9':
                    self['aspectratio'].setPixmapNum(0)
                else:
                    self['aspectratio'].setPixmapNum(1)
            except IndexError:
                self['aspectratio'].setPixmapNum(1)

            self['audiotype'].show()
            self['videomode'].show()
            self['videocodec'].show()
            self['aspectratio'].show()
            if ddd == 'yes':
                self['ddd'].hide()
                self['ddd2'].show()
            else:
                self['ddd'].hide()
                self['ddd2'].hide()
        else:
            self['audiotype'].hide()
            self['videomode'].hide()
            self['videocodec'].hide()
            self['aspectratio'].hide()
            if ddd == 'yes':
                self['ddd'].show()
                self['ddd2'].hide()
                self['ratings'].hide()
                self['ratingsback'].hide()

                try:
                    ratings = self.infolist[count][1]
                    try:
                        rating = int(10 * round(float(ratings), 1))
                    except ValueError:
                        ratings = '0.0'
                        rating = int(10 * round(float(ratings), 1))

                    self['ratings_up'].setValue(rating)
                    self['ratings_up'].show()
                    self['ratingsback_up'].show()
                except IndexError:
                    self['ratings_up'].hide()

            else:
                self['ddd'].hide()
                self['ddd2'].hide()
                self['ratings_up'].hide()
                self['ratingsback_up'].hide()
                try:
                    ratings = self.infolist[count][1]
                    try:
                        rating = int(10 * round(float(ratings), 1))
                    except ValueError:
                        ratings = '0.0'
                        rating = int(10 * round(float(ratings), 1))

                    self['ratings'].setValue(rating)
                    self['ratings'].show()
                    self['ratingsback'].show()
                except IndexError:
                    self['ratings'].hide()

    def makeInfo2(self, count):
        try:
            self['2infoback'].show()
            name = self.namelist[count]
            if self.showfolder is True and name.startswith('<'):
                self['2name'].setText(name)
                self['2name'].show()
                self['2Runtime'].hide()
                self['2runtime'].hide()
                self['2Rating'].hide()
                self['2ratings'].hide()
                self['2ratingsback'].hide()
                self['2Director'].hide()
                self['2director'].hide()
                self['2Actors'].hide()
                self['2actors'].hide()
                self['2Genres'].hide()
                self['2genres'].hide()
                self['2Year'].hide()
                self['2year'].hide()
                self['2Country'].hide()
                self['2country'].hide()
                return

            if screenwidth.width() >= 1280:
                if len(name) > 63:
                    if name[62:63] == ' ':
                        name = name[0:62]
                    else:
                        name = name[0:63] + 'FIN'
                        name = sub(' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 66:
                if name[65:66] == ' ':
                    name = name[0:65]
                else:
                    name = name[0:66] + 'FIN'
                    name = sub(' \\S+FIN', '', name)
                name = name + ' ...'
            self['2name'].setText(str(name))
            self['2name'].show()
        except IndexError:
            self['2name'].hide()

        try:
            seen = self.seenlist[count]
            if seen == 'seen':
                self['2seen'].show()
            else:
                self['2seen'].hide()
        except IndexError:
            self['2seen'].hide()

        try:
            runtime = self.infolist[count][0]
            self['2Runtime'].show()
            self['2runtime'].setText(runtime)
            self['2runtime'].show()
        except IndexError:
            self['2Runtime'].hide()
            self['2runtime'].hide()

        try:
            ratings = self.infolist[count][1]
            try:
                rating = int(10 * round(float(ratings), 1))
            except ValueError:
                ratings = '0.0'
                rating = int(10 * round(float(ratings), 1))

            self['2Rating'].show()
            self['2ratings'].setValue(rating)
            self['2ratings'].show()
            self['2ratingsback'].show()
        except IndexError:
            self['2Rating'].hide()
            self['2ratings'].hide()

        try:
            director = self.infolist[count][2]
            self['2Director'].show()
            self['2director'].setText(director)
            self['2director'].show()
        except IndexError:
            self['2Director'].hide()
            self['2director'].hide()

        try:
            actors = self.infolist[count][3]
            self['2Actors'].show()
            self['2actors'].setText(actors)
            self['2actors'].show()
        except IndexError:
            self['2Actors'].hide()
            self['2actors'].hide()

        try:
            genres = self.infolist[count][4]
            self['2Genres'].show()
            self['2genres'].setText(genres)
            self['2genres'].show()
        except IndexError:
            self['2Genres'].hide()
            self['2genres'].hide()

        try:
            year = self.infolist[count][5]
            self['2Year'].show()
            self['2year'].setText(year)
            self['2year'].show()
        except IndexError:
            self['2Year'].hide()
            self['2year'].hide()

        try:
            country = self.infolist[count][6]
            self['2Country'].show()
            self['2country'].setText(country)
            self['2country'].show()
        except IndexError:
            self['2Country'].hide()
            self['2country'].hide()

    def makePlot(self, index):
        self['plotfullback'].show()
        try:
            plot = self.plotlist[self.index]
            self['plotfull'].setText(plot)
        except IndexError:
            pass

        self['plotfull'].hide()
        self.makeEPoster()
        return

    def makeEPoster(self):
        if self.content == ':::Movie:Top:::':
            self.toggleCount = 1
            self['eposter'].hide()
            self['banner'].hide()
            self['episodes'].hide()
            self['plotfull'].show()
        elif self.content == ':::Series:Top:::':
            self.toggleCount = 0
            try:
                posterurl = self.posterlist[self.index]
                if search('<episode>', posterurl) is not None:
                    bannerurl = search('<episode>(.*?)<episode>', posterurl)
                    bannerurl = bannerurl.group(1)
                    banner = sub('.*?[/]', '', bannerurl)
                    banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                    if fileExists(banner):
                        self["banner"].instance.setPixmapFromFile(banner)
                        self['banner'].show()
                    else:
                        if PY3:
                            bannerurl = bannerurl.encode()
                        callInThread(threadGetPage, url=bannerurl, file=banner, key=None, success=self.getBanner, fail=self.downloadError)
                else:
                    self['banner'].hide()
            except IndexError:
                pass

            self.filterSeasons()
        elif self.content == ':Top:::':
            try:
                content = self.contentlist[self.index]
                if content == 'Movie:Top':
                    self.toggleCount = 1
                    self.episodes = False
                    self.control = False
                    self['eposter'].hide()
                    self['banner'].hide()
                    self['episodes'].hide()
                    self['plotfull'].show()
                else:
                    self.toggleCount = 0
                    self.episodes = True
                    posterurl = self.posterlist[self.index]
                    if search('<episode>', posterurl) is not None:
                        bannerurl = search('<episode>(.*?)<episode>', posterurl)
                        bannerurl = bannerurl.group(1)
                        banner = sub('.*?[/]', '', bannerurl)
                        banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                        if fileExists(banner):
                            self["banner"].instance.setPixmapFromFile(banner)
                            self['banner'].show()
                        else:
                            if PY3:
                                bannerurl = bannerurl.encode()
                            callInThread(threadGetPage, url=bannerurl, file=banner, key=None, success=self.getBanner, fail=self.downloadError)
                    else:
                        self['banner'].hide()
                    self.filterSeasons()
            except IndexError:
                pass

        else:
            self.toggleCount = 0
            self['banner'].hide()
            self['episodes'].hide()
            self['plotfull'].hide()
            try:
                posterurl = self.posterlist[self.index]
                if search('<episode>', posterurl) is not None:
                    eposterurl = search('<episode>(.*?)<episode>', posterurl)
                    eposterurl = eposterurl.group(1)
                    eposter = sub('.*?[/]', '', eposterurl)
                    eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                    if fileExists(eposter):
                        self["eposter"].instance.setPixmapFromFile(eposter)
                        self['eposter'].show()
                    else:
                        if PY3:
                            eposterurl = eposterurl.encode()
                        callInThread(threadGetPage, url=eposterurl, file=eposter, key=None, success=self.getEPoster, fail=self.downloadError)
                else:
                    self.toggleCount = 1
                    self['eposter'].hide()
                    self['banner'].hide()
                    self['episodes'].hide()
                    self['plotfull'].show()
            except IndexError:
                pass

        return

    def getEPoster(self, output, eposter):
        try:
            open(eposter, 'wb').write(output)
            if fileExists(eposter):
                self["eposter"].instance.setPixmapFromFile(eposter)
                self['eposter'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
            self['eposter'].hide()
        return

    def getBanner(self, output, banner):
        try:
            open(banner, 'wb').write(output)
            if fileExists(banner):
                self["banner"].instance.setPixmapFromFile(banner)
                self['banner'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
            self['banner'].hide()
        return

    def makePoster(self, page):
        for x in range(self.posterALL):
            try:
                index = x + page * self.posterALL
                posterurl = self.posterlist[index]
                posterurl = sub('<episode>.*?<episode>', '', posterurl)
                poster = sub('.*?[/]', '', posterurl)
                poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
                if fileExists(poster):
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
                else:
                    if PY3:
                        posterurl = posterurl.encode()
                    callInThread(threadGetPage, url=posterurl, file=poster, key=x, success=self.getPoster, fail=self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        self['poster_back' + str(self.wallindex)].hide()
        return

    def getPoster(self, output, poster, x):
        try:
            open(poster, 'wb').write(output)
            if fileExists(poster):
                if self['poster' + str(x)].instance:
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
        except Exception as e:
            print('error ', str(e))
            self['poster' + str(x)].hide()
        return

    def paintFrame(self):
        try:
            pos = self.positionlist[self.wallindex]
            self['frame'].instance.move(ePoint(pos[0], pos[1]))
            self['poster_back' + str(self.oldwallindex)].show()
            self['poster_back' + str(self.wallindex)].hide()
            posterurl = self.posterlist[self.index]
            posterurl = sub('<episode>.*?<episode>', '', posterurl)
            poster = sub('.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                self["frame"].instance.setPixmapFromFile(poster)
                self['frame'].show()
        except IndexError:
            pass

        return

    def showBackdrops(self, index):
        try:
            backdropurl = self.backdroplist[index]
            if backdropurl != self.oldbackdropurl:
                self.oldbackdropurl = backdropurl
                backdrop = sub('.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        if PY3:
                            backdropurl = backdropurl.encode()
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        popen('/usr/bin/showiframe %s') % no_m1v
                elif fileExists(backdrop):
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
                else:
                    if PY3:
                        backdropurl = backdropurl.encode()
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            open(backdrop, 'wb').write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        backdrop = default_backdrop  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = default_backdropm1v  # config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
                popen('/usr/bin/showiframe %s') % no_m1v
        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def _updateUI(self):
        self.paintFrame()
        try:
            if self.backdrops == "auto":
                self.showBackdrops(self.index)
            if self.infofull is True:
                self.makeInfo2(self.index)
            if self.plotfull is True:
                self.makePlot(self.index)
            self.makeName(self.index)
            self.makeInfo(self.index)
        except IndexError:
            pass

    def updateUI(self):
        self._updateUI()

    def down(self):
        if not self.ready:
            return
        if self.control:
            self['episodes'].down()
        elif self.plotfull:
            self['plotfull'].pageDown()
        else:
            self.oldwallindex = self.wallindex
            self.wallindex += self.posterX
            if self.pagecount == self.pagemax - 1 and self.wallindex > self.posterALL + self.posterREST - 2:
                self.wallindex = self.posterREST - 1
                if self.wallindex < 0:
                    self.wallindex = 0
                self.pagecount += 1
                self.makePoster(self.pagecount - 1)
                self.index = self.maxentry - 1
            elif self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
                if self.wallindex >= self.posterX:
                    self.wallindex = self.wallindex % self.posterX
                self.pagecount = 1
                self.makePoster(self.pagecount - 1)
                if self.wallindex >= self.maxentry % self.posterX:
                    self.index += self.posterX + self.maxentry % self.posterX
                    if self.index >= self.maxentry:
                        self.index -= self.maxentry
                else:
                    self.index += self.maxentry % self.posterX
                    if self.index >= self.maxentry:
                        self.index -= self.maxentry
            elif self.wallindex > self.posterALL - 1:
                self.wallindex -= self.posterALL
                if self.wallindex < 0:
                    self.wallindex = 0
                self.pagecount += 1
                self.makePoster(self.pagecount - 1)
                self.index += self.posterX
                if self.index >= self.maxentry:
                    self.index -= self.maxentry
            else:
                self.index += self.posterX
                if self.index >= self.maxentry:
                    self.index -= self.maxentry
            self._updateUI()

    def up(self):
        if not self.ready:
            return
        if self.control:
            self['episodes'].up()
        elif self.plotfull:
            self['plotfull'].pageUp()
        else:
            self.oldwallindex = self.wallindex
            self.wallindex -= self.posterX
            if self.wallindex < 0:
                if self.pagecount == 1:
                    if self.oldwallindex < self.posterREST % self.posterX:
                        self.wallindex = (self.posterREST // self.posterX) * self.posterX + self.oldwallindex
                        if self.wallindex < 0:
                            self.wallindex = 0
                        self.index -= self.posterREST % self.posterX
                        if self.index < 0:
                            self.index += self.maxentry
                    else:
                        self.wallindex = self.posterREST - 1
                        if self.wallindex < 0:
                            self.wallindex = 0
                        self.index = self.maxentry - 1
                    self.pagecount = self.pagemax
                    self.makePoster(self.pagecount - 1)
                else:
                    self.wallindex += self.posterALL
                    if self.wallindex < 0:
                        self.wallindex = 0
                    self.pagecount -= 1
                    self.makePoster(self.pagecount - 1)
                    self.index -= self.posterX
                    if self.index < 0:
                        self.index += self.maxentry
            else:
                self.index -= self.posterX
                if self.index < 0:
                    self.index += self.maxentry
            self._updateUI()

    def rightDown(self):
        if not self.ready:
            return
        self.oldwallindex = self.wallindex
        self.wallindex += 1
        if self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
            self.wallindex = 0
            self.pagecount = 1
            self.makePoster(self.pagecount - 1)
        elif self.wallindex == self.posterALL:
            self.wallindex = 0
            self.pagecount += 1
            self.makePoster(self.pagecount - 1)
        self.index += 1
        if self.index == self.maxentry:
            self.index = 0
        self._updateUI()

    def leftUp(self):
        if not self.ready:
            return
        self.oldwallindex = self.wallindex
        self.wallindex -= 1
        if self.wallindex < 0:
            if self.pagecount == 1:
                self.wallindex = self.posterREST - 1
                self.pagecount = self.pagemax
            else:
                self.wallindex = self.posterALL - 1
                self.pagecount -= 1
            if self.wallindex < 0:
                self.wallindex = 0
            self.makePoster(self.pagecount - 1)
        self.index -= 1
        if self.index < 0:
            self.index = self.maxentry - 1
        self._updateUI()

    def PageDown(self):
        if not self.ready:
            return
        self.oldwallindex = self.wallindex
        self.wallindex += self.posterALL
        if self.pagecount == self.pagemax - 1 and self.wallindex > self.posterALL + self.posterREST - 2:
            self.wallindex = self.posterREST - 1
            if self.wallindex < 0:
                self.wallindex = 0
            self.pagecount += 1
            self.makePoster(self.pagecount - 1)
            self.index = self.maxentry - 1
        elif self.pagecount == self.pagemax and self.wallindex > self.posterREST - 1:
            if self.wallindex >= self.posterX:
                self.wallindex %= self.posterX
            self.pagecount = 1
            self.makePoster(self.pagecount - 1)
            if self.wallindex >= self.maxentry % self.posterX:
                self.index = self.wallindex
                if self.index >= self.maxentry:
                    self.index -= self.maxentry
            else:
                self.index += self.maxentry % self.posterX
                if self.index >= self.maxentry:
                    self.index -= self.maxentry
        elif self.wallindex > self.posterALL - 1:
            self.wallindex -= self.posterALL
            if self.wallindex < 0:
                self.wallindex = 0
            self.pagecount += 1
            self.makePoster(self.pagecount - 1)
            self.index += self.posterALL
            if self.index >= self.maxentry:
                self.index -= self.maxentry
        else:
            self.index += self.posterALL
            if self.index >= self.maxentry:
                self.index -= self.maxentry
        self._updateUI()

    def PageUp(self):
        if not self.ready:
            return
        self.oldwallindex = self.wallindex
        self.wallindex -= self.posterALL
        if self.wallindex < 0:
            if self.pagecount == 1:
                if self.oldwallindex < self.posterREST % self.posterX:
                    self.wallindex = (self.posterREST // self.posterX) * self.posterX + self.oldwallindex
                    if self.wallindex < 0:
                        self.wallindex = 0
                    self.index -= self.posterREST % self.posterX
                    if self.index < 0:
                        self.index += self.maxentry
                else:
                    self.wallindex = self.posterREST - 1
                    if self.wallindex < 0:
                        self.wallindex = 0
                    self.index = self.maxentry - 1
                self.pagecount = self.pagemax
                self.makePoster(self.pagecount - 1)
            else:
                self.wallindex += self.posterALL
                if self.wallindex < 0:
                    self.wallindex = 0
                self.pagecount -= 1
                self.makePoster(self.pagecount - 1)
                self.index -= self.posterALL
                if self.index < 0:
                    self.index += self.maxentry
        else:
            self.index -= self.posterALL
            if self.index < 0:
                self.index += self.maxentry
        self._updateUI()

    def gotoEnd(self):
        if not self.ready:
            return
        self.oldwallindex = self.wallindex
        self.wallindex = self.posterREST - 1
        if self.wallindex < 0:
            self.wallindex = 0
        self.pagecount = self.pagemax
        self.makePoster(self.pagecount - 1)
        self.index = self.maxentry - 1
        self._updateUI()

    def controlMovies(self):
        if self.ready is True:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.open(MessageBox, _('Series Folder: No Info possible'), MessageBox.TYPE_ERROR)
                return

            self.movies = []
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, "r") as f:
                    for line in f:
                        if self.content in line and self.filter in line:
                            movieline = line.split(":::")
                            try:
                                self.movies.append((movieline[0], movieline[1], movieline[12]))
                            except IndexError:
                                pass

                if self.showfolder is True:
                    self.movies.append(("<List of Movie Folder>", config.plugins.moviebrowser.moviefolder.value + "...", str(default_backdrop)))
                self.session.openWithCallback(self.gotoMovie, movieControlList, self.movies, self.index, self.content)

    def gotoMovie(self, index, rebuild):
        if index is not None:
            self.index = index
            if rebuild is True:
                if self.index == self.maxentry - 1:
                    self.index = 0
                    self.oldwallindex = self.wallindex
                    self.wallindex = 0
                    self.pagecount = 1
                self.makeMovies(self.filter)
            else:
                self.oldwallindex = self.wallindex
                self.wallindex = self.index % self.posterALL
                self.pagecount = self.index // self.posterALL + 1
                self.makePoster(self.pagecount - 1)
                self.paintFrame()
                try:
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    if self.infofull is True:
                        self.makeInfo2(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                except IndexError:
                    pass

        return

    def gotoABC(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, False)

    def gotoXYZ(self):
        self.session.openWithCallback(self.enterABC, getABC, self.ABC, True)

    def enterABC(self, ABC):
        if ABC is None:
            pass
        else:
            self.ABC = ABC
            ABC = ABC[0].lower()
            try:
                self.index = next((index for index, value in enumerate(self.namelist) if value.lower().replace('der ', '').replace('die ', '').replace('das ', '').replace('the ', '').startswith(ABC)))
                self.oldwallindex = self.wallindex
                self.wallindex = self.index % self.posterALL
                self.pagecount = self.index // self.posterALL + 1
                self.makePoster(self.pagecount - 1)
                self.paintFrame()
                try:
                    if self.backdrops == 'auto':
                        self.showBackdrops(self.index)
                    if self.infofull is True:
                        self.makeInfo2(self.index)
                    if self.plotfull is True:
                        self.makePlot(self.index)
                    self.makeName(self.index)
                    self.makeInfo(self.index)
                except IndexError:
                    pass

            except StopIteration:
                pass

        return

    def filterSeen(self):
        if self.ready is True:
            if self.filterseen is False:
                self.filterseen = True
                self.filter = ':::unseen:::'
                self.index = 0
                self.toggleCount = 0
                self.wallindex = 0
                self.oldwallindex = 0
                self.pagecount = 1
                self.pagemax = 1
                self.makeMovies(self.filter)
            else:
                self.filterseen = False
                self.filter = self.content
                self.index = 0
                self.toggleCount = 0
                self.wallindex = 0
                self.oldwallindex = 0
                self.pagecount = 1
                self.pagemax = 1
                self.makeMovies(self.filter)

    def filterFolder(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _('Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            genres = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            genre = movieline[7]
                        except IndexError:
                            genre = ' '

                        if genre != ' ':
                            genres = genres + genre + ', '

                self.genres = [i for i in genres.split(', ')]
                self.genres.sort()
                self.genres.pop(0)
                try:
                    last = self.genres[-1]
                    for i in range(len(self.genres) - 2, -1, -1):
                        if last == self.genres[i]:
                            del self.genres[i]
                        else:
                            last = self.genres[i]
                            if len(last) > max:
                                max = len(last)
                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _('Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            actors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            actor = movieline[6]
                        except IndexError:
                            actor = ' '

                        if actor != ' ':
                            actors = actors + actor + ', '
                self.actors = [i for i in actors.split(', ')]
                self.actors.sort()
                self.actors.pop(0)
                try:
                    last = self.actors[-1]
                    for i in range(len(self.actors) - 2, -1, -1):
                        if last == self.actors[i]:
                            del self.actors[i]
                        else:
                            last = self.actors[i]
                            if len(last) > max:
                                max = len(last)
                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _('Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub('Specials', '(S00', current)
                    current = sub('specials', '(s00', current)
                    current = sub('Season ', '(S', current)
                    filter = sub('season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            directors = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                max = 25
                for line in f:
                    if filter in line:
                        movieline = line.split(':::')
                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        if director != ' ':
                            directors = directors + director + ', '
                self.directors = [i for i in directors.split(', ')]
                self.directors.sort()
                self.directors.pop(0)
                try:
                    last = self.directors[-1]
                    for i in range(len(self.directors) - 2, -1, -1):
                        if last == self.directors[i]:
                            del self.directors[i]
                        else:
                            last = self.directors[i]
                            if len(last) > max:
                                max = len(last)

                except IndexError:
                    pass
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _('Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
                filter = sub('FIN', '', filter)
            content = ':::Series:::'
            seasons = ''
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                for line in f:
                    if line.startswith(filter) and content in line:
                        movieline = line.split(':::')
                        try:
                            season = movieline[0]
                            season = season + 'FIN'
                            season = sub('[(]S00', 'Specials', season)
                            season = sub('[(]s00', 'specials', season)
                            season = sub('[(]S', 'Season ', season)
                            season = sub('[(]s', 'season ', season)
                            season = sub('[Ee][0-9]+[)].*?FIN', '', season)
                            season = sub('FIN', '', season)
                            season = sub(',', '', season)
                        except IndexError:
                            season = ' '

                            if season.strip():
                                seasons += season + ', '
                seasons = seasons.rstrip(', ')
                self.seasons = [i for i in seasons.split(', ')]
                self.seasons.sort()
                self.seasons.pop(0)
                try:
                    last = self.seasons[-1]
                    for i in range(len(self.seasons) - 2, -1, -1):
                        if last == self.seasons[i]:
                            del self.seasons[i]
                        else:
                            last = self.seasons[i]

                except IndexError:
                    pass

            if self.episodes is True or self.content == ':::Series:::':
                self.control = True
                self['eposter'].hide()
                self['plotfull'].hide()
                self['plotfullback'].show()
                self['banner'].show()
                self.entries = []
                if config.plugins.moviebrowser.metrixcolor.value != '0x00000000':
                    backcolor = True
                    back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
                else:
                    backcolor = False
                if screenwidth.width() == 1920:
                    listwidth = 760
                elif screenwidth.width() == 1280:
                    listwidth = 500
                else:
                    listwidth = 440
                idx = 0
                for x in self.seasons:
                    idx += 1

                for i in range(idx):
                    try:
                        res = ['']
                        if screenwidth.width() == 1920:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(10, 0), size=(listwidth, 28), font=30, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(10, 0), size=(listwidth, 28), font=30, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(5, 0), size=(listwidth, 25), font=26, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(5, 0), size=(listwidth, 25), font=26, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.seasons[i]))
                        self.entries.append(res)
                    except IndexError:
                        pass

                self['episodes'].l.setList(self.entries)
                self['episodes'].show()
            else:
                self.session.openWithCallback(self.filter_return, filterSeasonList, self.seasons, self.content)

    def filter_return(self, filter):
        if filter and filter is not None:
            self['poster_back' + str(self.wallindex)].show()
            self.index = 0
            self.wallindex = 0
            self.oldwallindex = 0
            self.pagecount = 1
            self.pagemax = 1
            self.makeMovies(filter)
        return

    def switchStyle(self):
        if self.ready is True:
            self.ready = False
            self.session.openWithCallback(self.returnStyle, switchScreen, 1, 'style')

    def returnStyle(self, number):
        if number is None or number == 3:
            self.ready = True
        elif number == 1:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserMetrix, self.index, self.content, self.filter)
        elif number == 2:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserBackdrop, self.index, self.content, self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(self.returnContent, switchScreen, 3, 'content')

    def returnContent(self, number):
        if number is None:
            self.ready = True
        elif number == 1 and self.content != ':::Movie:Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            else:
                self.filter = ':::Movie:Top:::'
                self.content = ':::Movie:Top:::'
                self.index = 0
                self.wallindex = self.index % self.posterALL
                self.pagecount = self.index // self.posterALL + 1
                self.oldwallindex = 0
                self.pagemax = 1
                self.toggleCount = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = True
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = False
                else:
                    self.infofull = False
                    self.plotfull = False
                    self.episodes = False
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
        elif number == 2 and self.content != ':::Series:Top:::':
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
            else:
                self.filter = ':::Series:Top:::'
                self.content = ':::Series:Top:::'
                self.index = 0
                self.wallindex = self.index % self.posterALL
                self.pagecount = self.index // self.posterALL + 1
                self.oldwallindex = 0
                self.pagemax = 1
                self.toggleCount = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = True
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = False
                else:
                    self.infofull = False
                    self.plotfull = False
                    self.episodes = False
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
        elif number == 3 and self.content != ':Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':Top:::', ':Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':Top:::', ':Top:::')
            else:
                self.filter = ':Top:::'
                self.content = ':Top:::'
                self.index = 0
                self.wallindex = self.index % self.posterALL
                self.pagecount = self.index // self.posterALL + 1
                self.oldwallindex = 0
                self.pagemax = 1
                self.toggleCount = 0
                self.topseries = False
                if self.content == ':::Series:Top:::':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = True
                elif config.plugins.moviebrowser.plotfull.value == 'show':
                    self.infofull = True
                    self.plotfull = True
                    self.episodes = False
                else:
                    self.infofull = False
                    self.plotfull = False
                    self.episodes = False
                self.control = False
                self.renew = False
                self.makeMovies(self.filter)
        else:
            self.ready = True
        return

    def editDatabase(self):
        if self.ready is True:
            try:
                movie = self.movielist[self.index]
            except IndexError:
                movie = 'None'

            self.session.openWithCallback(self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub("\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
            self.sortDatabase()

            count = 0
            with open(DATABASE_PATH, "r") as f:
                for line in f:
                    if self.content in line and self.filter in line:
                        if movie in line:
                            self.index = count
                            break
                        count += 1

            self.makeMovies(self.filter)

    def sortDatabase(self):
        series = ""
        with open(DATABASE_PATH, "r") as f:
            for line in f:
                if ":::Series:::" in line:
                    series += line

        with open(DATABASE_PATH + ".series", "w") as fseries:
            fseries.write(series)

        with open(DATABASE_PATH + ".series", "r") as fseries:
            series = fseries.readlines()
        series.sort(key=lambda line: line.split(":::")[0])
        with open(DATABASE_PATH + ".series", "w") as fseries:
            fseries.writelines(series)

        movies = ""
        with open(DATABASE_PATH, "r") as f:
            for line in f:
                if ":::Series:::" not in line:
                    movies += line

        with open(DATABASE_PATH + ".movies", "w") as fmovies:
            fmovies.write(movies)

        with open(DATABASE_PATH + ".movies", "r") as fmovies:
            lines = fmovies.readlines()

        self.sortorder = config.plugins.moviebrowser.sortorder.value
        try:
            if self.sortorder == 'name':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower())
            elif self.sortorder == 'name_reverse':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower(), reverse=True)
            elif self.sortorder == 'rating':
                lines.sort(key=lambda line: line.split(':::')[4])
            elif self.sortorder == 'rating_reverse':
                lines.sort(key=lambda line: line.split(':::')[4], reverse=True)
            elif self.sortorder == 'year':
                lines.sort(key=lambda line: line.split(':::')[8])
            elif self.sortorder == 'year_reverse':
                lines.sort(key=lambda line: line.split(':::')[8], reverse=True)
            elif self.sortorder == 'date':
                lines.sort(key=lambda line: line.split(':::')[2])
            elif self.sortorder == 'date_reverse':
                lines.sort(key=lambda line: line.split(':::')[2], reverse=True)
            elif self.sortorder == 'folder':
                lines.sort(key=lambda line: line.split(':::')[1])
            elif self.sortorder == 'folder_reverse':
                lines.sort(key=lambda line: line.split(':::')[1], reverse=True)
            elif self.sortorder == 'runtime':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')))
            elif self.sortorder == 'runtime_reverse':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')), reverse=True)
        except IndexError:
            pass
        except ValueError:
            self.session.open(MessageBox, _('\nDatabase Error: Entry without runtime'), MessageBox.TYPE_ERROR)

        with open(DATABASE_PATH + '.movies', "w") as f:
            f.write(lines)

        files = [DATABASE_PATH + '.movies', DATABASE_PATH + '.series']
        with open(DATABASE_PATH + '.sorted', 'w') as outfile:
            for name in files:
                with open(name, 'r') as infile:
                    outfile.write(infile.read())

        if fileExists(DATABASE_PATH + '.movies'):
            remove(DATABASE_PATH + '.movies')
        if fileExists(DATABASE_PATH + '.series'):
            remove(DATABASE_PATH + '.series')
        rename(DATABASE_PATH + '.sorted', DATABASE_PATH)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if PY3:
            link = link.encode()
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.exit, movieBrowserConfig)

    def zap(self):
        if self.ready is True:
            servicelist = self.session.instantiateDialog(ChannelSelection)
            self.session.execDialog(servicelist)

    def showHelp(self):
        if self.showhelp is False:
            self.showhelp = True
            self.toogleHelp.show()
        else:
            self.showhelp = False
            self.toogleHelp.hide()

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        if self.showhelp is True:
            self.showhelp = False
            self.toogleHelp.hide()
        elif config.plugins.moviebrowser.plotfull.value == 'hide' and self.topseries is False and self.infofull is True:
            self.toggleCount = 0
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.episodes = True
                else:
                    self.episodes = False
            except IndexError:
                self.episodes = False

            self.infofull = False
            self.plotfull = False
            self.control = False
            self.hideInfo2()
            self['banner'].hide()
            self['episodes'].hide()
            self.hidePlot()
        elif self.topseries is True:
            self.topseries = False
            self.episodes = True
            self.plotfull = True
            self.infofull = True
            self.control = True
            self.toggleCount = 0
            self.content = self.oldcontent
            self.filter = self.oldfilter
            self.index = self.topindex
            self['poster_back' + str(self.wallindex)].show()
            self.oldwallindex = self.topwallindex
            self.wallindex = self.index % self.posterALL
            self.pagecount = self.index // self.posterALL + 1
            self.makeMovies(self.filter)
        else:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w") as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value is True:
                with open(FILTER_PATH, "w") as f:
                    f.write(self.filter)

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            self.session.deleteDialog(self.toogleHelp)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.close()


class UpdateDatabase():

    def __init__(self, renew, name, movie, date):
        self.name = name
        self.renew = renew
        self.newseries = False
        self.orphaned = 0
        self.moviecount = 0
        self.seriescount = 0
        self.results = (0, 0, 0, 0)
        self.dbcount = 1
        self.dbcountmax = 1
        self.fileCount = 0
        self.tmdbCount = 0
        self.tvdbCount = 0
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value
        self.namelist = []
        self.movielist = []
        self.datelist = []
        self.infolist = []
        self.plotlist = []
        self.posterlist = []
        self.backdroplist = []
        self.contentlist = []
        self.seenlist = []
        self.medialist = []
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        # BLACKLIST_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        # self.updatelog = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/update.log'
        if self.renew is True:
            self.starttime = ''
            self.namelist.append(name)
            self.movielist.append(movie)
            self.datelist.append(date)
        else:
            self.makeUpdate()

    def makeUpdate(self):
        self.starttime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data = open(DATABASE_PATH).read()

        if fileExists(BLACKLIST_PATH):
            blacklist = open(BLACKLIST_PATH).read()

            alldata = data + blacklist
        else:
            alldata = data
        allfiles = ':::'
        count = 0
        folder = config.plugins.moviebrowser.moviefolder.value
        for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
            for name in files:
                count += 1
                if name.endswith('.ts') or name.endswith('.avi') or name.endswith('.divx') or name.endswith('.flv') or name.lower().endswith('.iso') or name.endswith('.m2ts') or name.endswith('.m4v') or name.endswith('.mov') or name.endswith('.mp4') or name.endswith('.mpg') or name.endswith('.mpeg') or name.endswith('.mkv') or name.endswith('.vob'):
                    filename = join(root, name)
                    allfiles = allfiles + filename + ':::'
                    movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
                    if search(movie, alldata) is None:
                        self.movielist.append(filename)
                        date = getmtime(filename)
                        self.datelist.append(str(datetime.datetime.fromtimestamp(date)))
                        if name.endswith('.ts'):
                            name = sub('_', ' ', name)
                            name = sub('^.*? - .*? - ', '', name)
                            name = sub('^[0-9]+ [0-9]+ - ', '', name)
                            name = sub('^[0-9]+ - ', '', name)
                            name = sub('[.]ts', '', name)
                        else:
                            name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                        self.namelist.append(name)
                self.fileCount = count

        for line in data.split('\n'):
            movieline = line.split(':::')
            try:
                moviefolder = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movieline[1])
            except IndexError:
                moviefolder = ''

            if search(config.plugins.moviebrowser.moviefolder.value, moviefolder) is not None and search(moviefolder, allfiles) is None:
                self.orphaned += 1
                data = data.replace(line + '\n', '')

        if self.orphaned > 0:
            if search('https://cf2.imgobject.com/t/p/', data) is not None:
                data = data.replace('https://cf2.imgobject.com/t/p/', 'https://image.tmdb.org/t/p/')
            with open(DATABASE_PATH, "w") as f:
                f.write(data)
        del data
        del alldata
        del allfiles
        self.dbcountmax = len(self.movielist)
        if self.dbcountmax == 0:
            self.results = (0, self.orphaned, self.moviecount, self.seriescount)
            self.showResult(False)
        else:
            self.name = self.namelist[0]
            if search('[Ss][0-9]+[Ee][0-9]+', self.name) is not None:
                series = self.name + 'FIN'
                series = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub('FIN', '', series)
                series = transSERIES(series)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (series, self.language)
                print('url tmdb=', url)
                self.getTVDbData(url, '0')
            else:
                movie = transMOVIE(self.name)
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (str(tmdb_api), movie, self.language)
                print('url tmdb=', url)
                self.getTMDbData(url, '0', False)
        return

    def getTMDbData(self, url, tmdbid, renew):
        self.tmdbCount += 1
        output = fetch_url(url)
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")

        if search('"total_results":0', output) is not None:
            series = self.name + "FIN"
            series = sub(" - [Ss][0-9]+[Ee][0-9]+.*?FIN", "", series)
            series = sub("[Ss][0-9]+[Ee][0-9]+.*?FIN", "", series)
            series = sub("FIN", "", series)
            series = transSERIES(series)
            url = "https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s" % (series, self.language)
            print("getTMDbData  url  tmdb =", url)
            self.getTVDbData(url, "0")
        else:
            output = output.replace("&amp;", "&").replace("\\/", "/").replace("}", ",")
            if tmdbid == "0":
                tmdbid = findall('"id":(.*?),', output)
                try:
                    tmdbid = tmdbid[0]
                except IndexError:
                    tmdbid = "0"

            name = findall('"title":"(.*?)"', output)
            backdrop = findall('"backdrop_path":"(.*?)"', output)
            year = findall('"release_date":"(.*?)"', output)
            poster = findall('"poster_path":"(.*?)"', output)
            rating = findall('"vote_average":(.*?),', output)
            try:
                self.namelist[self.dbcount - 1] = name[0]
            except IndexError:
                self.namelist[self.dbcount - 1] = self.name
            try:
                self.backdroplist.append('https://image.tmdb.org/t/p/w1280' + backdrop[0])
            except IndexError:
                self.backdroplist.append(str(default_backdrop))
            try:
                self.posterlist.append('https://image.tmdb.org/t/p/w185' + poster[0])
            except IndexError:
                self.posterlist.append(str(default_poster))
            url = 'https://api.themoviedb.org/3/movie/%s%s?api_key=%s' % (tmdbid, self.language, str(tmdb_api))
            print('getTMDbData  url - tmdb =', url)
            output = fetch_url(url)
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            output = output.decode("utf-8", "ignore")

            plot = findall('"overview":"(.*?)","', output)
            if renew is True:
                output = sub('"belongs_to_collection":{.*?}', '', output)
                name = findall('"title":"(.*?)"', output)
                backdrop = findall('"backdrop_path":"(.*?)"', output)
                poster = findall('"poster_path":"(.*?)"', output)
            url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdbid, str(tmdb_api))
            print('getTMDbData tmdbid url - tmdb =', url)
            output = fetch_url(url)
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            output = output.decode("utf-8", "ignore")

            output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
            output = sub('"belongs_to_collection":{.*?}', '', output)
            if not plot:
                plot = findall('"overview":"(.*?)","', output)
            genre = findall('"genres":[[]."id":[0-9]+,"name":"(.*?)"', output)
            genre2 = findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre3 = findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre4 = findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre5 = findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            country = findall('"iso_3166_1":"(.*?)"', output)
            runtime = findall('"runtime":(.*?),', output)
            if renew is True:
                year = findall('"release_date":"(.*?)"', output)
                rating = findall('"vote_average":(.*?),', output)
                if not backdrop:
                    backdrop = findall('"backdrop_path":"(.*?)"', output)
                if not poster:
                    poster = findall('"poster_path":"(.*?)"', output)
                try:
                    self.namelist[self.dbcount - 1] = name[0]
                except IndexError:
                    self.namelist[self.dbcount - 1] = self.name

                try:
                    self.backdroplist.append('https://image.tmdb.org/t/p/w1280' + backdrop[0])
                except IndexError:
                    self.backdroplist.append(str(default_backdrop))
                try:
                    self.posterlist.append('https://image.tmdb.org/t/p/w185' + poster[0])
                except IndexError:
                    self.posterlist.append(str(default_poster))
            url = 'https://api.themoviedb.org/3/movie/%s/casts?api_key=%s' % (tmdbid, str(tmdb_api))
            print('getTMDbData tmdbid 2 url - tmdb =', url)
            output = fetch_url(url)
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            output = output.decode("utf-8", "ignore")

            actor = findall('"name":"(.*?)"', output)
            actor2 = findall('"name":".*?"name":"(.*?)"', output)
            actor3 = findall('"name":".*?"name":".*?"name":"(.*?)"', output)
            actor4 = findall('"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor5 = findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor6 = findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor7 = findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            director = findall('"job":"Director","name":"(.*?)"', output)
            # director = findall('"known_for_department":"Writing","name":"(.*?)"', output)  # director fixed
            res = []
            try:
                res.append(runtime[0] + ' min')
            except IndexError:
                res.append(' ')

            try:
                res.append(rating[0])
            except IndexError:
                res.append('0.0')

            try:
                res.append(director[0])
            except IndexError:
                res.append(' ')
            actors = ' '
            try:
                actors = actor[0]
                actors = actors + ', ' + actor2[0]
                actors = actors + ', ' + actor3[0]
                actors = actors + ', ' + actor4[0]
                actors = actors + ', ' + actor5[0]
                actors = actors + ', ' + actor6[0]
            except IndexError:
                pass

            if len(actors) < 95:
                try:
                    actors = actors + ', ' + actor7[0]
                except IndexError:
                    pass

            res.append(actors)
            genres = ' '
            try:
                genres = genre[0]
                genres = genres + ', ' + genre2[0]
                genres = genres + ', ' + genre3[0]
                genres = genres + ', ' + genre4[0]
                genres = genres + ', ' + genre5[0]
            except IndexError:
                pass
            res.append(genres.replace('Science Fiction', 'Sci-Fi'))
            try:
                year = sub('-[0-9][0-9]-[0-9][0-9]', '', year[0])
                res.append(year)
            except IndexError:
                res.append(' ')

            try:
                res.append(country[0].replace('US', 'USA'))
            except IndexError:
                res.append(' ')

            self.infolist.append(res)
            try:
                self.plotlist.append(plot[0].replace('\r', '').replace('\n', ' ').replace('\\', ''))
            except IndexError:
                self.plotlist.append(' ')

            self.makeDataEntry(self.dbcount - 1, True)
        return

    def getTVDbData(self, url, seriesid):
        self.tvdbCount += 1
        output = fetch_url(url)
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")

        if search('<Series>', output) is None:
            res = []
            res.append(' ')
            res.append('0.0')
            res.append(' ')
            res.append(' ')
            res.append(' ')
            res.append(' ')
            res.append(' ')
            self.infolist.append(res)
            self.plotlist.append(' ')
            if self.newseries is True:
                name = self.name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                self.namelist.insert(self.dbcount - 1, name)
                self.movielist.insert(self.dbcount - 1, name)
                self.datelist.insert(self.dbcount - 1, str(datetime.datetime.now()))
                self.backdroplist.append(str(default_backdrop))
                self.posterlist.append(str(default_poster) + '<episode>' + str(default_banner) + '<episode>')
                self.makeDataEntry(self.dbcount - 1, False)
            else:
                self.backdroplist.append(str(default_backdrop))
                self.posterlist.append(str(default_poster))
                self.namelist[self.dbcount - 1] = self.name
                self.makeDataEntry(self.dbcount - 1, True)
        else:
            if seriesid == '0':
                seriesid = findall('<seriesid>(.*?)</seriesid>', output)
                try:
                    seriesid = seriesid[0]
                except IndexError:
                    seriesid = '0'

            if search('[Ss][0-9]+[Ee][0-9]+', self.name) is not None and self.newseries is False:
                data = search('([Ss][0-9]+[Ee][0-9]+)', self.name)
                data = data.group(1)
                season = search('[Ss]([0-9]+)[Ee]', data)
                season = season.group(1).lstrip('0')
                if season == '':
                    season = '0'
                episode = search('[Ss][0-9]+[Ee]([0-9]+)', data)
                episode = episode.group(1).lstrip('0')
                url = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/default/' + season + '/' + episode + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('getTVDbData url thetvdb =', url)
                output = fetch_url(url)
                if output is None:
                    # Handle error: log, skip, or ritorna un valore di fallback
                    print("Failed to fetch URL: " + url)
                    return None

                if output is None:
                    # Handle error: log, skip, or ritorna un valore di fallback
                    print("Failed to fetch URL: " + url)
                    return None

                output = output.decode("utf-8", "ignore")

                output = sub('\n', '', output)
                output = sub('&amp;', '&', output)
                episode = findall('<EpisodeName>(.*?)</EpisodeName>', output)
                year = findall('<FirstAired>([0-9]+)-', output)
                guest = findall('<GuestStars>[|](.*?)[|]</GuestStars>', output)
                director = findall('<Director>[|](.*?)[|]</Director>', output)
                if not director:
                    director = findall('<Director>(.*?)[|]', output)
                    if not director:
                        director = findall('<Director>[|](.*?)[|]', output)
                plotfull = findall('<Overview>(.*?)</Overview>', output, S)
                rating = findall('<Rating>(.*?)</Rating>', output)
                eposter = findall('<filename>(.*?)</filename>', output)
            else:
                data = ''
                episode = []
                year = []
                guest = []
                director = []
                plotfull = []
                rating = []
                eposter = []
            url = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
            print('getTVDbData url - thetvdb =', url)
            output = fetch_url(url)
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None

            output = output.decode("utf-8", "ignore")


            output = sub('\n', '', output)
            output = sub('&amp;', '&', output)
            output = sub('&quot;', '"', output)
            name = findall('<SeriesName>(.*?)</SeriesName>', output)
            runtime = findall('<Runtime>(.*?)</Runtime>', output)
            if not rating:
                rating = findall('<Rating>(.*?)</Rating>', output)
            actors = findall('<Actors>(.*?)</Actors>', output)
            actor = actor2 = actor3 = actor4 = actor5 = actor6 = actor7 = genre = genre2 = genre3 = genre4 = genre5 = []
            try:
                actor = findall('[|](.*?)[|]', actors[0])
                actor2 = findall('[|].*?[|](.*?)[|]', actors[0])
                actor3 = findall('[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor4 = findall('[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor5 = findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor6 = findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor7 = findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                pass

            genres = findall('<Genre>(.*?)</Genre>', output)
            try:
                genre = findall('[|](.*?)[|]', genres[0])
                genre2 = findall('[|].*?[|](.*?)[|]', genres[0])
                genre3 = findall('[|].*?[|].*?[|](.*?)[|]', genres[0])
                genre4 = findall('[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
                genre5 = findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                pass
            if not year:
                year = findall('<FirstAired>([0-9]+)-', output)
            if not plotfull:
                plotfull = findall('<Overview>(.*?)</Overview>', output, S)
            backdrop = findall('<fanart>(.*?)</fanart>', output)
            poster = findall('<poster>(.*?)</poster>', output)
            if self.newseries is True:
                eposter = findall('<banner>(.*?)</banner>', output)
            if self.newseries is False:
                try:
                    name = name[0]
                    if not episode:
                        self.namelist[self.dbcount - 1] = name + ' - (S00E00) - TheTVDb: ' + data + ' not found.'
                        self.name = name
                    else:
                        self.namelist[self.dbcount - 1] = name + ' - (' + data + ') ' + episode[0]
                        self.name = name + ' ' + data
                except IndexError:
                    self.namelist[self.dbcount - 1] = self.name

            else:
                try:
                    name = name[0]
                    self.namelist.insert(self.dbcount - 1, name)
                    self.movielist.insert(self.dbcount - 1, name)
                    self.datelist.insert(self.dbcount - 1, str(datetime.datetime.now()))
                except IndexError:
                    self.namelist.insert(self.dbcount - 1, self.name)
                    self.movielist.insert(self.dbcount - 1, self.name)
                    self.datelist.insert(self.dbcount - 1, str(datetime.datetime.now()))

            res = []
            try:
                res.append(runtime[0] + ' min')
            except IndexError:
                res.append(' ')

            try:
                res.append(rating[0])
            except IndexError:
                res.append('0.0')

            try:
                if not director:
                    res.append('Various')
                else:
                    res.append(director[0])
            except IndexError:
                res.append('Various')
            actors = " "
            try:
                actors = actor[0]
                actors = actors + ', ' + actor2[0]
                actors = actors + ', ' + actor3[0]
                actors = actors + ', ' + actor4[0]
                actors = actors + ', ' + actor5[0]
                actors = actors + ', ' + actor6[0]
            except IndexError:
                pass

            if len(actors) < 95:
                try:
                    actors = actors + ', ' + actor7[0]
                except IndexError:
                    pass

            res.append(actors)
            genres = ' '
            try:
                genres = genre[0]
                genres = genres + ', ' + genre2[0]
                genres = genres + ', ' + genre3[0]
                genres = genres + ', ' + genre4[0]
                genres = genres + ', ' + genre5[0]
            except IndexError:
                pass

            try:
                res.append(genres.replace('Science-Fiction', 'Sci-Fi'))
            except IndexError:
                res.append(' ')

            try:
                res.append(year[0])
            except IndexError:
                res.append(' ')
            country = config.plugins.moviebrowser.language.getValue()
            country = country.upper()

            res.append(country)
            self.infolist.append(res)
            try:
                if not guest:
                    plotfull = plotfull[0].replace('\r', '').replace('\n', ' ').replace('\\', '').replace('&quot;', '"')
                else:
                    plotfull = plotfull[0].replace('\r', '').replace('\n', ' ').replace('\\', '').replace('&quot;', '"')
                    plotfull = plotfull + ' Guest Stars: ' + guest[0].replace('|', ', ') + '.'
                self.plotlist.append(plotfull)
            except IndexError:
                self.plotlist.append(' ')

            try:
                self.backdroplist.append('https://www.thetvdb.com/banners/' + backdrop[0])
            except IndexError:
                self.backdroplist.append(str(default_backdrop))
            try:
                if self.newseries is True:
                    if not eposter:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + str(default_banner) + '<episode>')
                    elif eposter[0] == '':
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + str(default_banner) + '<episode>')
                    else:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
                elif not eposter:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0])
                else:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
            except IndexError:
                if self.newseries is True:
                    self.posterlist.append(str(default_poster) + '<episode>' + str(default_banner) + '<episode>')
                else:
                    self.posterlist.append(str(default_poster))

            self.makeDataEntry(self.dbcount - 1, False)
        return

    def makeDataEntry(self, count, content):
        if self.renew is False:
            try:
                with open(DATABASE_PATH, 'a', encoding="utf-8") as f:
                    if content is True:
                        self.moviecount += 1
                        parts = [
                            self.namelist[count],
                            self.movielist[count],
                            self.datelist[count],
                            self.infolist[count][0],
                            self.infolist[count][1],
                            self.infolist[count][2],
                            self.infolist[count][3],
                            self.infolist[count][4],
                            self.infolist[count][5],
                            self.infolist[count][6],
                            self.plotlist[count],
                            self.posterlist[count],
                            self.backdroplist[count],
                            "Movie:Top",
                            "unseen",
                            ""
                        ]
                        data = ":::".join(parts) + "\n"
                    elif self.newseries is True:
                        self.newseries = False
                        parts = [
                            self.namelist[count],
                            self.movielist[count],
                            self.datelist[count],
                            self.infolist[count][0],
                            self.infolist[count][1],
                            self.infolist[count][2],
                            self.infolist[count][3],
                            self.infolist[count][4],
                            self.infolist[count][5],
                            self.infolist[count][6],
                            self.plotlist[count],
                            self.posterlist[count],
                            self.backdroplist[count],
                            "Series:Top",
                            "unseen",
                            ""
                        ]
                        data = ":::".join(parts) + "\n"
                    else:
                        name = self.namelist[count] + "FIN"
                        name = sub(r"\([Ss][0-9]+[Ee][0-9]+.*?FIN", "", name)
                        name = sub("FIN", "", name)
                        name = sub(r"[\(\)\[\]\+\?]", ".", name)

                        with open(DATABASE_PATH, "r", encoding="utf-8") as fcheck:
                            existing_data = fcheck.read()

                        if search(escape(name) + r"\(", existing_data) is None:
                            self.newseries = True

                        self.seriescount += 1
                        parts = [
                            self.namelist[count],
                            self.movielist[count],
                            self.datelist[count],
                            self.infolist[count][0],
                            self.infolist[count][1],
                            self.infolist[count][2],
                            self.infolist[count][3],
                            self.infolist[count][4],
                            self.infolist[count][5],
                            self.infolist[count][6],
                            self.plotlist[count],
                            self.posterlist[count],
                            self.backdroplist[count],
                            "Series",
                            "unseen",
                            ""
                        ]
                        data = ":::".join(parts) + "\n"

                    f.write(data)

                    if config.plugins.moviebrowser.download.value == "update":
                        url = self.backdroplist[count]
                        backdrop = url.split("/")[-1]
                        cache_dir = config.plugins.moviebrowser.cachefolder.value
                        cache_path = join(cache_dir, backdrop)

                        if not exists(cache_dir):
                            try:
                                makedirs(cache_dir)
                            except OSError as e:
                                if not exists(cache_dir):
                                    print("Failed to create cache folder:", e)

                        if not fileExists(cache_path):
                            try:
                                if url.startswith("http://") or url.startswith("https://"):
                                    output = fetch_url(url)
                                elif exists(url):
                                    with open(url, "rb") as f:
                                        output = f.read()
                                else:
                                    print("Invalid backdrop path or URL:", url)
                                    output = None

                                if output:
                                    with open(cache_path, "wb") as imgfile:
                                        imgfile.write(output)
                            except Exception as e:
                                print("Error while saving backdrop:", e)

            except IndexError:
                pass

        else:
            try:
                if content is True:
                    self.moviecount += 1
                    newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Movie:Top:::unseen:::'
                else:
                    name = self.namelist[count] + 'FIN'
                    name = sub(' - \\([Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    name = sub('FIN', '', name)
                    name = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', name)
                    data = open(DATABASE_PATH).read()
                    if search(name + '.*?:::Series:Top:::unseen:::\n', data) is None:
                        self.newseries = True
                        self.renew = False
                    self.seriescount += 1
                    newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:::unseen:::'
            except IndexError:
                newdata = ''

            movie = self.movielist[count]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            data = open(DATABASE_PATH).read()
            if search(movie, data) is not None:
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        data = data.replace(line, newdata)

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)

        if self.newseries is True:
            self.dbcount += 1
            self.dbcountmax += 1
            series = self.name + 'FIN'
            series = sub(' - .[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('FIN', '', series)
            series = transSERIES(series)
            url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (series, self.language)
            print('url tmdb seriesname=', url)
            try:
                self.getTVDbData(url, '0')
            except RuntimeError:
                return (1, self.orphaned, self.moviecount, self.seriescount)

        elif self.dbcount < self.dbcountmax:
            self.dbcount += 1
            try:
                self.name = self.namelist[self.dbcount - 1]
                if search('[Ss][0-9]+[Ee][0-9]+', self.name) is not None:
                    series = self.name + 'FIN'
                    series = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub('FIN', '', series)
                    series = transSERIES(series)
                    url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (series, self.language)
                    print('url tmdb=', url)
                    try:
                        self.getTVDbData(url, '0')
                    except RuntimeError:
                        return (1, self.orphaned, self.moviecount, self.seriescount)
                else:
                    movie = transMOVIE(self.name)
                    movie = sub('\\+[1-2][0-9][0-9][0-9]', '', movie)
                    url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (str(tmdb_api), movie, self.language)
                    print('url tmdb=', url)
                    try:
                        self.getTMDbData(url, '0', False)
                    except RuntimeError:
                        return (1, self.orphaned, self.moviecount, self.seriescount)

            except IndexError:
                self.results = (1, self.orphaned, self.moviecount, self.seriescount)
                self.showResult(False)

        else:
            self.results = (1, self.orphaned, self.moviecount, self.seriescount)
            self.showResult(False)
        return

    def showResult(self, show):
        found, orphaned, moviecount, seriescount = self.results
        endtime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        result = _('Start time: %s\nEnd time: %s\nTotal scanned files: %s\nTheTVDb Database Requests: %s\nTMDb Database Requests: %s\nOrphaned Movies/Series: %s\nNew Series: %s\nNew Movies: %s\n\n') % (self.starttime, endtime, self.fileCount, self.tvdbCount, self.tmdbCount, orphaned, seriescount, moviecount)
        if found != 0:
            self.sortDatabase()
        if show is False:
            print('Movie Browser Datenbank Update\n' + result)
        else:
            if not self.renew:
                with open(UPDATE_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(result)
                return (found, orphaned, moviecount, seriescount)
            return True

    def sortDatabase(self):
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            series = [line for line in f if ":::Series:::" in line]
            movies = [line for line in f if ":::Series:::" not in line]  # questa riga in realtà non verrà mai eseguita, perché il file è già stato letto sopra

        series.sort(key=lambda line: line.split(":::")[0])

        with open(DATABASE_PATH + ".series", "w", encoding="utf-8") as f:
            f.writelines(series)

        # Riapri il file per i film, oppure leggi una sola volta tutto e dividi
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            movies = [line for line in f if ":::Series:::" not in line]

        with open(DATABASE_PATH + ".movies", "w", encoding="utf-8") as f:
            f.writelines(movies)

        with open(DATABASE_PATH + ".movies", "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.sortorder = config.plugins.moviebrowser.sortorder.value
        try:
            if self.sortorder == 'name':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower())
            elif self.sortorder == 'name_reverse':
                lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower(), reverse=True)
            elif self.sortorder == 'rating':
                lines.sort(key=lambda line: line.split(':::')[4])
            elif self.sortorder == 'rating_reverse':
                lines.sort(key=lambda line: line.split(':::')[4], reverse=True)
            elif self.sortorder == 'year':
                lines.sort(key=lambda line: line.split(':::')[8])
            elif self.sortorder == 'year_reverse':
                lines.sort(key=lambda line: line.split(':::')[8], reverse=True)
            elif self.sortorder == 'date':
                lines.sort(key=lambda line: line.split(':::')[2])
            elif self.sortorder == 'date_reverse':
                lines.sort(key=lambda line: line.split(':::')[2], reverse=True)
            elif self.sortorder == 'folder':
                lines.sort(key=lambda line: line.split(':::')[1])
            elif self.sortorder == 'folder_reverse':
                lines.sort(key=lambda line: line.split(':::')[1], reverse=True)
            elif self.sortorder == 'runtime':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')))
            elif self.sortorder == 'runtime_reverse':
                lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')), reverse=True)
        except IndexError:
            pass
        except ValueError:
            self.session.open(MessageBox, _('\nDatabase Error: Entry without runtime'), MessageBox.TYPE_ERROR)

        with open(DATABASE_PATH + ".movies", "w", encoding="utf-8") as f:
            f.writelines(lines)
        files = [DATABASE_PATH + '.movies', DATABASE_PATH + '.series']
        with open(DATABASE_PATH + '.sorted', 'w') as outfile:
            for name in files:
                with open(name, 'r') as infile:
                    outfile.write(infile.read())

        if fileExists(DATABASE_PATH + '.movies'):
            remove(DATABASE_PATH + '.movies')
        if fileExists(DATABASE_PATH + '.series'):
            remove(DATABASE_PATH + '.series')
        rename(DATABASE_PATH + '.sorted', DATABASE_PATH)


class movieControlList(Screen):

    def __init__(self, session, list, index, content):
        skin = join(skin_path + "movieControlList.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.hideflag = True
        self.log = False
        self.ready = False
        self.delete = False
        self.list = list
        self.index = index
        self.content = content
        self.lang = config.plugins.moviebrowser.language.value
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.listentries = []
        self['list'] = ItemList([])
        self['log'] = ScrollLabel()
        self['log'].hide()
        # self['label'] = Label('= MovieCut')
        # self['label2'] = Label('= CutListEditor')
        self['label3'] = Label('Info')
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.zap,
            'prevBouquet': self.zap,
            # 'red': self.movieCut,
            # 'green': self.cutlistEditor,
            'yellow': self.showInfo,
            'blue': self.hideScreen,
            '0': self.gotoEnd,
            '1': self.gotoFirst,
        }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        idx = 0
        for x in self.list:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if screenwidth.width() == 1920:
                    if self.content != ':::Series:::':
                        res.append(MultiContentEntryText(pos=(10, 0), size=(1700, 40), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list[i][0]))
                    else:
                        series = sub('[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(MultiContentEntryText(pos=(10, 0), size=(1700, 30), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=series))
                else:
                    if self.content != ':::Series:::':
                        res.append(MultiContentEntryText(pos=(5, 0), size=(1200, 40), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list[i][0]))
                    else:
                        series = sub('[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(MultiContentEntryText(pos=(5, 0), size=(1200, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=series))
                self.listentries.append(res)
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)
        try:
            self['list'].moveToIndex(self.index)
        except IndexError:
            pass

        self.ready = True
        totalMovies = len(self.listentries)
        if config.plugins.moviebrowser.showfolder.value is True:
            totalMovies -= 1
        free = 'Free Space:'
        folder = 'Movie Folder'
        movies = 'Movies'
        series = 'Series'
        if exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = statvfs(config.plugins.moviebrowser.moviefolder.value)
            try:
                stat = movieFolder
                freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
            except Exception as e:
                print(e)
                freeSize = "-?-"

            if self.content == ':::Movie:Top:::':
                title = '%s %s (%s %s)' % (str(totalMovies), movies, str(freeSize), free)
            elif self.content == ':::Series:::' or self.content == ':::Series:Top:::':
                title = '%s %s (%s %s)' % (str(totalMovies), series, str(freeSize), free)
            else:
                title = '%s %s & %s (%s %s)' % (str(totalMovies), movies, series, str(freeSize), free)
            self.setTitle(title)
        else:
            if self.content == ':::Movie:Top:::':
                title = '%s %s (%s offline)' % (str(totalMovies), movies, folder)
            elif self.content == ':::Series:::' or self.content == ':::Series:Top:::':
                title = '%s %s (%s offline)' % (str(totalMovies), series, folder)
            else:
                title = '%s %s & %s (%s offline)' % (str(totalMovies), movies, series, folder)
            self.setTitle(title)

    def ok(self):
        if self.ready is True and self.log is False:
            index = self['list'].getSelectedIndex()
            if self.delete is False:
                self.close(index, False)
            else:
                self.close(index, True)

    def showInfo(self):
        if self.ready is True:
            loglist = [
                (_('Movie File Informations'), 'info'),
                (_('Delete Movie File'), 'delete'),
                (_('Blacklist Movie File'), 'blacklist'),
                (_('Database Update Log'), 'update'),
                (_('Database Timer Log'), 'timer'),
                (_('Cleanup Cache Folder Log'), 'cleanup')
            ]
            self.session.openWithCallback(self.choiceLog, ChoiceBox, title='Movie Browser', list=loglist)

    def choiceLog(self, choice):
        choice = choice and choice[1]
        if choice == 'info':
            self.log = True
            self['log'].show()
            self['list'].hide()
            index = self['list'].getSelectedIndex()
            moviefile = self.list[index][1]
            if moviefile.endswith('.ts'):
                size = getsize(moviefile)
                suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
                suffixIndex = 0
                while size > 1024:
                    suffixIndex += 1
                    size = size // 1024.0

                size = round(size, 2)
                size = str(size) + ' ' + suffixes[suffixIndex]
                date = getmtime(moviefile)
                date = str(datetime.datetime.fromtimestamp(date))
                service = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + moviefile)
                from enigma import eServiceCenter
                info = eServiceCenter.getInstance().info(service)
                name = info.getName(service)
                event = info.getEvent(service)
                duration = '%d min' % (event.getDuration() // 60)
                description = event.getShortDescription()
                extDescription = event.getExtendedDescription()
                infotext = '%s\n%s\n%s\n\n%s, %s, %s\n%s' % (moviefile, date, size, name, description, duration, extDescription)
            elif moviefile == config.plugins.moviebrowser.moviefolder.value + '...':
                folder = config.plugins.moviebrowser.moviefolder.value
                infotext = config.plugins.moviebrowser.moviefolder.value + '\n'
                for root, dirs, files in walk(folder, topdown=False, onerror=None, followlinks=True):
                    for name in dirs:
                        folder = join(root, name)
                        infotext = infotext + folder + '\n'

            else:
                size = getsize(moviefile)
                suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
                suffixIndex = 0
                while size > 1024:
                    suffixIndex += 1
                    size = size // 1024.0

                size = round(size, 2)
                size = str(size) + ' ' + suffixes[suffixIndex]
                date = getmtime(moviefile)
                date = str(datetime.datetime.fromtimestamp(date))
                infotext = '%s\n%s\n%s' % (moviefile, date, size)
            self['log'].setText(infotext)
        elif choice == 'delete':
            self.deleteMovie()
        elif choice == 'blacklist':
            self.blacklistMovie()
        elif choice == 'update':
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open(UPDATE_LOG_PATH).read()
            self['log'].setText(data)
        elif choice == 'timer':
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open(TIMER_LOG_PATH).read()
            self['log'].setText(data)
        else:
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open(CLEANUP_LOG_PATH).read()
            self['log'].setText(data)
        return

    def restartGUI(self, answer):
        if answer is True:
            try:
                self.session.open(TryQuitMainloop, 3)
            except RuntimeError:
                self.close(None, False)

        return

    def deleteMovie(self):
        try:
            index = self['list'].getSelectedIndex()
            name = self.list[index][0]
            movie = self.list[index][1]
            if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                self.session.open(MessageBox, _('\nThe List of Movie Folder can not be deleted.'), MessageBox.TYPE_ERROR)
            elif name == movie:
                self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
            else:
                self.session.openWithCallback(self.delete_return, MessageBox, _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
        except IndexError:
            pass

    def delete_return(self, answer):
        if answer is True:
            try:
                # database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                if fileExists(movie):
                    remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        remove(eitfile)
                    if fileExists(movie + '.ap'):
                        remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        remove(srtfile)
                data = open(DATABASE_PATH).read()
                if name == movie:
                    for line in data.split('\n'):
                        if search(movie + '.*?:::Series:', line) is not None:
                            data = data.replace(line + '\n', '')

                else:
                    for line in data.split('\n'):
                        if search(movie, line) is not None:
                            data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)
                self.delete = True
                del self.list[index]
                if index != 0:
                    self.index = index - 1
                else:
                    self.index = 0
                self.listentries = []
                self.onLayoutFinished()
            except IndexError:
                pass

        return

    def blacklistMovie(self):
        try:
            index = self['list'].getSelectedIndex()
            name = self.list[index][0]
            self.session.openWithCallback(self.blacklist_return, MessageBox, _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
        except IndexError:
            pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                # database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
                # blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(BLACKLIST_PATH):
                    fremove = open(BLACKLIST_PATH, 'a')
                else:
                    fremove = open(BLACKLIST_PATH, 'w')
                data = open(DATABASE_PATH).read()
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        fremove.write(line + '\n')
                        fremove.close()
                        data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(episode, data) is None and search(name, data) is not None:
                    for line in data.split('\n'):
                        if search(name, line) is not None and search(':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w") as f:
                    f.write(data)
                self.delete = True
                del self.list[index]
                if index != 0:
                    self.index = index - 1
                else:
                    self.index = 0
                self.listentries = []
                self.onLayoutFinished()
            except IndexError:
                pass

            self.ready = True
        return

    def down(self):
        if self.log is False:
            self['list'].down()
        else:
            self['log'].pageDown()

    def up(self):
        if self.log is False:
            self['list'].up()
        else:
            self['log'].pageUp()

    def leftUp(self):
        if self.log is False:
            self['list'].pageUp()
        else:
            self['log'].pageUp()

    def rightDown(self):
        if self.log is False:
            self['list'].pageDown()
        else:
            self['log'].pageDown()

    def gotoEnd(self):
        if self.log is False:
            end = len(self.listentries) - 1
            self['list'].moveToIndex(end)
        else:
            self['log'].lastPage()

    def gotoFirst(self):
        self['list'].moveToIndex(0)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        if self.log is True:
            self.log = False
            self['log'].hide()
            self['list'].show()
        elif self.delete is False:
            self.close(None, False)
        else:
            index = self['list'].getSelectedIndex()
            self.close(index, True)
        return


class movieDatabase(Screen):

    def __init__(self, session, movie):
        Screen.__init__(self, session)
        skin = join(skin_path + "movieDatabase.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        self.hideflag = True
        self.ready = False
        self.change = False
        self.first = False
        self.movie = movie
        self.lang = config.plugins.moviebrowser.language.value
        self['list'] = ItemList([])
        self['list2'] = ItemList([])
        self.actlist = 'list'
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.zap,
            'prevBouquet': self.zap,
            'blue': self.hideScreen,
            '0': self.gotoEnd,
            '1': self.gotoFirst,
        }, -1)
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.onLayoutFinish.append(self.makeList)

    def makeList(self):
        self.namelist = []
        self.movielist = []
        self.datelist = []
        self.runtimelist = []
        self.ratinglist = []
        self.directorlist = []
        self.actorslist = []
        self.genreslist = []
        self.yearlist = []
        self.countrylist = []
        self.posterlist = []
        self.backdroplist = []
        self.medialist = []
        self.list = []
        self.listentries = []
        if fileExists(DATABASE_PATH):
            count = 0
            index = 0
            f = open(DATABASE_PATH, 'r')
            for line in f:
                name = ""
                movie = ""
                date = ""
                runtime = ""
                rating = ""
                director = ""
                actors = ""
                genres = ""
                year = ""
                country = ""
                poster = str(default_poster)
                backdrop = str(default_backdrop)
                media = '\n'
                movieline = line.split(':::')
                try:
                    name = movieline[0]
                    name = sub('[Ss][0]+[Ee]', 'Special ', name)
                    movie = movieline[1]
                    if movie == self.movie:
                        index = count
                    date = movieline[2]
                    runtime = movieline[3]
                    rating = movieline[4]
                    director = movieline[5]
                    actors = movieline[6]
                    genres = movieline[7]
                    year = movieline[8]
                    country = movieline[9]
                    poster = movieline[11]
                    backdrop = movieline[12]
                    media = movieline[15]
                except IndexError:
                    pass
                self.namelist.append(name)
                self.movielist.append(movie)
                self.datelist.append(date)
                self.runtimelist.append(runtime)
                self.ratinglist.append(rating)
                self.directorlist.append(director)
                self.actorslist.append(actors)
                self.genreslist.append(genres)
                self.yearlist.append(year)
                self.countrylist.append(country)
                self.posterlist.append(poster)
                self.backdroplist.append(backdrop)
                self.medialist.append(media)
                self.list.append(name)
                count += 1
                res = ['']
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(1240, 40), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=name))
                else:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(710, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=name))
                self.listentries.append(res)

            self['list'].l.setList(self.listentries)
            self['list'].moveToIndex(index)
            self.selectList()
            self.ready = True
            totalMovies = len(self.list)
            database = _('Database')
            free = _('Free Space')
            folder = _('Movie Folder')
            movies = _('Movies')
            if exists(config.plugins.moviebrowser.moviefolder.value):
                movieFolder = statvfs(config.plugins.moviebrowser.moviefolder.value)
                try:
                    stat = movieFolder
                    freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
                except Exception as e:
                    print(e)
                    freeSize = "-?-"
                title = '%s Editor: %s %s (%s %s)' % (database, str(totalMovies), movies, str(freeSize), free)
                self.setTitle(title)
            else:
                title = '%s Editor: %s %s (%s offline)' % (database, str(totalMovies), movies, folder)
                self.setTitle(title)

    def makeList2(self):
        self.list2 = []
        self.list2.append('Movie: ' + self.namelist[self.index])
        self.list2.append('Rating: ' + self.ratinglist[self.index])
        self.list2.append('Director: ' + self.directorlist[self.index])
        self.list2.append('Country: ' + self.countrylist[self.index])
        self.list2.append('Actors: ' + self.actorslist[self.index])
        self.list2.append('Year: ' + self.yearlist[self.index])
        self.list2.append('Runtime: ' + self.runtimelist[self.index])
        self.list2.append('Genres: ' + self.genreslist[self.index])
        if self.medialist[self.index] != '\n':
            self.list2.append('MediaInfo: ' + self.medialist[self.index])
            self.mediainfo = True
        else:
            self.mediainfo = False
        self.list2.append('Poster: ' + self.posterlist[self.index])
        self.list2.append('Backdrop: ' + self.backdroplist[self.index])
        self.list2entries = []
        idx = 0
        for x in self.list2:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(1240, 40), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list2[i]))
                else:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(710, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list2[i]))
                self.list2entries.append(res)
            except IndexError:
                pass

        self['list2'].l.setList(self.list2entries)
        self.selectList2()
        self.ready = True

    def ok(self):
        if self.ready is True:
            if self.actlist == 'list':
                self.index = self['list'].getSelectedIndex()
                try:
                    self.ready = False
                    movie = self.movielist[self.index]
                    self.movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                    self.makeList2()
                except IndexError:
                    self.ready = True

            elif self.actlist == 'list2':
                index = self['list2'].getSelectedIndex()
                if index == 0:
                    self.first = True
                    self.data = self.namelist[self.index]
                elif index == 1:
                    self.data = self.ratinglist[self.index]
                elif index == 2:
                    self.data = self.directorlist[self.index]
                elif index == 3:
                    self.data = self.countrylist[self.index]
                elif index == 4:
                    self.data = self.actorslist[self.index]
                elif index == 5:
                    self.data = self.yearlist[self.index]
                elif index == 6:
                    self.data = self.runtimelist[self.index]
                elif index == 7:
                    self.data = self.genreslist[self.index]
                elif index == 8:
                    if self.mediainfo is True:
                        self.data = self.medialist[self.index]
                    else:
                        self.data = self.posterlist[self.index]
                elif index == 9:
                    if self.mediainfo is True:
                        self.data = self.posterlist[self.index]
                    else:
                        self.data = self.backdroplist[self.index]
                elif index == 10:
                    if self.mediainfo is True:
                        self.data = self.backdroplist[self.index]
                self.session.openWithCallback(self.databaseReturn, VirtualKeyBoard, title=_('Database Editor:'), text=self.data)

    def databaseReturn(self, newdata):
        if newdata and newdata != "" and newdata != self.data:
            if self.first is True:
                self.first = False
                newdata = newdata + ":::"
                olddata = self.data + ":::"
            else:
                newdata = ":::" + newdata + ":::"
                olddata = ":::" + self.data + ":::"

            with open(DATABASE_PATH, "r") as f:
                database = f.read()

            for line in database.split("\n"):
                if search(self.movie, line) is not None:
                    newline = line.replace(olddata, newdata)
                    database = database.replace(line, newline)
                    break

            with open(DATABASE_PATH + ".new", "w") as f:
                f.write(database)

            rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.makeList()
            self.makeList2()
            self.change = True
        return

    def selectList(self):
        self.actlist = 'list'
        self['list'].show()
        self['list2'].hide()
        self['list'].selectionEnabled(1)
        self['list2'].selectionEnabled(0)

    def selectList2(self):
        self.actlist = 'list2'
        self['list'].hide()
        self['list2'].show()
        self['list'].selectionEnabled(0)
        self['list2'].selectionEnabled(1)

    def up(self):
        self[self.actlist].up()

    def down(self):
        self[self.actlist].down()

    def leftUp(self):
        self[self.actlist].pageUp()

    def rightDown(self):
        self[self.actlist].pageDown()

    def gotoEnd(self):
        if self.actlist == 'list':
            end = len(self.list) - 1
        else:
            end = len(self.list2) - 1
        self[self.actlist].moveToIndex(end)

    def gotoFirst(self):
        self[self.actlist].moveToIndex(0)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        if self.actlist == 'list':
            if self.change is True:
                self.close(True)
            else:
                self.close(False)
        elif self.actlist == 'list2':
            self.selectList()


class moviesList(Screen):

    def __init__(self, session, titel, rating, year, titles, poster, id, country, movie, top):
        Screen.__init__(self, session)
        skin = join(skin_path + "moviesList.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        self.titel = titel
        self.rating = rating
        self.year = year
        self.titles = titles
        self.poster = poster
        self.id = id
        self.country = country
        self.movie = movie
        self.top = top
        self.choice = 'movie'
        self.language = config.plugins.moviebrowser.language.value
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value
        self.movielist = []
        self.imagelist = []
        self.poster1 = '/tmp/moviebrowser1.jpg'
        self.poster2 = '/tmp/moviebrowser2.jpg'
        self.poster3 = '/tmp/moviebrowser3.jpg'
        self.poster4 = '/tmp/moviebrowser4.jpg'
        self['poster1'] = Pixmap()
        self['poster2'] = Pixmap()
        self['poster3'] = Pixmap()
        self['poster4'] = Pixmap()
        self.banner1 = '/tmp/moviebrowser5.jpg'
        self.banner2 = '/tmp/moviebrowser6.jpg'
        self.banner3 = '/tmp/moviebrowser7.jpg'
        self.banner4 = '/tmp/moviebrowser8.jpg'
        self['banner1'] = Pixmap()
        self['banner2'] = Pixmap()
        self['banner3'] = Pixmap()
        self['banner4'] = Pixmap()
        self.ready = False
        self.first = True
        self.hideflag = True
        self.setTitle(titel)
        self['list'] = ItemList([])
        self['piclist'] = ItemList([])
        self['piclist'].hide()
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.zap,
            'prevBouquet': self.zap,
            'blue': self.hideScreen,
            '0': self.gotoEnd,
            '1': self.gotoFirst,
        }, -1)
        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        try:
            poster1 = self.poster[0]
            self.download(poster1, self.getPoster1)
            self['poster1'].show()
        except IndexError:
            self['poster1'].hide()

        try:
            poster2 = self.poster[1]
            self.download(poster2, self.getPoster2)
            self['poster2'].show()
        except IndexError:
            self['poster2'].hide()

        try:
            poster3 = self.poster[2]
            self.download(poster3, self.getPoster3)
            self['poster3'].show()
        except IndexError:
            self['poster3'].hide()

        try:
            poster4 = self.poster[3]
            self.download(poster4, self.getPoster4)
            self['poster4'].show()
        except IndexError:
            self['poster4'].hide()

        for x in range(len(self.titles)):
            res = ['']
            png = '%spic/browser/ratings_back.png' % skin_directory
            png2 = '%spic/browser/ratings.png' % skin_directory
            try:
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(810, 225), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=''))
                    res.append(MultiContentEntryText(pos=(10, 13), size=(800, 45), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.titles[x]))
                    res.append(MultiContentEntryText(pos=(10, 54), size=(200, 45), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.year[x]))
                    res.append(MultiContentEntryText(pos=(10, 260), size=(200, 45), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(10 * round(float(self.rating[x]), 1)) // 10
                else:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(620, 125), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=''))
                    res.append(MultiContentEntryText(pos=(5, 13), size=(610, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.titles[x]))
                    res.append(MultiContentEntryText(pos=(5, 48), size=(200, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.year[x]))
                    res.append(MultiContentEntryText(pos=(5, 48), size=(200, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(10 * round(float(self.rating[x]), 1)) // 10

            except (IndexError, ValueError):
                rating = 0

            try:
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 90), size=(350, 45), png=loadPNG(png)))
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 90), size=(rating, 45), png=loadPNG(png2)))
                    res.append(MultiContentEntryText(pos=(410, 90), size=(50, 45), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.rating[x]))
                else:
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(210, 21), png=loadPNG(png)))
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(rating, 21), png=loadPNG(png2)))
                    res.append(MultiContentEntryText(pos=(225, 84), size=(50, 21), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=self.rating[x]))
            except IndexError:
                pass

            self.movielist.append(res)

        self['list'].l.setList(self.movielist)
        if screenwidth.width() == 1920:
            self['list'].l.setItemHeight(225)
        else:
            self['list'].l.setItemHeight(125)
        self.ready = True

    def ok(self):
        if self.ready is True:
            if self.first is True:
                if self.movie is True:
                    choicelist = [('Update Movie', _('movie')), ('Update Poster', _('poster')), ('Update Backdrop', _('backdrop'))]
                    self.session.openWithCallback(self.updateMovie, ChoiceBox, title='Update Movie', list=choicelist)
                elif self.top is True:
                    choicelist = [('Update Banner', _('banner')), ('Update Backdrop', _('backdrop'))]
                    self.session.openWithCallback(self.updateSeries, ChoiceBox, title=_('Update Series'), list=choicelist)
                else:
                    choicelist = [('Update Series', _('series'))]
                    self.session.openWithCallback(self.updateSeries, ChoiceBox, title=_('Update Series'), list=choicelist)
            else:
                c = self['piclist'].getSelectedIndex()
                current = self.banner[c]
                if fileExists(self.banner1):
                    remove(self.banner1)
                if fileExists(self.banner2):
                    remove(self.banner2)
                if fileExists(self.banner3):
                    remove(self.banner3)
                if fileExists(self.banner4):
                    remove(self.banner4)
                self.close(current, self.choice)

    def updateMovie(self, choice):
        try:
            c = self['list'].getSelectedIndex()
            current = self.id[c]
            self.choice = choice and choice[1]
            if self.choice == 'movie':
                if fileExists(self.poster1):
                    remove(self.poster1)
                if fileExists(self.poster2):
                    remove(self.poster2)
                if fileExists(self.poster3):
                    remove(self.poster3)
                if fileExists(self.poster4):
                    remove(self.poster4)
                self.session.open(MessageBox, _('All /tmp/posters Cleaned'), MessageBox.TYPE_INFO, timeout=4)
                self.close(current, self.choice)
            elif self.choice == 'poster':
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (current, str(tmdb_api))
                self.getTMDbPosters(url)
            elif self.choice == 'backdrop':
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (current, str(tmdb_api))
                self.getTMDbBackdrops(url)
        except Exception as e:
            print('error get ', str(e))

    def getTMDbPosters(self, url):
        try:
            try:
                output = fetch_url(url)
            except Exception:
                self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
                return
            if output is None:
                # Handle error: log, skip, or ritorna un valore di fallback
                print("Failed to fetch URL: " + url)
                return None
            output = output.decode("utf-8", "ignore")
            output = sub('"backdrops".*?"posters"', '', output, flags=S)
            output = sub('"file_path":"', '"file_path":"https://image.tmdb.org/t/p/w185', output)
            self.banner = findall('"file_path":"(.*?)"', output)
            self.makeList()
        except Exception as e:
            print('error get ', str(e))

    def getTMDbBackdrops(self, url):
        try:
            output = fetch_url(url)
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")

        output = output + 'FIN'
        output = sub('"posters".*?FIN', '', output, flags=S)
        output = sub('"file_path":"', '"file_path":"https://image.tmdb.org/t/p/w1280', output)
        self.banner = findall('"file_path":"(.*?)"', output)
        self.makeList()

    def updateSeries(self, choice):
        try:
            c = self['list'].getSelectedIndex()
            current = self.id[c]
            self.choice = choice and choice[1]
            if self.choice == 'series':
                if fileExists(self.poster1):
                    remove(self.poster1)
                if fileExists(self.poster2):
                    remove(self.poster2)
                if fileExists(self.poster3):
                    remove(self.poster3)
                if fileExists(self.poster4):
                    remove(self.poster4)
                self.close(current, self.choice)
            elif self.choice == 'banner':
                url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (thetvdb_api, current)
                self.getTVDbBanners(url)
            elif self.choice == 'backdrop':
                url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (thetvdb_api, current)
                self.getTVDbBackdrops(url)
        except Exception as e:
            print('error get ', str(e))

    def getTVDbBanners(self, url):
        try:
            output = fetch_url(url)
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")
        output = sub('<BannerPath>graphical', '<BannerPath>https://www.thetvdb.com/banners/graphical', output)
        self.banner = findall('<BannerPath>(.*?)</BannerPath>\n\\s+<BannerType>series</BannerType>', output)
        self.makeList()

    def getTVDbBackdrops(self, url):
        try:
            output = fetch_url(url)
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return
        if output is None:
            # Handle error: log, skip, or ritorna un valore di fallback
            print("Failed to fetch URL: " + url)
            return None

        output = output.decode("utf-8", "ignore")
        output = sub('<BannerPath>fanart', '<BannerPath>https://www.thetvdb.com/banners/fanart', output)
        self.banner = findall('<BannerPath>(.*?)</BannerPath>\n\\s+<BannerType>fanart</BannerType>', output)
        self.makeList()

    def makeList(self):
        self['list'].hide()
        self['poster1'].hide()
        self['poster2'].hide()
        self['poster3'].hide()
        self['poster4'].hide()
        try:
            banner1 = self.banner[0]
            self.download(banner1, self.getBanner1)
            self['banner1'].show()
        except IndexError:
            self['banner1'].hide()

        try:
            banner2 = self.banner[1]
            self.download(banner2, self.getBanner2)
            self['banner2'].show()
        except IndexError:
            self['banner2'].hide()

        try:
            banner3 = self.banner[2]
            self.download(banner3, self.getBanner3)
            self['banner3'].show()
        except IndexError:
            self['banner3'].hide()

        try:
            banner4 = self.banner[3]
            self.download(banner4, self.getBanner4)
            self['banner4'].show()
        except IndexError:
            self['banner4'].hide()

        self.titles = self.banner
        for x in range(len(self.titles)):
            res = ['']
            if screenwidth.width() == 1920:
                res.append(MultiContentEntryText(pos=(5, 0), size=(1240, 225), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=''))
                self.imagelist.append(res)
                self['piclist'].l.setList(self.imagelist)
                self['piclist'].l.setItemHeight(225)

            else:
                res.append(MultiContentEntryText(pos=(5, 0), size=(710, 125), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT, text=''))
                self.imagelist.append(res)
                self['piclist'].l.setList(self.imagelist)
                self['piclist'].l.setItemHeight(125)
        self['piclist'].show()
        self.first = False
        self.ready = True

    def down(self):
        if self.ready is True:
            def load_group(start, is_poster=True):
                for i in range(4):
                    idx = start + i
                    widget = "poster" + str(i + 1) if is_poster else "banner" + str(i + 1)
                    try:
                        item = self.poster[idx] if is_poster else self.banner[idx]
                        callback = getattr(self, "getPoster" + str(i + 1)) if is_poster else getattr(self, "getBanner" + str(i + 1))
                        self.download(item, callback)
                        self[widget].show()
                    except IndexError:
                        self[widget].hide()

            try:
                if self.first is True:
                    c = self["list"].getSelectedIndex()
                    self["list"].down()
                    if c + 1 == len(self.titles):
                        load_group(0, True)
                    elif (c + 1) % 4 == 0:
                        load_group(c + 1, True)
                else:
                    c = self["piclist"].getSelectedIndex()
                    self["piclist"].down()
                    if c + 1 == len(self.titles):
                        load_group(0, False)
                    elif (c + 1) % 4 == 0:
                        load_group(c + 1, False)
            except IndexError:
                return

    def up(self):
        if self.ready is True:
            def load_group(start, is_poster=True):
                for i in range(4):
                    idx = start + i
                    widget = "poster" + str(i + 1) if is_poster else "banner" + str(i + 1)
                    try:
                        item = self.poster[idx] if is_poster else self.banner[idx]
                        callback = getattr(self, "getPoster" + str(i + 1)) if is_poster else getattr(self, "getBanner" + str(i + 1))
                        self.download(item, callback)
                        self[widget].show()
                    except IndexError:
                        self[widget].hide()

            try:
                if self.first is True:
                    c = self["list"].getSelectedIndex()
                    self["list"].up()
                    if c == 0:
                        length = len(self.titles)
                        d = length % 4 or 4
                        load_group(length - d, True)
                    elif c % 4 == 0:
                        load_group(c - 4, True)
                else:
                    c = self["piclist"].getSelectedIndex()
                    self["piclist"].up()
                    if c == 0:
                        length = len(self.titles)
                        d = length % 4 or 4
                        load_group(length - d, False)
                    elif c % 4 == 0:
                        load_group(c - 4, False)
            except IndexError:
                return

    def rightDown(self):
        if self.ready is True and self.first is True:
            def load_group(start):
                for i in range(4):
                    widget = "poster" + str(i + 1)
                    try:
                        item = self.poster[start + i]
                        callback = getattr(self, "getPoster" + str(i + 1))
                        self.download(item, callback)
                        self[widget].show()
                    except IndexError:
                        self[widget].hide()

            try:
                c = self["list"].getSelectedIndex()
                self["list"].pageDown()
                length = len(self.titles)
                d = c % 4
                e = length % 4 or 4
                if c + e >= length:
                    return
                offset = {0: 4, 1: 3, 2: 2, 3: 1}.get(d, 0)
                load_group(c + offset)
            except IndexError:
                return

    def leftUp(self):
        if self.ready is True and self.first is True:
            def load_group(start):
                for i in range(4):
                    widget = "poster" + str(i + 1)
                    try:
                        item = self.poster[start + i]
                        callback = getattr(self, "getPoster" + str(i + 1))
                        self.download(item, callback)
                        self[widget].show()
                    except IndexError:
                        self[widget].hide()

            try:
                c = self["list"].getSelectedIndex()
                self["list"].pageUp()
                d = c % 4
                offset = {0: 4, 1: 5, 2: 6, 3: 7}.get(d, 4)
                start_index = c - offset
                if start_index < 0:
                    return
                load_group(start_index)
            except IndexError:
                return

    def gotoEnd(self):
        if self.ready is True:
            end = len(self.titles) - 1
            if end >= 4:
                if self.first is True:
                    self['list'].moveToIndex(end)
                else:
                    self['piclist'].moveToIndex(end)
                self.leftUp()
                self.rightDown()

    def gotoFirst(self):
        self['list'].moveToIndex(0)
        self.rightDown()
        self.leftUp()

    def getPoster1(self, output):
        with open(self.poster1, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showPoster1(self.poster1)

    def showPoster1(self, poster1):
        if fileExists(poster1):
            self["poster1"].instance.setPixmapFromFile(poster1)
            self['poster1'].show()
        return

    def getPoster2(self, output):
        with open(self.poster2, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        if fileExists(poster2):
            self["poster2"].instance.setPixmapFromFile(poster2)
            self['poster2'].show()
        return

    def getPoster3(self, output):
        with open(self.poster3, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        if fileExists(poster3):
            self["poster3"].instance.setPixmapFromFile(poster3)
            self['poster3'].show()
        return

    def getPoster4(self, output):
        with open(self.poster4, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        if fileExists(poster4):
            self["poster4"].instance.setPixmapFromFile(poster4)
            self['poster4'].show()
        return

    def getBanner1(self, output):
        with open(self.banner1, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showBanner1(self.banner1)

    def showBanner1(self, banner1):
        if fileExists(banner1):
            self["banner1"].instance.setPixmapFromFile(banner1)
            self['banner1'].show()
        return

    def getBanner2(self, output):
        with open(self.banner2, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showBanner2(self.banner2)

    def showBanner2(self, banner2):
        if fileExists(banner2):
            self["banner2"].instance.setPixmapFromFile(banner2)
            self['banner2'].show()
        return

    def getBanner3(self, output):
        with open(self.banner3, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showBanner3(self.banner3)

    def showBanner3(self, banner3):
        if fileExists(banner3):
            self["banner3"].instance.setPixmapFromFile(banner3)
            self['banner3'].show()
        return

    def getBanner4(self, output):
        with open(self.banner4, 'wb', encoding='utf-8') as file:
            file.write(output)
        self.showBanner4(self.banner4)

    def showBanner4(self, banner4):
        if fileExists(banner4):
            self["banner4"].instance.setPixmapFromFile(banner4)
            self['banner4'].show()
        return

    def download(self, link, name):
        try:
            if PY3:
                link = link.encode()
            callInThread(threadGetPage, url=link, file=None, key=None, success=name, fail=self.downloadError)
        except Exception as e:
            print(str(e))

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        files_to_remove = [
            self.poster1, self.poster2, self.poster3, self.poster4,
            self.banner1, self.banner2, self.banner3, self.banner4
        ]
        for filepath in files_to_remove:
            if fileExists(filepath):
                try:
                    remove(filepath)
                except Exception:
                    pass
        OnclearMem()
        self.close(None, None)


class filterList(Screen):

    def __init__(self, session, list, titel, filter, len, max):
        skin = join(skin_path + "filterList.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.hideflag = True
        self.filter = filter
        self.setTitle(titel)
        self.list = list
        self.listentries = []
        self['list'] = ItemList([])
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.zap,
            'prevBouquet': self.zap,
            'blue': self.hideScreen,
            '6': self.resetFilter,
            '7': self.resetFilter,
            '8': self.resetFilter,
            '9': self.resetFilter,
            '0': self.gotoEnd,
            '1': self.gotoFirst,
        }, -1)
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        idx = 0
        for x in self.list:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryText(pos=(10, 0), size=(1240, 40), font=30, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list[i]))
                else:
                    res.append(MultiContentEntryText(pos=(5, 0), size=(700, 30), font=26, color=0xFFFFFF, backcolor_sel=0x0043ac, color_sel=0xFFFFFF, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=self.list[i]))
                self.listentries.append(res)
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)

    def ok(self):
        index = self['list'].getSelectedIndex()
        current = self.list[index]
        self.close(current)

    def resetFilter(self):
        self.close(self.filter)

    def down(self):
        self['list'].down()

    def up(self):
        self['list'].up()

    def gotoEnd(self):
        end = len(self.list) - 1
        self['list'].moveToIndex(end)

    def gotoFirst(self):
        self['list'].moveToIndex(0)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
        else:
            self.hideflag = True

    def exit(self, result=None):
        self.close(None)
        return


class filterSeasonList(Screen):

    def __init__(self, session, season_list, content):
        Screen.__init__(self, session)
        skin_file = join(skin_path, "filterSeasonList.xml")
        with open(skin_file, "r") as f:
            self.skin = f.read()
        self.hideflag = True
        self.content = content
        self.list = season_list
        self.listentries = []

        self['list'] = ItemList([])
        self['actions'] = ActionMap(
            ['OkCancelActions', 'DirectionActions', 'ColorActions',
             'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'],
            {
                'ok': self.ok,
                'cancel': self.exit,
                'down': self.down,
                'up': self.up,
                'nextBouquet': self.zap,
                'prevBouquet': self.zap,
                'blue': self.hideScreen,
                '4': self.resetFilter,
                '0': self.gotoEnd,
                '1': self.gotoFirst,
            }, -1)

        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        # Clear the listentries to avoid duplicates if layout is refreshed
        self.listentries = []
        totalSeasons = len(self.list)

        # Determine font size and position based on screen width
        if screenwidth.width() == 1920:
            font_size = 30
            pos_x = 10
            size = (760, 40)
        else:
            font_size = 26
            pos_x = 5
            size = (510, 30)

        # Create list entries with proper UI formatting
        for item in self.list:
            entry = [MultiContentEntryText(
                pos=(pos_x, 0),
                size=size,
                font=font_size,
                color=0xFFFFFF,
                backcolor_sel=0x0043ac,
                color_sel=0xFFFFFF,
                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                text=item
            )]
            self.listentries.append(entry)

        self['list'].l.setList(self.listentries)
        series = _('Series Episodes')
        free = _('Free Space:')
        folder = _('Movie Folder')
        movie_folder_path = config.plugins.moviebrowser.moviefolder.value

        if exists(movie_folder_path):
            try:
                stat = statvfs(movie_folder_path)
                freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
            except Exception as e:
                print("Error getting free disk space:", e)
                freeSize = "-?-"
            title = '%d %s (%s %s)' % (totalSeasons, series, freeSize, free)
        else:
            title = '%d %s (%s offline)' % (totalSeasons, series, folder)

        self.setTitle(title)

    def ok(self):
        index = self['list'].getSelectedIndex()
        if index < 0 or index >= len(self.list):
            return

        current = self.list[index]
        # Replace 'Specials' and 'Season ' with proper season format
        current = sub(r'(?i)specials', '(S00', current)
        current = sub(r'(?i)season ', '(S', current)

        self.close(current)

    def resetFilter(self):
        # Close dialog returning original content to reset filter
        self.close(self.content)

    def down(self):
        self['list'].down()

    def up(self):
        self['list'].up()

    def gotoEnd(self):
        end_index = len(self.list) - 1
        self['list'].moveToIndex(end_index)

    def gotoFirst(self):
        self['list'].moveToIndex(0)

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        self.hideflag = not self.hideflag

    def exit(self, result=None):
        self.close(None)


class getABC(Screen):

    LETTER_GROUPS = ["ABC", "DEF", "GHI", "JKL", "MNO", "PQRS", "TUV", "WXYZ"]

    def __init__(self, session, ABC, XYZ):
        skin = join(skin_path + "getABC.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        if XYZ is True and ABC == "ABC":
            self.field = "WXYZ"
        else:
            self.field = ABC
        self["ABC"] = Label(self.field)
        self["actions"] = ActionMap(
            ["OkCancelActions", "ChannelSelectBaseActions", "NumberActions"],
            {
                "cancel": self.quit,
                "ok": self.OK,
                "nextMarker": self.next_group,
                "prevMarker": self.prev_group,
                "2": lambda: self.cycle_letter_in_group("ABC"),
                "3": lambda: self.cycle_letter_in_group("DEF"),
                "4": lambda: self.cycle_letter_in_group("GHI"),
                "5": lambda: self.cycle_letter_in_group("JKL"),
                "6": lambda: self.cycle_letter_in_group("MNO"),
                "7": lambda: self.cycle_letter_in_group("PQRS"),
                "8": lambda: self.cycle_letter_in_group("TUV"),
                "9": lambda: self.cycle_letter_in_group("WXYZ"),
            },
        )

        self.Timer = eTimer()
        self.Timer.callback.append(self.returnABC)
        self.Timer.start(2500, True)

    def next_group(self):
        self.Timer.start(2000, True)
        self.field = self._next_group(self.field)
        self["ABC"].setText(self.field)

    def prev_group(self):
        self.Timer.start(2000, True)
        self.field = self._prev_group(self.field)
        self["ABC"].setText(self.field)

    def cycle_letter_in_group(self, group):
        self.Timer.start(2000, True)
        if self.field not in group:
            # Set to first letter of group
            self.field = group[0]
        else:
            # Cycle letter within the group
            index = group.index(self.field)
            index = (index + 1) % len(group)
            self.field = group[index]
        self["ABC"].setText(self.field)

    def OK(self):
        self.Timer.start(2000, True)
        if self.field in self.LETTER_GROUPS:
            self.field = self.field[1]
        else:
            for group in self.LETTER_GROUPS:
                if self.field in group:
                    index = group.index(self.field)
                    index = (index + 1) % len(group)
                    self.field = group[index]
                    break
        self["ABC"].setText(self.field)

    def _next_group(self, current):
        for i, group in enumerate(self.LETTER_GROUPS):
            if current == group or current in group:
                return self.LETTER_GROUPS[(i + 1) % len(self.LETTER_GROUPS)]
        return self.LETTER_GROUPS[0]

    def _prev_group(self, current):
        for i, group in enumerate(self.LETTER_GROUPS):
            if current == group or current in group:
                return self.LETTER_GROUPS[(i - 1) % len(self.LETTER_GROUPS)]
        return self.LETTER_GROUPS[-1]

    def returnABC(self):
        self.Timer.stop()
        self.close(self.field)

    def quit(self):
        self.Timer.stop()
        self.close(None)
        return


class switchScreen(Screen):

    def __init__(self, session, number, mode):
        skin_file = join(skin_path, "switchScreen.xml")
        with open(skin_file, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)

        # Initialize pixmaps
        self.select_pixmaps = [Pixmap(), Pixmap(), Pixmap()]
        for i, pixmap in enumerate(self.select_pixmaps, 1):
            self[str("select_" + str(i))] = pixmap
            pixmap.hide()

        # Labels text according to mode
        if mode == "content":
            labels_text = ['MOVIES', 'SERIES', 'MOVIES & SERIES']
        else:
            labels_text = ['METRIX', 'BACKDROP', 'POSTERWALL']

        # Initialize normal and selected labels
        self.label_normal = []
        self.label_selected = []

        for i, text in enumerate(labels_text, 1):
            label = Label(text)
            label_select = Label(text)
            self[str("label_" + str(i))] = label
            self[str("label_select_" + str(i))] = label_select
            label_select.hide()
            self.label_normal.append(label)
            self.label_selected.append(label_select)

        self.number = number
        self.show_selection(self.number)

        self["actions"] = ActionMap(
            ['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions'],
            {
                'ok': self.returnNumber,
                'cancel': self.quit,
                'down': self.next,
                'up': self.next,
                'red': self.next,
                '5': self.next
            }, -1
        )

        self.Timer = eTimer()
        self.Timer.callback.append(self.returnNumber)
        self.Timer.start(2500, True)

    def show_selection(self, index):
        for i in range(3):
            self.label_normal[i].show()
            self.select_pixmaps[i].hide()
            self.label_selected[i].hide()

        idx = index - 1
        self.label_normal[idx].hide()
        self.select_pixmaps[idx].show()
        self.label_selected[idx].show()

    def next(self):
        self.Timer.start(2000, True)
        self.number += 1
        if self.number > 3:
            self.number = 1
        self.show_selection(self.number)

    def returnNumber(self):
        self.Timer.stop()
        self.close(self.number)

    def quit(self):
        self.Timer.stop()
        self.close(None)


class switchStart(Screen):

    def __init__(self, session, number):
        skin_file = join(skin_path, "switchStart.xml")
        with open(skin_file, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)

        # Define groups of widgets for easier management
        self.select_pixmaps = [
            self["select_1"] if "select_1" in self else Pixmap(),
            self["select_2"] if "select_2" in self else Pixmap(),
            self["select_3"] if "select_3" in self else Pixmap()
        ]
        self.label_normal = [
            self["label_1"] if "label_1" in self else Label('MOVIES'),
            self["label_2"] if "label_2" in self else Label('SERIES'),
            self["label_3"] if "label_3" in self else Label('MOVIES & SERIES')
        ]
        self.label_selected = [
            self["label_select_1"] if "label_select_1" in self else Label('MOVIES'),
            self["label_select_2"] if "label_select_2" in self else Label('SERIES'),
            self["label_select_3"] if "label_select_3" in self else Label('MOVIES & SERIES')
        ]

        # Initialize widget states
        for pixmap in self.select_pixmaps:
            pixmap.hide()
        for label in self.label_selected:
            label.hide()

        self.number = number
        self.show_selection(self.number)

        self["actions"] = ActionMap(
            ['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions', 'InfobarActions'],
            {
                'ok': self.returnNumber,
                'cancel': self.quit,
                'showMovies': self.next,
                'down': self.next,
                '5': self.next
            }, -1
        )

        self.Timer = eTimer()
        self.Timer.callback.append(self.returnNumber)
        self.Timer.start(4000, True)

    def show_selection(self, index):
        # Hide all first
        for i in range(3):
            self.label_normal[i].show()
            self.select_pixmaps[i].hide()
            self.label_selected[i].hide()

        # Show selected
        idx = index - 1
        self.label_normal[idx].hide()
        self.select_pixmaps[idx].show()
        self.label_selected[idx].show()

    def next(self):
        self.Timer.start(2000, True)
        self.number += 1
        if self.number > 3:
            self.number = 1
        self.show_selection(self.number)

    def returnNumber(self):
        self.Timer.stop()

        # Mapping styles and calls
        def open_browser(style, section, topref1, topref2):
            if style == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, topref1, topref2)
            elif style == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, topref1, topref2)
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, topref1, topref2)

        if self.number == 1:
            open_browser(config.plugins.moviebrowser.style.value, 'movie', ':::Movie:Top:::', ':::Movie:Top:::')
        elif self.number == 2:
            open_browser(config.plugins.moviebrowser.seriesstyle.value, 'series', ':::Series:Top:::', ':::Series:Top:::')
        elif self.number == 3:
            open_browser(config.plugins.moviebrowser.style.value, 'all', ':Top:::', ':Top:::')

    def quit(self):
        self.close()


class helpScreen(Screen):

    def __init__(self, session):
        skin_file = join(skin_path, "helpScreen.xml")
        with open(skin_file, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        self.setTitle(_('Movie Browser Key Assignment'))
        self["label"] = Label()
        self['actions'] = ActionMap(['OkCancelActions'], {
            'ok': self.close,
            'cancel': self.close
        }, -1)
        self.onLayoutFinish.append(self.finishLayout)

    def finishLayout(self):
        helpdesc = self.homecontext()
        self["label"].setText(helpdesc)

    def homecontext(self):
        lines = [
            _('Manage your Movies & Series V.%s') % str(version),
            _('Help'),
            _('Toggle Plugin Style'),
            _('Toggle hide/show plugin'),
            _('Info Button: Toggle show/hide infos'),
            _('Video Button: Update Database'),
            _('Text Button: Edit Database'),
            _('Stop Button: Mark movie as seen'),
            _('Radio Button: Delete/Blacklist movie'),
            _('<- -> Button: Go to first letter'),
            _('Button 1: CutListEditor/MovieCut/LogView'),
            _('Button 2: Renew infos on TMDb'),
            _('Button 3: Renew infos on TheTVDb'),
            _('Button 4: Hide/show seen movies'),
            _('Button 5: Toggle Movies/Series view'),
            _('Button 6: Movie Folder Selection'),
            _('Button 7: Movie Director Selection'),
            _('Button 8: Movie Actor Selection'),
            _('Button 9: Movie Genre Selection'),
            _('Button 0: Go to end of list'),
        ]
        return "\n".join(lines)


class movieBrowserConfig(ConfigListScreen, Screen):

    def __init__(self, session):

        skin = join(skin_path + "movieBrowserConfig.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.session = session
        self.onChangedEntry = []
        self.sortorder = config.plugins.moviebrowser.sortorder.value
        self.moviefolder = config.plugins.moviebrowser.moviefolder.value
        self.cachefolder = config.plugins.moviebrowser.cachefolder.value
        # DATABASE_PATH = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.m1v = config.plugins.moviebrowser.m1v.value
        self.timer_update = config.plugins.moviebrowser.timerupdate.value
        self.timer_hour = config.plugins.moviebrowser.timer.value[0]
        self.timer_min = config.plugins.moviebrowser.timer.value[1]
        self['save'] = Label(_('Save'))
        self['cancel'] = Label(_('Cancel'))
        self['plugin'] = Pixmap()
        self['status'] = StaticText()
        self.ready = True
        list = []
        ConfigListScreen.__init__(self, list, session=self.session, on_change=self.UpdateComponents)
        self.createSetup()

        self['actions'] = ActionMap(['HelpActions', 'SetupActions', 'VirtualKeyboardActions', 'ColorActions', 'DirectionActions'], {
            'ok': self.keyRun,
            'showVirtualKeyboard': self.KeyText,
            'cancel': self.cancel,
            'red': self.cancel,
            'green': self.save,
            'save': self.save,
            'left': self.keyLeft,
            'down': self.keyDown,
            'up': self.keyUp,
            'right': self.keyRight}, -1)

        self.onLayoutFinish.append(self.UpdateComponents)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        pass

    def createSetup(self):
        self.editListEntry = None
        list = []
        list.append(getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style))
        list.append(getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle))
        list.append(getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie))
        list.append(getConfigListEntry(_('Load last Selection/Filter on Start:'), config.plugins.moviebrowser.lastfilter))
        list.append(getConfigListEntry(_('Movie Folder:'), config.plugins.moviebrowser.moviefolder))
        list.append(getConfigListEntry(_('Cache Folder:'), config.plugins.moviebrowser.cachefolder))
        list.append(getConfigListEntry(_('Movie Sort Order:'), config.plugins.moviebrowser.sortorder))
        list.append(getConfigListEntry(_('Show List of Movie Folder:'), config.plugins.moviebrowser.showfolder))
        list.append(getConfigListEntry(_('Movies or Series:'), config.plugins.moviebrowser.filter))
        list.append(getConfigListEntry(_('Movies or Series Selection at Start:'), config.plugins.moviebrowser.showswitch))
        list.append(getConfigListEntry(_('Show Backdrops:'), config.plugins.moviebrowser.backdrops))
        list.append(getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v))
        list.append(getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv))
        list.append(getConfigListEntry(_('Download new Backdrops:'), config.plugins.moviebrowser.download))
        list.append(getConfigListEntry(_('Posterwall/Backdrop Show Plot:'), config.plugins.moviebrowser.plotfull))
        list.append(getConfigListEntry(_('Metrix List Selection Color:'), config.plugins.moviebrowser.metrixcolor))
        list.append(getConfigListEntry(_('TMDb/TheTVDb Language:'), config.plugins.moviebrowser.language))
        list.append(getConfigListEntry(_("Load TMDB Apikey from /tmp/tmdb_api.txt"), config.plugins.moviebrowser.api))
        list.append(getConfigListEntry(_("Signup on TMDB and input free personal ApiKey"), config.plugins.moviebrowser.txtapi))
        list.append(getConfigListEntry(_("Load TheTVDb Apikey from /tmp/thetvdb_api.txt"), config.plugins.moviebrowser.tvdbapi))
        list.append(getConfigListEntry(_("Signup on TheTVDb and input free personal ApiKey"), config.plugins.moviebrowser.txttvdbapi))
        list.append(getConfigListEntry(_('Update Database with Timer:'), config.plugins.moviebrowser.timerupdate))
        if config.plugins.moviebrowser.timerupdate.getValue():
            list.append(getConfigListEntry(_('Timer Database Update:'), config.plugins.moviebrowser.timer))
            list.append(getConfigListEntry(_('Hide Plugin during Update:'), config.plugins.moviebrowser.hideupdate))

        list.append(getConfigListEntry(_('Reset Database:'), config.plugins.moviebrowser.reset))
        list.append(getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup))
        list.append(getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup))
        list.append(getConfigListEntry(_('Restore Database:'), config.plugins.moviebrowser.restore))
        list.append(getConfigListEntry(_('Select skin *Restart GUI Required:'), config.plugins.moviebrowser.skin))
        list.append(getConfigListEntry(_('Start Plugin with Video Button:'), config.plugins.moviebrowser.videobutton))
        list.append(getConfigListEntry(_('Plugin Transparency:'), config.plugins.moviebrowser.transparency))
        list.append(getConfigListEntry(_('Plugin in Enigma Menu:'), config.plugins.moviebrowser.showmenu))
        self["config"].list = list
        self["config"].l.setList(list)

    def finished(self, retval):
        del self.container.appClosed[:]
        del self.container
        new_cache = config.plugins.moviebrowser.cachefolder.value
        old_cache = self.cachefolder
        try:
            makedirs(new_cache, exist_ok=True)
            if exists(old_cache):
                for item in listdir(old_cache):
                    s = join(old_cache, item)
                    d = join(new_cache, item)
                    if isdir(s):
                        copytree(s, d, symlinks=True)
                    else:
                        copy2(s, d)
                rmtree(old_cache)
        except Exception as e:
            self.session.open(MessageBox,
                              _("Error moving cache folder: %s") % str(e),
                              MessageBox.TYPE_ERROR)
        for x in self['config'].list:
            x[1].save()
        configfile.save()
        configfile.load()

    def UpdateComponents(self):
        current = self['config'].getCurrent()
        # Movie and Series style preview update
        if current == getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style):
            self.updateStylePreview(config.plugins.moviebrowser.style.value)
        elif current == getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle):
            self.updateStylePreview(config.plugins.moviebrowser.seriesstyle.value)
        # Manage m1v Backdrops and TV Background option consistency
        elif current == getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v) or \
                current == getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv):
            self.ensureBackdropSettings()
        # Fix last movie startup config
        elif current == getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie):
            self.fixLastMovieSetting()
        # Backup database if requested
        elif current == getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup):
            self.backupDatabase()
        # Restore database if requested
        elif current == getConfigListEntry(_('Restore Database:'), config.plugins.moviebrowser.restore):
            self.restoreDatabase()
        # Cleanup cache folder if requested
        elif current == getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup):
            self.cleanupCache()
        self.createSetup()

    def updateStylePreview(self, style_value):
        png = skin_directory + "pic/setup/" + str(style_value) + ".png"
        if fileExists(png):
            self["plugin"].instance.setPixmapFromFile(png)
            self['plugin'].show()

    def ensureBackdropSettings(self):
        if config.plugins.moviebrowser.m1v.value is True:
            config.plugins.moviebrowser.showtv.value = 'hide'

    def fixLastMovieSetting(self):
        if config.plugins.moviebrowser.showfolder.value and config.plugins.moviebrowser.lastmovie.value == 'folder':
            config.plugins.moviebrowser.lastmovie.value = 'yes'

    def backupDatabase(self):
        if not exists(self.cachefolder):
            self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Backup canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
            return
        if not fileExists(DATABASE_PATH):
            self.session.open(MessageBox, _('\nDatabase %s not found:\nMovie Browser Database Backup canceled.') % str(DATABASE_PATH), MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.backup.value:
            try:
                makedirs(self.cachefolder + '/backup')
            except OSError:
                pass
            with open(DATABASE_PATH, 'r') as f:
                data = f.read()
            with open(self.cachefolder + '/backup/database', 'w') as f:
                f.write(data)
            self.session.open(MessageBox, _('\nDatabase backed up to %s') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
        config.plugins.moviebrowser.backup.setValue(False)
        config.plugins.moviebrowser.backup.save()
        configfile.load()

    def restoreDatabase(self):
        if not exists(self.cachefolder):
            self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Restore canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
            return
        backup_path = self.cachefolder + '/backup/database'
        if not fileExists(backup_path):
            self.session.open(MessageBox, _('\nDatabase Backup %s not found:\nMovie Browser Database Restore canceled.') % backup_path, MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.restore.value:
            with open(backup_path, 'r') as f:
                data = f.read()
            with open(DATABASE_PATH, 'w') as f:
                f.write(data)
            self.session.open(MessageBox, _('\nDatabase restored from %s') % backup_path, MessageBox.TYPE_INFO, close_on_any_key=True)
        config.plugins.moviebrowser.restore.setValue(False)
        config.plugins.moviebrowser.restore.save()
        configfile.load()

    def cleanupCache(self):
        if not exists(self.cachefolder):
            self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nCleanup Cache Folder canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
            return
        if not fileExists(DATABASE_PATH):
            self.session.open(MessageBox, _('\nDatabase %s not found:\nCleanup Cache Folder canceled.') % str(DATABASE_PATH), MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.cleanup.value:
            with open(DATABASE_PATH, 'r') as f:
                data = f.read()
            data += ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
            count = 0
            for root, dirs, files in walk(self.cachefolder, topdown=False):
                for name in files:
                    shortname = sub('[.]jpg', '', name)
                    shortname = sub('[.]m1v', '', shortname)
                    if search(shortname, data) is None:
                        filename = join(root, name)
                        if fileExists(filename):
                            remove(filename)
                            count += 1
            if count == 0:
                self.session.open(MessageBox, _('\nNo orphaned Backdrops or Posters found:\nYour Cache Folder is clean.'), MessageBox.TYPE_INFO, close_on_any_key=True)
            else:
                self.session.open(MessageBox, _('\nCleanup Cache Folder finished:\n%s orphaned Backdrops or Posters removed.') % str(count), MessageBox.TYPE_INFO, close_on_any_key=True)
            config.plugins.moviebrowser.cleanup.setValue(False)
            config.plugins.moviebrowser.cleanup.save()
            configfile.load()

    def keyRun(self):
        current = self["config"].getCurrent()[1]
        if current == config.plugins.moviebrowser.moviefolder:
            self.openDirectoryBrowser(config.plugins.moviebrowser.moviefolder.value)
        elif current == config.plugins.moviebrowser.tvdbapi:
            self.tvdbkeyApi()
        elif current == config.plugins.moviebrowser.api:
            self.keyApi()
        else:
            self.save()

    def openDirectoryBrowser(self, path):
        try:
            from Screens.LocationBox import LocationBox
            self.session.openWithCallback(self.openDirectoryBrowserCB,
                                          LocationBox,
                                          windowTitle=_('Choose Directory:'),
                                          text=_('Choose Directory'),
                                          currDir=str(path),
                                          bookmarks=config.movielist.videodirs,
                                          autoAdd=False,
                                          editDir=True,
                                          inhibitDirs=['/bin', '/boot', '/dev', '/home', '/lib', '/proc', '/run', '/sbin', '/sys', '/var'],
                                          minFree=15)
        except Exception as e:
            print('openDirectoryBrowser get failed: ', str(e))

    def openDirectoryBrowserCB(self, path):
        if path is not None:
            config.plugins.moviebrowser.moviefolder.setValue(path)
            self.createSetup()
        return

    def _handle_api_key(self, config_entry, key_path, success_message):
        if not fileExists(key_path):
            self.session.open(MessageBox, _("File %s non trovato!") % key_path, MessageBox.TYPE_ERROR)
            return

        with open(key_path, 'r') as f:
            key = f.readline().strip()
            config_entry.value = key
            config_entry.save()

        self.session.open(MessageBox, success_message, MessageBox.TYPE_INFO)

    def keyApi(self):
        self._handle_api_key(
            config.plugins.moviebrowser.txtapi,
            "/tmp/tmdb_api.txt",
            _("TMDB API key successfully imported!")
        )

    def tvdbkeyApi(self):
        self._handle_api_key(
            config.plugins.moviebrowser.txttvdbapi,
            "/tmp/thetvdb_api.txt",
            _("TheTVDb API key successfully imported!")
        )

    def selectionChanged(self):
        self['status'].setText(self['config'].getCurrent()[0])

    def save(self):
        if self.ready is True:
            self.ready = False
            series = ''
            if config.plugins.moviebrowser.sortorder.value != self.sortorder:
                if fileExists(DATABASE_PATH):
                    try:
                        with open(DATABASE_PATH, "r") as f:
                            lines = f.readlines()

                        series = [line for line in lines if ":::Series:::" in line]
                        movies = [line for line in lines if ":::Series:::" not in line]
                        series.sort(key=lambda line: line.split(":::")[0])

                        with open(DATABASE_PATH + ".series", "w") as fseries:
                            fseries.writelines(series)

                        with open(DATABASE_PATH + ".movies", "w") as fmovies:
                            fmovies.writelines(movies)

                    except Exception as e:
                        print("Error processing database:", e)

                    try:
                        if config.plugins.moviebrowser.sortorder.value == 'name':
                            lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower())
                        elif config.plugins.moviebrowser.sortorder.value == 'name_reverse':
                            lines.sort(key=lambda line: line.split(':::')[0].replace('Der ', '').replace('Die ', '').replace('Das ', '').replace('The ', '').lower(), reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'rating':
                            lines.sort(key=lambda line: line.split(':::')[4])
                        elif config.plugins.moviebrowser.sortorder.value == 'rating_reverse':
                            lines.sort(key=lambda line: line.split(':::')[4], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'year':
                            lines.sort(key=lambda line: line.split(':::')[8])
                        elif config.plugins.moviebrowser.sortorder.value == 'year_reverse':
                            lines.sort(key=lambda line: line.split(':::')[8], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'date':
                            lines.sort(key=lambda line: line.split(':::')[2])
                        elif config.plugins.moviebrowser.sortorder.value == 'date_reverse':
                            lines.sort(key=lambda line: line.split(':::')[2], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'folder':
                            lines.sort(key=lambda line: line.split(':::')[1])
                        elif config.plugins.moviebrowser.sortorder.value == 'folder_reverse':
                            lines.sort(key=lambda line: line.split(':::')[1], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'runtime':
                            lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')))
                        elif config.plugins.moviebrowser.sortorder.value == 'runtime_reverse':
                            lines.sort(key=lambda line: int(line.split(':::')[3].replace(' min', '')), reverse=True)
                    except IndexError:
                        pass
                    except ValueError:
                        self.session.open(MessageBox, _('\nDatabase Error: Entry without runtime'), MessageBox.TYPE_ERROR)

                    with open(DATABASE_PATH + ".movies", "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    files = [DATABASE_PATH + ".movies", DATABASE_PATH + ".series"]
                    with open(DATABASE_PATH + ".sorted", "w", encoding="utf-8") as outfile:
                        for name in files:
                            if fileExists(name):
                                with open(name, "r", encoding="utf-8") as infile:
                                    outfile.write(infile.read())

                    for tmp in files:
                        if fileExists(tmp):
                            remove(tmp)

                    rename(DATABASE_PATH + ".sorted", DATABASE_PATH)

            if config.plugins.moviebrowser.timerupdate.value is True:
                if self.timer_hour != config.plugins.moviebrowser.timer.value[0] or self.timer_min != config.plugins.moviebrowser.timer.value[1] or self.timer_update is False:
                    if timerupdate.session is None:
                        timerupdate.saveSession(self.session)
                    timerupdate.restart()

            # Move cache folder if changed
            if config.plugins.moviebrowser.cachefolder.value != self.cachefolder:
                self.container = eConsoleAppContainer()
                self.container.appClosed.append(self.finished)
                newcache = sub(r'/cache', '', config.plugins.moviebrowser.cachefolder.value)
                self.container.execute(
                    "mkdir -p '%s' && cp -r '%s' '%s' && rm -rf '%s'" % (
                        config.plugins.moviebrowser.cachefolder.value,
                        self.cachefolder,
                        newcache,
                        self.cachefolder
                    )
                )
                self.cachefolder = config.plugins.moviebrowser.cachefolder.value
                config.plugins.moviebrowser.cachefolder.save()

            # Handle reset flag
            if config.plugins.moviebrowser.reset.value:
                open(DATABASE_RESET, "w").close()
                config.plugins.moviebrowser.reset.setValue(False)
                config.plugins.moviebrowser.reset.save()

            # Handle backup flag
            if config.plugins.moviebrowser.backup.value:
                config.plugins.moviebrowser.backup.setValue(False)
                config.plugins.moviebrowser.backup.save()

            # Handle restore flag
            if config.plugins.moviebrowser.restore.value:
                config.plugins.moviebrowser.restore.setValue(False)
                config.plugins.moviebrowser.restore.save()

            # Handle cleanup flag
            if config.plugins.moviebrowser.cleanup.value:
                config.plugins.moviebrowser.cleanup.setValue(False)
                config.plugins.moviebrowser.cleanup.save()
            else:
                configfile.save()
            configfile.load()
            # Close dialog
            self.close(True)

        return

    def KeyText(self):
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        current = self['config'].getCurrent()
        if current:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback:
            current_config = self["config"].getCurrent()[1]
            if current_config in [config.plugins.moviebrowser.moviefolder, config.plugins.moviebrowser.cachefolder]:
                callback = normpath(callback)

            current_config.value = callback
            self["config"].invalidateCurrent()

    def cancel(self, answer=None):
        if answer is None:
            if self["config"].isChanged():
                self.session.openWithCallback(
                    self.cancel,
                    MessageBox,
                    _("Really close without saving settings?")
                )
                return
            else:
                configfile.load()
                self.close(False)
        elif answer:
            for entry in self["config"].list:
                entry[1].cancel()
            self.close(False)
        else:
            pass

    def exit(self):
        if self.m1v is False and config.plugins.moviebrowser.m1v.value is True:
            config.plugins.moviebrowser.transparency.value = 200
            config.plugins.moviebrowser.transparency.save()
            configfile.save()
        elif self.m1v is True and config.plugins.moviebrowser.m1v.value is False:
            config.plugins.moviebrowser.transparency.value = 255
            config.plugins.moviebrowser.transparency.save()
            configfile.save()
        if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
            number = 1
        elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
            number = 2
        else:
            number = 3
        if config.plugins.moviebrowser.showswitch.value is True:
            self.session.openWithCallback(self.close, switchStart, number)
        elif number == 2:
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif config.plugins.moviebrowser.style.value == 'metrix':
            self.session.openWithCallback(self.close, movieBrowserMetrix, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
        elif config.plugins.moviebrowser.style.value == 'backdrop':
            self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
        else:
            self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)

    def keySave(self):  # why don't work
        for i in range(0, len(config.plugins.moviebrowser)):
            config.plugins.moviebrowser[i].save()
        ConfigListScreen.keySave(self)
        configfile.load()

    def changedEntry(self):
        self.item = self["config"].getCurrent()
        for x in self.onChangedEntry:
            x()
        try:
            if isinstance(self["config"].getCurrent()[1], ConfigYesNo) or isinstance(self["config"].getCurrent()[1], ConfigOnOff) or isinstance(self["config"].getCurrent()[1], ConfigSelection) or isinstance(self["config"].getCurrent()[1], ConfigText):
                self.createSetup()
        except:
            pass

    def getCurrentEntry(self):
        return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

    def getCurrentValue(self):
        return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def keyLeft(self):
        ConfigListScreen.keyLeft(self)
        self.createSetup()

    def keyRight(self):
        ConfigListScreen.keyRight(self)
        self.createSetup()

    def keyDown(self):
        self['config'].instance.moveSelection(self['config'].instance.moveDown)
        self.createSetup()

    def keyUp(self):
        self['config'].instance.moveSelection(self['config'].instance.moveUp)
        self.createSetup()


class timerUpdate():

    def __init__(self):
        self.session = None
        self.startTimer = eTimer()
        self.dailyTimer = eTimer()

    def saveSession(self, session):
        self.session = session

    def start(self):
        self._remove_callback(self.startTimer, self.daily)
        self.startTimer.callback.append(self.daily)
        now = datetime.datetime.now()
        current_minutes = now.hour * 60 + now.minute
        target_minutes = config.plugins.moviebrowser.timer.value[0] * 60 + config.plugins.moviebrowser.timer.value[1]
        delay_minutes = target_minutes - current_minutes if current_minutes < target_minutes else 1440 - current_minutes + target_minutes
        self.startTimer.start(delay_minutes * 60 * 1000, True)
        self._log("Initial Update Timer started: %s\nTimer Value (min): %s\n" % (now.strftime('%Y-%m-%d %H:%M:%S'), str(delay_minutes)))

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        self.startTimer.stop()
        self._remove_callback(self.startTimer, self.daily)
        self.dailyTimer.stop()
        self._remove_callback(self.dailyTimer, self.runUpdate)
        self._log("Database Update Timer stopped: %s\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def daily(self):
        self.startTimer.stop()
        self._remove_callback(self.startTimer, self.daily)
        self.runUpdate()
        self._remove_callback(self.dailyTimer, self.runUpdate)
        self.dailyTimer.callback.append(self.runUpdate)
        self.dailyTimer.start(1440 * 60 * 1000, False)
        self._log("Database Update Timer started: %s\nTimer Value (min): 1440\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def runUpdate(self):
        UpdateDatabase(False, "", "", "").showResult(True)
        self._log("Movie Database Update started: %s\n" % datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _remove_callback(self, timer, func):
        if func in timer.callback:
            timer.callback.remove(func)

    def _log(self, message):
        with open(TIMER_LOG_PATH, "a") as f:
            f.write(_("*******Movie Browser Database Update Timer*******\n") + message)


def main(session, **kwargs):
    if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
        number = 1
    elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
        number = 2
    else:
        number = 3
    if config.plugins.moviebrowser.showswitch.value is True:
        session.open(switchStart, number)
    elif number == 2:
        if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
            session.open(movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
            session.open(movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
        else:
            session.open(movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
    elif config.plugins.moviebrowser.style.value == 'metrix':
        session.open(movieBrowserMetrix, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
    elif config.plugins.moviebrowser.style.value == 'backdrop':
        session.open(movieBrowserBackdrop, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
    else:
        session.open(movieBrowserPosterwall, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)


def mainInfoBar(session, **kwargs):
    # global infobarsession
    if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
        number = 1
    elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
        number = 2
    else:
        number = 3
    if config.plugins.moviebrowser.showswitch.value is True:
        infobarsession.open(switchStart, number)
    elif number == 2:
        if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
            infobarsession.open(movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
            infobarsession.open(movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
        else:
            infobarsession.open(movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
    elif config.plugins.moviebrowser.style.value == 'metrix':
        infobarsession.open(movieBrowserMetrix, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
    elif config.plugins.moviebrowser.style.value == 'backdrop':
        infobarsession.open(movieBrowserBackdrop, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)
    else:
        infobarsession.open(movieBrowserPosterwall, 0, config.plugins.moviebrowser.filter.value, config.plugins.moviebrowser.filter.value)


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [('Movie Browser', main, 'moviebrowser', 42)]
    return []


def autostart(reason, **kwargs):
    global infobarsession
    if 'session' in kwargs:
        info = _('*******Movie Browser Database Update*******\n')
        with open(UPDATE_LOG_PATH, 'w') as f:
            f.write(info)
        if config.plugins.moviebrowser.videobutton.value is True:
            infobarsession = kwargs['session']
            from Screens.InfoBar import InfoBar
            InfoBar.showMovies = mainInfoBar
        if config.plugins.moviebrowser.timerupdate.value is True:
            with open(TIMER_LOG_PATH, 'w') as f:
                f.close()
            session = kwargs['session']
            timerupdate.saveSession(session)
            try:
                timerupdate.start()
            except:
                error = sys.exc_info()[1]
                errortype = sys.exc_info()[0]
                now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                result = _('*******Movie Browser Database Update*******\nTime: %s\nError: %s\nReason: %s') % (now, str(errortype), str(error))
                print(result)
                with open(UPDATE_LOG_PATH, 'w') as f:
                    f.write(result)

        if exists(DATABASE_CACHE):
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r') as data:
                    data = data.read()
                    data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
                folder = DATABASE_CACHE
                count = 0
                now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                for root, dirs, files in walk(folder, topdown=False, onerror=None):
                    for name in files:
                        shortname = sub(r'[.]jpg', '', name)
                        shortname = sub(r'[.]m1v', '', shortname)
                        if search(shortname, data) is None:
                            filename = join(root, name)
                            if fileExists(filename):
                                remove(filename)
                                count += 1
                del data
                end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                info = _('*******Cleanup Cache Folder*******\nStart time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
                with open(CLEANUP_LOG_PATH, 'w') as f:
                    f.write(info)
    return


timerupdate = timerUpdate()


def Plugins(**kwargs):
    plugindesc = _("Manage your Movies & Series V.%s" % str(version))
    pluginname = "Movie Browser"
    plugin_list = [
        PluginDescriptor(name=pluginname, description=plugindesc, where=[PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main),
        PluginDescriptor(name=pluginname, description=plugindesc, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main),
        PluginDescriptor(name=pluginname, description=plugindesc, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)
    ]
    if config.plugins.moviebrowser.showmenu.value:
        plugin_list.append(PluginDescriptor(name=pluginname, description=plugindesc, where=[PluginDescriptor.WHERE_MENU], fnc=menu))
    return plugin_list
