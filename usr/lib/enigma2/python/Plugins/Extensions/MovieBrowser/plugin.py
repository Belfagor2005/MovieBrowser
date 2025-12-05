#!/usr/bin/python
# -*- coding: utf-8 -*-

# 20221004 Kiddac edit: python 3 support et al
# 20221204 Lululla edit & add: language, config, major fix
# 20221208 Lululla add callInThread getMountDefault
# 20221222 Lululla recoded, major fix
# 20240920 Lululla recoded - clean unnecessary code
# 20250516 Lululla refactoryzed all Cls and clean unnecessary all code
# 20251202 Lululla all recoded:
#  fixed screen (rewrite) - code source - api url
#  separate libraries into other modules
#  dabase rewrite code
#  removed unused code
#  new api v4
# fixed banner on MovieList

from __future__ import print_function
import datetime
from io import open
from sys import exc_info, path
from re import sub, search, findall, S, escape
from os import statvfs, remove, rename, walk, popen, makedirs
from os.path import exists, join, getsize, getmtime
from enigma import (
    RT_HALIGN_LEFT,
    RT_VALIGN_CENTER,
    eListboxPythonMultiContent,
    ePoint,
    eServiceReference,
    eTimer,
    getDesktop,
    gFont,
    iPlayableService,
    iServiceInformation,
    loadPNG
)

from Components.ActionMap import ActionMap
from Components.Label import Label
from Components.MenuList import MenuList
from Components.MultiContent import (
    MultiContentEntryPixmapAlphaTest,
    MultiContentEntryText,
)
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import config

from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists
from twisted.web.client import downloadPage
from . import _, PY3
from .library import (
    convert_size,
    isFHD,
    OnclearMem,
    transSERIES,
    transMOVIE,
    _renewTMDb,
    _renewTVDb,
    threadGetPage,
    fetch_url,
    agents,
    agents_json,
    tmdb_api,
    thetvdb_api,
    quote
)
from .movie_config import (
    switchStart,
    skin_path,
    movieBrowserConfig,
    timerUpdate
)


try:
    from twisted.internet.reactor import callInThread
