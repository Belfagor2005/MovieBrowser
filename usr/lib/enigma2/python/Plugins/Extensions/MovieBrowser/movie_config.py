#!/usr/bin/python
# -*- coding: utf-8 -*-

# 20221004 Kiddac edit: python 3 support et al
# 20221204 Lululla edit & add: language, config, major fix
# 20221208 Lululla add callInThread getMountDefault
# 20221222 Lululla recoded, major fix
# 20240920 Lululla recoded - clean unnecessary code
# 20250516 Lululla refactoryzed all Cls and clean unnecessary all code
# 20251202 Lululla all recoded: fixed screen- code - url - bad code -
# separate libraries into other modules
from __future__ import print_function
import datetime
from sys import path
from re import sub, search, findall, S
from os import remove, rename, walk, makedirs, listdir
from os.path import exists, join, getmtime, isdir, normpath, dirname, abspath
from shutil import copytree, copy2, rmtree
from enigma import (
    eConsoleAppContainer,
    eTimer,
)
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.Label import Label
from Components.Language import language
from Components.Pixmap import Pixmap
from Components.Sources.StaticText import StaticText
from Components.config import (
    ConfigClock,
    ConfigDirectory,
    ConfigEnableDisable,
    ConfigOnOff,
    ConfigSelection,
    ConfigSlider,
    ConfigSubsection,
    ConfigText,
    ConfigYesNo,
    NoSave,
    config,
    configfile,
    getConfigListEntry,
)
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Tools.Directories import fileExists

from . import _, PY3
from .library import isFHD, transMOVIE, transSERIES


try:
    from urllib2 import Request, urlopen
except BaseException:
    from urllib.request import Request, urlopen


dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser"
if dir_plugins not in path:
    path.append(dir_plugins)

db_dir = join(dir_plugins, "db")
log_dir = join(dir_plugins, "log")
UPDATE_LOG_PATH = join(log_dir, "update.log")
TIMER_LOG_PATH = join(log_dir, "timer.log")
DATABASE_PATH = join(db_dir, "database")
DATABASE_RESET = join(db_dir, "reset")
DATABASE_CACHE = join(db_dir, "cache")
DATABASE_CACHE_HDD = join('/media/hdd', "moviebrowser/cache")
DATABASE_CACHE_USB = join('/media/usb', "moviebrowser/cache")
DATABASE_CACHE_NET = join('/media/net', "moviebrowser/cache")
BLACKLIST_PATH = join(db_dir, "blacklist")
skin_directory = "/".join([dir_plugins, "skin", "hd", ""])
if isFHD():
    skin_directory = "/".join([dir_plugins, "skin", "fhd", ""])

default_backdrop = "/".join([skin_directory, "pic",
                            "setup", "default_backdrop.png"])
default_folder = "/".join([skin_directory, "pic",
                          "browser", "default_folder.png"])
default_poster = "/".join([skin_directory, "pic",
                          "browser", "default_poster.png"])
default_banner = "/".join([skin_directory, "pic",
                          "browser", "default_banner.png"])
default_backdropm1v = "/".join([skin_directory,
                               "pic", "browser", "default_backdrop.m1v"])
infoBackPNG = "/".join([skin_directory, "pic",
                       "browser", "info_small_back.png"])
infosmallBackPNG = infoBackPNG
no_m1v = "/".join([skin_directory, "pic", "browser", "no.m1v"])
wiki_png = "/".join([skin_directory, "pic", "browser", "wiki.png"])

agents = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.10 Safari/605.1.1'}

tmdb_api = '3c3efcf47c3577558812bb9d64019d65'
thetvdb_api = 'a99d487bb3426e5f3a60dea6d3d3c7ef'
# thetvdb_api = 'D19315B88B2DE21F'


folders = listdir(skin_directory)
if "pic" in folders:
    folders.remove("pic")