except ImportError:
    import threading

    def callInThread(func, *args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()


class ItemList(MenuList):

    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(
            self,
            items,
            enableWrapAround,
            eListboxPythonMultiContent)
        if isFHD():
            self.l.setItemHeight(50)
            self.l.setFont(36, gFont('Regular', 36))
            self.l.setFont(32, gFont('Regular', 32))
            self.l.setFont(30, gFont('Regular', 30))
        else:
            self.l.setItemHeight(50)
            self.l.setFont(26, gFont('Regular', 26))
            self.l.setFont(24, gFont('Regular', 24))


version = '4.0'
screenwidth = getDesktop(0).size()
dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser"
if dir_plugins not in path:
    path.append(dir_plugins)

# constant
db_dir = join(dir_plugins, "db")
log_dir = join(dir_plugins, "log")

           
                                                               
                                                               
                                                               
UPDATE_LOG_PATH = join(log_dir, "update.log")
TIMER_LOG_PATH = join(log_dir, "timer.log")
DATABASE_PATH = join(db_dir, "database")
DATABASE_RESET = join(db_dir, "reset")
DATABASE_CACHE = join(db_dir, "cache")
BLACKLIST_PATH = join(db_dir, "blacklist")
FILTER_PATH = join(db_dir, "filter")
LAST_PATH = join(db_dir, "last")
CLEANUP_LOG_PATH = join(log_dir, "cleanup.log")


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


class movieBrowserMetrix(Screen):

    def __init__(self, session, index, content, filter):

        skin = join(skin_path, "movieBrowserMetrix.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(
            screen=self, eventmap={
                iPlayableService.evEOF: self.seenEOF})
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
            self.back_color = int(
                config.plugins.moviebrowser.metrixcolor.value, 16)

        self['posterback'].hide()
        self['yellow'].hide()
        self['red'].hide()
        self['green'].hide()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
            self.session.nav.stopService()

        if fileExists(DATABASE_PATH):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value is True:
                    with open(FILTER_PATH, 'r', encoding='utf-8') as f:
                        self.filter = f.read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    with open(LAST_PATH, 'r', encoding='utf-8') as f:
                        movie = f.read()
                    if movie.endswith('...'):
                        self.index = -1
                    else:
                        movie = sub(r'\(|\)|\[|\]|\+|\?', '.', movie)
                        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                            data = f.read()
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
            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)
        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(
                self.reset_return,
                MessageBox,
                'The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?',
                MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(
                self.first_return,
                MessageBox,
                _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'),
                MessageBox.TYPE_YESNO)

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
                    for line in f:
                        if self.content in line and filter in line:
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
                            self.dddlist.append(
                                'yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director,
                                   actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)
                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(
                        config.plugins.moviebrowser.moviefolder.value + '...')
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

                if self.index is None:
                    self.index = 0
                elif self.index < 0:
                    self.index = 0
                elif self.maxentry > 0 and self.index >= self.maxentry:
                    self.index = self.maxentry - 1
                elif self.maxentry == 0:
                    self.index = 0

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
                            movie = sub(r".*? - \\(", "", movieline[0])
                            movie = sub(r"\\) ", " ", movie)
                            movie = sub(r"S00E00 - ", "", movie)
                            movie = sub(r"[Ss][0]+[Ee]", "Special ", movie)
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
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                810,
                                50),
                            font=30,
                            color=16777215,
                            color_sel=16777215,
                            backcolor_sel=self.back_color,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=_('<List of Movie Folder>')))
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                810,
                                50),
                            font=30,
                            color=16777215,
                            color_sel=16777215,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=_('<List of Movie Folder>')))
            else:
                if self.backcolor is True:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                540,
                                40),
                            font=26,
                            color=16777215,
                            color_sel=16777215,
                            backcolor_sel=self.back_color,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=_('<List of Movie Folder>')))
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                540,
                                40),
                            font=26,
                            color=16777215,
                            color_sel=16777215,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=_('<List of Movie Folder>')))
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
            movieFolder = statvfs(
                config.plugins.moviebrowser.moviefolder.value)
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
            self['label3'].setText('Item %s/%s' %
                                   (str(self.index + 1), str(self.totalItem)))
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
            self['label3'].setText('Item %s/%s' %
                                   (str(self.index + 1), str(self.totalItem)))

    def updateDatabase(self):
        if self.ready is True:
            if exists(
                    config.plugins.moviebrowser.moviefolder.value) and exists(
                    config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(
                    self.database_return,
                    MessageBox,
                    '\nUpdate Movie Browser Database?',
                    MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(
                    MessageBox,
                    _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.moviefolder.value),
                    MessageBox.TYPE_ERROR)
            else:
                self.session.open(
                    MessageBox,
                    _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.cachefolder.value),
                    MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, 'w', encoding='utf-8') as f:
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
        found, orphaned, moviecount, seriescount = UpdateDatabase(
            False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()
        with open(LAST_PATH, 'r', encoding='utf-8') as file:
            movie = file.read()
            movie = sub(r'\(|\)|\[|\]|\+|\?', '.', movie)
        with open(DATABASE_PATH, 'r', encoding='utf-8') as file:
            data = file.read()
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
            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(
                MessageBox,
                _('\nNo new Movies or Series found:\nYour Database is up to date.'),
                MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movie imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movies imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox, _('\n%s Movies and %s Series imported into Database.') %
                    (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(seriescount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                else:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(seriescount),
                            str(orphaned)),
                        MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(seriescount),
                        str(orphaned)),
                    MessageBox.TYPE_INFO)
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
                            current = sub(r'Specials', '(S00', current)
                            current = sub(r'specials', '(s00', current)
                            current = sub(r'Season ', '(S', current)
                            current = sub(r'season ', '(s', current)
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
                            sref = eServiceReference(
                                '1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(
                                MessageBox, _('\nMovie file %s not available.') %
                                filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists(
                                '/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(
                                    DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(
                                    MessageBox, _('\nMovie file %s not available.') %
                                    filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(
                                MessageBox,
                                _('\nDVD Player Plugin not installed.'),
                                MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference(
                            '4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(
                            MessageBox, _('\nMovie file %s not available.') %
                            filename, MessageBox.TYPE_ERROR)
                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(
                        self.getMediaInfo)
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
                height = info and info.getInfo(
                    iServiceInformation.sVideoHeight)
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
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub(
                        r'seen:::.*?FIN',
                        'seen:::' + media + ':::',
                        newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)
            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(
                        MessageBox,
                        _('\nTMDb Movie Update Error:\nSeries Folder'),
                        MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                self.name = name
                name = transMOVIE(name)
                name = sub(r'\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name

                encoded_name = quote(name)

                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                    str(tmdb_api), encoded_name, self.language)
                print('url tmdb=', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        output = fetch_url(url, agents_json)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTMDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        output = output.replace('&amp;', '&').replace(
            '\\/', '/').replace('}', ',')
        output = sub(
            r'"poster_path":"',
            '"poster_path":"https://image.tmdb.org/t/p/w185',
            output)

        output = sub(
            r'"poster_path":null',
            f'"poster_path":"{default_poster}"',
            output)

        rating = findall(r'"vote_average":(.*?),', output)
        year = findall(r'"release_date":"(.*?)"', output)
        titles = findall(r'"title":"(.*?)"', output)
        poster = findall(r'"poster_path":"(.*?)"', output)
        id = findall(r'"id":(.*?),', output)
        country = findall(r'"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(
                MessageBox,
                _('\nNo TMDb Results for %s.') % self.name,
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        else:
            self.session.openWithCallback(
                self.makeTMDbUpdate,
                moviesList,
                titel,
                rating,
                year,
                titles,
                poster,
                id,
                country,
                True,
                False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            print("newwwwwwwwww ", new)
            if select == "movie":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                movie_id = str(new).strip()
                url = "https://api.themoviedb.org/3/movie/%s?api_key=%s%s" % (
                    movie_id, str(tmdb_api), self.language)
                print("url sls ", url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTMDbData(
                    url,
                    new,
                    True)
            elif select in ("poster", "backdrop"):
                if select == "poster":
                    old = self.posterlist[self.index]
                else:
                    old = self.backdroplist[self.index]
                new_val = new

                with open(DATABASE_PATH, "r", encoding='utf-8') as f:
                    database = f.read()

                database = database.replace(old, new_val)

                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
                    f.write(database)

                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                name = name + 'FIN'
                name = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    name, self.language)
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
        output = fetch_url(url, agents)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTheTVDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        # Extract series IDs
        seriesid = findall(r'<seriesid>(.*?)</seriesid>', output)

        for x in range(len(seriesid)):
            url = ('https://www.thetvdb.com/api/%s/series/' +
                   seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
            print('getTVDbMovies url=', url)
            output = fetch_url(url)
            if output is None:
                print("Failed to fetch URL: " + url)
                continue

            if isinstance(output, bytes):
                try:
                    output = output.decode("utf-8", "ignore")
                except Exception as e:
                    print("Decode error for URL {}: {}".format(url, str(e)))
                    output = output.decode("latin-1", "ignore")

            output = sub(
                r'<poster>',
                '<poster>https://artworks.thetvdb.com/banners/_cache/',
                output)
            # Rebuild URL (looks redundant, but kept to match original code)
            url = ('https://www.thetvdb.com/api/%s/series/' +
                   seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)

            # Replace empty ratings with default 0.0
            output = sub(r'<Rating></Rating>', '<Rating>0.0</Rating>', output)
            output = sub(r'&amp;', '&', output)

            Rating = findall(r'<Rating>(.*?)</Rating>', output)
            Year = findall(r'<FirstAired>([0-9]+)-', output)
            Added = findall(r'<added>([0-9]+)-', output)
            Titles = findall(r'<SeriesName>(.*?)</SeriesName>', output)
            Poster = findall(r'<poster>(.*?)</poster>', output)
            TVDbid = findall(r'<id>(.*?)</id>', output)
            Country = findall(r'<Status>(.*?)</Status>', output)

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
            self.session.open(
                MessageBox,
                _('\nNo TheTVDb Results for %s.') % self.name,
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        else:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.openWithCallback(
                    self.makeTVDbUpdate,
                    moviesList,
                    titel,
                    rating,
                    year,
                    titles,
                    poster,
                    id,
                    country,
                    False,
                    True)
            else:
                self.session.openWithCallback(
                    self.makeTVDbUpdate,
                    moviesList,
                    titel,
                    rating,
                    year,
                    titles,
                    poster,
                    id,
                    country,
                    False,
                    False)

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == "series":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ("https://www.thetvdb.com/api/%s/series/" + new + "/" +
                       config.plugins.moviebrowser.language.value + ".xml") % str(thetvdb_api)
                print("makeTVDbUpdate url=", url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTVDbData(
                    url,
                    new)
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
                    self.session.open(
                        MessageBox,
                        _('\nThe List of Movie Folder can not be deleted.'),
                        MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
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
                movie = sub(r"\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
                if search("[.]ts", movie) is not None:
                    eitfile = sub(r"[.]ts", ".eit", movie)
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
                name = sub(r" - [(][Ss][0-9]+[Ee][0-9]+.*?FIN", "", name)
                name = sub("FIN", "", name)
                episode = name + " - .*?:::Series:::"
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split("\n"):
                        if search(
                                name, line) is not None and search(
                                ":::Series:Top:::", line) is not None:
                            data = data.replace(line + "\n", "")

                with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
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
                self.session.openWithCallback(
                    self.blacklist_return,
                    MessageBox,
                    _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') %
                    name,
                    MessageBox.TYPE_YESNO)
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
                with open(BLACKLIST_PATH, mode, encoding='utf-8') as fremove, open(DATABASE_PATH, "r") as fdb:
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
                name = sub("FIN", "", name)

                episode = name + " - .*?:::Series:::"
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    lines = data.split("\n")
                    data_lines = []
                    for line in lines:
                        if not (
                            search(
                                name,
                                line) and search(
                                ":::Series:Top:::",
                                line)):
                            data_lines.append(line)
                    data = "\n".join(data_lines)

                with open(DATABASE_PATH, "w", encoding='utf-8') as f:
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

            with open(DATABASE_PATH, "r", encoding='utf-8') as f:
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
                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
                    f.write(new_database)
                rename(DATABASE_PATH + ".new", DATABASE_PATH)

            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ":::Series:Top:::":
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub(r"\(|\)|\[|\]|\+|\?", ".", movie)
            with open(DATABASE_PATH, "r", encoding='utf-8') as f:
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
                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
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
                    name = sub(r' \\S+FIN', '', name)
                name = name + ' ...'
            self['name'].setText(str(name))
            self['name'].show()
            self.setTitle(str(name))
            if self.content == ':::Series:::':
                name = sub(r'.*? - \\(', '', name)
                name = sub(r'\\) ', ' ', name)
                name = sub(r'S00E00 - ', '', name)
            if len(name) > 50:
                if name[49:50] == ' ':
                    name = name[0:49]
                else:
                    name = name[0:50] + 'FIN'
                    name = sub(r' \\S+FIN', '', name)
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
                banner = sub(r'.*?[/]', '', bannerurl)
                banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                if fileExists(banner):
                    self["banner"].instance.setScale(1)
                    self["banner"].instance.setPixmapFromFile(banner)
                    self['banner'].show()
                if 'themoviedb.org' in bannerurl or 'image.tmdb.org' in bannerurl:
                    headers_to_use = agents_json
                else:
                    headers_to_use = agents

                callInThread(
                    threadGetPage,
                    url=bannerurl,
                    file=banner,
                    key=None,
                    success=self.getBanner,
                    fail=self.downloadError,
                    custom_headers=headers_to_use
                )
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
                self["banner"].instance.setScale(1)
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
                eposter = sub(r'.*?[/]', '', eposterurl)
                eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                if fileExists(eposter):
                    self["eposter"].instance.setScale(1)
                    self["eposter"].instance.setPixmapFromFile(eposter)
                    self['eposter'].show()
                if 'themoviedb.org' in eposterurl or 'image.tmdb.org' in eposterurl:
                    headers_to_use = agents_json
                else:
                    headers_to_use = agents

                callInThread(
                    threadGetPage,
                    url=eposterurl,
                    file=eposter,
                    key=None,
                    success=self.getEPoster,
                    fail=self.downloadError,
                    custom_headers=headers_to_use)
        except IndexError:
            pass

        return

    def getEPoster(self, output, eposter):
        try:
            open(eposter, 'wb').write(output)
            if fileExists(eposter):
                self["eposter"].instance.setScale(1)
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
            posterurl = sub(r'<episode>.*?<episode>', '', posterurl)
            poster = sub(r'.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                self["poster"].instance.setScale(1)
                self["poster"].instance.setPixmapFromFile(poster)
                self['posterback'].show()
                self['poster'].show()
            else:
                if 'themoviedb.org' in posterurl or 'image.tmdb.org' in posterurl:
                    headers_to_use = agents_json  # TMDB
                else:
                    headers_to_use = agents  # TVDB oo other

                callInThread(
                    threadGetPage,
                    url=posterurl,
                    file=poster,
                    key=None,
                    success=self.getPoster,
                    fail=self.downloadError,
                    custom_headers=headers_to_use)

        except IndexError:
            self['posterback'].hide()
            self['poster'].hide()

        return

    def getPoster(self, output, poster):
        try:
            open(poster, 'wb').write(output)
            self['posterback'].show()
            self["poster"].instance.setScale(1)
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
                backdrop = sub(r'.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setScale(1)
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        if 'themoviedb.org' in backdropurl or 'image.tmdb.org' in backdropurl:
                            headers_to_use = agents_json
                        else:
                            headers_to_use = agents

                        callInThread(
                            threadGetPage,
                            url=backdropurl,
                            file=backdrop,
                            key=index,
                            success=self.getBackdrop,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)

                        popen('/usr/bin/showiframe %s') % no_m1v

                elif fileExists(backdrop):
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()

                else:
                    if 'themoviedb.org' in backdropurl or 'image.tmdb.org' in backdropurl:
                        headers_to_use = agents_json
                    else:
                        headers_to_use = agents

                    callInThread(
                        threadGetPage,
                        url=backdropurl,
                        file=backdrop,
                        key=index,
                        success=self.getBackdrop,
                        fail=self.downloadError,
                        custom_headers=headers_to_use)

        except IndexError:
            self['backdrop'].hide()
        return

    def getBackdrop(self, output, backdrop, index):
        try:
            with open(backdrop, 'wb') as f:
                f.write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(default_backdropm1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % default_backdropm1v)
            elif fileExists(default_backdrop):
                self["backdrop"].instance.setScale(1)
                self["backdrop"].instance.setPixmapFromFile(default_backdrop)
                self['backdrop'].show()
        elif fileExists(default_backdrop):
            self["backdrop"].instance.setScale(1)
            self["backdrop"].instance.setPixmapFromFile(default_backdrop)
            self['backdrop'].show()
        return

    def _update_display(self):
        self['label3'].setText("Item %s/%s" %
                               (str(self.index + 1), str(self.totalItem)))
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
                self.session.open(
                    MessageBox,
                    _('Series Folder: No Info possible'),
                    MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, "r", encoding='utf-8') as f:
                    for line in f:
                        if self.content in line and self.filter in line:
                            movieline = line.split(":::")
                            try:
                                self.movies.append(
                                    (movieline[0], movieline[1], movieline[12]))
                            except IndexError:
                                pass

                if self.showfolder is True:
                    self.movies.append(
                        (_("<List of Movie Folder>"),
                         config.plugins.moviebrowser.moviefolder.value + "...",
                         str(default_backdrop)))

                self.session.openWithCallback(
                    self.gotoMovie,
                    movieControlList,
                    self.movies,
                    self.index,
                    self.content)

    def gotoMovie(self, index, rebuild):
        if index is not None:
            self.index = index
            if rebuild is True:
                if self.index == self.maxentry - 1:
                    self.index -= 1
                self.makeMovies(self.filter)
            else:
                self['label3'].setText('Item %s/%s' %
                                       (str(self.index + 1), str(self.totalItem)))
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
                self.index = next(
                    (index for index,
                     value in enumerate(
                         self.namelist) if value.lower().replace(
                         'der ',
                         '').replace(
                         'die ',
                         '').replace(
                         'das ',
                         '').replace(
                         'the ',
                         '').startswith(ABC)))
                try:
                    self['label3'].setText('Item %s/%s' %
                                           (str(self.index + 1), str(self.totalItem)))
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
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(
                    folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _(
                'Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _(
                    'Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _(
                    'Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                current = self['seasons'].getCurrent()
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _(
                    'Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
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
                            season = sub(r'[(]S00', 'Specials', season)
                            season = sub(r'[(]s00', 'specials', season)
                            season = sub(r'[(]S', 'Season ', season)
                            season = sub(r'[(]s', 'season ', season)
                            season = sub(r'[Ee][0-9]+[)].*?FIN', '', season)
                            season = sub('FIN', '', season)
                            season = sub(r',', '', season)
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
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    10,
                                    0),
                                size=(
                                    810,
                                    40),
                                font=30,
                                flags=RT_HALIGN_LEFT,
                                text=self.seasons[i]))
                    else:
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    5,
                                    0),
                                size=(
                                    540,
                                    30),
                                font=26,
                                flags=RT_HALIGN_LEFT,
                                text=self.seasons[i]))
                    list.append(res)

                self['episodes'].l.setList(list)
                self['episodes'].selectionEnabled(0)
                self['episodes'].show()
            else:
                self.session.openWithCallback(
                    self.filter_return, filterSeasonList, self.seasons, self.content)

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
            self.session.openWithCallback(
                self.returnStyle, switchScreen, 2, 'style')

    def returnStyle(self, number):
        if number is None or number == 1:
            self.ready = True
        elif number == 2:
            if config.plugins.moviebrowser.lastmovie.value == "yes":
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w", encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == "hide" or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserBackdrop,
                self.index,
                self.content,
                self.filter)

        elif number == 3:
            if config.plugins.moviebrowser.lastmovie.value == "yes":
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w", encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserPosterwall,
                self.index,
                self.content,
                self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 3, 'content')

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
                self.session.openWithCallback(
                    self.close,
                    movieBrowserBackdrop,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
            else:
                self.session.openWithCallback(
                    self.close,
                    movieBrowserPosterwall,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
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
                self.session.openWithCallback(
                    self.close,
                    movieBrowserBackdrop,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
            else:
                self.session.openWithCallback(
                    self.close,
                    movieBrowserPosterwall,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
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
                self.session.openWithCallback(
                    self.close, movieBrowserBackdrop, 0, ':Top:::', ':Top:::')
            else:
                self.session.openWithCallback(
                    self.close, movieBrowserPosterwall, 0, ':Top:::', ':Top:::')
        else:
            self.ready = True
        return

    def editDatabase(self):
        if self.ready is True:
            try:
                movie = self.movielist[self.index]
            except IndexError:
                movie = 'None'
            self.session.openWithCallback(
                self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub(r"\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
            self.sortDatabase()
            count = 0
            with open(DATABASE_PATH, "r", encoding='utf-8') as f:
                for line in f:
                    if self.content in line and self.filter in line:
                        if movie in line:
                            self.index = count
                            break
                        count += 1
            self.makeMovies(self.filter)

    def sortDatabase(self):
        series = ''
        with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
            for line in f:
                if ':::Series:::' in line:
                    series += line

        with open(DATABASE_PATH + '.series', 'w', encoding='utf-8') as fseries:
            fseries.write(series)

        with open(DATABASE_PATH + '.series', 'r', encoding='utf-8') as fseries:
            series_lines = fseries.readlines()

        series_lines.sort(key=lambda line: line.split(':::')[0])

        with open(DATABASE_PATH + '.series', 'w', encoding='utf-8') as fseries:
            fseries.writelines(series_lines)

        movies = ''
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

        with open(DATABASE_PATH + ".movies", "w", encoding='utf-8') as f:
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

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if PY3:
            link = link.encode()

        link_str = link if PY3 else link

        if 'themoviedb.org' in link_str or 'api.themoviedb.org' in link_str:
            headers_to_use = agents_json  # TMDB (JSON API)
        else:
            headers_to_use = agents  # Other (TVDB, image, ecc.)

        callInThread(
            threadGetPage,
            url=link,
            file=None,
            key=None,
            success=name,
            fail=self.downloadError,
            custom_headers=headers_to_use)

    def downloadError(self, output=None):
        if output:
            print(
                "[MovieBrowser] Download error: {}".format(
                    str(output)[
                        :100]))
        else:
            print("[MovieBrowser] Download error")

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
                with open(FILTER_PATH, "w", encoding='utf-8') as f:
                    f.write(self.filter)
            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            self.session.deleteDialog(self.toogleHelp)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
        self.close()


class movieBrowserBackdrop(Screen):

    def __init__(self, session, index, content, filter):
        skin = join(skin_path, "movieBrowserBackdrop.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(
            screen=self, eventmap={
                iPlayableService.evEOF: self.seenEOF})
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

        self['poster_back0'] = Pixmap()
        self['poster_back1'] = Pixmap()
        self['poster_back2'] = Pixmap()
        self['poster_back3'] = Pixmap()
        self['poster_back4'] = Pixmap()
        self['poster_back5'] = Pixmap()
        self['poster_back6'] = Pixmap()
        self['poster_back7'] = Pixmap()
        self['poster_back8'] = Pixmap()
        self['poster_back9'] = Pixmap()
        self['poster_back10'] = Pixmap()

        self.index = index
        if screenwidth.width() >= 1280:
            self.posterindex = 6
            self.posterALL = 13
            self['poster11'] = Pixmap()
            self['poster12'] = Pixmap()
            self['poster_back11'] = Pixmap()
            self['poster_back12'] = Pixmap()
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
        self['actions'] = ActionMap(
            [
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
            ],
            {
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
            }, -1
        )

        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(DATABASE_PATH):
            size = getsize(DATABASE_PATH)
            if size < 10:
                remove(DATABASE_PATH)

        if fileExists(infosmallBackPNG):
            if self["infoback"].instance:
                self["infoback"].instance.setScale(1)
                self["infoback"].instance.setPixmapFromFile(infosmallBackPNG)
                self['infoback'].show()

        if fileExists(infoBackPNG):
            if self["plotfullback"].instance:
                self["plotfullback"].instance.setScale(1)
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
                        movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)
        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(
                self.reset_return,
                MessageBox,
                _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'),
                MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(
                self.first_return,
                MessageBox,
                _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'),
                MessageBox.TYPE_YESNO)

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
                    for line in f:
                        if self.content in line and filter in line:
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
                            self.dddlist.append(
                                'yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director,
                                   actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)
                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(
                        config.plugins.moviebrowser.moviefolder.value + '...')
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

                if self.index is None:
                    self.index = 0
                elif self.index < 0:
                    self.index = 0
                elif self.maxentry > 0 and self.index >= self.maxentry:
                    self.index = self.maxentry - 1

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
            if exists(
                    config.plugins.moviebrowser.moviefolder.value) and exists(
                    config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(
                    self.database_return,
                    MessageBox,
                    '\nUpdate Movie Browser Database?',
                    MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(
                    MessageBox,
                    _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.moviefolder.value),
                    MessageBox.TYPE_ERROR)
            else:
                self.session.open(
                    MessageBox,
                    _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.cachefolder.value),
                    MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, "w", encoding='utf-8') as f:
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
        found, orphaned, moviecount, seriescount = UpdateDatabase(
            False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()
        with open(LAST_PATH, 'r', encoding='utf-8') as file:
            movie = file.read()
            movie = sub(r'\(|\)|\[|\]|\+|\?', '.', movie)
        with open(DATABASE_PATH, 'r', encoding='utf-8') as file:
            data = file.read()
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

            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(
                MessageBox,
                _('\nNo new Movies or Series found:\nYour Database is up to date.'),
                MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movie imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movies imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox, _('\n%s Movies and %s Series imported into Database.') %
                    (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(seriescount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                else:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(seriescount),
                            str(orphaned)),
                        MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(seriescount),
                        str(orphaned)),
                    MessageBox.TYPE_INFO)
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
                            current = sub(r'Specials', '(S00', current)
                            current = sub(r'specials', '(s00', current)
                            current = sub(r'Season ', '(S', current)
                            current = sub(r'season ', '(s', current)
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
                            sref = eServiceReference(
                                '1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(
                                MessageBox, _('\nMovie file %s not available.') %
                                filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists(
                                '/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(
                                    DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(
                                    MessageBox, _('\nMovie file %s not available.') %
                                    filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(
                                MessageBox,
                                _('\nDVD Player Plugin not installed.'),
                                MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference(
                            '4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(
                            MessageBox, _('\nMovie file %s not available.') %
                            filename, MessageBox.TYPE_ERROR)

                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(
                        self.getMediaInfo)
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
                height = info and info.getInfo(
                    iServiceInformation.sVideoHeight)
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
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub(
                        r'seen:::.*?FIN',
                        'seen:::' + media + ':::',
                        newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(
                        MessageBox,
                        _('\nTMDb Movie Update Error:\nSeries Folder'),
                        MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                name = transMOVIE(name)
                name = sub(r'\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name

                encoded_name = quote(name)

                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                    str(tmdb_api), encoded_name, self.language)
                print('renewTMDb url tmdb=', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        output = fetch_url(url, agents_json)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTMDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        output = output.replace('&amp;', '&').replace(
            '\\/', '/').replace('}', ',')
        output = sub(
            r'"poster_path":"',
            '"poster_path":"https://image.tmdb.org/t/p/w185',
            output)

        output = sub(
            r'"poster_path":null',
            f'"poster_path":"{default_poster}"',
            output)
        rating = findall(r'"vote_average":(.*?),', output)
        year = findall(r'"release_date":"(.*?)"', output)
        titles = findall(r'"title":"(.*?)"', output)
        poster = findall(r'"poster_path":"(.*?)"', output)
        id = findall(r'"id":(.*?),', output)
        country = findall(r'"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(
                MessageBox,
                _('\nNo TMDb Results for %s.') % self.name,
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        else:
            self.session.openWithCallback(
                self.makeTMDbUpdate,
                moviesList,
                titel,
                rating,
                year,
                titles,
                poster,
                id,
                country,
                True,
                False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == 'movie':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]

                movie_id = ''.join(filter(str.isdigit, str(new)))

                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s%s' % (
                    movie_id, str(tmdb_api), self.language)

                print('makeTMDbUpdate url tmdb=', url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTMDbData(
                    url,
                    new,
                    True)
            elif select == 'poster':
                poster = self.posterlist[self.index]
                posternew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(poster, posternew)
                with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                    f.write(database)

                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                    f.write(database)
                rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                name = name + 'FIN'
                name = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    name, self.language)
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
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTheTVDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        try:
            output = output.replace('&amp;', '&')
            seriesid = findall(r'<seriesid>(.*?)</seriesid>', output)
            for x in range(len(seriesid)):
                url = ('https://www.thetvdb.com/api/%s/series/' +
                       seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('getTVDbMovies url tmdb=', url)
                output = fetch_url(url)
                if output is None:
                    print("Failed to fetch URL: " + url)
                    output = ''
                    continue

                if isinstance(output, bytes):
                    try:
                        output = output.decode("utf-8", "ignore")
                    except Exception as e:
                        print(
                            "Decode error for URL {}: {}".format(
                                url, str(e)))
                        output = output.decode("latin-1", "ignore")

                output = sub(
                    r'<poster>',
                    '<poster>https://www.thetvdb.com/banners/_cache/',
                    output)
                output = sub(
                    r'<poster>https://www.thetvdb.com/banners/_cache/</poster>',
                    '<poster>' + wiki_png + '</poster>',
                    output)
                output = sub(
                    r'<Rating></Rating>',
                    '<Rating>0.0</Rating>',
                    output)
                output = sub(r'&amp;', '&', output)
                Rating = findall(r'<Rating>(.*?)</Rating>', output)
                Year = findall(r'<FirstAired>([0-9]+)-', output)
                Added = findall(r'<added>([0-9]+)-', output)
                Titles = findall(r'<SeriesName>(.*?)</SeriesName>', output)
                Poster = findall(r'<poster>(.*?)</poster>', output)
                TVDbid = findall(r'<id>(.*?)</id>', output)
                Country = findall(r'<Status>(.*?)</Status>', output)
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
                self.session.open(
                    MessageBox,
                    _('\nNo TheTVDb Results for %s.') % self.name,
                    MessageBox.TYPE_INFO,
                    close_on_any_key=True)
            else:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.openWithCallback(
                        self.makeTVDbUpdate,
                        moviesList,
                        titel,
                        rating,
                        year,
                        titles,
                        poster,
                        id,
                        country,
                        False,
                        True)
                else:
                    self.session.openWithCallback(
                        self.makeTVDbUpdate,
                        moviesList,
                        titel,
                        rating,
                        year,
                        titles,
                        poster,
                        id,
                        country,
                        False,
                        False)
        except Exception as e:
            print('error get ', str(e))

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ('https://www.thetvdb.com/api/%s/series/' + new + '/' +
                       config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('makeTVDbUpdate url tmdb=', url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTVDbData(
                    url,
                    new)
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
                with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
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
                    self.session.open(
                        MessageBox,
                        _('\nThe List of Movie Folder can not be deleted.'),
                        MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
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
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub(r'[.]ts', '.eit', movie)
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
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w", encoding='utf-8') as f:
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
                self.session.openWithCallback(
                    self.blacklist_return,
                    MessageBox,
                    _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') %
                    name,
                    MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w", encoding='utf-8') as f:
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
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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

            with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        database = database.replace(line, newline)

            with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
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
                        name = sub(r' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 66:
                if name[65:66] == ' ':
                    name = name[0:65]
                else:
                    name = name[0:66] + 'FIN'
                    name = sub(r' \\S+FIN', '', name)
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
            plot = None

            # Basic control to avoid IndexError
            if (hasattr(self, 'plotlist') and
                self.plotlist is not None and
                    0 <= index < len(self.plotlist)):
                plot = self.plotlist[index]

            # # If plot is None or list not valid
            # if plot is None:
                # plot = _("Description not available")
            # elif isinstance(plot, text_type):
                # plot = plot.encode('utf-8')

            self['plotfull'].setText(plot)

        except Exception as e:
            print("[MovieBrowser] Error in makePlot: " + str(e))
            self['plotfull'].setText(_("Error while loading"))

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
                    banner = sub(r'.*?[/]', '', bannerurl)
                    banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                    if fileExists(banner):
                        self["banner"].instance.setScale(1)
                        self["banner"].instance.setPixmapFromFile(banner)
                        self['banner'].show()
                    else:
                        bannerurl_str = bannerurl.decode(
                            'utf-8') if PY3 and isinstance(bannerurl, bytes) else str(bannerurl)
                        if 'themoviedb.org' in bannerurl_str or 'image.tmdb.org' in bannerurl_str:
                            headers_to_use = agents_json
                        else:
                            headers_to_use = agents

                        callInThread(
                            threadGetPage,
                            url=bannerurl,
                            file=banner,
                            key=None,
                            success=self.getBanner,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)
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
                        bannerurl = search(
                            '<episode>(.*?)<episode>', posterurl)
                        bannerurl = bannerurl.group(1)
                        banner = sub(r'.*?[/]', '', bannerurl)
                        banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                        if fileExists(banner):
                            self["banner"].instance.setScale(1)
                            self["banner"].instance.setPixmapFromFile(banner)
                            self['banner'].show()
                        else:
                            bannerurl_str = bannerurl.decode(
                                'utf-8') if PY3 and isinstance(bannerurl, bytes) else str(bannerurl)
                            if 'themoviedb.org' in bannerurl_str or 'image.tmdb.org' in bannerurl_str:
                                headers_to_use = agents_json
                            else:
                                headers_to_use = agents

                            callInThread(
                                threadGetPage,
                                url=bannerurl,
                                file=banner,
                                key=None,
                                success=self.getBanner,
                                fail=self.downloadError,
                                custom_headers=headers_to_use)
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
                    eposter = sub(r'.*?[/]', '', eposterurl)
                    eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                    if fileExists(eposter):
                        self["eposter"].instance.setScale(1)
                        self["eposter"].instance.setPixmapFromFile(eposter)
                        self['eposter'].show()
                    else:
                        eposterurl_str = eposterurl.decode(
                            'utf-8') if PY3 and isinstance(eposterurl, bytes) else str(eposterurl)
                        if 'themoviedb.org' in eposterurl_str or 'image.tmdb.org' in eposterurl_str:
                            headers_to_use = agents_json
                        else:
                            headers_to_use = agents

                        callInThread(
                            threadGetPage,
                            url=eposterurl,
                            file=eposter,
                            key=None,
                            success=self.getEPoster,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)
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
                self["eposter"].instance.setScale(1)
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
                self["eposter"].instance.setScale(1)
                self["eposter"].instance.setPixmapFromFile(banner)
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
                posterurl = sub(r'<episode>.*?<episode>', '', posterurl)
                poster = sub(r'.*?[/]', '', posterurl)
                poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
                if fileExists(poster):
                    self["poster" + str(x)].instance.setScale(1)
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
                else:
                    posterurl_str = posterurl.decode(
                        'utf-8') if PY3 and isinstance(posterurl, bytes) else str(posterurl)
                    if 'themoviedb.org' in posterurl_str or 'image.tmdb.org' in posterurl_str:
                        headers_to_use = agents_json
                    else:
                        headers_to_use = agents

                    callInThread(
                        threadGetPage,
                        url=posterurl,
                        file=poster,
                        key=x,
                        success=self.getPoster,
                        fail=self.downloadError,
                        custom_headers=headers_to_use)

            except IndexError:
                self['poster' + str(x)].hide()
        return

    def getPoster(self, output, poster, x):
        try:
            with open(poster, 'wb') as f:
                f.write(output)
            if fileExists(poster):
                if self['poster' + str(x)].instance:
                    self["poster" + str(x)].instance.setScale(1)
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
                if 'themoviedb.org' in backdropurl or 'image.tmdb.org' in backdropurl:
                    headers_to_use = agents_json
                else:
                    headers_to_use = agents

                backdrop = sub(r'.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setScale(1)
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        callInThread(
                            threadGetPage,
                            url=backdropurl,
                            file=backdrop,
                            key=index,
                            success=self.getBackdrop,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)

                        popen('/usr/bin/showiframe %s') % no_m1v

                elif fileExists(backdrop):
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()

                else:
                    callInThread(
                        threadGetPage,
                        url=backdropurl,
                        file=backdrop,
                        key=index,
                        success=self.getBackdrop,
                        fail=self.downloadError,
                        custom_headers=headers_to_use)
        except IndexError:
            self['backdrop'].hide()
        return

    def getBackdrop(self, output, backdrop, index):
        try:
            with open(backdrop, 'wb') as f:
                f.write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(default_backdropm1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % default_backdropm1v)
            elif fileExists(default_backdrop):
                self["backdrop"].instance.setScale(1)
                self["backdrop"].instance.setPixmapFromFile(default_backdrop)
                self['backdrop'].show()
                popen('/usr/bin/showiframe %s') % no_m1v
        elif fileExists(default_backdrop):
            self["backdrop"].instance.setScale(1)
            self["backdrop"].instance.setPixmapFromFile(default_backdrop)
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
                self.session.open(
                    MessageBox,
                    _('Series Folder: No Info possible'),
                    MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(DATABASE_PATH):
                f = open(DATABASE_PATH, 'r')
                for line in f:
                    if self.content in line and self.filter in line:
                        movieline = line.split(':::')
                        try:
                            self.movies.append(
                                (movieline[0], movieline[1], movieline[12]))
                        except IndexError:
                            pass

                if self.showfolder is True:
                    self.movies.append(
                        _('<List of Movie Folder>'),
                        config.plugins.moviebrowser.moviefolder.value + '...',
                        str(default_backdrop))
                f.close()
                self.session.openWithCallback(
                    self.gotoMovie,
                    movieControlList,
                    self.movies,
                    self.index,
                    self.content)

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
                self.index = next(
                    (index for index,
                     value in enumerate(
                         self.namelist) if value.lower().replace(
                         'der ',
                         '').replace(
                         'die ',
                         '').replace(
                         'das ',
                         '').replace(
                         'the ',
                         '').startswith(ABC)))
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
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(
                    folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _(
                'Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _(
                    'Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _(
                    'Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
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
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _(
                    'Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
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
                            season = sub(r'[(]S00', 'Specials', season)
                            season = sub(r'[(]s00', 'specials', season)
                            season = sub(r'[(]S', 'Season ', season)
                            season = sub(r'[(]s', 'season ', season)
                            season = sub(r'[Ee][0-9]+[)].*?FIN', '', season)
                            season = sub('FIN', '', season)
                            season = sub(r',', '', season)
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
                    back_color = int(
                        config.plugins.moviebrowser.metrixcolor.value, 16)
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
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            10,
                                            0),
                                        size=(
                                            listwidth,
                                            40),
                                        font=30,
                                        color=16777215,
                                        color_sel=16777215,
                                        backcolor_sel=back_color,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                            else:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            10,
                                            0),
                                        size=(
                                            listwidth,
                                            30),
                                        font=30,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            5,
                                            0),
                                        size=(
                                            listwidth,
                                            40),
                                        font=26,
                                        color=16777215,
                                        color_sel=16777215,
                                        backcolor_sel=back_color,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                            else:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            5,
                                            0),
                                        size=(
                                            listwidth,
                                            3),
                                        font=26,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                        self.entries.append(res)
                    except IndexError:
                        pass

                self['episodes'].l.setList(self.entries)
                self['episodes'].show()
            else:
                self.session.openWithCallback(
                    self.filter_return, filterSeasonList, self.seasons, self.content)

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
            self.session.openWithCallback(
                self.returnStyle, switchScreen, 3, 'style')

    def returnStyle(self, number):
        if number is None or number == 2:
            self.ready = True

        elif number == 3:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w", encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserPosterwall,
                self.index,
                self.content,
                self.filter)

        elif number == 1:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w", encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserMetrix,
                self.index,
                self.content,
                self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 3, 'content')

    def returnContent(self, number):
        if number is None:
            self.ready = True
        elif number == 1 and self.content != ':::Movie:Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(
                    self.close,
                    movieBrowserMetrix,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
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
                self.session.openWithCallback(
                    self.close,
                    movieBrowserPosterwall,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
        elif number == 2 and self.content != ':::Series:Top:::':
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.session.openWithCallback(
                    self.close,
                    movieBrowserMetrix,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
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
                self.session.openWithCallback(
                    self.close,
                    movieBrowserPosterwall,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
        elif number == 3 and self.content != ':Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(
                    self.close, movieBrowserMetrix, 0, ':Top:::', ':Top:::')
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
                self.session.openWithCallback(
                    self.close, movieBrowserPosterwall, 0, ':Top:::', ':Top:::')
        else:
            self.ready = True
        return

    def editDatabase(self):
        if self.ready is True:
            try:
                movie = self.movielist[self.index]
            except IndexError:
                movie = 'None'

            self.session.openWithCallback(
                self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
        with open(DATABASE_PATH, "r", encoding='utf-8') as f:
            series_lines = [line for line in f if ":::Series:::" in line]

        with open(DATABASE_PATH + ".series", "w", encoding='utf-8') as fseries:
            fseries.writelines(series_lines)

        with open(DATABASE_PATH + ".series", "r", encoding='utf-8') as fseries:
            series = fseries.readlines()
        series.sort(key=lambda line: line.split(":::")[0])
        with open(DATABASE_PATH + ".series", "w", encoding='utf-8') as fseries:
            fseries.writelines(series)

        with open(DATABASE_PATH, "r", encoding='utf-8') as f:
            movies_lines = [line for line in f if ":::Series:::" not in line]

        with open(DATABASE_PATH + ".movies", "w", encoding='utf-8') as fmovies:
            fmovies.writelines(movies_lines)

        with open(DATABASE_PATH + ".movies", "r", encoding='utf-8') as fmovies:
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

        f = open(DATABASE_PATH + '.movies', 'w')
        f.writelines(lines)
        f.close()
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

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if PY3:
            link = link.encode()

        link_str = link if PY3 else link

        if 'themoviedb.org' in link_str or 'api.themoviedb.org' in link_str:
            headers_to_use = agents_json  # TMDB (JSON API)
        else:
            headers_to_use = agents  # Other (TVDB, image, ecc.)

        callInThread(
            threadGetPage,
            url=link,
            file=None,
            key=None,
            success=name,
            fail=self.downloadError,
            custom_headers=headers_to_use)

    def downloadError(self, output=None):
        if output:
            print(
                "[MovieBrowser] Download error: {}".format(
                    str(output)[
                        :100]))
        else:
            print("[MovieBrowser] Download error")

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
                    with open(LAST_PATH, 'w', encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value is True:
                with open(FILTER_PATH, 'w', encoding='utf-8') as f:
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
            skincontent = ' <screen name="movieBrowserPosterwall" position="center,center" size="1280,720" flags="wfNoBorder" title="  ">'
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
            skincontent += ' <widget name="2Rating" position="40,100" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="14"/>'
            skincontent += ' <widget name="2ratings" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="15"/>'
            skincontent += ' <widget name="2ratingsback" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/pic/browser/ratings_back.png" alphatest="on" zPosition="16"/>'
            skincontent += ' <widget name="2Director" position="40,170" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="18"/>'
            skincontent += ' <widget name="2director" position="40,200" size="320,28" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="19"/>'
            skincontent += ' <widget name="2Country" position="370,170" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="20"/>'
            skincontent += ' <widget name="2country" position="370,200" size="125,28" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="21"/>'
            skincontent += ' <widget name="2Actors" position="40,240" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="22"/>'
            skincontent += ' <widget name="2actors" position="40,270" size="320,102" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="23"/>'
            skincontent += ' <widget name="2Year" position="370,240" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="24"/>'
            skincontent += ' <widget name="2year" position="370,270" size="125,28" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="25"/>'
            skincontent += ' <widget name="2Runtime" position="370,310" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="26"/>'
            skincontent += ' <widget name="2runtime" position="370,340" size="125,28" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="27"/>'
            skincontent += ' <widget name="2Genres" position="40,380" size="125,28" font="Regular;22" halign="left" foregroundColor="#ffffff" transparent="1" zPosition="28"/>'
            skincontent += ' <widget name="2genres" position="40,410" size="500,28" font="Regular;22" foregroundColor="yellow" transparent="1" zPosition="29"/>'
            skincontent += ' <widget name="eposter" position="742,53" size="500,375" scale="1" alphatest="on" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="banner" position="742,53" size="500,92" scale="1" alphatest="on" transparent="1" zPosition="30"/>'
            skincontent += ' <widget name="frame" position="7,-9" size="160,230" scale="1" zPosition="-2" alphatest="on"/>'

        self.positionlist = []
        numX = -1
        for x in range(self.posterALL):
            numY = x // self.posterX
            numX += 1
            if numX >= self.posterX:
                numX = 0
            posX = self.spaceLeft + self.spaceX + \
                numX * (self.spaceX + self.picX)
            posY = self.spaceTop + self.spaceY + \
                numY * (self.spaceY + self.picY)

            if screenwidth.width() >= 1920:
                self.positionlist.append((posX - 16, posY - 18))
            elif screenwidth.width() == 1280:
                self.positionlist.append((posX - 13, posY - 15))
            else:
                self.positionlist.append((posX - 8, posY - 10))
            skincontent += '<widget name="poster' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(
                self.picX) + ',' + str(self.picY) + '" zPosition="-54" transparent="1" alphatest="on" />'
            skincontent += '<widget name="poster_back' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(
                self.picY) + '" zPosition="-53" transparent="1" alphatest="blend" pixmap="%spic/browser/default_poster.png" />' % skin_directory
        skincontent += '\n</screen>'

        self.skin = skincontent
        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(
            screen=self, eventmap={
                iPlayableService.evEOF: self.seenEOF})
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
        self['actions'] = ActionMap(
            [
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
            ],
            {
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
            }, -1
        )
        self.movie_stop = config.usage.on_movie_stop.value
        self.movie_eof = config.usage.on_movie_eof.value
        config.usage.on_movie_stop.value = 'quit'
        config.usage.on_movie_eof.value = 'quit'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(DATABASE_PATH):
            size = getsize(DATABASE_PATH)
            if size < 10:
                remove(DATABASE_PATH)

        if fileExists(infosmallBackPNG):
            if self["infoback"].instance:
                self["infoback"].instance.setScale(1)
                self["infoback"].instance.setPixmapFromFile(infosmallBackPNG)
                self['infoback'].show()

        if fileExists(infoBackPNG):
            if self["2infoback"].instance:
                self["2infoback"].instance.setScale(1)
                self["2infoback"].instance.setPixmapFromFile(infoBackPNG)
                self['2infoback'].hide()

        if fileExists(infoBackPNG):
            if self["plotfullback"].instance:
                self["plotfullback"].instance.setScale(1)
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
                    movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
            self.makeMovieBrowserTimer.start(500, True)
        else:
            self.openTimer = eTimer()
            self.openTimer.callback.append(self.openInfo)
            self.openTimer.start(500, True)

        return

    def openInfo(self):
        if fileExists(DATABASE_RESET):
            self.session.openWithCallback(
                self.reset_return,
                MessageBox,
                _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'),
                MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(
                self.first_return,
                MessageBox,
                _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'),
                MessageBox.TYPE_YESNO)

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
                    for line in f:
                        if self.content in line and filter in line:
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
                            self.dddlist.append(
                                'yes' if '3d' in filename.lower() else 'no')
                            self.datelist.append(date)
                            res = [runtime, rating, director,
                                   actors, genres, year, country]
                            self.infolist.append(res)
                            self.plotlist.append(plotfull)
                            self.posterlist.append(poster)
                            self.backdroplist.append(backdrop)
                            self.contentlist.append(content)
                            self.seenlist.append(seen)
                            self.medialist.append(media)

                if self.showfolder is True:
                    self.namelist.append(_('<List of Movie Folder>'))
                    self.movielist.append(
                        config.plugins.moviebrowser.moviefolder.value + '...')
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
                    self.posterlist.append(
                        'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_folder.png')
                    self.backdroplist.append(
                        'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png')
                    self.contentlist.append(':Top')
                    self.seenlist.append('unseen')
                    self.medialist.append('\n')
                self.maxentry = len(self.namelist)

                if self.index is None:
                    self.index = 0
                elif self.index < 0:
                    self.index = 0
                elif self.maxentry > 0 and self.index >= self.maxentry:
                    self.index = self.maxentry - 1

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
            if exists(
                    config.plugins.moviebrowser.moviefolder.value) and exists(
                    config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, _(
                    '\nUpdate Movie Browser Database?'), MessageBox.TYPE_YESNO)
            elif exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(
                    MessageBox,
                    _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.moviefolder.value),
                    MessageBox.TYPE_ERROR)
            else:
                self.session.open(
                    MessageBox,
                    _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(
                        config.plugins.moviebrowser.cachefolder.value),
                    MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                with open(LAST_PATH, "w", encoding='utf-8') as f:
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
        found, orphaned, moviecount, seriescount = UpdateDatabase(
            False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value is True and self.hideflag is False:
            self.hideScreen()

        with open(LAST_PATH, 'r', encoding='utf-8') as file:
            movie = file.read()
            movie = sub(r'\(|\)|\[|\]|\+|\?', '.', movie)
        with open(DATABASE_PATH, 'r', encoding='utf-8') as file:
            data = file.read()
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
            self.makeMovieBrowserTimer.callback.append(
                self.makeMovies(self.filter))
        elif found == 0 and orphaned == 0:
            self.session.open(
                MessageBox,
                _('\nNo new Movies or Series found:\nYour Database is up to date.'),
                MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            if orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') %
                    str(orphaned),
                    MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            if moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movie imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox, _('\n%s Movies imported into Database.') %
                    str(moviecount), MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox, _('\n%s Series imported into Database.') %
                    str(seriescount), MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox, _('\n%s Movies and %s Series imported into Database.') %
                    (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        else:
            if moviecount == 1 and seriescount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 1 and seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movie imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif seriescount == 1 and moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif orphaned == 1:
                if seriescount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                elif moviecount == 0:
                    self.session.open(
                        MessageBox,
                        _('\n%s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(seriescount),
                         str(orphaned)),
                        MessageBox.TYPE_INFO)
                else:
                    self.session.open(
                        MessageBox,
                        _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entry deleted.') %
                        (str(moviecount),
                         str(seriescount),
                            str(orphaned)),
                        MessageBox.TYPE_INFO)
            elif seriescount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            elif moviecount == 0:
                self.session.open(
                    MessageBox,
                    _('\n%s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(seriescount),
                     str(orphaned)),
                    MessageBox.TYPE_INFO)
            else:
                self.session.open(
                    MessageBox,
                    _('\n%s Movies and %s Series imported into Database.\n%s orphaned Database Entries deleted.') %
                    (str(moviecount),
                     str(seriescount),
                        str(orphaned)),
                    MessageBox.TYPE_INFO)
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
                            current = sub(r'Specials', '(S00', current)
                            current = sub(r'specials', '(s00', current)
                            current = sub(r'Season ', '(S', current)
                            current = sub(r'season ', '(s', current)
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
                            sref = eServiceReference(
                                '1:0:0:0:0:0:0:0:0:0:' + filename)
                            sref.setName(self.namelist[self.index])
                            self.session.open(MoviePlayer, sref)
                        else:
                            self.session.open(
                                MessageBox, _('\nMovie file %s not available.') %
                                filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if exists(
                                '/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(
                                    DVDPlayer, dvd_filelist=[filename])
                            else:
                                self.session.open(
                                    MessageBox, _('\nMovie file %s not available.') %
                                    filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(
                                MessageBox,
                                _('\nDVD Player Plugin not installed.'),
                                MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference(
                            '4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    else:
                        self.session.open(
                            MessageBox, _('\nMovie file %s not available.') %
                            filename, MessageBox.TYPE_ERROR)

                    self.makeMovieBrowserTimer.stop()
                    self.makeMovieBrowserTimer.callback.append(
                        self.getMediaInfo)
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
                height = info and info.getInfo(
                    iServiceInformation.sVideoHeight)
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
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
            database = open(DATABASE_PATH).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub(
                        r'seen:::.*?FIN',
                        'seen:::' + media + ':::',
                        newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(
                        MessageBox,
                        _('\nTMDb Movie Update Error:\nSeries Folder'),
                        MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = _renewTMDb(name)
                name = transMOVIE(name)
                name = sub(r'\\+[1-2][0-9][0-9][0-9]', '', name)
                self.name = name

                encoded_name = quote(name)

                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                    str(tmdb_api), encoded_name, self.language)
                print('renewTMDb  url tmdb =', url)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        output = fetch_url(url, agents_json)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTMDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        output = output.replace('&amp;', '&').replace(
            '\\/', '/').replace('}', ',')
        output = sub(
            r'"poster_path":"',
            '"poster_path":"https://image.tmdb.org/t/p/w185',
            output)

        output = sub(
            r'"poster_path":null',
            f'"poster_path":"{default_poster}"',
            output)

        rating = findall(r'"vote_average":(.*?),', output)
        year = findall(r'"release_date":"(.*?)"', output)
        titles = findall(r'"title":"(.*?)"', output)
        poster = findall(r'"poster_path":"(.*?)"', output)
        id = findall(r'"id":(.*?),', output)
        country = findall(r'"backdrop(.*?)_path"', output)
        titel = _('TMDb Results')
        if not titles:
            self.session.open(
                MessageBox,
                _('\nNo TMDb Results for %s.') % self.name,
                MessageBox.TYPE_INFO,
                close_on_any_key=True)
        else:
            self.session.openWithCallback(
                self.makeTMDbUpdate,
                moviesList,
                titel,
                rating,
                year,
                titles,
                poster,
                id,
                country,
                True,
                False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == "movie":
                movie = self.movielist[self.index]
                date = self.datelist[self.index]

                movie_id = str(new).strip()

                url = "https://api.themoviedb.org/3/movie/%s?api_key=%s" % (
                    movie_id, str(tmdb_api))
                print("makeTMDbUpdate  url tmdb =", url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTMDbData(
                    url,
                    new,
                    True)
            elif select in ("poster", "backdrop"):
                if select == "poster":
                    old_value = self.posterlist[self.index]
                else:
                    old_value = self.backdroplist[self.index]
                new_value = new
                database = open(DATABASE_PATH).read()
                database = database.replace(old_value, new_value)
                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
                    f.write(database)

                rename(DATABASE_PATH + ".new", DATABASE_PATH)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = _renewTVDb(name)
                name = name + 'FIN'
                name = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                self.name = name
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    name, self.language)
                print('renewTVDb url =', url)
                self.getTVDbMovies(url)
            except IndexError:
                pass

    def getTVDbMovies(self, url):
        rating = []
        year = []
        titles = []
        poster = []
        # banner = []
        id = []
        country = []
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTheTVDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        try:
            output = output.replace('&amp;', '&')
            seriesid = findall(r'<seriesid>(.*?)</seriesid>', output)
            for x in range(len(seriesid)):
                url = ('https://www.thetvdb.com/api/%s/series/' +
                       seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('getTVDbMovies  url tmdb =', url)
                series_data = fetch_url(url)
                if series_data is None:
                    print("Failed to fetch URL: " + url)
                    output = ''
                    continue

                try:
                    output = series_data.decode("utf-8", "ignore")
                except Exception as e:
                    print(
                        "Decode error for series URL {}: {}".format(
                            url, str(e)))
                    output = series_data.decode("latin-1", "ignore")

                output = sub(
                    r'<poster>',
                    '<poster>https://www.thetvdb.com/banners/_cache/',
                    output)
                output = sub(
                    r'<poster>https://www.thetvdb.com/banners/_cache/</poster>',
                    '<poster>' + wiki_png + '</poster>',
                    output)
                output = sub(
                    r'<Rating></Rating>',
                    '<Rating>0.0</Rating>',
                    output)
                output = sub(r'&amp;', '&', output)
                Rating = findall(r'<Rating>(.*?)</Rating>', output)
                Year = findall(r'<FirstAired>([0-9]+)-', output)
                Added = findall(r'<added>([0-9]+)-', output)
                Titles = findall(r'<SeriesName>(.*?)</SeriesName>', output)
                Poster = findall(r'<poster>(.*?)</poster>', output)
                TVDbid = findall(r'<id>(.*?)</id>', output)
                Country = findall(r'<Status>(.*?)</Status>', output)
                                                                     
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
                self.session.open(
                    MessageBox,
                    _('\nNo TheTVDb Results for %s.') % self.name,
                    MessageBox.TYPE_INFO,
                    close_on_any_key=True)
            else:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.openWithCallback(
                        self.makeTVDbUpdate,
                        moviesList,
                        titel,
                        rating,
                        year,
                        titles,
                        poster,
                        id,
                        country,
                        False,
                        True)
                else:
                    self.session.openWithCallback(
                        self.makeTVDbUpdate,
                        moviesList,
                        titel,
                        rating,
                        year,
                        titles,
                        poster,
                        id,
                        country,
                        False,
                        False)
        except Exception as e:
            print('error get ', str(e))

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = ('https://www.thetvdb.com/api/%s/series/' + new + '/' +
                       config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
                print('makeTVDbUpdate  url tmdb =', url)
                UpdateDatabase(
                    True,
                    self.name,
                    movie,
                    date).getTVDbData(
                    url,
                    new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return

                bannernew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(banner, bannernew)
                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
                    f.write(database)

                rename(DATABASE_PATH + ".new", DATABASE_PATH)

            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(DATABASE_PATH).read()
                database = database.replace(backdrop, backdropnew)
                with open(DATABASE_PATH + ".new", "w", encoding='utf-8') as f:
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
                    self.session.open(
                        MessageBox,
                        _('\nThe List of Movie Folder can not be deleted.'),
                        MessageBox.TYPE_ERROR)
                elif content == 'Series:Top':
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
                else:
                    self.session.openWithCallback(
                        self.delete_return,
                        MessageBox,
                        _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') %
                        name,
                        MessageBox.TYPE_YESNO)
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
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub(r'[.]ts', '.eit', movie)
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
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w", encoding='utf-8') as f:
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
                self.session.openWithCallback(
                    self.blacklist_return,
                    MessageBox,
                    _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') %
                    name,
                    MessageBox.TYPE_YESNO)
            except IndexError:
                pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                name = self.namelist[self.index]
                movie = self.movielist[self.index]
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, "w", encoding='utf-8') as f:
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
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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

            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
                f.write(database)
            rename(DATABASE_PATH + '.new', DATABASE_PATH)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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

            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
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
                        name = sub(r' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 64:
                if name[63:64] == ' ':
                    name = name[0:63]
                else:
                    name = name[0:64] + 'FIN'
                    name = sub(r' \\S+FIN', '', name)
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
                        name = sub(r' \\S+FIN', '', name)
                    name = name + ' ...'
            elif len(name) > 66:
                if name[65:66] == ' ':
                    name = name[0:65]
                else:
                    name = name[0:66] + 'FIN'
                    name = sub(r' \\S+FIN', '', name)
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
            plot = None

            # Basic control to avoid IndexError
            if (hasattr(self, 'plotlist') and
                    self.plotlist is not None and
                    0 <= index < len(self.plotlist)):
                plot = self.plotlist[index]

            # # If plot is None or list not valid
            # if plot is None:
                # plot = _("Description not available")
            # elif isinstance(plot, text_type):
                # plot = plot.encode('utf-8')

            self['plotfull'].setText(plot)

        except Exception as e:
            print("[MovieBrowser] Error in makePlot: " + str(e))
            self['plotfull'].setText(_("Error while loading"))

        self['plotfull'].hide()
        self.makeEPoster()
              

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
                    banner = sub(r'.*?[/]', '', bannerurl)
                    banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                    if fileExists(banner):
                        self["banner"].instance.setScale(1)
                        self["banner"].instance.setPixmapFromFile(banner)
                        self['banner'].show()
                    else:
                        bannerurl_str = bannerurl.decode(
                            'utf-8') if PY3 and isinstance(bannerurl, bytes) else str(bannerurl)
                        if 'themoviedb.org' in bannerurl_str or 'image.tmdb.org' in bannerurl_str:
                            headers_to_use = agents_json
                        else:
                            headers_to_use = agents

                        callInThread(
                            threadGetPage,
                            url=bannerurl,
                            file=banner,
                            key=None,
                            success=self.getBanner,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)
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
                        bannerurl = search(
                            '<episode>(.*?)<episode>', posterurl)
                        bannerurl = bannerurl.group(1)
                        banner = sub(r'.*?[/]', '', bannerurl)
                        banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner

                        if fileExists(banner):
                            self["banner"].instance.setScale(1)
                            self["banner"].instance.setPixmapFromFile(banner)
                            self['banner'].show()
                        else:
                            bannerurl_str = bannerurl.decode(
                                'utf-8') if PY3 and isinstance(bannerurl, bytes) else str(bannerurl)
                            if 'themoviedb.org' in bannerurl_str or 'image.tmdb.org' in bannerurl_str:
                                headers_to_use = agents_json
                            else:
                                headers_to_use = agents

                            callInThread(
                                threadGetPage,
                                url=bannerurl,
                                file=banner,
                                key=None,
                                success=self.getBanner,
                                fail=self.downloadError,
                                custom_headers=headers_to_use)
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
                    eposter = sub(r'.*?[/]', '', eposterurl)
                    eposter = config.plugins.moviebrowser.cachefolder.value + '/' + eposter
                    if fileExists(eposter):
                        self["eposter"].instance.setScale(1)
                        self["eposter"].instance.setPixmapFromFile(eposter)
                        self['eposter'].show()
                    else:
                        eposterurl_str = eposterurl.decode(
                            'utf-8') if PY3 and isinstance(eposterurl, bytes) else str(eposterurl)
                        if 'themoviedb.org' in eposterurl_str or 'image.tmdb.org' in eposterurl_str:
                            headers_to_use = agents_json
                        else:
                            headers_to_use = agents

                        callInThread(
                            threadGetPage,
                            url=eposterurl,
                            file=eposter,
                            key=None,
                            success=self.getEPoster,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)
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
                self["eposter"].instance.setScale(1)
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
                self["banner"].instance.setScale(1)
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
                posterurl_clean = sub(r'<episode>.*?<episode>', '', posterurl)
                poster = sub(r'.*?[/]', '', posterurl_clean)
                poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
                if fileExists(poster):
                    self["poster" + str(x)].instance.setScale(1)
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
                else:
                    posterurl_str = posterurl_clean.decode(
                        'utf-8') if PY3 and isinstance(posterurl_clean, bytes) else str(posterurl_clean)
                    if 'themoviedb.org' in posterurl_str or 'image.tmdb.org' in posterurl_str:
                        headers_to_use = agents_json
                    else:
                        headers_to_use = agents

                    callInThread(
                        threadGetPage,
                        url=posterurl_clean,
                        file=poster,
                        key=x,
                        success=self.getPoster,
                        fail=self.downloadError,
                        custom_headers=headers_to_use)

            except IndexError:
                self['poster' + str(x)].hide()

        try:
            self['poster_back' + str(self.wallindex)].hide()
        except Exception:
            pass

        return

    def getPoster(self, output, poster, x):
        try:
            with open(poster, 'wb') as f:
                f.write(output)
            if fileExists(poster):
                if self['poster' + str(x)].instance:
                    self["poster" + str(x)].instance.setScale(1)
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
            posterurl = sub(r'<episode>.*?<episode>', '', posterurl)
            poster = sub(r'.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                self["frame"].instance.setScale(1)
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
                if 'themoviedb.org' in backdropurl or 'image.tmdb.org' in backdropurl:
                    headers_to_use = agents_json
                else:
                    headers_to_use = agents

                backdrop = sub(r'.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop

                if config.plugins.moviebrowser.m1v.value is True:
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setScale(1)
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        popen('/usr/bin/showiframe %s') % no_m1v
                    else:
                        callInThread(
                            threadGetPage,
                            url=backdropurl,
                            file=backdrop,
                            key=index,
                            success=self.getBackdrop,
                            fail=self.downloadError,
                            custom_headers=headers_to_use)

                        popen('/usr/bin/showiframe %s') % no_m1v

                elif fileExists(backdrop):
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()

                else:
                    callInThread(
                        threadGetPage,
                        url=backdropurl,
                        file=backdrop,
                        key=index,
                        success=self.getBackdrop,
                        fail=self.downloadError,
                        custom_headers=headers_to_use)

        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            with open(backdrop, 'wb') as f:
                f.write(output)
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setScale(1)
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
            self['backdrop'].hide()
        return

    def showDefaultBackdrop(self):
        if config.plugins.moviebrowser.m1v.value is True:
            if fileExists(default_backdropm1v):
                self['backdrop'].hide()
                popen("/usr/bin/showiframe '%s'" % default_backdropm1v)
            elif fileExists(default_backdrop):
                self["backdrop"].instance.setScale(1)
                self["backdrop"].instance.setPixmapFromFile(default_backdrop)
                self['backdrop'].show()
                popen('/usr/bin/showiframe %s') % no_m1v
        elif fileExists(default_backdrop):
            self["backdrop"].instance.setScale(1)
            self["backdrop"].instance.setPixmapFromFile(default_backdrop)
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
            if self.pagecount == self.pagemax - \
                    1 and self.wallindex > self.posterALL + self.posterREST - 2:
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
                        self.wallindex = (
                            self.posterREST // self.posterX) * self.posterX + self.oldwallindex
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
        if self.pagecount == self.pagemax - \
                1 and self.wallindex > self.posterALL + self.posterREST - 2:
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
                    self.wallindex = (
                        self.posterREST // self.posterX) * self.posterX + self.oldwallindex
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
                self.session.open(
                    MessageBox,
                    _('Series Folder: No Info possible'),
                    MessageBox.TYPE_ERROR)
                return

            self.movies = []
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, "r", encoding='utf-8') as f:
                    for line in f:
                        if self.content in line and self.filter in line:
                            movieline = line.split(":::")
                            try:
                                self.movies.append(
                                    (movieline[0], movieline[1], movieline[12]))
                            except IndexError:
                                pass

                if self.showfolder is True:
                    self.movies.append(
                        ("<List of Movie Folder>",
                         config.plugins.moviebrowser.moviefolder.value + "...",
                         str(default_backdrop)))
                self.session.openWithCallback(
                    self.gotoMovie,
                    movieControlList,
                    self.movies,
                    self.index,
                    self.content)

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
                self.index = next(
                    (index for index,
                     value in enumerate(
                         self.namelist) if value.lower().replace(
                         'der ',
                         '').replace(
                         'die ',
                         '').replace(
                         'das ',
                         '').replace(
                         'the ',
                         '').startswith(ABC)))
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
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            max = 25
            folder = config.plugins.moviebrowser.moviefolder.value
            self.folders = []
            self.folders.append(folder[:-1])
            for root, dirs, files in walk(
                    folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = join(root, name)
                    self.folders.append(folder)
                    if len(folder) > max:
                        max = len(folder)
            self.folders.sort()
            self.session.openWithCallback(self.filter_return, filterList, self.folders, _(
                'Movie Folder Selection'), filter, len(self.folders), max)
        return

    def filterGenre(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            genres = ''
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
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
                self.session.openWithCallback(self.filter_return, filterList, self.genres, _(
                    'Genre Selection'), filter, len(self.genres), max)
        return

    def filterActor(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            actors = ''
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
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
                self.session.openWithCallback(self.filter_return, filterList, self.actors, _(
                    'Actor Selection'), filter, len(self.actors), max)
        return

    def filterDirector(self):
        if self.ready is True:
            if self.content == ':::Series:::':
                index = self['episodes'].getSelectedIndex()
                current = self.seasons[index]
                if current is not None:
                    current = sub(r'Specials', '(S00', current)
                    current = sub(r'specials', '(s00', current)
                    current = sub(r'Season ', '(S', current)
                    filter = sub(r'season ', '(s', current)
                else:
                    filter = self.namelist[self.index]
            else:
                filter = self.content
            directors = ''
            if fileExists(DATABASE_PATH):
                max = 25
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
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
                self.session.openWithCallback(self.filter_return, filterList, self.directors, _(
                    'Director Selection'), filter, len(self.directors), max)
        return

    def filterSeasons(self):
        if self.ready is True or self.episodes is True:
            if self.episodes is True:
                filter = self.namelist[self.index]
            else:
                filter = self.namelist[self.index]
                filter = filter + 'FIN'
                filter = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', filter)
                filter = sub('FIN', '', filter)
            content = ':::Series:::'
            seasons = ''
            if fileExists(DATABASE_PATH):
                with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith(filter) and content in line:
                            movieline = line.split(':::')
                            try:
                                season = movieline[0] + 'FIN'
                                season = sub(r'[(]S00', 'Specials', season)
                                season = sub(r'[(]s00', 'specials', season)
                                season = sub(r'[(]S', 'Season ', season)
                                season = sub(r'[(]s', 'season ', season)
                                season = sub(
                                    r'[Ee][0-9]+[)].*?FIN', '', season)
                                season = sub('FIN', '', season)
                                season = sub(r',', '', season)
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
                    back_color = int(
                        config.plugins.moviebrowser.metrixcolor.value, 16)
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
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            10,
                                            0),
                                        size=(
                                            listwidth,
                                            28),
                                        font=30,
                                        color=16777215,
                                        color_sel=16777215,
                                        backcolor_sel=back_color,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                            else:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            10,
                                            0),
                                        size=(
                                            listwidth,
                                            28),
                                        font=30,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            5,
                                            0),
                                        size=(
                                            listwidth,
                                            25),
                                        font=26,
                                        color=16777215,
                                        color_sel=16777215,
                                        backcolor_sel=back_color,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                            else:
                                res.append(
                                    MultiContentEntryText(
                                        pos=(
                                            5,
                                            0),
                                        size=(
                                            listwidth,
                                            25),
                                        font=26,
                                        flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                        text=self.seasons[i]))
                        self.entries.append(res)
                    except IndexError:
                        pass

                self['episodes'].l.setList(self.entries)
                self['episodes'].show()
            else:
                self.session.openWithCallback(
                    self.filter_return, filterSeasonList, self.seasons, self.content)

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
            self.session.openWithCallback(
                self.returnStyle, switchScreen, 1, 'style')

    def returnStyle(self, number):
        if number is None or number == 3:
            self.ready = True
        elif number == 1:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, "w", encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserMetrix,
                self.index,
                self.content,
                self.filter)
        elif number == 2:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    with open(LAST_PATH, 'w', encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value is True:
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(
                self.close,
                movieBrowserBackdrop,
                self.index,
                self.content,
                self.filter)
        return

    def toogleContent(self):
        if self.ready is True:
            self.ready = False
            if self.content == ':Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 1, 'content')
            elif self.content == ':::Movie:Top:::':
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 2, 'content')
            else:
                self.session.openWithCallback(
                    self.returnContent, switchScreen, 3, 'content')

    def returnContent(self, number):
        if number is None:
            self.ready = True
        elif number == 1 and self.content != ':::Movie:Top:::':
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(
                    self.close,
                    movieBrowserMetrix,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(
                    self.close,
                    movieBrowserBackdrop,
                    0,
                    ':::Movie:Top:::',
                    ':::Movie:Top:::')
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
                self.session.openWithCallback(
                    self.close,
                    movieBrowserMetrix,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.session.openWithCallback(
                    self.close,
                    movieBrowserBackdrop,
                    0,
                    ':::Series:Top:::',
                    ':::Series:Top:::')
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
                self.session.openWithCallback(
                    self.close, movieBrowserMetrix, 0, ':Top:::', ':Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(
                    self.close, movieBrowserBackdrop, 0, ':Top:::', ':Top:::')
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

            self.session.openWithCallback(
                self.returnDatabase, movieDatabase, movie)

    def returnDatabase(self, changed):
        if changed is True:
            movie = self.movielist[self.index]
            movie = sub(r"\\(|\\)|\\[|\\]|\\+|\\?", ".", movie)
            self.sortDatabase()

            count = 0
            with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                for line in f:
                    if self.content in line and self.filter in line:
                        if movie in line:
                            self.index = count
                            break
                        count += 1

            self.makeMovies(self.filter)

    def sortDatabase(self):
        series = ""
        with open(DATABASE_PATH, "r", encoding='utf-8') as f:
            for line in f:
                if ":::Series:::" in line:
                    series += line

        with open(DATABASE_PATH + ".series", "w", encoding='utf-8') as fseries:
            fseries.write(series)

        with open(DATABASE_PATH + ".series", "r", encoding='utf-8') as fseries:
            series = fseries.readlines()
        series.sort(key=lambda line: line.split(":::")[0])

        with open(DATABASE_PATH + ".series", "w", encoding='utf-8') as fseries:
            fseries.writelines(series)

        movies = ""
        with open(DATABASE_PATH, "r", encoding='utf-8') as f:
            for line in f:
                if ":::Series:::" not in line:
                    movies += line

        with open(DATABASE_PATH + ".movies", "w", encoding='utf-8') as fmovies:
            fmovies.write(movies)

        with open(DATABASE_PATH + ".movies", "r", encoding='utf-8') as fmovies:
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

        with open(DATABASE_PATH + '.movies', "w", encoding='utf-8') as f:
            f.write(lines)

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

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        try:
            link_str = str(link)
            if PY3 and isinstance(link, bytes):
                link_str = link.decode('utf-8')

            if 'themoviedb.org' in link_str or 'api.themoviedb.org' in link_str:
                headers_to_use = agents_json
            else:
                headers_to_use = agents

            if PY3 and isinstance(link, str):
                link = link.encode('utf-8')

            callInThread(
                threadGetPage,
                url=link,
                file=None,
                key=None,
                success=name,
                fail=self.downloadError,
                custom_headers=headers_to_use)

        except Exception as e:
            print("Error in download method: {}".format(str(e)))

    def downloadError(self, output=None):
        if output:
            print(
                "[MovieBrowser] Download error: {}".format(
                    str(output)[
                        :100]))
        else:
            print("[MovieBrowser] Download error")

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
                    with open(LAST_PATH, 'w', encoding='utf-8') as f:
                        f.write(movie)
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value is True:
                with open(FILTER_PATH, 'w', encoding='utf-8') as f:
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
        if self.renew is True:
            self.starttime = ''
            self.namelist.append(name)
            self.movielist.append(movie)
            self.datelist.append(date)
        else:
            self.makeUpdate()

    def makeUpdate(self):
        self.starttime = str(
            datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        with open(DATABASE_PATH, 'r', encoding='utf-8') as data_file:
            data = data_file.read()
        if fileExists(BLACKLIST_PATH):
            with open(BLACKLIST_PATH, 'r', encoding='utf-8') as blacklist_file:
                blacklist = blacklist_file.read()
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
                if (name.endswith('.ts') or name.endswith('.avi') or name.endswith('.divx') or
                        name.endswith('.flv') or name.lower().endswith('.iso') or name.endswith('.m2ts') or
                        name.endswith('.m4v') or name.endswith('.mov') or name.endswith('.mp4') or
                        name.endswith('.mpg') or name.endswith('.mpeg') or name.endswith('.mkv') or
                        name.endswith('.vob')):
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

            if (search(config.plugins.moviebrowser.moviefolder.value, moviefolder)
                    is not None and search(moviefolder, allfiles) is None):
                self.orphaned += 1
                data = data.replace(line + '\n', '')

        if self.orphaned > 0:
            if search('https://cf2.imgobject.com/t/p/', data) is not None:
                data = data.replace(
                    'https://cf2.imgobject.com/t/p/',
                    'https://image.tmdb.org/t/p/')
            with open(DATABASE_PATH, "w", encoding='utf-8') as f:
                f.write(data)
        del data
        del alldata
        del allfiles
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
            series_pattern = r'([Ss]t?[0-9]+[Ee]?[0-9]+|[Ss][0-9]+[Ee][0-9]+|[Ss]tagione\s*[0-9]+\s*[Ee]pisodio\s*[0-9]+|[Ss]eason\s*[0-9]+\s*[Ee]pisode\s*[0-9]+)'

            if search(series_pattern, self.name) is not None:
                # print("[DEBUG] Series pattern detected in: " + self.name)
                series = self.name + 'FIN'
                series = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                series = sub('FIN', '', series)
                series = transSERIES(series)

                encoded_series = quote(series)

                # Option A: Use TVDB (old)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                    encoded_series, self.language)
                print("TVDB URL for series= " + url)
                self.getTVDbData(url, '0')

                # Option B: Use TMDB for series (recommended)
                # url = 'https://api.themoviedb.org/3/search/tv?api_key=' + str(tmdb_api) + '&query=' + encoded_series + self.language
                # print("TMDB URL for TV series= " + url)
                # self.getTMDbTVData(url, '0', False)

            else:
                print(
                    "[DEBUG] No series pattern, treating as movie: " +
                    self.name)
                movie = transMOVIE(self.name)

                encoded_movie = quote(movie)

                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                    str(tmdb_api), encoded_movie, self.language)
                print("TMDB URL for movie= " + url)
                self.getTMDbData(url, '0', False)
        return

    def getTMDbData(self, url, tmdbid, renew):
        self.tmdbCount += 1

        import json
        # 1. If tmdbid is "0", search for the movie by name
        if tmdbid == "0":
            output = fetch_url(url)
            if output is None:
                print("Failed to fetch URL: " + url)
                return None

            if isinstance(output, bytes):
                try:
                    output = output.decode("utf-8", "ignore")
                except Exception as e:
                    print("Decode error for URL {}: {}".format(url, str(e)))
                    output = output.decode("latin-1", "ignore")

            if search('"total_results":0', output) is not None:
                # Fallback to TVDB if not found on TMDB
                series = self.name + "FIN"
                series = sub(r" - [Ss][0-9]+[Ee][0-9]+.*?FIN", "", series)
                series = sub(r"[Ss][0-9]+[Ee][0-9]+.*?FIN", "", series)
                series = sub("FIN", "", series)
                series = transSERIES(series)
                encoded_series = quote(series)
                url = "https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s" % (
                    encoded_series, self.language)
                print("getTMDbData - fallback to TVDB:", url)
                self.getTVDbData(url, "0")
                return

            # Extract movie ID from search response
            tmdbid_match = findall(r'"id":(.*?),', output)
            try:
                tmdbid = tmdbid_match[0]
            except IndexError:
                tmdbid = "0"
                print("ERROR: Unable to extract tmdbid from search")
                return

        # 2. COMBINED API CALL (DETAILS + CREDITS at once)
        url_combinata = f'https://api.themoviedb.org/3/movie/{tmdbid}?api_key={str(tmdb_api)}{self.language}&append_to_response=credits'
        print('getTMDbData - URL COMBINATA:', url_combinata)

        output = fetch_url(url_combinata)
        if output is None:
            print("Failed to fetch URL: " + url_combinata)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error: {}".format(str(e)))
                output = output.decode("latin-1", "ignore")

        # 3. COMBINED JSON PARSING
        try:
            movie_data = json.loads(output)

            # 3a. Extract main data FROM THE ROOT
            title = movie_data.get('title', self.name)
            backdrop_path = movie_data.get('backdrop_path', '')
            poster_path = movie_data.get('poster_path', '')
            release_date = movie_data.get('release_date', '')
            runtime = movie_data.get('runtime', 0)
            vote_average = movie_data.get('vote_average', 0.0)
            overview = movie_data.get('overview', '')

            # 3b. Extract genres
            genres_list = movie_data.get('genres', [])
            genres = ', '.join([g.get('name', '')
                               for g in genres_list]) if genres_list else ' '

            # 3c. Extract country of manufacture
            countries_list = movie_data.get('production_countries', [])
            country = countries_list[0].get(
                'iso_3166_1', '') if countries_list else ' '

            # 3d. Extract YEAR from the release date
            year = release_date.split('-')[0] if release_date else ' '

            # 4. CAST AND CREW EXTRACTOR FROM THE SUB-OBJECT 'Credits'
            credits = movie_data.get('credits', {})
            cast_list = credits.get('cast', [])
            crew_list = credits.get('crew', [])

            # 4a. SEARCH FOR DIRECTORS
            directors = []
            for member in crew_list:
                if member.get('job') == 'Director':
                    directors.append(member.get('name', ''))
            director_string = ', '.join(directors) if directors else ' '

            # 4b. Take the first actors
            actors = []
            for actor in cast_list[:7]:  # Take the first 7 actors
                actors.append(actor.get('name', ''))
            actors_string = ', '.join(actors) if actors else ' '

            # 5. UPDATE CLASS LISTS
            try:
                self.namelist[self.dbcount - 1] = title
            except IndexError:
                self.namelist[self.dbcount - 1] = self.name

            # Poster and backdrop
            if poster_path:
                self.posterlist.append(
                    'https://image.tmdb.org/t/p/w185' + poster_path)
            else:
                self.posterlist.append(str(default_poster))

            if backdrop_path:
                self.backdroplist.append(
                    'https://image.tmdb.org/t/p/w1280' + backdrop_path)
            else:
                self.backdroplist.append(str(default_backdrop))

            # 6. BUILD THE 'res' LIST
            res = []
            # 1. Runtime
            res.append(
                str(runtime) +
                ' min' if runtime and runtime > 0 else ' ')
            # 2. Rating
            res.append(
                str(vote_average) if vote_average and vote_average > 0 else '0.0')
            # 3. Director
            res.append(director_string if director_string else ' ')
            # 4. Actors
            res.append(actors_string if actors_string else ' ')
            # 5. Genres
            res.append(
                genres.replace(
                    'Science Fiction',
                    'Sci-Fi') if genres else ' ')
            # 6. Year
            res.append(year if year else ' ')
            # 7. Country
            res.append(country.replace('US', 'USA') if country else ' ')

            # 7. ADD TO FINAL LISTS
            self.infolist.append(res)
            self.plotlist.append(
                overview.replace(
                    '\r',
                    '').replace(
                    '\n',
                    ' ').replace(
                    '\\',
                    ''))

            # print("[SUCCESS] Movie '{}' elaborate. Directors found: {}".format(title, director_string))

        except json.JSONDecodeError as e:
            print("CRITICAL ERROR in JSON parsing: {}".format(e))
            print("Problematic API response (first 500 characters): {}".format(
                output[:500] if output else "No response"))
            # Fallback: use empty values ​​but continue
            res = [' ', '0.0', ' ', ' ', ' ', ' ', ' ']
            self.infolist.append(res)
            self.plotlist.append(' ')
            self.posterlist.append(str(default_poster))
            self.backdroplist.append(str(default_backdrop))

        # 8. FINAL CALL TO SAVE TO DATABASE
        self.makeDataEntry(self.dbcount - 1, True)
        return

    def getTVDbData(self, url, seriesid):
        self.tvdbCount += 1
        output = fetch_url(url)
        if output is None:
            print("Failed to fetch URL: " + url)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        # Case Management: Series not found on TVDB
        if search('<Series>', output) is None:
            print("[TVDB] Series not found, using default values")
            res = [' ', '0.0', ' ', ' ', ' ', ' ', ' ']
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
                self.makeDataEntry(self.dbcount - 1, False)
            else:
                self.backdroplist.append(str(default_backdrop))
                self.posterlist.append(str(default_poster))
                self.namelist[self.dbcount - 1] = self.name
                self.makeDataEntry(self.dbcount - 1, True)
            return

        # Extract series ID if not provided
        if seriesid == '0':
            seriesid_match = findall(r'<seriesid>(.*?)</seriesid>', output)
            try:
                seriesid = seriesid_match[0]
            except IndexError:
                seriesid = '0'
                print("[TVDB] Unable to extract seriesid")

        # Episode management for TV series
        episode_data = {}
        if search(
            '[Ss][0-9]+[Ee][0-9]+',
                self.name) is not None and self.newseries is False:
            data = search('([Ss][0-9]+[Ee][0-9]+)', self.name)
            data = data.group(1)
            season = search('[Ss]([0-9]+)[Ee]', data)
            season = season.group(1).lstrip('0')
            if season == '':
                season = '0'
            episode = search('[Ss][0-9]+[Ee]([0-9]+)', data)
            episode = episode.group(1).lstrip('0')

            # URL for episode details
            url_episode = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/default/' + season + '/' +
                           episode + '/' + config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
            print('[TVDB] URL episode:', url_episode)

            output_episode = fetch_url(url_episode)
            if output_episode:
                if isinstance(output_episode, bytes):
                    output_episode = output_episode.decode("utf-8", "ignore")

                output_episode = sub(r'\n', '', output_episode)
                output_episode = sub(r'&amp;', '&', output_episode)

                # Episode data extraction
                episode_data['name'] = findall(
                    r'<EpisodeName>(.*?)</EpisodeName>', output_episode)
                episode_data['year'] = findall(
                    r'<FirstAired>([0-9]+)-', output_episode)
                episode_data['guest'] = findall(
                    r'<GuestStars>[|](.*?)[|]</GuestStars>', output_episode)
                episode_data['director'] = findall(
                    r'<Director>[|](.*?)[|]</Director>', output_episode)
                if not episode_data['director']:
                    episode_data['director'] = findall(
                        r'<Director>(.*?)[|]', output_episode)
                    if not episode_data['director']:
                        episode_data['director'] = findall(
                            r'<Director>[|](.*?)[|]', output_episode)
                episode_data['plot'] = findall(
                    r'<Overview>(.*?)</Overview>', output_episode, S)
                episode_data['rating'] = findall(
                    r'<Rating>(.*?)</Rating>', output_episode)
                episode_data['poster'] = findall(
                    r'<filename>(.*?)</filename>', output_episode)
            else:
                print("[TVDB] Impossibile recuperare dati episodio")

        # URL for main series details
        url_series = ('https://www.thetvdb.com/api/%s/series/' + seriesid + '/' +
                      config.plugins.moviebrowser.language.value + '.xml') % str(thetvdb_api)
        print('[TVDB] URL serie:', url_series)

        output_series = fetch_url(url_series)
        if output_series is None:
            print("[TVDB] Failed to fetch series URL: " + url_series)
            return None

        if isinstance(output_series, bytes):
            output_series = output_series.decode("utf-8", "ignore")

        output_series = sub(r'\n', '', output_series)
        output_series = sub(r'&amp;', '&', output_series)
        output_series = sub(r'&quot;', '"', output_series)

        # Data series extraction
        series_data = {}

        # Series Title
        series_data['name'] = findall(
            r'<SeriesName>(.*?)</SeriesName>', output_series)
        series_data['runtime'] = findall(
            r'<Runtime>(.*?)</Runtime>', output_series)

        # Rating (use episode if available, otherwise series)
        if episode_data.get('rating'):
            series_data['rating'] = episode_data['rating']
        else:
            series_data['rating'] = findall(
                r'<Rating>(.*?)</Rating>', output_series)

        # Actors
        actors_text = findall(r'<Actors>(.*?)</Actors>', output_series)
        actors_list = []
        if actors_text:
            actors_split = actors_text[0].split('|')
            actors_list = [actor.strip()
                           for actor in actors_split if actor.strip()]

        # Generes
        genres_text = findall(r'<Genre>(.*?)</Genre>', output_series)
        genres_list = []
        if genres_text:
            genres_split = genres_text[0].split('|')
            genres_list = [genre.strip()
                           for genre in genres_split if genre.strip()]

        # Year (priority: episode > series)
        if episode_data.get('year'):
            series_data['year'] = episode_data['year']
        else:
            series_data['year'] = findall(
                r'<FirstAired>([0-9]+)-', output_series)

        # Plot (priority: episode > series)
        if episode_data.get('plot'):
            series_data['plot'] = episode_data['plot']
        else:
            series_data['plot'] = findall(
                r'<Overview>(.*?)</Overview>', output_series, S)

        # Image
        series_data['backdrop'] = findall(
            r'<fanart>(.*?)</fanart>', output_series)
        series_data['poster'] = findall(
            r'<poster>(.*?)</poster>', output_series)

        if self.newseries is True:
            series_data['banner'] = findall(
                r'<banner>(.*?)</banner>', output_series)

        # New series entry management
        if self.newseries is False:
            try:
                series_name = series_data['name'][0] if series_data['name'] else self.name
                if not episode_data.get('name'):
                    self.namelist[self.dbcount - 1] = series_name + \
                        ' - (S00E00) - TheTVDb: ' + data + ' not found.'
                    self.name = series_name
                else:
                    self.namelist[self.dbcount - 1] = series_name + \
                        ' - (' + data + ') ' + episode_data['name'][0]
                    self.name = series_name + ' ' + data
            except (IndexError, KeyError):
                self.namelist[self.dbcount - 1] = self.name
        else:
            try:
                series_name = series_data['name'][0] if series_data['name'] else self.name
                self.namelist.insert(self.dbcount - 1, series_name)
                self.movielist.insert(self.dbcount - 1, series_name)
                self.datelist.insert(
                    self.dbcount - 1, str(datetime.datetime.now()))
            except (IndexError, KeyError):
                self.namelist.insert(self.dbcount - 1, self.name)
                self.movielist.insert(self.dbcount - 1, self.name)
                self.datelist.insert(
                    self.dbcount - 1, str(datetime.datetime.now()))

        # Result Construction
        res = []

        # 1. Runtime
        try:
            runtime_val = series_data['runtime'][0] if series_data['runtime'] else ' '
            res.append(runtime_val + ' min')
        except (IndexError, KeyError):
            res.append(' ')

        # 2. Rating
        try:
            rating_val = series_data['rating'][0] if series_data['rating'] else '0.0'
            res.append(rating_val)
        except (IndexError, KeyError):
            res.append('0.0')

        # 3. Director (use episode if available)
        try:
            if episode_data.get('director'):
                director_val = episode_data['director'][0] if episode_data['director'] else 'Various'
            else:
                director_val = 'Various'
            res.append(director_val)
        except (IndexError, KeyError):
            res.append('Various')

        # 4. Actors (takes a maximum of 6 actors)
        actors_string = ' '
        if actors_list:
            actors_string = ', '.join(actors_list[:6])
        res.append(actors_string)

        # 5. Genres
        genres_string = ' '
        if genres_list:
            genres_string = ', '.join(genres_list)
        res.append(genres_string.replace('Science-Fiction', 'Sci-Fi'))

        # 6. Year
        try:
            year_val = series_data['year'][0] if series_data['year'] else ' '
            res.append(year_val)
        except (IndexError, KeyError):
            res.append(' ')

        # 7. Country (use plugin language setting)
        country = config.plugins.moviebrowser.language.getValue()
        country = country.upper()
        res.append(country)

        # Add to lists
        self.infolist.append(res)

        # Trame
        try:
            plot_text = series_data['plot'][0] if series_data['plot'] else ' '
            if episode_data.get('guest'):
                plot_text = plot_text + ' Guest Stars: ' + \
                    episode_data['guest'][0].replace('|', ', ') + '.'
            self.plotlist.append(plot_text.replace('\r', '').replace(
                '\n', ' ').replace('\\', '').replace('&quot;', '"'))
        except (IndexError, KeyError):
            self.plotlist.append(' ')

        # Image
        try:
            backdrop_url = 'https://www.thetvdb.com/banners/' + \
                series_data['backdrop'][0] if series_data['backdrop'] else str(default_backdrop)
            self.backdroplist.append(backdrop_url)
        except (IndexError, KeyError):
            self.backdroplist.append(str(default_backdrop))

        try:
            if self.newseries is True:
                banner_url = ''
                if series_data.get('banner'):
                    banner_url = series_data['banner'][0] if series_data['banner'][0] else str(
                        default_banner)
                else:
                    banner_url = str(default_banner)

                poster_url = 'https://www.thetvdb.com/banners/_cache/' + \
                    series_data['poster'][0] if series_data['poster'] else str(default_poster)
                self.posterlist.append(
                    poster_url + '<episode>' + banner_url + '<episode>')
            elif episode_data.get('poster'):
                poster_url = 'https://www.thetvdb.com/banners/_cache/' + \
                    series_data['poster'][0] if series_data['poster'] else str(default_poster)
                episode_poster = 'https://www.thetvdb.com/banners/' + \
                    episode_data['poster'][0]
                self.posterlist.append(
                    poster_url +
                    '<episode>' +
                    episode_poster +
                    '<episode>')
            else:
                poster_url = 'https://www.thetvdb.com/banners/_cache/' + \
                    series_data['poster'][0] if series_data['poster'] else str(default_poster)
                self.posterlist.append(poster_url)
        except (IndexError, KeyError):
            if self.newseries is True:
                self.posterlist.append(
                    str(default_poster) +
                    '<episode>' +
                    str(default_banner) +
                    '<episode>')
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
                                if url.startswith(
                                        "http://") or url.startswith("https://"):
                                    output = fetch_url(url)
                                elif exists(url):
                                    with open(url, "rb") as f:
                                        output = f.read()
                                else:
                                    print("Invalid backdrop path or URL:", url)
                                    output = None
                            except Exception as e:
                                print(
                                    "Error fetching backdrop {}: {}".format(
                                        url, str(e)))
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
                    newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + \
                        ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Movie:Top:::unseen:::'
                else:
                    name = self.namelist[count] + 'FIN'
                    name = sub(r' - \\([Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
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
            encoded_series = quote(series)

            url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                encoded_series, self.language)
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
                    series = sub(r' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub(r'[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
                    series = sub('FIN', '', series)
                    series = transSERIES(series)

                    encoded_series = quote(series)

                    url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=%s%s' % (
                        encoded_series, self.language)
                    print('url tmdb=', url)
                    try:
                        self.getTVDbData(url, '0')
                    except RuntimeError:
                        return (
                            1,
                            self.orphaned,
                            self.moviecount,
                            self.seriescount)
                else:
                    movie = transMOVIE(self.name)
                    movie = sub(r'\\+[1-2][0-9][0-9][0-9]', '', movie)

                    encoded_movie = quote(movie)

                    url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&include_adult=true&query=%s%s' % (
                        str(tmdb_api), encoded_movie, self.language)
                    print('url tmdb=', url)
                    try:
                        self.getTMDbData(url, '0', False)
                    except RuntimeError:
                        return (
                            1,
                            self.orphaned,
                            self.moviecount,
                            self.seriescount)

            except IndexError:
                self.results = (
                    1,
                    self.orphaned,
                    self.moviecount,
                    self.seriescount)
                self.showResult(False)

        else:
            self.results = (
                1,
                self.orphaned,
                self.moviecount,
                self.seriescount)
            self.showResult(False)
        return

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
            if not self.renew:
                with open(UPDATE_LOG_PATH, "a", encoding="utf-8") as f:
                    f.write(result)
                return (found, orphaned, moviecount, seriescount)
            return True

    def sortDatabase(self):
        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            series = [line for line in f if ":::Series:::" in line]
            movies = [line for line in f if ":::Series:::" not in line]

        series.sort(key=lambda line: line.split(":::")[0])

        with open(DATABASE_PATH + ".series", "w", encoding="utf-8") as f:
            f.writelines(series)

        with open(DATABASE_PATH, "r", encoding="utf-8") as f:
            movies = [line for line in f if ":::Series:::" not in line]

        with open(DATABASE_PATH + ".movies", "w", encoding="utf-8") as f:
            f.writelines(movies)

        with open(DATABASE_PATH + ".movies", "r", encoding="utf-8") as f:
            lines = f.readlines()

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


class movieControlList(Screen):

    def __init__(self, session, list, index, content):
        skin = join(skin_path, "movieControlList.xml")
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
        self["Title"] = Label()
        self['list'] = ItemList([])
        self['log'] = ScrollLabel()
        self['log'].hide()
        self['label3'] = Label('Info')
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'ColorActions',
                'ChannelSelectBaseActions',
                'HelpActions',
                'NumberActions'
            ],
            {
                'ok': self.ok,
                'cancel': self.exit,
                'right': self.rightDown,
                'left': self.leftUp,
                'down': self.down,
                'up': self.up,
                'nextBouquet': self.zap,
                'prevBouquet': self.zap,
                'yellow': self.showInfo,
                'blue': self.hideScreen,
                '0': self.gotoEnd,
                '1': self.gotoFirst,

            }, -1
        )
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        title = "Movie Control List"
        idx = 0
        for x in self.list:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if screenwidth.width() == 1920:
                    if self.content != ':::Series:::':
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    10,
                                    0),
                                size=(
                                    1700,
                                    50),
                                font=28,
                                color=0xFFFFFF,
                                backcolor_sel=0x0043ac,
                                color_sel=0xFFFFFF,
                                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                text=self.list[i][0]))
                    else:
                        series = sub(
                            r'[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    10,
                                    0),
                                size=(
                                    1700,
                                    50),
                                font=28,
                                color=0xFFFFFF,
                                backcolor_sel=0x0043ac,
                                color_sel=0xFFFFFF,
                                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                text=series))
                else:
                    if self.content != ':::Series:::':
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    5,
                                    0),
                                size=(
                                    1200,
                                    50),
                                font=24,
                                color=0xFFFFFF,
                                backcolor_sel=0x0043ac,
                                color_sel=0xFFFFFF,
                                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                text=self.list[i][0]))
                    else:
                        series = sub(
                            r'[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(
                            MultiContentEntryText(
                                pos=(
                                    5,
                                    0),
                                size=(
                                    1200,
                                    40),
                                font=24,
                                color=0xFFFFFF,
                                backcolor_sel=0x0043ac,
                                color_sel=0xFFFFFF,
                                flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                                text=series))
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
            movieFolder = statvfs(
                config.plugins.moviebrowser.moviefolder.value)
            try:
                stat = movieFolder
                freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
            except Exception as e:
                print(e)
                freeSize = "-?-"

            if self.content == ':::Movie:Top:::':
                title = '%s %s (%s %s)' % (str(totalMovies),
                                           movies, str(freeSize), free)
            elif self.content == ':::Series:::' or self.content == ':::Series:Top:::':
                title = '%s %s (%s %s)' % (str(totalMovies),
                                           series, str(freeSize), free)
            else:
                title = '%s %s & %s (%s %s)' % (
                    str(totalMovies), movies, series, str(freeSize), free)
            self.setTitle(title)
        else:
            if self.content == ':::Movie:Top:::':
                title = '%s %s (%s offline)' % (
                    str(totalMovies), movies, folder)
            elif self.content == ':::Series:::' or self.content == ':::Series:Top:::':
                title = '%s %s (%s offline)' % (
                    str(totalMovies), series, folder)
            else:
                title = '%s %s & %s (%s offline)' % (
                    str(totalMovies), movies, series, folder)
        self.setTitle(title)
        self["Title"].setText(title)

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
            self.session.openWithCallback(
                self.choiceLog,
                ChoiceBox,
                title='Movie Browser',
                list=loglist)

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
                infotext = '%s\n%s\n%s\n\n%s, %s, %s\n%s' % (
                    moviefile, date, size, name, description, duration, extDescription)
            elif moviefile == config.plugins.moviebrowser.moviefolder.value + '...':
                folder = config.plugins.moviebrowser.moviefolder.value
                infotext = config.plugins.moviebrowser.moviefolder.value + '\n'
                for root, dirs, files in walk(
                        folder, topdown=False, onerror=None, followlinks=True):
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
            with open(UPDATE_LOG_PATH, 'r', encoding='utf-8') as data:
                data = data.read()
            self['log'].setText(data)
        elif choice == 'timer':
            self.log = True
            self['log'].show()
            self['list'].hide()
            with open(TIMER_LOG_PATH, 'r', encoding='utf-8') as data:
                data = data.read()
            self['log'].setText(data)
        else:
            self.log = True
            self['log'].show()
            self['list'].hide()
            with open(CLEANUP_LOG_PATH, 'r', encoding='utf-8') as data:
                data = data.read()
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
                self.session.open(
                    MessageBox,
                    _('\nThe List of Movie Folder can not be deleted.'),
                    MessageBox.TYPE_ERROR)
            elif name == movie:
                self.session.openWithCallback(
                    self.delete_return,
                    MessageBox,
                    _('\nThis will delete all %s entries from the Database but not from the Movie Folder.\n\nDo you want to continue?') %
                    name,
                    MessageBox.TYPE_YESNO)
            else:
                self.session.openWithCallback(
                    self.delete_return,
                    MessageBox,
                    _('\nThis will delete %s from the Database and from the Movie Folder!\n\nDo you want to continue?') %
                    name,
                    MessageBox.TYPE_YESNO)
        except IndexError:
            pass

    def delete_return(self, answer):
        if answer is True:
            try:
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                if fileExists(movie):
                    remove(movie)
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub(r'[.]ts', '.eit', movie)
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
                with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                    data = data.read()
                if name == movie:
                    for line in data.split('\n'):
                        if search(movie + '.*?:::Series:', line) is not None:
                            data = data.replace(line + '\n', '')

                else:
                    for line in data.split('\n'):
                        if search(movie, line) is not None:
                            data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
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
            self.session.openWithCallback(
                self.blacklist_return,
                MessageBox,
                _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') %
                name,
                MessageBox.TYPE_YESNO)
        except IndexError:
            pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(BLACKLIST_PATH):
                    fremove = open(BLACKLIST_PATH, 'a', encoding='utf-8')
                else:
                    fremove = open(BLACKLIST_PATH, 'w', encoding='utf-8')
                with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                    data = data.read()
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        fremove.write(line + '\n')
                        fremove.close()
                        data = data.replace(line + '\n', '')

                name = name + 'FIN'
                name = sub(r' - [(][Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                episode = name + ' - .*?:::Series:::'
                if search(
                        episode,
                        data) is None and search(
                        name,
                        data) is not None:
                    for line in data.split('\n'):
                        if search(
                                name, line) is not None and search(
                                ':::Series:Top:::', line) is not None:
                            data = data.replace(line + '\n', '')

                with open(DATABASE_PATH, 'w', encoding='utf-8') as f:
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
        skin = join(skin_path, "movieDatabase.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self["Title"] = Label()
        self.hideflag = True
        self.ready = False
        self.change = False
        self.first = False
        self.movie = movie
        self.lang = config.plugins.moviebrowser.language.value
        self['list'] = ItemList([])
        self['list2'] = ItemList([])
        self.actlist = 'list'
        self['actions'] = ActionMap(
            ['OkCancelActions',
             'DirectionActions',
             'ColorActions',
             'ChannelSelectBaseActions',
             'HelpActions',
             'NumberActions'
             ],
            {'ok': self.ok,
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
             },
            -1
        )
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
                    name = sub(r'[Ss][0]+[Ee]', 'Special ', name)
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
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                1240,
                                40),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=name))
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                710,
                                30),
                            font=26,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=name))
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
                movieFolder = statvfs(
                    config.plugins.moviebrowser.moviefolder.value)
                try:
                    stat = movieFolder
                    freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
                except Exception as e:
                    print(e)
                    freeSize = "-?-"
                title = '%s Editor: %s %s (%s %s)' % (
                    database, str(totalMovies), movies, str(freeSize), free)
            else:
                title = '%s Editor: %s %s (%s offline)' % (
                    database, str(totalMovies), movies, folder)

            self.setTitle(title)
            self["Title"].setText(title)

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
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                1240,
                                40),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=self.list2[i]))
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                710,
                                30),
                            font=26,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=self.list2[i]))
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
                    self.movie = sub(r'\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
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
                self.session.openWithCallback(
                    self.databaseReturn,
                    VirtualKeyBoard,
                    title=_('Database Editor:'),
                    text=self.data)

    def databaseReturn(self, newdata):
        if newdata and newdata != "" and newdata != self.data:
            if self.first is True:
                self.first = False
                newdata = newdata + ":::"
                olddata = self.data + ":::"
            else:
                newdata = ":::" + newdata + ":::"
                olddata = ":::" + self.data + ":::"

            with open(DATABASE_PATH, 'r', encoding='utf-8') as f:
                database = f.read()

            for line in database.split("\n"):
                if search(self.movie, line) is not None:
                    newline = line.replace(olddata, newdata)
                    database = database.replace(line, newline)
                    break

            with open(DATABASE_PATH + '.new', 'w', encoding='utf-8') as f:
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

    def __init__(
            self,
            session,
            titel,
            rating,
            year,
            titles,
            poster,
            id,
            country,
            movie,
            top):

        Screen.__init__(self, session)
        skin = join(skin_path, "moviesList.xml")
        with open(skin, "r") as f:
            self.skin = f.read()

        self.titel = titel
        self.rating = rating
        self.year = year
        self.titles = titles
        self.poster = poster
        self.id = id
        self.country = country
            
       

              
        print("[moviesList.__init__] Received: movie=" + str(movie) + ", top=" + str(top))
                        
                      
                     
                                                
        self.movie = movie
        self.top = top
        self.choice = 'movie'

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

        self.banners_cache = []

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
        self['list'].onSelectionChanged.append(self.showBannersForIndex)
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'ColorActions',
                'ChannelSelectBaseActions',
                'HelpActions',
                'NumberActions'
            ],
            {
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
            }, -1
        )
        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(
                config.plugins.moviebrowser.metrixcolor.value, 16)

        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        try:
            poster1 = self.poster[0]
            # print("[DEBUG] onLayoutFinished poster1: " + str(poster1))
            self.download(poster1, self.getPoster1)
            self['poster1'].show()
        except IndexError:
            self['poster1'].hide()

        try:
            poster2 = self.poster[1]
            # print("[DEBUG] onLayoutFinished poster2: " + str(poster2))
            self.download(poster2, self.getPoster2)
            self['poster2'].show()
        except IndexError:
            self['poster2'].hide()

        try:
            poster3 = self.poster[2]
            # print("[DEBUG] onLayoutFinished poster3: " + str(poster3))
            self.download(poster3, self.getPoster3)
            self['poster3'].show()
        except IndexError:
            self['poster3'].hide()

        try:
            poster4 = self.poster[3]
            # print("[DEBUG] onLayoutFinished poster4: " + str(poster4))
            self.download(poster4, self.getPoster4)
            self['poster4'].show()
        except IndexError:
            self['poster4'].hide()

        self.preloadBanners()

        if hasattr(self['list'], 'onSelectionChanged'):
            self['list'].onSelectionChanged.append(self.showBannersForIndex)

        self.startup_timer = eTimer()
        self.startup_timer.callback.append(self.showInitialBanner)
        self.startup_timer.start(1000)

        try:
            # Check if we have series IDs
            if hasattr(self, 'id') and self.id and len(self.id) > 0:
                series_id = self.id[0]
                # print("[DEBUG] Downloading banners for series: " + str(series_id))

                # Use fetchBannersForSeries
                banners = self.fetchBannersForSeries(series_id)
                # print("[DEBUG] Banners found: " + str(banners))

                # Banner 1
                if len(banners) > 0:
                    self.download(banners[0], self.getBanner1)
                    self['banner1'].show()
                    # print("[DEBUG] Banner1 downloaded: " + str(banners[0]))
                else:
                    # print("[DEBUG] No banner1, hide")
                    self['banner1'].hide()

                # Banner 2
                if len(banners) > 1:
                    self.download(banners[1], self.getBanner2)
                    self['banner2'].show()
                else:
                    self['banner2'].hide()

                # Banner 3
                if len(banners) > 2:
                    self.download(banners[2], self.getBanner3)
                    self['banner3'].show()
                else:
                    self['banner3'].hide()

                # Banner 4
                if len(banners) > 3:
                    self.download(banners[3], self.getBanner4)
                    self['banner4'].show()
                else:
                    self['banner4'].hide()

            else:
                print("[DEBUG] No series ID, hide all banners")
                self['banner1'].hide()
                self['banner2'].hide()
                self['banner3'].hide()
                self['banner4'].hide()

        except Exception as e:
            print("[ERROR] Banner loading error: " + str(e))
            self['banner1'].hide()
            self['banner2'].hide()
            self['banner3'].hide()
            self['banner4'].hide()

        for x in range(len(self.titles)):
            res = ['']
            png = '%spic/browser/ratings_back.png' % skin_directory
            png2 = '%spic/browser/ratings.png' % skin_directory
            try:
                if screenwidth.width() == 1920:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                1210,
                                225),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=''))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                13),
                            size=(
                                800,
                                45),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.titles[x]))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                54),
                            size=(
                                200,
                                45),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.year[x]))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                260),
                            size=(
                                200,
                                45),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(
                        10 * round(float(self.rating[x]), 1)) // 10
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                810,
                                145),
                            font=24,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=''))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                13),
                            size=(
                                610,
                                30),
                            font=24,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.titles[x]))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                48),
                            size=(
                                200,
                                30),
                            font=24,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.year[x]))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                200),
                            size=(
                                200,
                                30),
                            font=26,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(
                        10 * round(float(self.rating[x]), 1)) // 10
            except (IndexError, ValueError):
                rating = 0

            try:
                if screenwidth.width() == 1920:
                    res.append(
                        MultiContentEntryPixmapAlphaTest(
                            pos=(
                                10, 90), size=(
                                350, 45), png=loadPNG(png)))
                    res.append(
                        MultiContentEntryPixmapAlphaTest(
                            pos=(
                                10, 90), size=(
                                rating, 45), png=loadPNG(png2)))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                400,
                                90),
                            size=(
                                50,
                                45),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.rating[x]))
                else:
                    res.append(
                        MultiContentEntryPixmapAlphaTest(
                            pos=(
                                5, 80), size=(
                                210, 21), png=loadPNG(png)))
                    res.append(
                        MultiContentEntryPixmapAlphaTest(
                            pos=(
                                5, 80), size=(
                                rating, 21), png=loadPNG(png2)))
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                240,
                                75),
                            size=(
                                50,
                                30),
                            font=24,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT,
                            text=self.rating[x]))
            except IndexError:
                pass

            self.movielist.append(res)

        self['list'].l.setList(self.movielist)
        if screenwidth.width() == 1920:
            self['list'].l.setItemHeight(225)
        else:
            self['list'].l.setItemHeight(150)
        self.ready = True

    def ok(self):
        if self.ready is True:
            if self.first is True:
            
                                      
                                                                                    
                                                                       
                                                  
                                                                                           
                                      
                                                                 
                                                                     
                                                  
                                                                                                
                     
                                                                 
                                                  
                                                                                                
       
                # DEBUG: show what we have
                print("[DEBUG moviesList.ok] Showing ALL options")
                                                    
                print("[DEBUG] Parameters: movie=" + str(self.movie) + ", top=" + str(self.top))

                if self.id and len(self.id) > 0:
                    print("[DEBUG] First ID: " + str(self.id[0]))
                    print("[DEBUG] Is numeric ID: " + str(self.id[0].isdigit()))
                                                    

                # ALWAYS SHOW ALL OPTIONS
                # User decides what to update

                choicelist = [
                    ('Update Movie', 'movie'),
                    ('Update Poster', 'poster'),
                    ('Update Backdrop', 'backdrop'),
                    ('Update Series', 'series'),
                    ('Update Banner', 'banner')
                ]

                # Smart title based on data
                title = _('Update Selection')
                if self.id and len(self.id) > 0:
                    first_id = str(self.id[0])
                    if first_id.isdigit() and len(first_id) >= 4:
                        title = _('Update Movie/Series') + " (TMDb ID: " + first_id + ")"
                                                          
                    else:
                        title = _('Update Movie/Series') + " (TVDb ID: " + first_id + ")"
                                                          

                self.session.openWithCallback(
                    self.smartUpdate,
                    ChoiceBox,
                    title=title,
                    list=choicelist
                )
                                                
            else:
                # Second screen (banner/poster selection)
                c = self['piclist'].getSelectedIndex()
                try:
                    current = self.banner[c]
                except IndexError:
                    current = None

                # Clean temp files
                for i in range(1, 5):
                    filepath = getattr(self, 'banner' + str(i), None)
                    if filepath and fileExists(filepath):
                        try:
                            remove(filepath)
                        except Exception:
                            pass

                self.close(current, self.choice)

            
       
    def smartUpdate(self, choice):
        """Handles all update options with intelligent checks"""
        if choice is None:
            return
            
        self.choice = choice[1]
        print("[DEBUG smartUpdate] User selected: " + self.choice)
        
        try:
            c = self['list'].getSelectedIndex()
            if c < 0 or c >= len(self.id):
                self.session.open(
                    MessageBox,
                    _('Invalid selection'),
                    MessageBox.TYPE_ERROR)
                return
                
            current = self.id[c]
            print("[DEBUG] Selected ID: " + str(current))
            
            # INTELLIGENT CONTROLS BEFORE CONTINUING
            if self.choice in ['poster', 'backdrop', 'movie']:
                # For TMDb, check if the ID is numeric
                if not str(current).strip().isdigit():
                    self.session.open(
                        MessageBox,
                        _('Cannot update with TMDb: ID is not numeric\nThis appears to be a TV series, not a movie.'),
                        MessageBox.TYPE_ERROR)
                    return
                    
            elif self.choice in ['series', 'banner']:
                # For TVDb, check if it looks like a valid ID
                if str(current).strip().isdigit() and len(str(current)) > 5:
                    # Long numeric ID = probably TMDb, not TVDb
                    self.session.open(
                        MessageBox,
                        _('Cannot update with TheTVDb: ID appears to be a movie ID\nTry "Update Movie" instead.'),
                        MessageBox.TYPE_ERROR)
                    return
            
            # OPERATION HANDLING
            if self.choice == 'movie':
                print("[DEBUG] Movie update with TMDb")
                # Clean temporary posters
                for i in range(1, 5):
                    filepath = getattr(self, 'poster' + str(i), None)
                    if filepath and fileExists(filepath):
                        remove(filepath)
                self.close(current, self.choice)
                
            elif self.choice == 'poster':
                print("[DEBUG] Poster update with TMDb")
                movie_id = str(current).strip()
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (
                    movie_id, str(tmdb_api))
                self.getTMDbPosters(url)
                
            elif self.choice == 'backdrop':
                print("[DEBUG] Backdrop update with TMDb")
                movie_id = str(current).strip()
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (
                    movie_id, str(tmdb_api))
                self.getTMDbBackdrops(url)
                
            elif self.choice == 'series':
                print("[DEBUG] Series update with TheTVDb")
                # Clean temporary posters
                for i in range(1, 5):
                    filepath = getattr(self, 'poster' + str(i), None)
                    if filepath and fileExists(filepath):
                        remove(filepath)
                self.close(current, self.choice)
                
            elif self.choice == 'banner':
                print("[DEBUG] Banner update with TheTVDb")
                url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (
                    thetvdb_api, current)
                self.getTVDbBanners(url)
                    
        except Exception as e:
            print('[ERROR smartUpdate] ' + str(e))
            self.session.open(
                MessageBox,
                _('Update error: ') + str(e),
                MessageBox.TYPE_ERROR
            )

                                                
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
                self.session.open(
                    MessageBox,
                    _('All /tmp/posters Cleaned'),
                    MessageBox.TYPE_INFO,
                    timeout=4)
                self.close(current, self.choice)
            elif self.choice == 'poster':
                movie_id = str(current).strip()
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (
                    movie_id, str(tmdb_api))
                self.getTMDbPosters(url)
            elif self.choice == 'backdrop':
                movie_id = str(current).strip()
                url = 'https://api.themoviedb.org/3/movie/%s/images?api_key=%s' % (
                    movie_id, str(tmdb_api))
                self.getTMDbBackdrops(url)
        except Exception as e:
            print('error get ', str(e))

    def preloadBanners(self):
        """Preload banners for all series"""
        print("[DEBUG] === START BANNER PRELOAD ===")
        self.banners_cache = []

        for i, series_id in enumerate(self.id):
            # print("[DEBUG] Loading banner for series " + str(i) + ": " + str(series_id))

            # CALL TO fetchBannersForSeries
            banners = self.fetchBannersForSeries(series_id)

            # print("[DEBUG] fetchBannersForSeries returned: " + str(banners))

            if banners and len(banners) > 0:
                self.banners_cache.append(banners[0])
                print("[DEBUG] Saved in cache[" +
                      str(i) + "]: " + str(banners[0]))
            else:
                self.banners_cache.append(None)
                print("[DEBUG] No banner, saved None in cache[" + str(i) + "]")

        # print("[DEBUG] Final cache: " + str(self.banners_cache))
        print("[DEBUG] === END BANNER PRELOAD ===")

    def showInitialBanner(self):
        """Display the initial banner after everything is loaded"""
        print("[DEBUG] Showing initial banner")
        self.showBannersForIndex(0)
        if hasattr(self, 'startup_timer'):
            self.startup_timer.stop()
            del self.startup_timer

    def showBannersForIndex(self, index=None):
        if index is None:
            index = self['list'].getSelectedIndex()

        # print("[DEBUG] ======= BANNER DEBUG =======")
        # print("[DEBUG] Selected index: " + str(index))

        if not hasattr(self, 'banners_cache'):
            print("[DEBUG] No banners_cache!")
            return

        if index < 0 or index >= len(self.banners_cache):
            print("[DEBUG] Index " + str(index) +
                  " out of range (0-" + str(len(self.banners_cache) - 1) + ")")
            return

        banner_url = self.banners_cache[index]
        # print("[DEBUG] Banner URL for index " + str(index) + ": " + str(banner_url))

        if banner_url:
            # CALCULATE VISUAL POSITION: index % 4
            # This determines WHICH of the 4 banner widgets to use
            visual_position = index % 4
            # print("[DEBUG] Visual position (index % 4): " + str(visual_position))

            # Choose the CORRECT widget
            if visual_position == 0:
                # print("[DEBUG] Downloading to banner1 (top position)")
                self.download(banner_url, self.getBanner1)
            elif visual_position == 1:
                # print("[DEBUG] Downloading to banner2 (second position)")
                self.download(banner_url, self.getBanner2)
            elif visual_position == 2:
                # print("[DEBUG] Downloading to banner3 (third position)")
                self.download(banner_url, self.getBanner3)
            else:  # visual_position == 3
                # print("[DEBUG] Downloading to banner4 (bottom position)")
                self.download(banner_url, self.getBanner4)
        else:
            print("[DEBUG] No banner URL, hiding banner at this position")
            # Hide ONLY the widget for this position
            visual_position = index % 4
            if visual_position == 0:
                self['banner1'].hide()
            elif visual_position == 1:
                self['banner2'].hide()
            elif visual_position == 2:
                self['banner3'].hide()
            else:
                self['banner4'].hide()

        print("[DEBUG] ======= END DEBUG =======\n")

    def hideAllBanners(self):
        """Hide all banner widgets"""
        self['banner1'].hide()
        self['banner2'].hide()
        self['banner3'].hide()
        self['banner4'].hide()

    def showOnlyBanner(self, banner_num):
        """Show only one banner and hide the others"""
        if banner_num == 1:
            self['banner1'].show()
            self['banner2'].hide()
            self['banner3'].hide()
            self['banner4'].hide()
        elif banner_num == 2:
            self['banner1'].hide()
            self['banner2'].show()
            self['banner3'].hide()
            self['banner4'].hide()
        elif banner_num == 3:
            self['banner1'].hide()
            self['banner2'].hide()
            self['banner3'].show()
            self['banner4'].hide()
        else:  # banner_num == 4
            self['banner1'].hide()
            self['banner2'].hide()
            self['banner3'].hide()
            self['banner4'].show()

    def downloadAndShowBanner(self, banner_url, index):
        """Download and display a banner"""
        print(
            "[DEBUG] Download banner: " +
            str(banner_url) +
            " for index " +
            str(index))

        if index == 0:
            banner_file = self.banner1
        elif index == 1:
            banner_file = self.banner2
        elif index == 2:
            banner_file = self.banner3
        elif index == 3:
            banner_file = self.banner4
        else:
            banner_file = "/tmp/banner_" + str(index) + ".jpg"

        downloadPage(
            banner_url.encode(),
            banner_file).addCallback(
            lambda result,
            idx=index: self.onBannerDownloaded(idx)).addErrback(
            lambda failure: print(
                "[ERROR] Banner download failed: " +
                str(failure)))

    def onBannerDownloaded(self, index):
        """Callback when the banner is downloaded"""
        print("[DEBUG] Banner downloaded for index " + str(index))

        if index == 0:
            self['banner1'].instance.setPixmapFromFile(self.banner1)
        elif index == 1:
            self['banner2'].instance.setPixmapFromFile(self.banner2)
        elif index == 2:
            self['banner3'].instance.setPixmapFromFile(self.banner3)
        elif index == 3:
            self['banner4'].instance.setPixmapFromFile(self.banner4)

        print("[DEBUG] Banner displayed for index " + str(index))

    def getTMDbPosters(self, url):
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTMDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        try:
            if isinstance(output, bytes):
                try:
                    output = output.decode("utf-8", "ignore")
                except Exception as e:
                    print("Decode error for URL {}: {}".format(url, str(e)))
                    output = output.decode("latin-1", "ignore")

            output = sub(r'"backdrops".*?"posters"', '', output, flags=S)
            output = sub(
                r'"file_path":"',
                '"file_path":"https://image.tmdb.org/t/p/w185',
                output)
            self.banner = findall(r'"file_path":"(.*?)"', output)
            self.makeList()

        except Exception as e:
            print('Error in getTMDbPosters: ', str(e))

    def getTMDbBackdrops(self, url):
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTMDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception as e:
                print("Decode error for URL {}: {}".format(url, str(e)))
                output = output.decode("latin-1", "ignore")

        output = output + 'FIN'
        output = sub(r'"posters".*?FIN', '', output, flags=S)
        output = sub(
            r'"file_path":"',
            '"file_path":"https://image.tmdb.org/t/p/w1280',
            output)
        self.banner = findall(r'"file_path":"(.*?)"', output)
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
                url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (
                    thetvdb_api, current)
                self.getTVDbBanners(url)
            elif self.choice == 'backdrop':
                url = 'https://thetvdb.com/api/%s/series/%s/banners.xml' % (
                    thetvdb_api, current)
                self.getTVDbBackdrops(url)
        except Exception as e:
            print('error get ', str(e))

    def getTVDbBanners(self, url):
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTheTVDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception:
                output = output.decode("latin-1", "ignore")

        # 1. Convert paths into full URLs
        output = sub(
            r'<BannerPath>(v4/)',
            r'<BannerPath>https://artworks.thetvdb.com/banners/\1',
            output
        )

        # 2. Extract ONLY poster-type paths (680x1000)
        self.banner = findall(
            r'<BannerPath>(https://artworks\.thetvdb\.com/banners/.*?)</BannerPath>.*?<BannerType2>680x1000</BannerType2>',
            output,
            flags=S)

        # Fallback: also search for <BannerType>poster</BannerType>
        if not self.banner:
            self.banner = findall(
                r'<BannerPath>(https://artworks\.thetvdb\.com/banners/.*?)</BannerPath>.*?<BannerType>poster</BannerType>',
                output,
                flags=S)

        print("[DEBUG] getTVDbBanners found " +
              str(len(self.banner)) + " banners")
        self.makeList()

    def getTVDbBackdrops(self, url):
        output = fetch_url(url)
        if output is None:
            self.session.open(
                MessageBox,
                _('\nTheTVDb API Server is not reachable.'),
                MessageBox.TYPE_ERROR)
            return None

        if isinstance(output, bytes):
            try:
                output = output.decode("utf-8", "ignore")
            except Exception:
                output = output.decode("latin-1", "ignore")

        # 1. Convert relative paths into full URLs
        output = sub(
            r'<BannerPath>(v4/)',
            r'<BannerPath>https://artworks.thetvdb.com/banners/\1',
            output
        )

        # 2. Extract ONLY fanart-type paths (1920x1080)
        self.banner = findall(
            r'<BannerPath>(https://artworks\.thetvdb\.com/banners/.*?)</BannerPath>.*?<BannerType2>1920x1080</BannerType2>',
            output,
            flags=S)

        # Fallback: also search for <BannerType>fanart</BannerType>
        if not self.banner:
            self.banner = findall(
                r'<BannerPath>(https://artworks\.thetvdb\.com/banners/.*?)</BannerPath>.*?<BannerType>fanart</BannerType>',
                output,
                flags=S)

        print("[DEBUG] getTVDbBackdrops found " +
              str(len(self.banner)) + " backdrops")
        self.makeList()

    def fetchBannersForSeries(self, series_id):
        """Find horizontal banners (fanart)"""
        url = 'https://www.thetvdb.com/api/' + \
            str(thetvdb_api) + '/series/' + str(series_id) + '/banners.xml'
        print(
            "[DEBUG] === FETCH BANNERS for series " +
            str(series_id) +
            " ===")

        output = fetch_url(url)
        if output is None:
            print("[DEBUG] No response from API")
            return []

        if isinstance(output, bytes):
            output = output.decode("utf-8", "ignore")

        banners = []

        # Split the XML into sections for each banner
        banner_sections = output.split('</Banner>')

        for section in banner_sections:
            if '<BannerPath>' in section and '<BannerType2>' in section:
                # Extract BannerPath
                banner_path_start = section.find(
                    '<BannerPath>') + len('<BannerPath>')
                banner_path_end = section.find(
                    '</BannerPath>', banner_path_start)

                # Extract BannerType2 (size)
                banner_type2_start = section.find(
                    '<BannerType2>') + len('<BannerType2>')
                banner_type2_end = section.find(
                    '</BannerType2>', banner_type2_start)

                if banner_path_start > 0 and banner_path_end > 0:
                    banner_path = section[banner_path_start:banner_path_end].strip(
                    )

                    if banner_type2_start > 0 and banner_type2_end > 0:
                        banner_type2 = section[banner_type2_start:banner_type2_end].strip(
                        )

                        # Check if horizontal (e.g., 1920x1080)
                        if 'x' in banner_type2:
                            try:
                                width, height = banner_type2.split('x')
                                width = int(width)
                                height = int(height)

                                # Look for horizontal FANART
                                if width > height and width >= 1000:
                                    print(
                                        "[DEBUG] Found horizontal fanart: " +
                                        banner_path +
                                        " (" +
                                        str(width) +
                                        "x" +
                                        str(height) +
                                        ")")
                                    banners.append(banner_path)
                            except BaseException:
                                pass

        # If no fanart found, look for any banner containing "fanart/"
        if not banners:
            for section in banner_sections:
                if '<BannerPath>' in section:
                    banner_path_start = section.find(
                        '<BannerPath>') + len('<BannerPath>')
                    banner_path_end = section.find(
                        '</BannerPath>', banner_path_start)

                    if banner_path_start > 0 and banner_path_end > 0:
                        banner_path = section[banner_path_start:banner_path_end].strip(
                        )

                        # Look for paths containing "fanart/"
                        if 'fanart/' in banner_path.lower():
                            print("[DEBUG] Found fanart path: " + banner_path)
                            banners.append(banner_path)

        print("[DEBUG] Total banners found: " + str(len(banners)))

        # Return only the first banner (or empty list)
        if banners:
            return [banners[0]]
        else:
            return []

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
                res.append(
                    MultiContentEntryText(
                        pos=(
                            5,
                            0),
                        size=(
                            1240,
                            225),
                        font=30,
                        color=0xFFFFFF,
                        backcolor_sel=0x0043ac,
                        color_sel=0xFFFFFF,
                        flags=RT_HALIGN_LEFT,
                        text=''))
                self.imagelist.append(res)
                self['piclist'].l.setList(self.imagelist)
                self['piclist'].l.setItemHeight(225)

            else:
                res.append(
                    MultiContentEntryText(
                        pos=(
                            5,
                            0),
                        size=(
                            710,
                            125),
                        font=26,
                        color=0xFFFFFF,
                        backcolor_sel=0x0043ac,
                        color_sel=0xFFFFFF,
                        flags=RT_HALIGN_LEFT,
                        text=''))
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
                    widget = "poster" + \
                        str(i + 1) if is_poster else "banner" + str(i + 1)
                    try:
                        item = self.poster[idx] if is_poster else self.banner[idx]
                        callback = getattr(
                            self, "getPoster" + str(i + 1)) if is_poster else getattr(self, "getBanner" + str(i + 1))
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
                    widget = "poster" + \
                        str(i + 1) if is_poster else "banner" + str(i + 1)
                    try:
                        item = self.poster[idx] if is_poster else self.banner[idx]
                        callback = getattr(
                            self, "getPoster" + str(i + 1)) if is_poster else getattr(self, "getBanner" + str(i + 1))
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
        with open(self.poster1, 'wb') as file:
            file.write(output)
        self.showPoster1(self.poster1)

    def showPoster1(self, poster1):
        if fileExists(poster1):
            self["poster1"].instance.setScale(1)
            self["poster1"].instance.setPixmapFromFile(poster1)
            self['poster1'].show()
        return

    def getPoster2(self, output):
        with open(self.poster2, 'wb') as file:
            file.write(output)
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        if fileExists(poster2):
            self["poster2"].instance.setScale(1)
            self["poster2"].instance.setPixmapFromFile(poster2)
            self['poster2'].show()
        return

    def getPoster3(self, output):
        with open(self.poster3, 'wb') as file:
            file.write(output)
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        if fileExists(poster3):
            self["poster3"].instance.setScale(1)
            self["poster3"].instance.setPixmapFromFile(poster3)
            self['poster3'].show()
        return

    def getPoster4(self, output):
        with open(self.poster4, 'wb') as file:
            file.write(output)
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        if fileExists(poster4):
            self["poster4"].instance.setScale(1)
            self["poster4"].instance.setPixmapFromFile(poster4)
            self['poster4'].show()
        return

    def getBanner1(self, output):
        with open(self.banner1, 'wb') as file:
            file.write(output)
        self.showBanner1(self.banner1)

    def showBanner1(self, banner1):
        if fileExists(banner1):
            self["banner1"].instance.setScale(1)
            self["banner1"].instance.setPixmapFromFile(banner1)
            self['banner1'].show()
        return

    def getBanner2(self, output):
        with open(self.banner2, 'wb') as file:
            file.write(output)
        self.showBanner2(self.banner2)

    def showBanner2(self, banner2):
        if fileExists(banner2):
            self["banner2"].instance.setScale(1)
            self["banner2"].instance.setPixmapFromFile(banner2)
            self['banner2'].show()
        return

    def getBanner3(self, output):
        with open(self.banner3, 'wb') as file:
            file.write(output)
        self.showBanner3(self.banner3)

    def showBanner3(self, banner3):
        if fileExists(banner3):
            self["banner3"].instance.setScale(1)
            self["banner3"].instance.setPixmapFromFile(banner3)
            self['banner3'].show()
        return

    def getBanner4(self, output):
        with open(self.banner4, 'wb') as file:
            file.write(output)
        self.showBanner4(self.banner4)

    def showBanner4(self, banner4):
        if fileExists(banner4):
            self["banner4"].instance.setScale(1)
            self["banner4"].instance.setPixmapFromFile(banner4)
            self['banner4'].show()
        return

    def download(self, link, name):
        try:
            link_str = link.decode(
                'utf-8') if PY3 and isinstance(link, bytes) else str(link)

            print("[DEBUG] download original link: " + link_str)

            # --- 1. CONVERT V4 PATHS ---
            if link_str.startswith('v4/'):
                link_str = 'https://artworks.thetvdb.com/banners/' + link_str
                print("[DEBUG] Converted v4/ path: " + link_str)

            # --- 2. CONVERT OLD PATHS (fanart/, posters/, etc.) ---
            elif (link_str.startswith('fanart/') or
                  link_str.startswith('posters/') or
                  link_str.startswith('graphical/') or
                  link_str.startswith('season/')):
                link_str = 'https://artworks.thetvdb.com/banners/' + link_str
                print("[DEBUG] Converted old path: " + link_str)

            # --- 3. HANDLE LOCAL PATHS ---
            if link_str.startswith('/'):
                print("[DEBUG] Local path: " + link_str)
                try:
                    with open(link_str, 'rb') as f:
                        data = f.read()
                    name(data)
                except Exception as e:
                    print("[ERROR] Local file read failed: " + str(e))
                    self.downloadError(str(e))
                return

            # --- 4. REMOVE _cache/ IF PRESENT ---
            if '_cache/' in link_str:
                link_str = link_str.replace('_cache/', '')
                print("[DEBUG] Removed _cache: " + link_str)

            # --- 5. FIX DOMAIN ---
            if 'www.thetvdb.com/banners' in link_str:
                link_str = link_str.replace(
                    'www.thetvdb.com/banners',
                    'artworks.thetvdb.com/banners')

            print("[DEBUG] final download URL: " + link_str)

            # Headers
            if ('themoviedb.org' in link_str) or (
                    'api.themoviedb.org' in link_str):
                headers_to_use = agents_json
            else:
                headers_to_use = agents

            if PY3 and isinstance(link_str, str):
                link = link_str.encode('utf-8')

            callInThread(
                threadGetPage,
                url=link,
                file=None,
                key=None,
                success=name,
                fail=self.downloadError,
                custom_headers=headers_to_use)

        except Exception as e:
            print("Error in download method: " + str(e))

    def downloadError(self, output=None):
        if output:
            print(
                "[MovieBrowser] Download error: {}".format(
                    str(output)[
                        :100]))
        else:
            print("[MovieBrowser] Download error")

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
        skin = join(skin_path, "filterList.xml")
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
        self.hideflag = True
        self.filter = filter
        self.setTitle(titel)
        self.list = list
        self.listentries = []
        self['list'] = ItemList([])
        self['actions'] = ActionMap(
            [
                'OkCancelActions',
                'DirectionActions',
                'ColorActions',
                'ChannelSelectBaseActions',
                'HelpActions',
                'NumberActions'
            ],
            {
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
            }, -1
        )
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        idx = 0
        for x in self.list:
            idx += 1

        for i in range(idx):
            try:
                res = ['']
                if screenwidth.width() == 1920:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                10,
                                0),
                            size=(
                                1240,
                                40),
                            font=30,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=self.list[i]))
                else:
                    res.append(
                        MultiContentEntryText(
                            pos=(
                                5,
                                0),
                            size=(
                                700,
                                30),
                            font=26,
                            color=0xFFFFFF,
                            backcolor_sel=0x0043ac,
                            color_sel=0xFFFFFF,
                            flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER,
                            text=self.list[i]))
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
        self.listentries = []
        totalSeasons = len(self.list)

        if screenwidth.width() == 1920:
            font_size = 30
            pos_x = 10
            size = (760, 40)
        else:
            font_size = 26
            pos_x = 5
            size = (510, 30)

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
        current = sub(r'(?i)specials', '(S00', current)
        current = sub(r'(?i)season ', '(S', current)
        self.close(current)

    def resetFilter(self):
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
        skin = join(skin_path, "getABC.xml")
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
            self.field = group[0]
        else:
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
            content = f.read()
        self.skin = content

        Screen.__init__(self, session)
        self['select_1'] = Pixmap()
        self['select_2'] = Pixmap()
        self['select_3'] = Pixmap()
        self['select_1'].hide()
        self['select_2'].hide()
        self['select_3'].hide()

        if mode == 'content':
            self['label_1'] = Label('MOVIES')
            self['label_2'] = Label('SERIES')
            self['label_3'] = Label('MOVIES & SERIES')
            self['label_select_1'] = Label('MOVIES')
            self['label_select_2'] = Label('SERIES')
            self['label_select_3'] = Label('MOVIES & SERIES')
        else:
            self['label_1'] = Label('METRIX')
            self['label_2'] = Label('BACKDROP')
            self['label_3'] = Label('POSTERWALL')
            self['label_select_1'] = Label('METRIX')
            self['label_select_2'] = Label('BACKDROP')
            self['label_select_3'] = Label('POSTERWALL')

        self['label_select_1'].hide()
        self['label_select_2'].hide()
        self['label_select_3'].hide()

        self.mode = mode
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

        self["actions"] = ActionMap(
            ['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions'],
            {
                'ok': self.returnNumber,
                'cancel': self.quit,
                'down': self.next,
                'up': self.prev,
                'red': self.next,
                '5': self.next
            }, -1
        )

        self.Timer = eTimer()
        self.Timer.callback.append(self.returnNumber)
        self.Timer.start(2500, True)

    def next(self):
        self.Timer.start(2000, True)

        if self.number == 1:
            self['label_select_1'].hide()
            self['select_1'].hide()
            self['label_1'].show()
            self['label_2'].hide()
            self['select_2'].show()
            self['label_select_2'].show()
            self.number = 2
        elif self.number == 2:
            self['label_select_2'].hide()
            self['select_2'].hide()
            self['label_2'].show()
            self['label_3'].hide()
            self['select_3'].show()
            self['label_select_3'].show()
            self.number = 3
        elif self.number == 3:
            self['label_select_3'].hide()
            self['select_3'].hide()
            self['label_3'].show()
            self['label_1'].hide()
            self['select_1'].show()
            self['label_select_1'].show()
            self.number = 1

    def prev(self):
        self.Timer.start(2000, True)

        if self.number == 1:
            self['label_select_1'].hide()
            self['select_1'].hide()
            self['label_1'].show()
            self['label_3'].hide()
            self['select_3'].show()
            self['label_select_3'].show()
            self.number = 3
        elif self.number == 2:
            self['label_select_2'].hide()
            self['select_2'].hide()
            self['label_2'].show()
            self['label_1'].hide()
            self['select_1'].show()
            self['label_select_1'].show()
            self.number = 1
        elif self.number == 3:
            self['label_select_3'].hide()
            self['select_3'].hide()
            self['label_3'].show()
            self['label_2'].hide()
            self['select_2'].show()
            self['label_select_2'].show()
            self.number = 2

    def returnNumber(self):
        self.Timer.stop()
        self.close(self.number)

    def quit(self):
        self.Timer.stop()
        self.close(None)


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
        return "\n".join(line for line in lines)

    def close(self):
        self.close()


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
            session.open(
                movieBrowserMetrix,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
        elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
            session.open(
                movieBrowserBackdrop,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
        else:
            session.open(
                movieBrowserPosterwall,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
    elif config.plugins.moviebrowser.style.value == 'metrix':
        session.open(
            movieBrowserMetrix,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)
    elif config.plugins.moviebrowser.style.value == 'backdrop':
        session.open(
            movieBrowserBackdrop,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)
    else:
        session.open(
            movieBrowserPosterwall,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)


def mainInfoBar(session, **kwargs):
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
            infobarsession.open(
                movieBrowserMetrix,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
        elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
            infobarsession.open(
                movieBrowserBackdrop,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
        else:
            infobarsession.open(
                movieBrowserPosterwall,
                0,
                ':::Series:Top:::',
                ':::Series:Top:::')
    elif config.plugins.moviebrowser.style.value == 'metrix':
        infobarsession.open(
            movieBrowserMetrix,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)
    elif config.plugins.moviebrowser.style.value == 'backdrop':
        infobarsession.open(
            movieBrowserBackdrop,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)
    else:
        infobarsession.open(
            movieBrowserPosterwall,
            0,
            config.plugins.moviebrowser.filter.value,
            config.plugins.moviebrowser.filter.value)


def menu(menuid, **kwargs):
    if menuid == 'mainmenu':
        return [('Movie Browser', main, 'moviebrowser', 42)]
    return []


infobarsession = None
timerupdate = timerUpdate()


def autostart(reason, **kwargs):
    global infobarsession
    if 'session' in kwargs:
        info = _('*******Movie Browser Database Update*******\n')
        with open(UPDATE_LOG_PATH, 'w', encoding='utf-8') as f:
            f.write(info)
        if config.plugins.moviebrowser.videobutton.value is True:
            infobarsession = kwargs['session']
            from Screens.InfoBar import InfoBar
            InfoBar.showMovies = mainInfoBar
        if config.plugins.moviebrowser.timerupdate.value is True:
            with open(TIMER_LOG_PATH, 'w', encoding='utf-8') as f:
                f.close()
            session = kwargs['session']
            timerupdate.saveSession(session)
            try:
                timerupdate.start()
            except BaseException:
                error = exc_info()[1]
                errortype = exc_info()[0]
                now = str(
                    datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                result = _('*******Movie Browser Database Update*******\nTime: %s\nError: %s\nReason: %s') % (
                    now, str(errortype), str(error))
                print(result)
                with open(UPDATE_LOG_PATH, 'w', encoding='utf-8') as f:
                    f.write(result)

        if exists(DATABASE_PATH):
            with open(DATABASE_PATH, 'r', encoding='utf-8') as data:
                data = data.read()
                data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
            folder = DATABASE_CACHE
            count = 0
            now = str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            for root, dirs, files in walk(
                    folder, topdown=False, onerror=None):
                for name in files:
                    shortname = sub(r'[.]jpg', '', name)
                    shortname = sub(r'[.]m1v', '', shortname)
                    if search(shortname, data) is None:
                        filename = join(root, name)
                        if fileExists(filename):
                            remove(filename)
                            count += 1
            del data
            end = str(
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            info = _(
                '*******Cleanup Cache Folder*******\nStart time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
        with open(CLEANUP_LOG_PATH, 'w', encoding='utf-8') as f:
            f.write(info)
    return


def Plugins(**kwargs):
    from Plugins.Plugin import PluginDescriptor
    plugindesc = _("Manage your Movies & Series V.%s" % str(version))
    pluginname = "Movie Browser"
    plugin_list = [
        PluginDescriptor(
            name=pluginname, description=plugindesc, where=[
                PluginDescriptor.WHERE_PLUGINMENU], icon="plugin.png", fnc=main), PluginDescriptor(
            name=pluginname, description=plugindesc, where=[
                PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main), PluginDescriptor(
            name=pluginname, description=plugindesc, where=[
                PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)]
    if config.plugins.moviebrowser.showmenu.value:
        plugin_list.append(
            PluginDescriptor(
                name=pluginname,
                description=plugindesc,
                where=[
                    PluginDescriptor.WHERE_MENU],
                fnc=menu))
    return plugin_list