""" init config """
config.plugins.moviebrowser = ConfigSubsection()
lang = language.getLanguage()[:2]
config.plugins.moviebrowser.language = ConfigSelection(default=lang, choices=[
    ('en', 'English'),
    ('de', 'German'),
    ('it', 'Italian'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('ru', 'Russian')
])

config.plugins.moviebrowser.filter = ConfigSelection(
    default=':::Movie:Top:::',
    choices=[
        (':::Movie:Top:::',
         _('Movies')),
        (':::Series:Top:::',
         _('Series')),
        (':Top:::',
         _('Movies & Series'))])
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
config.plugins.moviebrowser.download = ConfigSelection(
    default='update', choices=[
        ('access', _('On First Access')), ('update', _('On Database Update'))])
config.plugins.moviebrowser.m1v = ConfigOnOff(default=False)

if config.plugins.moviebrowser.m1v.value is True:
    config.plugins.moviebrowser.showtv = ConfigSelection(
        default='hide', choices=[('show', _('Show')), ('hide', _('Hide'))])
else:
    config.plugins.moviebrowser.showtv = ConfigSelection(
        default='show', choices=[('show', _('Show')), ('hide', _('Hide'))])

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
config.plugins.moviebrowser.skin = ConfigSelection(
    default='default', choices=folders)
skin_path = "%s%s/" % (skin_directory, config.plugins.moviebrowser.skin.value)
config.plugins.moviebrowser.plotfull = ConfigSelection(
    default='show', choices=[
        ('hide', _('Info Button')), ('show', _('Automatic'))])
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
config.plugins.moviebrowser.txtapi = ConfigText(
    default=tmdb_api, visible_width=60, fixed_size=False)
config.plugins.moviebrowser.tvdbapi = NoSave(ConfigSelection(['-> Ok']))
config.plugins.moviebrowser.txttvdbapi = ConfigText(
    default=thetvdb_api, visible_width=60, fixed_size=False)
config.plugins.moviebrowser.moviefolder = ConfigDirectory("/media/hdd/movie")

try:
    from Components.UsageConfig import defaultMoviePath
    downloadpath = defaultMoviePath()
    config.plugins.moviebrowser.moviefolder = ConfigDirectory(
        default=downloadpath)
except BaseException:
    if exists("/usr/bin/apt-get"):
        config.plugins.moviebrowser.moviefolder = ConfigDirectory(
            default='/media/hdd/movie/')

config.plugins.moviebrowser.cachefolder = ConfigSelection(
    default=DATABASE_CACHE,
    choices=[
        (DATABASE_CACHE,
         'Default'),
        (DATABASE_CACHE_HDD,
         '/media/hdd'),
        (DATABASE_CACHE_USB,
         '/media/usb'),
        (DATABASE_CACHE_NET,
         '/media/net'),
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
config.plugins.moviebrowser.transparency = ConfigSlider(
    default=255, limits=(100, 255))

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


def _import_browser_class(class_name):
    """Importa le classi da plugin.py evitando conflitti"""
    try:
        from Plugins.Extensions.MovieBrowser.plugin import movieBrowserMetrix, movieBrowserBackdrop, movieBrowserPosterwall
        classes = {
            'movieBrowserMetrix': movieBrowserMetrix,
            'movieBrowserBackdrop': movieBrowserBackdrop,
            'movieBrowserPosterwall': movieBrowserPosterwall
        }
        return classes.get(class_name)
    except ImportError:
        plugin_dir = dirname(abspath(__file__))
        if plugin_dir not in path:
            path.insert(0, plugin_dir)

        try:
            module = __import__('plugin')
            return getattr(module, class_name)
        except BaseException:
            return None


class switchStart(Screen):

    def __init__(self, session, number):
        skin = join(skin_path, "switchStart.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self["Title"] = Label("MovieBrowser")
        """
        self['select_1'] = Pixmap()
        self['select_2'] = Pixmap()
        self['select_3'] = Pixmap()
        self['select_1'].hide()
        self['select_2'].hide()
        self['select_3'].hide()
        self['label_1'] = Label('MOVIES')
        self['label_2'] = Label('SERIES')
        self['label_3'] = Label('MOVIES & SERIES')
        self['label_select_1'] = Label('MOVIES')
        self['label_select_2'] = Label('SERIES')
        self['label_select_3'] = Label('MOVIES & SERIES')
        self['label_select_1'].hide()
        self['label_select_2'].hide()
        self['label_select_3'].hide()
        self.number = number
        if self.number == 1:
            self['label_1'].hide()
            self['select_1'].show()
            self['label_select_1'].show()
        elif self.number == 2:
            self['label_2'].hide()
            self['select_2'].show()
            self['label_select_2'].show()
        elif self.number == 3:
            self['label_3'].hide()
            self['select_3'].show()
            self['label_select_3'].show()
        """
        self['select_1'].hide()
        self['select_2'].hide()
        self['select_3'].hide()
        self['label_select_1'].hide()
        self['label_select_2'].hide()
        self['label_select_3'].hide()

        self.number = number
        if self.number == 1:
            self['label_1'].hide()
            self['select_1'].show()
            self['label_select_1'].show()
        elif self.number == 2:
            self['label_2'].hide()
            self['select_2'].show()
            self['label_select_2'].show()
        elif self.number == 3:
            self['label_3'].hide()
            self['select_3'].show()
            self['label_select_3'].show()

        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'NumberActions',
                'ColorActions',
                'DirectionActions',
                'InfobarActions',
            ],
            {
                'ok': self.returnNumber,
                'cancel': self.quit,
                'showMovies': self.next,
                'down': self.next,
                '5': self.next
            }, -1
        )
        self.Timer = eTimer()
        try:
            self.Timer_conn = self.Timer.timeout.connect(self.returnNumber)
        except BaseException:
            self.Timer.callback.append(self.returnNumber)
        self.Timer.start(4000, True)

    def next(self):
        self.Timer.start(2000, True)

        for i in range(1, 4):
            self[f'select_{i}'].hide()
            self[f'label_{i}'].show()
            self[f'label_select_{i}'].hide()

        if self.number == 1:
            self.number = 2
        elif self.number == 2:
            self.number = 3
        elif self.number == 3:
            self.number = 1

        self[f'label_{self.number}'].hide()
        self[f'select_{self.number}'].show()
        self[f'label_select_{self.number}'].show()

    def returnNumber(self):
        self.Timer.stop()

        content_map = {
            1: (':::Movie:Top:::', 'style'),
            2: (':::Series:Top:::', 'seriesstyle'),
            3: (':Top:::', 'style')
        }

        if self.number not in content_map:
            self.close()
            return

        content_type, style_type = content_map[self.number]

        try:
            if style_type == 'seriesstyle':
                style_config = config.plugins.moviebrowser.seriesstyle.value
            else:
                style_config = config.plugins.moviebrowser.style.value

            if style_config == 'metrix':
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserMetrix as BrowserClass
            elif style_config == 'backdrop':
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserBackdrop as BrowserClass
            else:
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserPosterwall as BrowserClass

            self.session.openWithCallback(
                self.close, BrowserClass, 0, content_type, content_type)

        except ImportError as e:
            print("[MovieBrowser] Errore import in returnNumber:", e)
            self.close()

    def quit(self):
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
        self.recursion_depth = 0
        self.max_recursion = 5
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
        if self.renew is True:
            self.starttime = ''
            self.namelist.append(name)
            self.movielist.append(movie)
            self.datelist.append(date)
        else:
            self.makeUpdate()

    def makeUpdate(self):
        if self._in_make_update:
            print("[MovieBrowser] ERRORE: Ricorsione in makeUpdate!")
            return

        self._in_make_update = True
        try:
            self.starttime = str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                data = data.read()
            if fileExists(BLACKLIST_PATH):
                with open(BLACKLIST_PATH, 'r', encoding='utf-8') as blacklist:
                    blacklist.read()
                alldata = data + blacklist
            else:
                alldata = data
            allfiles = ':::'
            count = 0
            folder = config.plugins.moviebrowser.moviefolder.value
            for root, dirs, files in walk(
                    folder, topdown=False, onerror=None, followlinks=True):
                for name in files:
                    count += 1
                    if name.endswith('.ts') or name.endswith('.avi') or name.endswith('.divx') or name.endswith('.flv') or name.lower().endswith('.iso') or name.endswith('.m2ts') or name.endswith(
                            '.m4v') or name.endswith('.mov') or name.endswith('.mp4') or name.endswith('.mpg') or name.endswith('.mpeg') or name.endswith('.mkv') or name.endswith('.vob'):
                        filename = join(root, name)
                        allfiles = allfiles + filename + ':::'
                        movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
                        if search(movie, alldata) is None:
                            self.movielist.append(filename)
                            date = getmtime(filename)
                            self.datelist.append(
                                str(datetime.datetime.fromtimestamp(date)))
                            if name.endswith('.ts'):
                                name = sub(r'_', ' ', name)
                                name = sub(r'^.*? - .*? - ', '', name)
                                name = sub(r'^[0-9]+ [0-9]+ - ', '', name)
                                name = sub(r'^[0-9]+ - ', '', name)
                                name = sub(r'[.]ts', '', name)
                            else:
                                name = sub(
                                    r'\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob',
                                    '',
                                    name)
                            self.namelist.append(name)
                    self.fileCount = count

            for line in data.split('\n'):
                movieline = line.split(':::')
                try:
                    moviefolder = sub(
                        r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movieline[1])
                except IndexError:
                    moviefolder = ''

                if search(
                        config.plugins.moviebrowser.moviefolder.value,
                        moviefolder) is not None and search(
                        moviefolder,
                        allfiles) is None:
                    self.orphaned += 1
                    data = data.replace(line + '\n', '')

            if self.orphaned > 0:
                if search('https://cf2.imgobject.com/t/p/', data) is not None:
                    data = data.replace(
                        'https://cf2.imgobject.com/t/p/',
                        'https://image.tmdb.org/t/p/')
                with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
                    f.write(data)
            del data
            del alldata
            del allfiles
            self._in_make_update = False
            self._in_tmdb_data = False
            self._in_tvdb_data = False
            self._in_make_data = False

            self.dbcountmax = len(self.movielist)
            if self.dbcountmax == 0:
                self.results = (
                    0,
                    self.orphaned,
                    self.moviecount,
                    self.seriescount)
                self.showResult(False)
            else:
                self.name = self.namelist[0]
                if search('[Ss][0-9]+[Ee][0-9]+', self.name) is not None:
                    series = self.name + 'FIN'
                    series = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub('FIN', '', series)
                    series = transSERIES(series)
                    url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                        series, self.language)

                    if not self._in_tvdb_data:
                        self.getTVDbData(url, '0')
                else:
                    movie = transMOVIE(self.name)
                    url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=True&query=%s%s' % (
                        str(tmdb_api), movie, self.language)

                    if not self._in_tmdb_data:
                        self.getTMDbData(url, '0', False)
        finally:
            self._in_make_update = False
        return

    def getTMDbData(self, url, tmdbid, renew):
        self.tmdbCount += 1
        self.recursion_depth += 1

        if self.recursion_depth > self.max_recursion:
            print("[MovieBrowser] ERRORE: Ricorsione infinita in getTMDbData!")
            self.recursion_depth = 0
            return

        if self._in_tmdb_data:
            print("[MovieBrowser] ERRORE: Ricorsione in getTMDbData!")
            return

        self._in_tmdb_data = True

        try:
            headers = {'Accept': 'application/json'}
            request = Request(url, headers=headers)
            try:
                if PY3:
                    output = urlopen(
                        request, timeout=10).read().decode('utf-8')
                else:
                    output = urlopen(request, timeout=10).read()
            except Exception:
                output = ''

            if search('"total_results":0', output) is not None:
                series = self.name + 'FIN'
                series = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub('FIN', '', series)
                series = transSERIES(series)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    series, self.language)

                if not self._in_tvdb_data:
                    self.getTVDbData(url, '0')
                else:
                    print(
                        "[MovieBrowser] Warning: getTVDbData già in esecuzione, salto chiamata")

            else:
                output = output.replace('&amp;', '&').replace(
                    '\\/', '/').replace('}', ',')
                if tmdbid == '0':
                    tmdbid = findall(r'"id":(.*?),', output)
                    try:
                        tmdbid = tmdbid[0]
                    except IndexError:
                        tmdbid = '0'

                    name = findall(r'"title":"(.*?)"', output)
                    backdrop = findall(r'"backdrop_path":"(.*?)"', output)
                    year = findall(r'"release_date":"(.*?)"', output)
                    poster = findall(r'"poster_path":"(.*?)"', output)
                    rating = findall(r'"vote_average":(.*?),', output)
                    try:
                        self.namelist[self.dbcount - 1] = name[0]
                    except IndexError:
                        self.namelist[self.dbcount - 1] = self.name
                    try:
                        self.backdroplist.append(
                            'https://image.tmdb.org/t/p/w1280' + backdrop[0])
                    except IndexError:
                        self.backdroplist.append(str(default_backdrop))
                    try:
                        self.posterlist.append(
                            'https://image.tmdb.org/t/p/w185' + poster[0])
                    except IndexError:
                        self.posterlist.append(str(default_poster))
                    url = 'https://api.themoviedb.org/3/movie/%s%s?api_key=%s' % (
                        tmdbid, self.language, str(tmdb_api))
                    headers = {'Accept': 'application/json'}
                    request = Request(url, headers=headers)
                    try:
                        if PY3:
                            output = urlopen(
                                request, timeout=10).read().decode('utf-8')
                        else:
                            output = urlopen(request, timeout=10).read()

                    except Exception:
                        output = ''

                plot = findall(r'"overview":"(.*?)","', output)
                if renew is True:
                    output = sub(r'"belongs_to_collection":{.*?}', '', output)
                    name = findall(r'"title":"(.*?)"', output)
                    backdrop = findall(r'"backdrop_path":"(.*?)"', output)
                    poster = findall(r'"poster_path":"(.*?)"', output)
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (
                    tmdbid, str(tmdb_api))
                headers = {'Accept': 'application/json'}
                request = Request(url, headers=headers)
                try:
                    if PY3:
                        output = urlopen(
                            request, timeout=10).read().decode('utf-8')
                    else:
                        output = urlopen(request, timeout=10).read()
                except Exception:
                    output = ''

                output = output.replace('&amp;', '&').replace(
                    '\\/', '/').replace('}', ',')
                output = sub(r'"belongs_to_collection":{.*?}', '', output)
                if not plot:
                    plot = findall(r'"overview":"(.*?)","', output)
                genre = findall(
                    r'"genres":[[]."id":[0-9]+,"name":"(.*?)"', output)
                genre2 = findall(
                    r'"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
                genre3 = findall(
                    r'"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"',
                    output)
                genre4 = findall(
                    r'"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"',
                    output)
                genre5 = findall(
                    r'"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"',
                    output)
                country = findall(r'"iso_3166_1":"(.*?)"', output)
                runtime = findall(r'"runtime":(.*?),', output)
                if renew is True:
                    year = findall(r'"release_date":"(.*?)"', output)
                    rating = findall(r'"vote_average":(.*?),', output)
                    if not backdrop:
                        backdrop = findall(r'"backdrop_path":"(.*?)"', output)
                    if not poster:
                        poster = findall(r'"poster_path":"(.*?)"', output)
                    try:
                        self.namelist[self.dbcount - 1] = name[0]
                    except IndexError:
                        self.namelist[self.dbcount - 1] = self.name

                    try:
                        self.backdroplist.append(
                            'https://image.tmdb.org/t/p/w1280' + backdrop[0])
                    except IndexError:
                        self.backdroplist.append(str(default_backdrop))
                    try:
                        self.posterlist.append(
                            'https://image.tmdb.org/t/p/w185' + poster[0])
                    except IndexError:
                        self.posterlist.append(str(default_poster))
                url = 'https://api.themoviedb.org/3/movie/%s/casts?api_key=%s' % (
                    tmdbid, str(tmdb_api))
                headers = {'Accept': 'application/json'}
                request = Request(url, headers=headers)
                try:
                    if PY3:
                        output = urlopen(
                            request, timeout=10).read().decode('utf-8')
                    else:
                        output = urlopen(request, timeout=10).read()
                except Exception:
                    output = ''

                actor = findall(r'"name":"(.*?)"', output)
                actor2 = findall(r'"name":".*?"name":"(.*?)"', output)
                actor3 = findall(
                    r'"name":".*?"name":".*?"name":"(.*?)"', output)
                actor4 = findall(
                    r'"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
                actor5 = findall(
                    r'"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
                actor6 = findall(
                    r'"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"',
                    output)
                actor7 = findall(
                    r'"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"',
                    output)
                director = findall(r'"job":"Director","name":"(.*?)"', output)
                # director =
                # findall(r'"known_for_department":"Writing","name":"(.*?)"',
                # output)  # director fixed
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
                    year = sub(r'-[0-9][0-9]-[0-9][0-9]', '', year[0])
                    res.append(year)
                except IndexError:
                    res.append(' ')

                try:
                    res.append(country[0].replace('US', 'USA'))
                except IndexError:
                    res.append(' ')

                self.infolist.append(res)
                try:
                    self.plotlist.append(
                        plot[0].replace(
                            '\r',
                            '').replace(
                            '\n',
                            ' ').replace(
                            '\\',
                            ''))
                except IndexError:
                    self.plotlist.append(' ')

                if not self._in_make_data:
                    self.makeDataEntry(self.dbcount - 1, True)
                else:
                    print(
                        "[MovieBrowser] Warning: makeDataEntry già in esecuzione, salto chiamata")

        except Exception as e:
            print("[MovieBrowser] Errore in getTMDbData:", str(e))

        finally:
            self._in_tmdb_data = False
            self.recursion_depth = 0

        return

    def getTVDbData(self, url, seriesid):
        if self._in_tvdb_data:
            print("[MovieBrowser] ERRORE: Ricorsione in getTVDbData!")
            return

        self._in_tvdb_data = True

        self.tvdbCount += 1
        self.recursion_depth += 1

        if self.recursion_depth > self.max_recursion:
            print("[MovieBrowser] ERRORE: Ricorsione infinita in getTVDbData!")
            self.recursion_depth = 0
            self._in_tvdb_data = False
            return

        try:
            agents = {
                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
            request = Request(url, headers=agents)
            try:
                if PY3:
                    output = urlopen(
                        request, timeout=10).read().decode('utf-8')
                else:
                    output = urlopen(request, timeout=10).read()
            except Exception:
                output = ''

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
                    name = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    name = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    name = sub('FIN', '', name)
                    self.namelist.insert(self.dbcount - 1, name)
                    self.movielist.insert(self.dbcount - 1, name)
                    self.datelist.insert(
                        self.dbcount - 1, str(datetime.datetime.now()))
                    self.backdroplist.append(str(default_backdrop))
                    self.posterlist.append(
                        str(default_poster) +
                        '<episode>' +
                        str(default_banner) +
                        '<episode>')

                    if not self._in_make_data:
                        self.makeDataEntry(self.dbcount - 1, False)
                    else:
                        print(
                            "[MovieBrowser] Warning: makeDataEntry già in esecuzione")
                else:
                    self.backdroplist.append(str(default_backdrop))
                    self.posterlist.append(str(default_poster))
                    self.namelist[self.dbcount - 1] = self.name

                    if not self._in_make_data:
                        self.makeDataEntry(self.dbcount - 1, True)
                    else:
                        print(
                            "[MovieBrowser] Warning: makeDataEntry già in esecuzione")
            else:
                if seriesid == '0':
                    seriesid = findall(r'<seriesid>(.*?)</seriesid>', output)
                    try:
                        seriesid = seriesid[0]
                    except IndexError:
                        seriesid = '0'

                if search('[Ss][0-9]+[Ee][0-9]+',
                          self.name) is not None and self.newseries is False:
                    data = search('([Ss][0-9]+[Ee][0-9]+)', self.name)
                    data = data.group(1)
                    season = search('[Ss]([0-9]+)[Ee]', data)
                    season = season.group(1).lstrip('0')
                    if season == '':
                        season = '0'
                    episode = search('[Ss][0-9]+[Ee]([0-9]+)', data)
                    episode = episode.group(1).lstrip('0')
                    url = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/default/' + season + '/' +
                           episode + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                    agents = {
                        'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
                    request = Request(url, headers=agents)
                    try:
                        if PY3:
                            output = urlopen(
                                request, timeout=10).read().decode('utf-8')
                        else:
                            output = urlopen(request, timeout=10).read()
                    except Exception:
                        output = ''

                    output = sub(r'\n', '', output)
                    output = sub(r'&amp;', '&', output)
                    episode = findall(
                        r'<EpisodeName>(.*?)</EpisodeName>', output)
                    year = findall(r'<FirstAired>([0-9]+)-', output)
                    guest = findall(
                        r'<GuestStars>[|](.*?)[|]</GuestStars>', output)
                    director = findall(
                        '<Director>[|](.*?)[|]</Director>', output)
                    if not director:
                        director = findall('<Director>(.*?)[|]', output)
                        if not director:
                            director = findall('<Director>[|](.*?)[|]', output)
                    plotfull = findall(
                        r'<Overview>(.*?)</Overview>', output, S)
                    rating = findall(r'<Rating>(.*?)</Rating>', output)
                    eposter = findall(r'<filename>(.*?)</filename>', output)
                else:
                    data = ''
                    episode = []
                    year = []
                    guest = []
                    director = []
                    plotfull = []
                    rating = []
                    eposter = []
                url = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/' +
                       config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                agents = {
                    'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
                request = Request(url, headers=agents)
                try:
                    if PY3:
                        output = urlopen(
                            request, timeout=10).read().decode('utf-8')
                    else:
                        output = urlopen(request, timeout=10).read()
                except Exception:
                    output = ''

                output = sub(r'\n', '', output)
                output = sub(r'&amp;', '&', output)
                output = sub(r'&quot;', '"', output)
                name = findall(r'<SeriesName>(.*?)</SeriesName>', output)
                runtime = findall(r'<Runtime>(.*?)</Runtime>', output)
                if not rating:
                    rating = findall(r'<Rating>(.*?)</Rating>', output)
                actors = findall(r'<Actors>(.*?)</Actors>', output)
                actor = actor2 = actor3 = actor4 = actor5 = actor6 = actor7 = genre = genre2 = genre3 = genre4 = genre5 = []
                try:
                    actor = findall(r'[|](.*?)[|]', actors[0])
                    actor2 = findall(r'[|].*?[|](.*?)[|]', actors[0])
                    actor3 = findall(r'[|].*?[|].*?[|](.*?)[|]', actors[0])
                    actor4 = findall(
                        r'[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                    actor5 = findall(
                        r'[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                    actor6 = findall(
                        r'[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                    actor7 = findall(
                        r'[|].*?[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                except IndexError:
                    pass

                genres = findall(r'<Genre>(.*?)</Genre>', output)
                try:
                    genre = findall(r'[|](.*?)[|]', genres[0])
                    genre2 = findall(r'[|].*?[|](.*?)[|]', genres[0])
                    genre3 = findall(r'[|].*?[|].*?[|](.*?)[|]', genres[0])
                    genre4 = findall(
                        r'[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
                    genre5 = findall(
                        r'[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
                except IndexError:
                    pass
                if not year:
                    year = findall(r'<FirstAired>([0-9]+)-', output)
                if not plotfull:
                    plotfull = findall(
                        r'<Overview>(.*?)</Overview>', output, S)
                backdrop = findall(r'<fanart>(.*?)</fanart>', output)
                poster = findall(r'<poster>(.*?)</poster>', output)
                if self.newseries is True:
                    eposter = findall(r'<banner>(.*?)</banner>', output)
                if self.newseries is False:
                    try:
                        name = name[0]
                        if not episode:
                            self.namelist[self.dbcount - 1] = name + \
                                ' - (S00E00) - TheTVDb: ' + data + ' not found.'
                            self.name = name
                        else:
                            self.namelist[self.dbcount - 1] = name + \
                                ' - (' + data + ') ' + episode[0]
                            self.name = name + ' ' + data
                    except IndexError:
                        self.namelist[self.dbcount - 1] = self.name

                else:
                    try:
                        name = name[0]
                        self.namelist.insert(self.dbcount - 1, name)
                        self.movielist.insert(self.dbcount - 1, name)
                        self.datelist.insert(
                            self.dbcount - 1, str(datetime.datetime.now()))
                    except IndexError:
                        self.namelist.insert(self.dbcount - 1, self.name)
                        self.movielist.insert(self.dbcount - 1, self.name)
                        self.datelist.insert(
                            self.dbcount - 1, str(datetime.datetime.now()))

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
                        plotfull = plotfull[0].replace(
                            '\r',
                            '').replace(
                            '\n',
                            ' ').replace(
                            '\\',
                            '').replace(
                            '&quot;',
                            '"')
                    else:
                        plotfull = plotfull[0].replace(
                            '\r',
                            '').replace(
                            '\n',
                            ' ').replace(
                            '\\',
                            '').replace(
                            '&quot;',
                            '"')
                        plotfull = plotfull + ' Guest Stars: ' + \
                            guest[0].replace('|', ', ') + '.'
                    self.plotlist.append(plotfull)
                except IndexError:
                    self.plotlist.append(' ')

                try:
                    self.backdroplist.append(
                        'https://www.thetvdb.com/banners/' + backdrop[0])
                except IndexError:
                    self.backdroplist.append(str(default_backdrop))
                try:
                    if self.newseries is True:
                        if not eposter:
                            self.posterlist.append(
                                'https://www.thetvdb.com/banners/_cache/' +
                                poster[0] +
                                '<episode>' +
                                str(default_banner) +
                                '<episode>')
                        elif eposter[0] == '':
                            self.posterlist.append(
                                'https://www.thetvdb.com/banners/_cache/' +
                                poster[0] +
                                '<episode>' +
                                str(default_banner) +
                                '<episode>')
                        else:
                            self.posterlist.append(
                                'https://www.thetvdb.com/banners/_cache/' +
                                poster[0] +
                                '<episode>' +
                                'https://www.thetvdb.com/banners/' +
                                eposter[0] +
                                '<episode>')
                    elif not eposter:
                        self.posterlist.append(
                            'https://www.thetvdb.com/banners/_cache/' + poster[0])
                    else:
                        self.posterlist.append(
                            'https://www.thetvdb.com/banners/_cache/' +
                            poster[0] +
                            '<episode>' +
                            'https://www.thetvdb.com/banners/' +
                            eposter[0] +
                            '<episode>')
                except IndexError:
                    if self.newseries is True:
                        self.posterlist.append(
                            str(default_poster) +
                            '<episode>' +
                            str(default_banner) +
                            '<episode>')
                    else:
                        self.posterlist.append(str(default_poster))

                if not self._in_make_data:
                    self.makeDataEntry(self.dbcount - 1, False)
                else:
                    print("[MovieBrowser] Warning: makeDataEntry già in esecuzione")

        except Exception as e:
            print("[MovieBrowser] Errore in getTVDbData:", str(e))

        finally:
            self._in_tvdb_data = False
            self.recursion_depth = 0

        return

    def makeDataEntry(self, count, content):
        if self._in_make_data:
            print("[MovieBrowser] ERRORE: Ricorsione in makeDataEntry!")
            return

        self._in_make_data = True

        self.recursion_depth += 1

        if self.recursion_depth > self.max_recursion:
            print("[MovieBrowser] ERRORE: Ricorsione infinita in makeDataEntry!")
            self.recursion_depth = 0
            self._in_make_data = False
            return

        try:
            if self.renew is False:
                with open(DATABASE_PATH, 'a', encoding='utf-8') as f:
                    try:
                        if content is True:
                            self.moviecount += 1
                            data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + ':::'.join(
                                self.infolist[count][:7]) + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Movie:Top:::unseen:::\n'
                        elif self.newseries is True:
                            self.newseries = False
                            data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + ':::'.join(
                                self.infolist[count][:7]) + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:Top:::unseen:::\n'
                        else:
                            name = self.namelist[count] + 'FIN'
                            name = sub(
                                r'\\([Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                            name = sub('FIN', '', name)
                            name = sub(r'[\\(\\)\\[\\]\\+\\?]', '.', name)
                            with open(DATABASE_PATH, 'r', encoding='utf-8') as db_file:
                                data = db_file.read()
                            if search(name + r'\\(', data) is None:
                                self.newseries = True
                            self.seriescount += 1
                            data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + ':::'.join(
                                self.infolist[count][:7]) + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:::unseen:::\n'
                        f.write(data)
                        if config.plugins.moviebrowser.download.value == 'update':
                            url = self.backdroplist[count]
                            backdrop = sub(r'.*?/', '', url)
                            backdrop = join(
                                config.plugins.moviebrowser.cachefolder.value, backdrop)
                            if not exists(backdrop):
                                try:
                                    headers = {'Accept': 'application/json'}
                                    request = Request(url, headers=headers)
                                    if PY3:
                                        output = urlopen(
                                            request).read().decode('utf-8')
                                    else:
                                        output = urlopen(request).read()

                                    with open(backdrop, 'wb', encoding='utf-8') as f_backdrop:
                                        f_backdrop.write(output)
                                except Exception as e:
                                    print(
                                        "Errore nel download del backdrop:", e)
                    except IndexError:
                        pass
            else:
                try:
                    if content is True:
                        self.moviecount += 1
                        newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + \
                            ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Movie:Top:::unseen:::'
                    else:
                        name = self.namelist[count] + 'FIN'
                        name = sub(
                            r' - \\([Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                        name = sub('FIN', '', name)
                        name = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', name)
                        with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                            data = data.read()
                        if search(
                                name + '.*?:::Series:Top:::unseen:::\n',
                                data) is None:
                            self.newseries = True
                            self.renew = False
                        self.seriescount += 1
                        newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + \
                            ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:::unseen:::'
                except IndexError:
                    newdata = ''

                movie = self.movielist[count]
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                    data = data.read()
                if search(movie, data) is not None:
                    for line in data.split('\n'):
                        if search(movie, line) is not None:
                            data = data.replace(line, newdata)
                    with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
                        f.write(data)
            if self.newseries is True:
                self.dbcount += 1
                self.dbcountmax += 1
                series = self.name + 'FIN'
                series = sub(r' - .[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub('FIN', '', series)
                series = transSERIES(series)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    series, self.language)
                try:
                    self.getTVDbData(url, '0')
                except RuntimeError:
                    return (
                        1,
                        self.orphaned,
                        self.moviecount,
                        self.seriescount)

            elif self.dbcount < self.dbcountmax:
                self.dbcount += 1
                try:
                    self.name = self.namelist[self.dbcount - 1]
                    if search('[Ss][0-9]+[Ee][0-9]+', self.name) is not None:
                        series = self.name + 'FIN'
                        series = sub(
                            r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                        series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                        series = sub('FIN', '', series)
                        series = transSERIES(series)
                        url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                            series, self.language)
                        try:
                            if not hasattr(
                                    self, '_in_tmdb_call') or not self._in_tmdb_call:
                                self.getTMDbData(url, '0', False)
                        except RuntimeError:
                            return (
                                1, self.orphaned, self.moviecount, self.seriescount)
                    else:
                        movie = transMOVIE(self.name)
                        movie = sub(r'\\+[1-2][0-9][0-9][0-9]', '', movie)
                        url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                            str(tmdb_api), movie, self.language)
                        try:
                            if not hasattr(
                                    self, '_in_tmdb_call') or not self._in_tmdb_call:
                                self.getTMDbData(url, '0', False)
                        except RuntimeError:
                            return (
                                1, self.orphaned, self.moviecount, self.seriescount)

                except IndexError:
                    self.results = (
                        1, self.orphaned, self.moviecount, self.seriescount)
                    self.showResult(False)
                finally:
                    self._in_make_data = False
            else:
                self.results = (
                    1,
                    self.orphaned,
                    self.moviecount,
                    self.seriescount)
                self.showResult(False)

            if not self._in_tmdb_data:
                self.getTMDbData(url, '0', False)
            else:
                print("[MovieBrowser] Warning: getTMDbData già in esecuzione")

        except Exception as e:
            print("[MovieBrowser] Error in makeDataEntry:", str(e))

        finally:
            self._in_make_data = False
            self.recursion_depth = 0

    def showResult(self, show):
        found, orphaned, moviecount, seriescount = self.results
        endtime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        result = _('Start time: %s\nEnd time: %s\nTotal scanned files: %s\nTheTVDb Database Requests: %s\nTMDb Database Requests: %s\nOrphaned Movies/Series: %s\nNew Series: %s\nNew Movies: %s\n\n') % (
            self.starttime, endtime, self.fileCount, self.tvdbCount, self.tmdbCount, orphaned, seriescount, moviecount)
        if found != 0:
            self.sortDatabase()
        if show is False:
            print('Movie Browser Datenbank Update\n' + result)
        else:
            if self.renew is False:
                with open(UPDATE_LOG_PATH, 'a', encoding='utf-8') as f:
                    f.write(result)
                return (found, orphaned, moviecount, seriescount)
            return True

    def sortDatabase(self):
        series = ''
        movies = ''
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if ':::Series:::' in line:
                    series += line
        with open(DATABASE_PATH + '.series', 'w', encoding='utf-8') as fseries:
            fseries.write(series)
        with open(DATABASE_PATH + '.series', 'r', encoding='utf-8') as fseries:
            series = fseries.readlines()
        series.sort(key=lambda line: line.split(':::')[0])
        with open(DATABASE_PATH + '.series', 'w', encoding='utf-8') as fseries:
            fseries.writelines(series)
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if ':::Series:::' not in line:
                    movies += line
        with open(DATABASE_PATH + '.movies', 'w', encoding='utf-8') as fmovies:
            fmovies.write(movies)
        with open(DATABASE_PATH + '.movies', 'r', encoding='utf-8') as fmovies:
            lines = fmovies.readlines()
        self.sortorder = config.plugins.moviebrowser.sortorder.value
        try:
            if self.sortorder == 'name':
                lines.sort(
                    key=lambda line: line.split(':::')[0].replace(
                        'Der ',
                        '').replace(
                        'Die ',
                        '').replace(
                        'Das ',
                        '').replace(
                        'The ',
                        '').lower())
            elif self.sortorder == 'name_reverse':
                lines.sort(
                    key=lambda line: line.split(':::')[0].replace(
                        'Der ',
                        '').replace(
                        'Die ',
                        '').replace(
                        'Das ',
                        '').replace(
                        'The ',
                        '').lower(),
                    reverse=True)
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
                lines.sort(
                    key=lambda line: int(
                        line.split(':::')[3].replace(
                            ' min', '')))
            elif self.sortorder == 'runtime_reverse':
                lines.sort(
                    key=lambda line: int(
                        line.split(':::')[3].replace(
                            ' min', '')), reverse=True)
        except IndexError:
            pass
        except ValueError:
            self.session.open(
                MessageBox,
                _('\nDatabase Error: Entry without runtime'),
                MessageBox.TYPE_ERROR)

        with open(DATABASE_PATH + '.movies', 'w', encoding='utf-8') as f:
            f.writelines(lines)
        files = [DATABASE_PATH + '.movies', DATABASE_PATH + '.series']
        with open(DATABASE_PATH + '.sorted', 'w', encoding='utf-8') as outfile:
            for name in files:
                with open(name, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())

        if fileExists(DATABASE_PATH + '.movies'):
            remove(DATABASE_PATH + '.movies')
        if fileExists(DATABASE_PATH + '.series'):
            remove(DATABASE_PATH + '.series')
        rename(DATABASE_PATH + '.sorted', DATABASE_PATH)


class timerUpdate():
    """Handles database update timers with compatibility for both old and new eTimer APIs."""

    def __init__(self):
        """Initialize timerUpdate with two eTimers."""
        self.session = None
        self.startTimer = eTimer()
        self.dailyTimer = eTimer()
        return

    def saveSession(self, session):
        """Store the Enigma2 session reference."""
        self.session = session

    def _connect_timer(self, timer, callback):
        """Connect a callback to timer using modern or legacy API.

        Args:
            timer: eTimer instance
            callback: Function to call when timer fires
        """
        try:
            # Modern API (signal/slot style)
            timer.timeout.connect(callback)
        except AttributeError:
            # Legacy API (callback list)
            timer.callback.append(callback)

    def _disconnect_timer(self, timer, callback):
        """Disconnect a callback from timer using modern or legacy API.

        Args:
            timer: eTimer instance
            callback: Function to disconnect
        """
        try:
            # Modern API (signal/slot style)
            timer.timeout.disconnect(callback)
        except (AttributeError, TypeError):
            # Legacy API (callback list)
            if callback in timer.callback:
                timer.callback.remove(callback)

    def start(self):
        """Start the initial update timer."""
        # Disconnect any existing callback to prevent duplicates
        self._disconnect_timer(self.startTimer, self.daily)

        # Connect the callback using compatible method
        self._connect_timer(self.startTimer, self.daily)

        # Calculate initial delay
        now = datetime.datetime.now()
        now_minutes = now.hour * 60 + now.minute
        config_hour, config_minute = config.plugins.moviebrowser.timer.value
        start_time_minutes = config_hour * 60 + config_minute

        if now_minutes < start_time_minutes:
            delay_minutes = start_time_minutes - now_minutes
        else:
            delay_minutes = 1440 - now_minutes + start_time_minutes

        # Start timer with calculated delay (single shot)
        self.startTimer.start(delay_minutes * 60 * 1000, True)

        # Log the timer start
        now_str = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('*******Movie Browser Database Update Timer*******\nInitial Update Timer started: %s\nTimer Value (min): %s\n') % (now_str, str(delay_minutes))
        with open(TIMER_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(info)

    def restart(self):
        """Restart all timers."""
        self.stop()
        self.start()

    def stop(self):
        """Stop all timers and clean up callbacks."""
        # Stop and disconnect start timer
        self.startTimer.stop()
        self._disconnect_timer(self.startTimer, self.daily)

        # Stop and disconnect daily timer
        self.dailyTimer.stop()
        self._disconnect_timer(self.dailyTimer, self.runUpdate)

        # Log the timer stop
        now_str = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer stopped: %s\n') % now_str
        with open(TIMER_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(info)

    def daily(self):
        """Called when initial timer fires. Starts the daily repeating timer."""
        # Clean up initial timer
        self.startTimer.stop()
        self._disconnect_timer(self.startTimer, self.daily)

        # Run first update immediately
        self.runUpdate()

        # Set up daily repeating timer
        self._connect_timer(self.dailyTimer, self.runUpdate)

        # Start daily timer (24 hours, repeating)
        daily_delay_minutes = 1440
        self.dailyTimer.start(daily_delay_minutes * 60 * 1000, False)

        # Log the switch to daily timer
        now_str = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer started: %s\nTimer Value (min): %s\n') % (
            now_str, str(daily_delay_minutes))
        with open(TIMER_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(info)

    def runUpdate(self):
        """Execute the database update process."""
        UpdateDatabase(False, '', '', '').showResult(True)

        # Log the update execution
        now_str = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Movie Database Update started: %s\n') % now_str
        with open(TIMER_LOG_PATH, 'a', encoding='utf-8') as f:
            f.write(info)


timerupdate = timerUpdate()


class movieBrowserConfig(ConfigListScreen, Screen):

    def __init__(self, session):

        skin = join(skin_path, "movieBrowserConfig.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.session = session
        self["Title"] = Label("Movie Browser Setup")

        self.onChangedEntry = []
        self.sortorder = config.plugins.moviebrowser.sortorder.value
        self.moviefolder = config.plugins.moviebrowser.moviefolder.value
        self.cachefolder = config.plugins.moviebrowser.cachefolder.value
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
        ConfigListScreen.__init__(
            self,
            list,
            session=self.session,
            on_change=self.UpdateComponents)
        self.createSetup()
        self['actions'] = ActionMap(
            [
                'HelpActions',
                'SetupActions',
                'VirtualKeyboardActions',
                'ColorActions',
                'DirectionActions'
            ],
            {
                'ok': self.keyRun,
                'showVirtualKeyboard': self.KeyText,
                'cancel': self.cancel,
                'red': self.cancel,
                'green': self.save,
                'save': self.save,
                'left': self.keyLeft,
                'down': self.keyDown,
                'up': self.keyUp,
                'right': self.keyRight
            }, -1
        )
        self.onLayoutFinish.append(self.UpdateComponents)
        self.onLayoutFinish.append(self.layoutFinished)

    def layoutFinished(self):
        pass

    def createSetup(self):
        self.editListEntry = None
        list = []
        list.append(
            getConfigListEntry(
                _('Movies Style:'),
                config.plugins.moviebrowser.style))
        list.append(
            getConfigListEntry(
                _('Series Style:'),
                config.plugins.moviebrowser.seriesstyle))
        list.append(
            getConfigListEntry(
                _('Goto last Movie on Start:'),
                config.plugins.moviebrowser.lastmovie))
        list.append(
            getConfigListEntry(
                _('Load last Selection/Filter on Start:'),
                config.plugins.moviebrowser.lastfilter))
        list.append(
            getConfigListEntry(
                _('Movie Folder:'),
                config.plugins.moviebrowser.moviefolder))
        list.append(
            getConfigListEntry(
                _('Cache Folder:'),
                config.plugins.moviebrowser.cachefolder))
        list.append(
            getConfigListEntry(
                _('Movie Sort Order:'),
                config.plugins.moviebrowser.sortorder))
        list.append(
            getConfigListEntry(
                _('Show List of Movie Folder:'),
                config.plugins.moviebrowser.showfolder))
        list.append(
            getConfigListEntry(
                _('Movies or Series:'),
                config.plugins.moviebrowser.filter))
        list.append(
            getConfigListEntry(
                _('Movies or Series Selection at Start:'),
                config.plugins.moviebrowser.showswitch))
        list.append(
            getConfigListEntry(
                _('Show Backdrops:'),
                config.plugins.moviebrowser.backdrops))
        list.append(
            getConfigListEntry(
                _('Use m1v Backdrops:'),
                config.plugins.moviebrowser.m1v))
        list.append(
            getConfigListEntry(
                _('Show TV in Background (no m1v):'),
                config.plugins.moviebrowser.showtv))
        list.append(
            getConfigListEntry(
                _('Download new Backdrops:'),
                config.plugins.moviebrowser.download))
        list.append(
            getConfigListEntry(
                _('Posterwall/Backdrop Show Plot:'),
                config.plugins.moviebrowser.plotfull))
        list.append(
            getConfigListEntry(
                _('Metrix List Selection Color:'),
                config.plugins.moviebrowser.metrixcolor))
        list.append(
            getConfigListEntry(
                _('TMDb/TheTVDb Language:'),
                config.plugins.moviebrowser.language))
        list.append(
            getConfigListEntry(
                _("Load TMDB Apikey from /tmp/tmdb_api.txt"),
                config.plugins.moviebrowser.api))
        list.append(
            getConfigListEntry(
                _("Signup on TMDB and input free personal ApiKey"),
                config.plugins.moviebrowser.txtapi))
        list.append(
            getConfigListEntry(
                _("Load TheTVDb Apikey from /tmp/thetvdb_api.txt"),
                config.plugins.moviebrowser.tvdbapi))
        list.append(
            getConfigListEntry(
                _("Signup on TheTVDb and input free personal ApiKey"),
                config.plugins.moviebrowser.txttvdbapi))
        list.append(
            getConfigListEntry(
                _('Update Database with Timer:'),
                config.plugins.moviebrowser.timerupdate))
        if config.plugins.moviebrowser.timerupdate.getValue():
            list.append(
                getConfigListEntry(
                    _('Timer Database Update:'),
                    config.plugins.moviebrowser.timer))
            list.append(
                getConfigListEntry(
                    _('Hide Plugin during Update:'),
                    config.plugins.moviebrowser.hideupdate))

        list.append(
            getConfigListEntry(
                _('Reset Database:'),
                config.plugins.moviebrowser.reset))
        list.append(
            getConfigListEntry(
                _('Cleanup Cache Folder:'),
                config.plugins.moviebrowser.cleanup))
        list.append(
            getConfigListEntry(
                _('Backup Database:'),
                config.plugins.moviebrowser.backup))
        list.append(
            getConfigListEntry(
                _('Restore Database:'),
                config.plugins.moviebrowser.restore))
        list.append(
            getConfigListEntry(
                _('Select skin *Restart GUI Required:'),
                config.plugins.moviebrowser.skin))
        list.append(
            getConfigListEntry(
                _('Start Plugin with Video Button:'),
                config.plugins.moviebrowser.videobutton))
        list.append(
            getConfigListEntry(
                _('Plugin Transparency:'),
                config.plugins.moviebrowser.transparency))
        list.append(
            getConfigListEntry(
                _('Plugin in Enigma Menu:'),
                config.plugins.moviebrowser.showmenu))
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
        if current == getConfigListEntry(
                _('Movies Style:'),
                config.plugins.moviebrowser.style):
            self.updateStylePreview(config.plugins.moviebrowser.style.value)
        elif current == getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle):
            self.updateStylePreview(
                config.plugins.moviebrowser.seriesstyle.value)
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
            self.session.open(
                MessageBox,
                _('\nCache Folder %s not reachable:\nMovie Browser Database Backup canceled.') % str(
                    self.cachefolder),
                MessageBox.TYPE_ERROR)
            return
        if not fileExists(DATABASE_PATH):
            self.session.open(
                MessageBox,
                _('\nDatabase %s not found:\nMovie Browser Database Backup canceled.') %
                str(DATABASE_PATH),
                MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.backup.value:
            try:
                makedirs(self.cachefolder + '/backup')
            except OSError:
                pass
            with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(self.cachefolder + '/backup/database', 'w') as f:
                f.write(data)
            self.session.open(
                MessageBox,
                _('\nDatabase backed up to %s') % str(
                    self.cachefolder + '/backup/database'),
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        config.plugins.moviebrowser.backup.setValue(False)
        config.plugins.moviebrowser.backup.save()
        configfile.load()

    def restoreDatabase(self):
        if not exists(self.cachefolder):
            self.session.open(
                MessageBox,
                _('\nCache Folder %s not reachable:\nMovie Browser Database Restore canceled.') % str(
                    self.cachefolder),
                MessageBox.TYPE_ERROR)
            return
        backup_path = self.cachefolder + '/backup/database'
        if not fileExists(backup_path):
            self.session.open(
                MessageBox,
                _('\nDatabase Backup %s not found:\nMovie Browser Database Restore canceled.') %
                backup_path,
                MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.restore.value:
            with open(backup_path, 'r', encoding='utf-8') as f:
                data = f.read()
            with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
                f.write(data)
            self.session.open(
                MessageBox,
                _('\nDatabase restored from %s') %
                backup_path,
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        config.plugins.moviebrowser.restore.setValue(False)
        config.plugins.moviebrowser.restore.save()
        configfile.load()

    def cleanupCache(self):
        if not exists(self.cachefolder):
            self.session.open(
                MessageBox,
                _('\nCache Folder %s not reachable:\nCleanup Cache Folder canceled.') % str(
                    self.cachefolder),
                MessageBox.TYPE_ERROR)
            return
        if not fileExists(DATABASE_PATH):
            self.session.open(
                MessageBox,
                _('\nDatabase %s not found:\nCleanup Cache Folder canceled.') %
                str(DATABASE_PATH),
                MessageBox.TYPE_ERROR)
            return
        if config.plugins.moviebrowser.cleanup.value:
            with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                data = f.read()
            data += ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
            count = 0
            for root, dirs, files in walk(self.cachefolder, topdown=False):
                for name in files:
                    shortname = sub(r'[.]jpg', '', name)
                    shortname = sub(r'[.]m1v', '', shortname)
                    if search(shortname, data) is None:
                        filename = join(root, name)
                        if fileExists(filename):
                            remove(filename)
                            count += 1
            if count == 0:
                self.session.open(
                    MessageBox,
                    _('\nNo orphaned Backdrops or Posters found:\nYour Cache Folder is clean.'),
                    MessageBox.TYPE_INFO,
                    close_on_any_key=True)
            else:
                self.session.open(
                    MessageBox,
                    _('\nCleanup Cache Folder finished:\n%s orphaned Backdrops or Posters removed.') %
                    str(count),
                    MessageBox.TYPE_INFO,
                    close_on_any_key=True)
            config.plugins.moviebrowser.cleanup.setValue(False)
            config.plugins.moviebrowser.cleanup.save()
            configfile.load()

    def keyRun(self):
        current = self["config"].getCurrent()[1]
        if current == config.plugins.moviebrowser.moviefolder:
            self.openDirectoryBrowser(
                config.plugins.moviebrowser.moviefolder.value)
        elif current == config.plugins.moviebrowser.tvdbapi:
            self.tvdbkeyApi()
        elif current == config.plugins.moviebrowser.api:
            self.keyApi()
        else:
            self.save()

    def openDirectoryBrowser(self, path):
        try:
            from Screens.LocationBox import LocationBox
            self.session.openWithCallback(
                self.openDirectoryBrowserCB,
                LocationBox,
                windowTitle=_('Choose Directory:'),
                text=_('Choose Directory'),
                currDir=str(path),
                bookmarks=config.movielist.videodirs,
                autoAdd=False,
                editDir=True,
                inhibitDirs=[
                    '/bin',
                    '/boot',
                    '/dev',
                    '/home',
                    '/lib',
                    '/proc',
                    '/run',
                    '/sbin',
                    '/sys',
                    '/var'],
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
            self.session.open(
                MessageBox, _("File %s not found!") %
                key_path, MessageBox.TYPE_ERROR)
            return

        with open(key_path, 'r', encoding='utf-8') as f:
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
                        with open(DATABASE_PATH, "r", encoding='utf-8') as f:
                            lines = f.readlines()

                        series = [
                            line for line in lines if ":::Series:::" in line]
                        movies = [
                            line for line in lines if ":::Series:::" not in line]
                        series.sort(key=lambda line: line.split(":::")[0])

                        with open(DATABASE_PATH + ".series", "w", encoding='utf-8') as fseries:
                            fseries.writelines(series)

                        with open(DATABASE_PATH + ".movies", "w", encoding='utf-8') as fmovies:
                            fmovies.writelines(movies)

                    except Exception as e:
                        print("Error processing database:", e)

                    try:
                        if config.plugins.moviebrowser.sortorder.value == 'name':
                            lines.sort(
                                key=lambda line: line.split(':::')[0].replace(
                                    'Der ',
                                    '').replace(
                                    'Die ',
                                    '').replace(
                                    'Das ',
                                    '').replace(
                                    'The ',
                                    '').lower())
                        elif config.plugins.moviebrowser.sortorder.value == 'name_reverse':
                            lines.sort(
                                key=lambda line: line.split(':::')[0].replace(
                                    'Der ',
                                    '').replace(
                                    'Die ',
                                    '').replace(
                                    'Das ',
                                    '').replace(
                                    'The ',
                                    '').lower(),
                                reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'rating':
                            lines.sort(key=lambda line: line.split(':::')[4])
                        elif config.plugins.moviebrowser.sortorder.value == 'rating_reverse':
                            lines.sort(
                                key=lambda line: line.split(':::')[4], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'year':
                            lines.sort(key=lambda line: line.split(':::')[8])
                        elif config.plugins.moviebrowser.sortorder.value == 'year_reverse':
                            lines.sort(
                                key=lambda line: line.split(':::')[8], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'date':
                            lines.sort(key=lambda line: line.split(':::')[2])
                        elif config.plugins.moviebrowser.sortorder.value == 'date_reverse':
                            lines.sort(
                                key=lambda line: line.split(':::')[2], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'folder':
                            lines.sort(key=lambda line: line.split(':::')[1])
                        elif config.plugins.moviebrowser.sortorder.value == 'folder_reverse':
                            lines.sort(
                                key=lambda line: line.split(':::')[1], reverse=True)
                        elif config.plugins.moviebrowser.sortorder.value == 'runtime':
                            lines.sort(
                                key=lambda line: int(
                                    line.split(':::')[3].replace(
                                        ' min', '')))
                        elif config.plugins.moviebrowser.sortorder.value == 'runtime_reverse':
                            lines.sort(
                                key=lambda line: int(
                                    line.split(':::')[3].replace(
                                        ' min', '')), reverse=True)
                    except IndexError:
                        pass
                    except ValueError:
                        self.session.open(
                            MessageBox,
                            _('\nDatabase Error: Entry without runtime'),
                            MessageBox.TYPE_ERROR)

                    with open(DATABASE_PATH + ".movies", "w", encoding="utf-8") as f:
                        f.writelines(lines)

                    files = [
                        DATABASE_PATH + ".movies",
                        DATABASE_PATH + ".series"]
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
                if self.timer_hour != config.plugins.moviebrowser.timer.value[
                        0] or self.timer_min != config.plugins.moviebrowser.timer.value[1] or self.timer_update is False:
                    if timerupdate.session is None:
                        timerupdate.saveSession(self.session)
                    timerupdate.restart()

            # Move cache folder if changed
            if config.plugins.moviebrowser.cachefolder.value != self.cachefolder:
                self.container = eConsoleAppContainer()
                self.container.appClosed.append(self.finished)
                newcache = sub(
                    r'/cache', '', config.plugins.moviebrowser.cachefolder.value)
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
            self.close(True)

        return

    def KeyText(self):
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        current = self['config'].getCurrent()
        if current:
            self.session.openWithCallback(
                self.VirtualKeyBoardCallback,
                VirtualKeyBoard,
                title=self["config"].getCurrent()[0],
                text=self["config"].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback:
            current_config = self["config"].getCurrent()[1]
            if current_config in [
                    config.plugins.moviebrowser.moviefolder,
                    config.plugins.moviebrowser.cachefolder]:
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

        filter_value = config.plugins.moviebrowser.filter.value
        if filter_value == ':::Movie:Top:::':
            number = 1
            content_type = ':::Movie:Top:::'
        elif filter_value == ':::Series:Top:::':
            number = 2
            content_type = ':::Series:Top:::'
        else:
            number = 3
            content_type = ':Top:::'

        if config.plugins.moviebrowser.showswitch.value is True:
            self.session.openWithCallback(self.close, switchStart, number)
            return

        try:
            if number == 2:  # Serie
                style_config = config.plugins.moviebrowser.seriesstyle.value
            else:  # Film o tutti
                style_config = config.plugins.moviebrowser.style.value

            if style_config == 'metrix':
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserMetrix as BrowserClass
            elif style_config == 'backdrop':
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserBackdrop as BrowserClass
            else:
                from Plugins.Extensions.MovieBrowser.plugin import movieBrowserPosterwall as BrowserClass
            self.session.openWithCallback(lambda ret: self.close(
                ret), BrowserClass, 0, content_type, content_type)
        except ImportError as e:
            print("[MovieBrowser] Errore import:", e)
            self.close(False)

    def changedEntry(self):
        self.item = self["config"].getCurrent()
        for x in self.onChangedEntry:
            x()
        try:
            if isinstance(
                self["config"].getCurrent()[1],
                ConfigYesNo) or isinstance(
                self["config"].getCurrent()[1],
                ConfigOnOff) or isinstance(
                self["config"].getCurrent()[1],
                ConfigSelection) or isinstance(
                    self["config"].getCurrent()[1],
                    ConfigText):
                self.createSetup()
        except BaseException:
            pass

    def getCurrentEntry(self):
        return self["config"].getCurrent() and self["config"].getCurrent()[
            0] or ""

    def getCurrentValue(self):
        return self["config"].getCurrent() and str(
            self["config"].getCurrent()[1].getText()) or ""

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
