#!/usr/bin/python
# -*- coding: latin-1 -*-

# 20221004 Kiddac edit: python 3 support et al
# 20221204 Lululla edit & add: language, config, major fix
# 2022 Twol add ......callInThread ....getMountDefault
from __future__ import print_function
from . import _
from Components.ActionMap import ActionMap
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Harddisk import harddiskmanager
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryPixmapAlphaTest
from Components.MultiContent import MultiContentEntryText
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from Components.config import ConfigSelection, ConfigText
# from Components.config import ConfigDirectory
# from Components.config import ConfigSlider
from Components.config import ConfigSubsection  # , ConfigOnOff
from Components.config import config, configfile, ConfigClock
from Components.config import NoSave, getConfigListEntry
from Plugins.Plugin import PluginDescriptor
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists
from enigma import RT_HALIGN_CENTER, RT_VALIGN_CENTER
from enigma import RT_HALIGN_LEFT
# from enigma import RT_WRAP
from enigma import eConsoleAppContainer
from enigma import eListboxPythonMultiContent, ePoint
from enigma import eServiceReference, eTimer
from enigma import getDesktop, gFont, iPlayableService
from enigma import iServiceInformation, loadPNG  # , loadPic
from requests import get
# from requests import exceptions
from requests.exceptions import HTTPError
from twisted.internet.reactor import callInThread
# from twisted.web.client import getPage, downloadPage
import datetime
import os
import re
from re import search
from re import sub
import sys
import math
#
from enigma import gPixmapPtr
# from Components.AVSwitch import AVSwitch
# from enigma import ePicLoad

try:
    from urllib2 import Request, urlopen
except:
    from urllib.request import urlopen, Request

try:
    import statvfs
except:
    from os import statvfs


def getDesktopSize():
    from enigma import getDesktop
    s = getDesktop(0).size()
    return (s.width(), s.height())


def isFHD():
    desktopSize = getDesktopSize()
    return desktopSize[0] == 1920


def isDreamOS():
    isDreamOS = False
    if os.path.exists('/var/lib/dpkg/status'):
        isDreamOS = True
    return isDreamOS


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes // p, 2)
    return "%s %s" % (s, size_name[i])


def threadGetPage(url=None, file=None, key=None, success=None, fail=None, *args, **kwargs):
    print('[MovieBrowser][threadGetPage] url, file, key, args, kwargs', url, "   ", file, "   ", key, "   ", args, "   ", kwargs)
    try:
        response = get(url)
        response.raise_for_status()
        # print("[MovieBrowser][threadGetPage] content=", response.content)
        if file is None:
            success(response.content)
        elif key is not None:
            success(response.content, file, key)
        else:
            success(response.content, file)
    except HTTPError as httperror:
        print('[MovieBrowser][threadGetPage] Http error: ', httperror)
        fail(error)  # E0602 undefined name 'error' [pyflakes]
    except Exception as error:
        print('[MovieBrowser][threadGetPage] error: ', error)
        if fail is not None:
            fail(error)


version = '3.7rc6'
screenwidth = getDesktop(0).size()
dir_plugins = "/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/"
pythonVer = sys.version_info.major
dbmovie = '%sdb/database' % dir_plugins
dbreset = '%sdb/reset' % dir_plugins
dbcache = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/cache'
dbhddcache = '/media/hdd/moviebrowser/cache'
dbusbcache = '/media/usb/moviebrowser/cache'
blacklistmovie = '%sdb/blacklist' % dir_plugins
filtermovie = '%sdb/filter' % dir_plugins
lastfile = '%sdb/last' % dir_plugins
updatelog = '%slog/update.log' % dir_plugins
timerlog = '%slog/timer.log' % dir_plugins
cleanuplog = '%slog/cleanup.log' % dir_plugins
skin_directory = "%sskin/hd/" % (dir_plugins)
if isFHD():
    skin_directory = "%sskin/fhd/" % (dir_plugins)
default_backdrop = '%spic/browser/default_backdrop.png' % skin_directory
default_folder = '%spic/browser/default_folder.png' % skin_directory
default_poster = '%spic/browser/default_poster.png' % skin_directory
default_banner = '%spic/browser/default_banner.png' % skin_directory
wiki_png = '%spic/browser/wiki.png' % skin_directory
tmdb_api_key = 'dfc629f7ff6936a269f8c5cdb194c890'
thetvdb_api_key = 'D19315B88B2DE21F'
folders = os.listdir(skin_directory)
if "pic" in folders:
    folders.remove("pic")


class ItemList(MenuList):
    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        if isFHD():
            self.l.setItemHeight(50)
            self.l.setFont(36, gFont('Regular', 36))
            self.l.setFont(32, gFont('Regular', 32))
            self.l.setFont(28, gFont('Regular', 28))
            self.l.setFont(26, gFont('Regular', 26))
            self.l.setFont(24, gFont('Regular', 24))
            self.l.setFont(22, gFont('Regular', 22))
            self.l.setFont(20, gFont('Regular', 20))
            # textfont = int(34)
            # self.l.setFont(0, gFont('Regular', textfont))
        else:
            self.l.setItemHeight(35)
            self.l.setFont(32, gFont('Regular', 32))
            self.l.setFont(28, gFont('Regular', 28))
            self.l.setFont(26, gFont('Regular', 26))
            self.l.setFont(24, gFont('Regular', 24))
            self.l.setFont(22, gFont('Regular', 22))
            self.l.setFont(20, gFont('Regular', 20))
            # textfont = int(24)
            # self.l.setFont(0, gFont('Regular', textfont))


def getMountChoices():
    choices = []
    for p in harddiskmanager.getMountedPartitions():
        if os.path.exists(p.mountpoint):
            d = os.path.normpath(p.mountpoint)
            if p.mountpoint != "/":
                choices.append((p.mountpoint, d))
    choices.sort()
    return choices


def getMountDefault(choices):
    choices = {x[1]: x[0] for x in choices}
    default = choices.get("/media/hdd") or choices.get("/media/usb")
    # print("[MovieBrowser][getMountDefault] default, choices", default, "   ", choices)
    return default


choices = getMountChoices()
config.plugins.moviebrowser = ConfigSubsection()
lang = language.getLanguage()[:2]
config.plugins.moviebrowser.language = ConfigSelection(default=lang, choices=[
        ('en', 'English'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('it', 'Italian'),
        ('fr', 'French'),
        ('ru', 'Russian')
    ])
config.plugins.moviebrowser.filter = ConfigSelection(default=':::Movie:Top:::', choices=[(':::Movie:Top:::', _('Movies')), (':::Series:Top:::', _('Series')), (':Top:::', _('Movies & Series'))])
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
config.plugins.moviebrowser.backdrops = ConfigSelection(default='info', choices=[('info', _('Info Button')), ('auto', _('Automatic')), ('hide', _('Hide'))])
config.plugins.moviebrowser.m1v = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.download = ConfigSelection(default='update', choices=[('access', _('On First Access')), ('update', _('On Database Update'))])
if config.plugins.moviebrowser.m1v.value == 'yes':
    config.plugins.moviebrowser.showtv = ConfigSelection(default='hide', choices=[('show', _('Show')), ('hide', _('Hide'))])
else:
    config.plugins.moviebrowser.showtv = ConfigSelection(default='show', choices=[('show', _('Show')), ('hide', _('Hide'))])
config.plugins.moviebrowser.showswitch = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.showmenu = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.videobutton = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.lastmovie = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No')), ('folder', _('Folder Selection'))])
config.plugins.moviebrowser.lastfilter = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.showfolder = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
# config.plugins.moviebrowser.autocheck = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])

config.plugins.moviebrowser.skin = ConfigSelection(default='default', choices=folders)
skin_path = "%s%s/" % (skin_directory, config.plugins.moviebrowser.skin.value)
config.plugins.moviebrowser.plotfull = ConfigSelection(default='show', choices=[('hide', _('Info Button')), ('show', _('Automatic'))])

config.plugins.moviebrowser.timerupdate = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.timer = ConfigClock(default=6 * 3600)
config.plugins.moviebrowser.hideupdate = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])

config.plugins.moviebrowser.reset = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.style = ConfigSelection(default='metrix', choices=[('metrix', 'Metrix'), ('backdrop', 'Backdrop'), ('posterwall', 'Posterwall')])
config.plugins.moviebrowser.seriesstyle = ConfigSelection(default='metrix', choices=[('metrix', 'Metrix'), ('backdrop', 'Backdrop'), ('posterwall', 'Posterwall')])

# config.plugins.moviebrowser.data = NoSave(ConfigOnOff(default=False))
config.plugins.moviebrowser.api = NoSave(ConfigSelection(['-> Ok']))
config.plugins.moviebrowser.txtapi = ConfigText(default=tmdb_api_key, visible_width=60, fixed_size=False)
config.plugins.moviebrowser.tvdbapi = NoSave(ConfigSelection(['-> Ok']))
config.plugins.moviebrowser.txttvdbapi = ConfigText(default=thetvdb_api_key, visible_width=60, fixed_size=False)

# config.plugins.moviebrowser.moviefolder = ConfigDirectory(default='/media/hdd/')
config.plugins.moviebrowser.moviefolder = ConfigSelection(choices=choices, default=getMountDefault(choices))
config.plugins.moviebrowser.cachefolder = ConfigSelection(default=dbcache, choices=[(dbusbcache, '/media/usb'), (dbhddcache, '/media/hdd'), (dbcache, 'Default')])
config.plugins.moviebrowser.cleanup = ConfigSelection(default='no', choices=[('no', 'NO'), ('yes', '<Cleanup>')])
config.plugins.moviebrowser.backup = ConfigSelection(default='no', choices=[('no', 'NO'), ('yes', '<Backup>')])
config.plugins.moviebrowser.restore = ConfigSelection(default='no', choices=[('no', 'NO'), ('yes', '<Restore>')])
# if config.plugins.moviebrowser.backup.value == 'yes':
    # config.plugins.moviebrowser.restore = ConfigSelection(default='no', choices=[('no', 'NO'), ('no', '<Restore>')])
# if config.plugins.moviebrowser.restore.value == 'yes':
    # config.plugins.moviebrowser.backup = ConfigSelection(default='no', choices=[('no', 'NO'), ('no', '<Backup>')])

config.plugins.moviebrowser.color = ConfigSelection(default='#007895BC', choices=[
    ('#007895BC', 'Default'),
    ('#00F0A30A', 'Amber'),
    ('#00825A2C', 'Brown'),
    ('#000050EF', 'Cobalt'),
    ('#00911D10', 'Crimson'),
    ('#001BA1E2', 'Cyan'),
    ('#00008A00', 'Emerald'),
    ('#0070AD11', 'Green'),
    ('#006A00FF', 'Indigo'),
    ('#00A4C400', 'Lime'),
    ('#00A61D4D', 'Magenta'),
    ('#0076608A', 'Mauve'),
    ('#006D8764', 'Olive'),
    ('#00C3461B', 'Orange'),
    ('#00F472D0', 'Pink'),
    ('#00E51400', 'Red'),
    ('#007A3B3F', 'Sienna'),
    ('#00647687', 'Steel'),
    ('#00149BAF', 'Teal'),
    ('#004176B6', 'Tufts'),
    ('#006C0AAB', 'Violet'),
    ('#00BF9217', 'Yellow')
])

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


def applySkinVars(skin, dict):
    for key in dict.keys():
        try:
            skin = skin.replace('{' + key + '}', dict[key])
        except Exception as e:
            print(e, '@key=', key)
    return skin


def transHTML(text):
    text = text.replace('&nbsp;', ' ').replace('&szlig;', 'ss').replace('&quot;', '"').replace('&ndash;', '-').replace('&Oslash;', '').replace('&bdquo;', '"').replace('&ldquo;', '"').replace('&rsquo;', "'").replace('&gt;', '>').replace('&lt;', '<')
    text = text.replace('&copy;.*', ' ').replace('&amp;', '&').replace('&uuml;', '\xc3\x83\xc2\xbc').replace('&auml;', '\xc3\x83\xc2\xa4').replace('&ouml;', '\xc3\x83\xc2\xb6').replace('&eacute;', '\xc3\xa9').replace('&hellip;', '...').replace('&egrave;', '\xc3\xa8').replace('&agrave;', '\xc3\xa0')
    text = text.replace('&Uuml;', 'Ue').replace('&Auml;', 'Ae').replace('&Ouml;', 'Oe').replace('&#034;', '"').replace('&#34;', '"').replace('&#38;', 'und').replace('&#039;', "'").replace('&#39;', "'").replace('&#133;', '...').replace('&#196;', '\xc3\x83\xe2\x80\x9e').replace('&#214;', '\xc3\x83\xe2\x80\x93').replace('&#220;', '\xc3\x83\xc5\x93').replace('&#223;', '\xc3\x83\xc5\xb8').replace('&#228;', '\xc3\x83\xc2\xa4').replace('&#246;', '\xc3\x83\xc2\xb6').replace('&#252;', '\xc3\x83\xc2\xbc')
    return text


def transMOVIE(text):
    text = text.lower() + '+FIN'
    text = text.replace('  ', '+').replace(' ', '+').replace('&', '+').replace(':', '+').replace('_', '+').replace('.', '+').replace('"', '+').replace('(', '+').replace(')', '+').replace('[', '+').replace(']', '+').replace('!', '+').replace('++++', '+').replace('+++', '+').replace('++', '+')
    text = text.replace('+720p+', '++').replace('+1080i+', '+').replace('+1080p+', '++').replace('+dtshd+', '++').replace('+dtsrd+', '++').replace('+dtsd+', '++').replace('+dts+', '++').replace('+dd5+', '++').replace('+5+1+', '++').replace('+3d+', '++').replace('+ac3d+', '++').replace('+ac3+', '++').replace('+avchd+', '++').replace('+avc+', '++').replace('+dubbed+', '++').replace('+subbed+', '++').replace('+stereo+', '++')
    text = text.replace('+x264+', '++').replace('+mpeg2+', '++').replace('+avi+', '++').replace('+xvid+', '++').replace('+blu+', '++').replace('+ray+', '++').replace('+bluray+', '++').replace('+3dbd+', '++').replace('+bd+', '++').replace('+bdrip+', '++').replace('+dvdrip+', '++').replace('+rip+', '++').replace('+hdtv+', '++').replace('+hddvd+', '++')
    text = text.replace('+german+', '++').replace('+ger+', '++').replace('+english+', '++').replace('+eng+', '++').replace('+spanish+', '++').replace('+spa+', '++').replace('+italian+', '++').replace('+ita+', '++').replace('+russian+', '++').replace('+rus+', '++').replace('+dl+', '++').replace('+dc+', '++').replace('+sbs+', '++').replace('+se+', '++').replace('+ws+', '++').replace('+cee+', '++')
    text = text.replace('+remux+', '++').replace('+directors+', '++').replace('+cut+', '++').replace('+uncut+', '++').replace('+extended+', '++').replace('+repack+', '++').replace('+unrated+', '++').replace('+rated+', '++').replace('+retail+', '++').replace('+remastered+', '++').replace('+edition+', '++').replace('+version+', '++')
    text = sub('\\+tt[0-9]+\\+', '++', text)
    text = sub('\\+\\+\\+\\+.*?FIN', '', text)
    text = sub('\\+FIN', '', text)
    return text


def transSERIES(text):
    text = text.lower() + '+FIN'
    text = text.replace('  ', '+').replace(' ', '+').replace('&', '+').replace(':', '+').replace('_', '+').replace('u.s.', 'us').replace('l.a.', 'la').replace('.', '+').replace('"', '+').replace('(', '+').replace(')', '+').replace('[', '+').replace(']', '+').replace('!', '+').replace('++++', '+').replace('+++', '+').replace('++', '+')
    text = text.replace('+720p+', '++').replace('+1080i+', '+').replace('+1080p+', '++').replace('+dtshd+', '++').replace('+dtsrd+', '++').replace('+dtsd+', '++').replace('+dts+', '++').replace('+dd5+', '++').replace('+5+1+', '++').replace('+3d+', '++').replace('+ac3d+', '++').replace('+ac3+', '++').replace('+avchd+', '++').replace('+avc+', '++').replace('+dubbed+', '++').replace('+subbed+', '++').replace('+stereo+', '++')
    text = text.replace('+x264+', '++').replace('+mpeg2+', '++').replace('+avi+', '++').replace('+xvid+', '++').replace('+blu+', '++').replace('+ray+', '++').replace('+bluray+', '++').replace('+3dbd+', '++').replace('+bd+', '++').replace('+bdrip+', '++').replace('+dvdrip+', '++').replace('+rip+', '++').replace('+hdtv+', '++').replace('+hddvd+', '++')
    text = text.replace('+german+', '++').replace('+ger+', '++').replace('+english+', '++').replace('+eng+', '++').replace('+spanish+', '++').replace('+spa+', '++').replace('+italian+', '++').replace('+ita+', '++').replace('+russian+', '++').replace('+rus+', '++').replace('+dl+', '++').replace('+dc+', '++').replace('+sbs+', '++').replace('+se+', '++').replace('+ws+', '++').replace('+cee+', '++')
    text = text.replace('+remux+', '++').replace('+directors+', '++').replace('+cut+', '++').replace('+uncut+', '++').replace('+extended+', '++').replace('+repack+', '++').replace('+unrated+', '++').replace('+rated+', '++').replace('+retail+', '++').replace('+remastered+', '++').replace('+edition+', '++').replace('+version+', '++')
    text = text.replace('\xc3\x9f', '%C3%9F').replace('\xc3\xa4', '%C3%A4').replace('\xc3\xb6', '%C3%B6').replace('\xc3\xbc', '%C3%BC')
    text = sub('\\+tt[0-9]+\\+', '++', text)
    text = sub('\\+\\+\\+\\+.*?FIN', '', text)
    text = sub('\\+FIN', '', text)
    return text


class movieBrowserMetrix(Screen):

    def __init__(self, session, index, content, filter):
        skin = skin_path + "movieBrowserMetrix.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieBrowserMetrix.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.__event_tracker = ServiceEventTracker(screen=self, eventmap={iPlayableService.evEOF: self.seenEOF})
        self.toogleHelp = self.session.instantiateDialog(helpScreen)
        # ###########
        # self.picload = ePicLoad()
        # self.scale = AVSwitch().getFramebufferScale()
        # ###########
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
        if config.plugins.moviebrowser.showfolder.value == 'no':
            self.showfolder = False
        else:
            self.showfolder = True
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
        self['ddd'] = Pixmap()
        self['ddd'].hide()
        self['ddd2'] = Pixmap()
        self['ddd2'].hide()
        self['seen'] = Pixmap()
        self['seen'].hide()
        self['Director'] = Label(_('Director:'))
        self['Actors'] = Label(_('Actors:'))
        self['Year'] = Label(_('Years:'))
        self['Runtime'] = Label(_('Runtime:'))
        self['Country'] = Label(_('Country:'))
        self['text1'] = Label(_('Help'))
        self['text2'] = Label(_('Update'))
        self['text3'] = Label(_('Edit'))
        self['Genres'] = Label(_('Genres:'))
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
        self['metrixback'] = Pixmap()
        self['metrixback2'] = Pixmap()
        self['metrixback2'].hide()
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
        if config.plugins.moviebrowser.backdrops.value == 'auto':
            self.backdrops = 'auto'
        elif config.plugins.moviebrowser.backdrops.value == 'info':
            self.backdrops = 'info'
        else:
            self.backdrops = 'hide'
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
        self.database = dbmovie
        self.blacklist = blacklistmovie
        self.lastfilter = filtermovie
        self.lastfile = lastfile
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)
        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
        self['posterback'].hide()
        self['yellow'].hide()
        self['red'].hide()
        self['green'].hide()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
            self.session.nav.stopService()
        if fileExists(self.database):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value == 'yes':
                    self.filter = open(self.lastfilter).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(self.lastfile).read()
                    if movie.endswith('...'):
                        self.index = -1
                    else:
                        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                        data = open(self.database).read()
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
        if fileExists(dbreset):
            self.session.openWithCallback(self.reset_return, MessageBox, 'The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?', MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(dbreset, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            # self.session.openWithCallback(self.close, movieBrowserConfig)
            self.session.openWithCallback(self.exit, movieBrowserConfig)
        else:
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(dbreset):
                os.remove(dbreset)
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
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
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and filter in line:
                        name = filename = date = runtime = rating = director = actors = genres = year = country = plotfull = " "
                        poster = default_poster
                        backdrop = default_backdrop
                        seen = 'unseen'
                        content = 'Movie:Top'
                        media = '\n'
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
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
                        if '3d' in filename.lower():
                            self.dddlist.append('yes')
                        else:
                            self.dddlist.append('no')
                        self.datelist.append(date)
                        res = []
                        res.append(runtime)
                        res.append(rating)
                        res.append(director)
                        res.append(actors)
                        res.append(genres)
                        res.append(year)
                        res.append(country)
                        self.infolist.append(res)
                        self.plotlist.append(plotfull)
                        self.posterlist.append(poster)
                        self.backdroplist.append(backdrop)
                        self.contentlist.append(content)
                        self.seenlist.append(seen)
                        self.medialist.append(media)

                f.close()
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
                    self.posterlist.append(default_folder)
                    self.backdroplist.append(default_backdrop)
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
        return

    def makeList(self):
        f = open(self.database, 'r')
        movies = []
        for line in f:
            if self.content in line and self.filter in line:
                movieline = line.split(':::')
                try:
                    res = ['']
                    if self.content == ':::Series:::':
                        movie = sub('.*? - \\(', '', movieline[0])
                        movie = sub('\\) ', ' ', movie)
                        movie = sub('S00E00 - ', '', movie)
                        movie = sub('[Ss][0]+[Ee]', 'Special ', movie)
                    else:
                        movie = movieline[0]

                    if screenwidth.width() == 1920:
                        if self.backcolor is True:
                            res.append(MultiContentEntryText(pos=(0, 0), size=(810, 50), font=28, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=movie))
                        else:
                            res.append(MultiContentEntryText(pos=(0, 0), size=(810, 50), font=28, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=movie))

                    else:
                        if self.backcolor is True:
                            res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=movie))
                        else:
                            res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=movie))
                    movies.append(res)
                except IndexError:
                    pass

        f.close()
        if self.content == ':::Series:::':
            movies.sort()
        if self.showfolder is True:
            res = ['']
            if screenwidth.width() == 1920:
                if self.backcolor is True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(810, 50), font=28, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(810, 50), font=28, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            else:
                if self.backcolor is True:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            movies.append(res)

        self['list'].l.setList(movies)
        # if screenwidth.width() == 1920:
            # self['list'].l.setFont(26, gFont('Regular', 26))
            # self['list'].l.setItemHeight(50)
        # else:
            # self['list'].l.setFont(26, gFont('Regular', 26))
            # self['list'].l.setItemHeight(45)
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
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
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
            if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, '\nUpdate Movie Browser Database?', MessageBox.TYPE_YESNO)
            elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                f = open(self.lastfile, 'w')
                f.write(movie)
                f.close()
            except IndexError:
                pass

            if fileExists(self.database):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value == 'yes':
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value == 'yes' and self.hideflag is False:
            self.hideScreen()
        movie = open(self.lastfile).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(self.database).read()
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
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
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
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, ('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                url = ('https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s') % (tmdb_api_key, name + self.language)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w154', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = re.findall('"vote_average":(.*?),', output)
        year = re.findall('"release_date":"(.*?)"', output)
        titles = re.findall('"title":"(.*?)"', output)
        poster = re.findall('"poster_path":"(.*?)"', output)
        id = re.findall('"id":(.*?),', output)
        country = re.findall('"backdrop(.*?)_path"', output)
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
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (new + self.language, tmdb_api_key)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select == 'poster':
                poster = self.posterlist[self.index]
                posternew = new
                database = open(self.database).read()
                database = database.replace(poster, posternew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + name + self.language
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
        agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
        request = Request(url, headers=agents)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
            agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
            request = Request(url, headers=agents)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')

            except Exception:
                output = ''

            output = sub('<poster>', '<poster>https://artworks.thetvdb.com/banners/_cache/', output)
            output = sub('<poster>https://artworks.thetvdb.com/banners/_cache/</poster>', '<poster>' + wiki_png + '</poster>', output)
            output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
            output = sub('&amp;', '&', output)
            Rating = re.findall('<Rating>(.*?)</Rating>', output)
            Year = re.findall('<FirstAired>([0-9]+)-', output)
            Added = re.findall('<added>([0-9]+)-', output)
            Titles = re.findall('<SeriesName>(.*?)</SeriesName>', output)
            Poster = re.findall('<poster>(.*?)</poster>', output)
            TVDbid = re.findall('<id>(.*?)</id>', output)
            Country = re.findall('<Status>(.*?)</Status>', output)
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

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://www.thetvdb.com/api/%s/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return

                bannernew = new
                database = open(self.database).read()
                database = database.replace(banner, bannernew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
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
                    os.remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        os.remove(eitfile)
                    if fileExists(movie + '.ap'):
                        os.remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        os.remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        os.remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        os.remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        os.remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        os.remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        os.remove(srtfile)
                data = open(self.database).read()
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

                f = open(self.database, 'w')
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
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(self.blacklist):
                    fremove = open(self.blacklist, 'a')
                else:
                    fremove = open(self.blacklist, 'w')
                data = open(self.database).read()
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

                f = open(self.database, 'w')
                f.write(data)
                f.close()
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
            database = open(self.database).read()
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

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
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
        self['list'].hide()
        self['label'].hide()
        self['label2'].hide()
        self['label3'].hide()
        self['help'].hide()
        self['pvr'].hide()
        self['text'].hide()
        self['plotfull'].show()
        self['plotname'].show()
        self['yellow'].show()
        self['green'].show()
        self['red'].show()
        self['text1'].setText('')
        self['text2'].setText('Style')

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
        self['text1'].setText('Help')
        self['text2'].setText('Update')
        self['text3'].setText('Edit')

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

#####################
    # def showDefaultBanner(self):
        # from Tools.Directories import resolveFilename
        # from Tools.LoadPixmap import LoadPixmap
        # from Tools.Directories import SCOPE_CURRENT_SKIN
        # noCoverFile = resolveFilename(SCOPE_CURRENT_SKIN, "skin_default/no_coverArt.png")
        # self.noCoverPixmap = LoadPixmap(noCoverFile)

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
                    if pythonVer == 3:
                        bannerurl = bannerurl.encode()
                    # getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=bannerurl, file=banner, success=self.getBanner, fail=self.downloadError)
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
        f = open(banner, 'wb')
        f.write(output)
        f.close()
        if fileExists(banner):
            self["banner"].instance.setPixmapFromFile(banner)
            self['banner'].show()
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
                    if pythonVer == 3:
                        eposterurl = eposterurl.encode()
                    # getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=eposterurl, file=eposter, sucess=self.getEPoster, fail=self.downloadError)
        except IndexError:
            pass

        return

    def getEPoster(self, output, eposter):
        f = open(eposter, 'wb')
        f.write(output)
        f.close()
        if fileExists(eposter):
            self["eposter"].instance.setPixmapFromFile(eposter)
            self['eposter'].show()
        return

    def makePoster(self, poster=None):
        try:
            posterurl = self.posterlist[self.index]
            posterurl = sub('<episode>.*?<episode>', '', posterurl)
            poster = sub('.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                self["poster"].instance.setPixmapFromFile(poster)
                self['poster'].show()
                self['posterback'].show()
            else:
                if pythonVer == 3:
                    posterurl = posterurl.encode()
                # getPage(posterurl).addCallback(self.getPoster, poster).addErrback(self.downloadError)
                callInThread(threadGetPage, url=posterurl, file=poster, success=self.getPoster, fail=self.downloadError)
        except IndexError:
            self['posterback'].hide()
            self['poster'].hide()

        return

    def getPoster(self, output, poster):
        try:
            f = open(poster, 'wb')
            f.write(output)
            f.close()
            self["poster"].instance.setPixmapFromFile(poster)
            self['poster'].show()
            self['posterback'].show()
        except Exception as e:
            print('error ', str(e))
        return

    def showBackdrops(self, index):
        try:
            backdropurl = self.backdroplist[index]
            if backdropurl != self.oldbackdropurl:
                self.oldbackdropurl = backdropurl
                backdrop = sub('.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value == 'yes':
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()
                        # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                elif fileExists(backdrop):
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()
                    # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            f = open(backdrop, 'wb')
            f.write(output)
            f.close()
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                # if self["backdrop"].instance:
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
                os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)

        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def down(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].down()
                self['seasons'].down()
            else:
                self['list'].down()
                self.index = self['list'].getSelectedIndex()
                self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                try:
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

    def up(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].up()
                self['seasons'].up()
            else:
                self['list'].up()
                self.index = self['list'].getSelectedIndex()
                self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                try:
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

    def rightDown(self):
        if self.ready is True:
            if self.toggleCount == 1:
                self['plotfull'].pageDown()
            else:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.episodes = True
                else:
                    self.episodes = False
                if self.control is False and self.episodes is True:
                    self['list'].selectionEnabled(0)
                    self['episodes'].selectionEnabled(1)
                    self.control = True
                elif self.control is True:
                    self['episodes'].pageDown()
                    index = self['episodes'].getSelectedIndex()
                    self['seasons'].moveToIndex(index)
                else:
                    self['list'].pageDown()
                    self.index = self['list'].getSelectedIndex()
                    self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                    try:
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

    def leftUp(self):
        if self.ready is True:
            if self.toggleCount == 1:
                self['plotfull'].pageUp()
            elif self.control is True:
                self['episodes'].selectionEnabled(0)
                self['list'].selectionEnabled(1)
                self.control = False
            else:
                self['list'].pageUp()
                self.index = self['list'].getSelectedIndex()
                self['label3'].setText('Item %s/%s' % (str(self.index + 1), str(self.totalItem)))
                try:
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

    def gotoEnd(self):
        if self.ready is True:
            self.index = self.maxentry - 1
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

    def controlMovies(self):
        if self.ready is True:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.open(MessageBox, _('Series Folder: No Info possible'), MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and self.filter in line:
                        movieline = line.split(':::')
                        try:
                            self.movies.append((movieline[0], movieline[1], movieline[12]))
                        except IndexError:
                            pass

                if self.showfolder is True:
                    self.movies.append(_('<List of Movie Folder>'), config.plugins.moviebrowser.moviefolder.value + '...', default_backdrop)
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
            for root, dirs, files in os.walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = os.path.join(root, name)
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
                        res.append(MultiContentEntryText(pos=(0, 0), size=(810, 34), font=28, flags=RT_HALIGN_LEFT, text=self.seasons[i]))
                    else:
                        res.append(MultiContentEntryText(pos=(0, 0), size=(540, 30), font=22, flags=RT_HALIGN_LEFT, text=self.seasons[i]))
                    list.append(res)

                self['episodes'].l.setList(list)
                # self['episodes'].l.setItemHeight(45)
                self['episodes'].selectionEnabled(0)
                self['episodes'].show()
            else:
                self.session.openWithCallback(self.filter_return, filterSeasonList, self.seasons, self.content)

    def filter_return(self, filter):
        if filter and filter is not None:
            self.index = 0
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
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserBackdrop, self.index, self.content, self.filter)
        elif number == 3:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
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
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            self.sortDatabase()
            f = open(self.database, 'r')
            count = 0
            for line in f:
                if self.content in line and self.filter in line:
                    if movie in line:
                        self.index = count
                        break
                    count += 1

            f.close()
            self.makeMovies(self.filter)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        # getPage(link).addCallback(name).addErrback(self.downloadError)
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            # self.session.openWithCallback(self.close, movieBrowserConfig)
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

    def exit(self):
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
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value == 'yes':
                f = open(self.lastfilter, 'w')
                f.write(self.filter)
                f.close()
            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
                self.session.nav.playService(self.oldService)
            self.session.deleteDialog(self.toogleHelp)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof

        self.close()


class movieBrowserBackdrop(Screen):

    def __init__(self, session, index, content, filter):
        skin = skin_path + "movieBrowserBackdrop.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieBrowserBackdrop.xml"
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
        if config.plugins.moviebrowser.showfolder.value == 'no':
            self.showfolder = False
        else:
            self.showfolder = True
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
        if config.plugins.moviebrowser.backdrops.value == 'auto':
            self.backdrops = 'auto'
        elif config.plugins.moviebrowser.backdrops.value == 'info':
            self.backdrops = 'info'
        else:
            self.backdrops = 'hide'
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
            self['poster_back5'] = Pixmap()
            self['poster_back11'] = Pixmap()
            self['poster_back12'] = Pixmap()
        else:
            self.posterindex = 5
            self.posterALL = 11
            self['poster_back6'] = Pixmap()
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
        self.database = dbmovie
        self.blacklist = blacklistmovie
        self.lastfilter = filtermovie
        self.lastfile = lastfile
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)

        # if screenwidth.width() >= 1920:
            # self.infoBackPNG = '%spic/browser/info_backHD.png' % skin_directory
            # InfoBack = loadPic(self.infoBackPNG, 788, 645, 3, 0, 0, 0)
        # elif screenwidth.width() == 1280:
            # self.infoBackPNG = '%spic/browser/info_back.png' % skin_directory
            # InfoBack = loadPic(self.infoBackPNG, 525, 430, 3, 0, 0, 0)
        # else:
            # self.infoBackPNG = '%spic/browser/info_back.png' % skin_directory
            # InfoBack = loadPic(self.infoBackPNG, 460, 400, 3, 0, 0, 0)
        # if InfoBack is not None:
            # self['plotfullback'].instance.setPixmap(InfoBack)
            # self['infoback'].instance.setPixmap(InfoBack)
        self['plotfullback'].hide()
        self['infoback'].show()

        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
            self.session.nav.stopService()
        if fileExists(self.database):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value == 'yes':
                    self.filter = open(self.lastfilter).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(self.lastfile).read()
                    if movie.endswith('...'):
                        self.index = -1
                    else:
                        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                        data = open(self.database).read()
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
        if fileExists(dbreset):
            self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(dbreset, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            # self.session.openWithCallback(self.close, movieBrowserConfig)
            self.session.openWithCallback(self.exit, movieBrowserConfig)
        else:
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(dbreset):
                os.remove(dbreset)
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
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
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and filter in line:
                        name = filename = date = runtime = rating = director = actors = genres = year = country = plotfull = " "
                        poster = default_poster
                        backdrop = default_backdrop
                        seen = 'unseen'
                        content = 'Movie:Top'
                        media = '\n'
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
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
                        if '3d' in filename.lower():
                            self.dddlist.append('yes')
                        else:
                            self.dddlist.append('no')
                        self.datelist.append(date)
                        res = []
                        res.append(runtime)
                        res.append(rating)
                        res.append(director)
                        res.append(actors)
                        res.append(genres)
                        res.append(year)
                        res.append(country)
                        self.infolist.append(res)
                        self.plotlist.append(plotfull)
                        self.posterlist.append(poster)
                        self.backdroplist.append(backdrop)
                        self.contentlist.append(content)
                        self.seenlist.append(seen)
                        self.medialist.append(media)

                f.close()
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
                    self.posterlist.append(default_folder)
                    self.backdroplist.append(default_backdrop)
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
        return

    def updateDatabase(self):
        if self.ready is True:
            if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, '\nUpdate Movie Browser Database?', MessageBox.TYPE_YESNO)
            elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                f = open(self.lastfile, 'w')
                f.write(movie)
                f.close()
            except IndexError:
                pass

            if fileExists(self.database):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value == 'yes':
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value == 'yes' and self.hideflag is False:
            self.hideScreen()
        movie = open(self.lastfile).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(self.database).read()
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
                        # if self.xd is False:
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
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
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
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, _('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s' % (tmdb_api_key, name + self.language)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w154', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = re.findall('"vote_average":(.*?),', output)
        year = re.findall('"release_date":"(.*?)"', output)
        titles = re.findall('"title":"(.*?)"', output)
        poster = re.findall('"poster_path":"(.*?)"', output)
        id = re.findall('"id":(.*?),', output)
        country = re.findall('"backdrop(.*?)_path"', output)
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
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (new + self.language, tmdb_api_key)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select == 'poster':
                poster = self.posterlist[self.index]
                posternew = new
                database = open(self.database).read()
                database = database.replace(poster, posternew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + name + self.language
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
        agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
        request = Request(url, headers=agents)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
            agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
            request = Request(url, headers=agents)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')
            except Exception:
                output = ''

            output = sub('<poster>', '<poster>https://www.thetvdb.com/banners/_cache/', output)
            output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>' + wiki_png + '</poster>', output)
            output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
            output = sub('&amp;', '&', output)
            Rating = re.findall('<Rating>(.*?)</Rating>', output)
            Year = re.findall('<FirstAired>([0-9]+)-', output)
            Added = re.findall('<added>([0-9]+)-', output)
            Titles = re.findall('<SeriesName>(.*?)</SeriesName>', output)
            Poster = re.findall('<poster>(.*?)</poster>', output)
            TVDbid = re.findall('<id>(.*?)</id>', output)
            Country = re.findall('<Status>(.*?)</Status>', output)
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

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://www.thetvdb.com/api/%s/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return
                bannernew = new
                database = open(self.database).read()
                database = database.replace(banner, bannernew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
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
                    os.remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        os.remove(eitfile)
                    if fileExists(movie + '.ap'):
                        os.remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        os.remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        os.remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        os.remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        os.remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        os.remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        os.remove(srtfile)
                data = open(self.database).read()
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

                f = open(self.database, 'w')
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
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(self.blacklist):
                    fremove = open(self.blacklist, 'a')
                else:
                    fremove = open(self.blacklist, 'w')
                data = open(self.database).read()
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

                f = open(self.database, 'w')
                f.write(data)
                f.close()
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
            database = open(self.database).read()
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

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    if search(':::unseen:::', line) is not None:
                        newline = line.replace(':::unseen:::', ':::seen:::')
                        self.seenlist.pop(self.index)
                        self.seenlist.insert(self.index, 'seen')
                        self['seen'].show()
                        database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
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
                        if pythonVer == 3:
                            bannerurl = bannerurl.encode()
                        # getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=bannerurl, file=banner, success=self.getBanner, fail=self.downloadError)
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
                            if pythonVer == 3:
                                bannerurl = bannerurl.encode()
                            # getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
                            callInThread(threadGetPage, url=bannerurl, file=banner, success=self.getBanner, fail=self.downloadError)
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
                        if pythonVer == 3:
                            eposterurl = eposterurl.encode()
                        # getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=eposterurl, file=eposter, success=self.getEPoster, fail=self.downloadError)
                else:
                    self.toggleCount = 2
                    self['eposter'].hide()
                    self['plotfull'].show()
            except IndexError:
                pass

        return

    def getEPoster(self, output, eposter):
        try:
            f = open(eposter, 'wb')
            f.write(output)
            f.close()
            if fileExists(eposter):
                self["eposter"].instance.setPixmapFromFile(eposter)
                self['eposter'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
        return

    def getBanner(self, output, banner):
        try:
            f = open(banner, 'wb')
            f.write(output)
            f.close()
            if fileExists(banner):
                self["banner"].instance.setPixmapFromFile(banner)
                self['banner'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
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
                    if pythonVer == 3:
                        posterurl = posterurl.encode()
                    # getPage(posterurl).addCallback(self.getPoster, x, poster).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=posterurl, file=poster, key=x, success=self.getPoster, fail=self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        return

    def getPoster(self, output, x, poster):
        try:
            f = open(poster, 'wb')
            f.write(output)
            f.close()
            if fileExists(poster):
                self['poster' + str(x)].instance.setPixmapFromFile(poster)
                self['poster' + str(x)].show()
        except Exception as e:
            print('error ', str(e))
        return

    def showBackdrops(self, index):
        try:
            backdropurl = self.backdroplist[index]
            if backdropurl != self.oldbackdropurl:
                self.oldbackdropurl = backdropurl
                backdrop = sub('.*?[/]', '', backdropurl)
                backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                if config.plugins.moviebrowser.m1v.value == 'yes':
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()
                        # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()
                    # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            f = open(backdrop, 'wb')
            f.write(output)
            f.close()
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
                os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def down(self):
        if self.ready is True:
            if screenwidth.width() >= 1280:
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
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and self.filter in line:
                        movieline = line.split(':::')
                        try:
                            self.movies.append((movieline[0], movieline[1], movieline[12]))
                        except IndexError:
                            pass

                if self.showfolder is True:
                    self.movies.append(_('<List of Movie Folder>'), config.plugins.moviebrowser.moviefolder.value + '...', default_backdrop)
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
                # if self.xd is False:
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
            for root, dirs, files in os.walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = os.path.join(root, name)
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 30), font=26, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 30), font=26, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 25), font=20, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 25), font=20, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
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
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserPosterwall, self.index, self.content, self.filter)
        elif number == 1:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
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
            f = open(self.database, 'r')
            count = 0
            for line in f:
                if self.content in line and self.filter in line:
                    if movie in line:
                        self.index = count
                        break
                    count += 1

            f.close()
            self.makeMovies(self.filter)

    # def youTube(self):
        # if self.ready is True:
            # YouTubeSearch = False
            # try:
                # from Plugins.Extensions.YouTube.YouTubeSearch import YouTubeSearch as YouTubeSearch
                # YouTubeSearch = True
            # except:
                # pass
            # if YouTubeSearch:
                # from Plugins.Extensions.YouTube.YouTubeSearch import YouTubeSearch as YouTubeSearch
                # try:
                    # name = self.namelist[self.index]
                    # name = name + 'FIN'
                    # name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    # name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    # name = sub('FIN', '', name)

                    # self.session.openWithCallback(self.searchScreenCallback, YouTubeSearch, name)
                # # self.session.open(searchYouTube, name)
                # except IndexError:
                    # pass

    # def searchScreenCallback(self, search_value=None):
        # if not search_value:  # cancel in search
            # return
        # else:
            # pass

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        # getPage(link).addCallback(name).addErrback(self.downloadError)
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            # self.session.openWithCallback(self.close, movieBrowserConfig)
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

    def exit(self):
        if self.showhelp is True:
            self.showhelp = False
            self.toogleHelp.hide()
        elif config.plugins.moviebrowser.plotfull.value == 'hide' and self.topseries is False and self.plotfull is True:
            self.toggleCount = 0
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.episodes = True
                else:
                    self.episodes = False
            except IndexError:
                self.episodes = False

            self.plotfull = False
            self.control = False
            self.hidePlot()
            self.hideEPoster()
        elif self.topseries is True:
            self.topseries = False
            self.episodes = True
            self.plotfull = True
            self.control = True
            self.toggleCount = 1
            self.content = self.oldcontent
            self.filter = self.oldfilter
            self.index = self.topindex
            self.makeMovies(self.filter)
        else:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value == 'yes':
                f = open(self.lastfilter, 'w')
                f.write(self.filter)
                f.close()
            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
                self.session.nav.playService(self.oldService)
            self.session.deleteDialog(self.toogleHelp)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.close()


class movieBrowserPosterwall(Screen):

    def __init__(self, session, index, content, filter):

        if screenwidth.width() >= 1280:
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
        else:
            self.xd = True
            self.spaceTop = 0
            self.spaceLeft = 10
            self.spaceX = 5
            self.spaceY = 5
            self.picX = 106
            self.picY = 160
            self.posterX = 9
            self.posterY = 3
            self.posterALL = 27
            self.posterREST = 0
        self.positionlist = []
        skincontent = ''
        numX = -1
        for x in range(self.posterALL):
            numY = x // self.posterX
            numX += 1
            if numX >= self.posterX:
                numX = 0
            posX = self.spaceLeft + self.spaceX + numX * (self.spaceX + self.picX)
            posY = self.spaceTop + self.spaceY + numY * (self.spaceY + self.picY)
            # if self.xd is False:
            if screenwidth.width() >= 1280:
                self.positionlist.append((posX - 13, posY - 15))
            else:
                self.positionlist.append((posX - 8, posY - 10))
            skincontent += '<widget name="poster' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-4" transparent="1" alphatest="on" />'
            skincontent += '<widget name="poster_back' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-3" transparent="1" alphatest="blend" pixmap="%spic/browser/poster_backHD.png" />' % skin_directory

        skin = skin_path + "movieBrowserPosterwall.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieBrowserPosterwall.xml"
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
        self.index = index
        self.wallindex = self.index % self.posterALL
        self.pagecount = self.index // self.posterALL + 1
        self.oldwallindex = 0
        self.pagemax = 1
        self.content = content
        self.filter = filter
        self.language = '&language=%s' % config.plugins.moviebrowser.language.value

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
        if config.plugins.moviebrowser.showfolder.value == 'no':
            self.showfolder = False
        else:
            self.showfolder = True
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
        if config.plugins.moviebrowser.backdrops.value == 'auto':
            self.backdrops = 'auto'
        elif config.plugins.moviebrowser.backdrops.value == 'info':
            self.backdrops = 'info'
        else:
            self.backdrops = 'hide'
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
        self.database = dbmovie
        self.blacklist = blacklistmovie
        self.lastfilter = filtermovie
        self.lastfile = lastfile
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)

        self['infoback'].show()
        self['2infoback'].hide()
        self['plotfullback'].hide()
        if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
            self.session.nav.stopService()
        if fileExists(self.database):
            if self.index == 0:
                if config.plugins.moviebrowser.lastfilter.value == 'yes':
                    self.filter = open(self.lastfilter).read()
                if config.plugins.moviebrowser.lastmovie.value == 'yes':
                    movie = open(self.lastfile).read()
                    movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                    data = open(self.database).read()
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
                    self.index = sum((1 for line in open(self.database)))
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
        if fileExists(dbreset):
            self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open(dbreset, 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            # self.session.openWithCallback(self.close, movieBrowserConfig)
            self.session.openWithCallback(self.exit, movieBrowserConfig)
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists(dbreset):
                os.remove(dbreset)
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
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
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and filter in line:
                        name = filename = date = runtime = rating = director = actors = genres = year = country = plotfull = " "
                        poster = default_poster
                        backdrop = default_backdrop
                        seen = 'unseen'
                        content = 'Movie:Top'
                        media = '\n'
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
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
                        if '3d' in filename.lower():
                            self.dddlist.append('yes')
                        else:
                            self.dddlist.append('no')
                        self.datelist.append(date)
                        res = []
                        res.append(runtime)
                        res.append(rating)
                        res.append(director)
                        res.append(actors)
                        res.append(genres)
                        res.append(year)
                        res.append(country)
                        self.infolist.append(res)
                        self.plotlist.append(plotfull)
                        self.posterlist.append(poster)
                        self.backdroplist.append(backdrop)
                        self.contentlist.append(content)
                        self.seenlist.append(seen)
                        self.medialist.append(media)

                f.close()
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
                    self.posterlist.append(default_folder)
                    self.backdroplist.append(default_backdrop)
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
        return

    def updateDatabase(self):
        if self.ready is True:
            if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.openWithCallback(self.database_return, MessageBox, _('\nUpdate Movie Browser Database?'), MessageBox.TYPE_YESNO)
            elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                self.session.open(MessageBox, _('\nMovie Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Update canceled.') % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)

    def database_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                movie = self.movielist[self.index]
                f = open(self.lastfile, 'w')
                f.write(movie)
                f.close()
            except IndexError:
                pass

            if fileExists(self.database):
                self.runTimer = eTimer()
                self.runTimer.callback.append(self.database_run)
                self.runTimer.start(500, True)

    def database_run(self):
        if config.plugins.moviebrowser.hideupdate.value == 'yes':
            self.hideScreen()
        found, orphaned, moviecount, seriescount = UpdateDatabase(False, '', '', '').showResult(True)
        if config.plugins.moviebrowser.hideupdate.value == 'yes' and self.hideflag is False:
            self.hideScreen()
        movie = open(self.lastfile).read()
        movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
        data = open(self.database).read()
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
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
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
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(movie, line) is not None:
                    newline = line + 'FIN'
                    newline = sub('seen:::.*?FIN', 'seen:::' + media + ':::', newline)
                    newline = sub('FIN', '', newline)
                    database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
        return

    def renewTMDb(self):
        if self.ready is True:
            try:
                content = self.contentlist[self.index]
                if content == 'Series:Top':
                    self.session.open(MessageBox, _('\nTMDb Movie Update Error:\nSeries Folder'), MessageBox.TYPE_ERROR)
                    return
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = transMOVIE(name)
                name = sub('\\+[1-2][0-9][0-9][0-9]', '', name)
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s' % (tmdb_api_key, name + self.language)
                self.getTMDbMovies(url)
            except IndexError:
                pass

    def getTMDbMovies(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
        output = sub('"poster_path":"', '"poster_path":"https://image.tmdb.org/t/p/w154', output)
        output = sub('"poster_path":null', '"poster_path":"https://www.themoviedb.org/images/apps/moviebase.png"', output)
        rating = re.findall('"vote_average":(.*?),', output)
        year = re.findall('"release_date":"(.*?)"', output)
        titles = re.findall('"title":"(.*?)"', output)
        poster = re.findall('"poster_path":"(.*?)"', output)
        id = re.findall('"id":(.*?),', output)
        country = re.findall('"backdrop(.*?)_path"', output)
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
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (new + self.language, tmdb_api_key)
                UpdateDatabase(True, self.name, movie, date).getTMDbData(url, new, True)
            elif select == 'poster':
                poster = self.posterlist[self.index]
                posternew = new
                database = open(self.database).read()
                database = database.replace(poster, posternew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            self.renewFinished()
        return

    def renewTVDb(self):
        if self.ready is True:
            try:
                name = self.movielist[self.index]
                name = sub('.*?[/]', '', name)
                if name.endswith('.ts'):
                    name = sub('_', ' ', name)
                    name = sub('^.*? - .*? - ', '', name)
                    name = sub('^[0-9]+ [0-9]+ - ', '', name)
                    name = sub('^[0-9]+ - ', '', name)
                    name = sub('[.]ts', '', name)
                else:
                    name = sub('\\.avi|\\.divx|\\.flv|\\.iso|\\.ISO|\\.m2ts|\\.m4v|\\.mov|\\.mp4|\\.mpg|\\.mpeg|\\.mkv|\\.vob', '', name)
                self.name = name
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                name = transSERIES(name)
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + name + self.language
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
        agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
        request = Request(url, headers=agents)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/%s/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
            agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
            request = Request(url, headers=agents)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')
            except Exception:
                output = ''

            output = sub('<poster>', '<poster>https://www.thetvdb.com/banners/_cache/', output)
            output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>' + wiki_png + '</poster>', output)
            output = sub('<Rating></Rating>', '<Rating>0.0</Rating>', output)
            output = sub('&amp;', '&', output)
            Rating = re.findall('<Rating>(.*?)</Rating>', output)
            Year = re.findall('<FirstAired>([0-9]+)-', output)
            Added = re.findall('<added>([0-9]+)-', output)
            Titles = re.findall('<SeriesName>(.*?)</SeriesName>', output)
            Poster = re.findall('<poster>(.*?)</poster>', output)
            TVDbid = re.findall('<id>(.*?)</id>', output)
            Country = re.findall('<Status>(.*?)</Status>', output)
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

    def makeTVDbUpdate(self, new, select):
        if new is not None:
            if select == 'series':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://www.thetvdb.com/api/%s/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
                UpdateDatabase(True, self.name, movie, date).getTVDbData(url, new)
            elif select == 'banner':
                banner = self.posterlist[self.index].split('<episode>')
                try:
                    banner = banner[1]
                except IndexError:
                    return

                bannernew = new
                database = open(self.database).read()
                database = database.replace(banner, bannernew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
            elif select == 'backdrop':
                backdrop = self.backdroplist[self.index]
                backdropnew = new
                database = open(self.database).read()
                database = database.replace(backdrop, backdropnew)
                f = open(self.database + '.new', 'w')
                f.write(database)
                f.close()
                os.rename(self.database + '.new', self.database)
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
                    os.remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        os.remove(eitfile)
                    if fileExists(movie + '.ap'):
                        os.remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        os.remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        os.remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        os.remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        os.remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        os.remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        os.remove(srtfile)
                data = open(self.database).read()
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

                f = open(self.database, 'w')
                f.write(data)
                f.close()
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
                if fileExists(self.blacklist):
                    fremove = open(self.blacklist, 'a')
                else:
                    fremove = open(self.blacklist, 'w')
                data = open(self.database).read()
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

                f = open(self.database, 'w')
                f.write(data)
                f.close()
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
            database = open(self.database).read()
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

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
            self.ready = True
        return

    def seenEOF(self):
        if self.ready is True and self.content != ':::Series:Top:::':
            self.ready = False
            movie = self.movielist[self.index]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            database = open(self.database).read()
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

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
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

# check this please
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
                        if pythonVer == 3:
                            bannerurl = bannerurl.encode()
                        # getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=bannerurl, file=banner, success=self.getBanner, fail=self.downloadError)
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
                            if pythonVer == 3:
                                bannerurl = bannerurl.encode()
                            # getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
                            callInThread(threadGetPage, url=bannerurl, file=banner, success=self.getBanner, fail=self.downloadError)
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
                        if pythonVer == 3:
                            eposterurl = eposterurl.encode()
                        # getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=eposterurl, file=eposter, success=self.getEPoster, fail=self.downloadError)
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
        f = open(eposter, 'wb')
        f.write(output)
        f.close()
        if fileExists(eposter):
            self["eposter"].instance.setPixmapFromFile(eposter)
            self['eposter'].show()
            self['plotfull'].hide()
        return

    def getBanner(self, output, banner):
        try:
            f = open(banner, 'wb')
            f.write(output)
            f.close()
            if fileExists(banner):
                self["banner"].instance.setPixmapFromFile(banner)
                self['banner'].show()
                self['plotfull'].hide()
        except Exception as e:
            print('error ', str(e))
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
                    if pythonVer == 3:
                        posterurl = posterurl.encode()
                    # getPage(posterurl).addCallback(self.getPoster, x, poster).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=posterurl, file=poster, key=x, success=self.getPoster, fail=self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        self['poster_back' + str(self.wallindex)].hide()
        return

    def getPoster(self, output, x, poster):
        try:
            f = open(poster, 'wb')
            f.write(output)
            f.close()
            if fileExists(poster):
                if self["poster"].instance:
                    self['poster' + str(x)].instance.setPixmapFromFile(poster)
                    self['poster' + str(x)].show()
        except Exception as e:
            print('error ', str(e))
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
                if config.plugins.moviebrowser.m1v.value == 'yes':
                    backdrop_m1v = backdrop.replace('.jpg', '.m1v')
                    if fileExists(backdrop_m1v):
                        self['backdrop'].hide()
                        os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
                    elif fileExists(backdrop):
                        self["backdrop"].instance.setPixmapFromFile(backdrop)
                        self['backdrop'].show()
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()
                        # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
                        os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
                elif fileExists(backdrop):
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()
                    # getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                    callInThread(threadGetPage, url=backdropurl, file=backdrop, key=index, success=self.getBackdrop, fail=self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        try:
            f = open(backdrop, 'wb')
            f.write(output)
            f.close()
            if fileExists(backdrop):
                if self["backdrop"].instance:
                    self["backdrop"].instance.setPixmapFromFile(backdrop)
                    self['backdrop'].show()
        except Exception as e:
            print('error ', str(e))
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                self["backdrop"].instance.setPixmapFromFile(backdrop)
                self['backdrop'].show()
                os.popen('/usr/bin/showiframe %spic/browser/no.m1v' % skin_directory)
        elif fileExists(backdrop):
            self["backdrop"].instance.setPixmapFromFile(backdrop)
            self['backdrop'].show()
        return

    def down(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].down()
            elif self.plotfull is True:
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
                        self.index = self.index + (self.posterX + self.maxentry % self.posterX)
                        if self.index >= self.maxentry:
                            self.index = self.index - self.maxentry
                    else:
                        self.index = self.index + self.maxentry % self.posterX
                        if self.index >= self.maxentry:
                            self.index = self.index - self.maxentry
                elif self.wallindex > self.posterALL - 1:
                    self.wallindex = self.wallindex - self.posterALL
                    if self.wallindex < 0:
                        self.wallindex = 0
                    self.pagecount += 1
                    self.makePoster(self.pagecount - 1)
                    self.index = self.index + self.posterX
                    if self.index >= self.maxentry:
                        self.index = self.index - self.maxentry
                else:
                    self.index = self.index + self.posterX
                    if self.index >= self.maxentry:
                        self.index = self.index - self.maxentry
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

    def up(self):
        if self.ready is True:
            if self.control is True:
                self['episodes'].up()
            elif self.plotfull is True:
                self['plotfull'].pageUp()
            else:
                self.oldwallindex = self.wallindex
                self.wallindex -= self.posterX
                if self.wallindex < 0:
                    if self.pagecount == 1:
                        if self.oldwallindex < self.posterREST % self.posterX:
                            self.wallindex = self.posterREST // self.posterX * self.posterX + self.oldwallindex
                            if self.wallindex < 0:
                                self.wallindex = 0
                            self.index = self.index - self.posterREST % self.posterX
                            if self.index < 0:
                                self.index = self.maxentry + self.index
                        else:
                            self.wallindex = self.posterREST - 1
                            if self.wallindex < 0:
                                self.wallindex = 0
                            self.index = self.maxentry - 1
                        self.pagecount = self.pagemax
                        self.makePoster(self.pagecount - 1)
                    else:
                        self.wallindex = self.posterALL + self.wallindex
                        if self.wallindex < 0:
                            self.wallindex = 0
                        self.pagecount -= 1
                        self.makePoster(self.pagecount - 1)
                        self.index = self.index - self.posterX
                        if self.index < 0:
                            self.index = self.maxentry + self.index
                else:
                    self.index = self.index - self.posterX
                    if self.index < 0:
                        self.index = self.maxentry + self.index
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

    def rightDown(self):
        if self.ready is True:
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

    def leftUp(self):
        if self.ready is True:
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

    def PageDown(self):
        if self.ready is True:
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
                    self.wallindex = self.wallindex % self.posterX
                self.pagecount = 1
                self.makePoster(self.pagecount - 1)
                if self.wallindex >= self.maxentry % self.posterX:
                    self.index = self.wallindex
                    if self.index >= self.maxentry:
                        self.index = self.index - self.maxentry
                else:
                    self.index = self.index + self.maxentry % self.posterX
                    if self.index >= self.maxentry:
                        self.index = self.index - self.maxentry
            elif self.wallindex > self.posterALL - 1:
                self.wallindex = self.wallindex - self.posterALL
                if self.wallindex < 0:
                    self.wallindex = 0
                self.pagecount += 1
                self.makePoster(self.pagecount - 1)
                self.index = self.index + self.posterALL
                if self.index >= self.maxentry:
                    self.index = self.index - self.maxentry
            else:
                self.index = self.index + self.posterALL
                if self.index >= self.maxentry:
                    self.index = self.index - self.maxentry
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

    def PageUp(self):
        if self.ready is True:
            self.oldwallindex = self.wallindex
            self.wallindex -= self.posterALL
            if self.wallindex < 0:
                if self.pagecount == 1:
                    if self.oldwallindex < self.posterREST % self.posterX:
                        self.wallindex = self.posterREST // self.posterX * self.posterX + self.oldwallindex
                        if self.wallindex < 0:
                            self.wallindex = 0
                        self.index = self.index - self.posterREST % self.posterX
                        if self.index < 0:
                            self.index = self.maxentry + self.index
                    else:
                        self.wallindex = self.posterREST - 1
                        if self.wallindex < 0:
                            self.wallindex = 0
                        self.index = self.maxentry - 1
                    self.pagecount = self.pagemax
                    self.makePoster(self.pagecount - 1)
                else:
                    self.wallindex = self.posterALL + self.wallindex
                    if self.wallindex < 0:
                        self.wallindex = 0
                    self.pagecount -= 1
                    self.makePoster(self.pagecount - 1)
                    self.index = self.index - self.posterALL
                    if self.index < 0:
                        self.index = self.maxentry + self.index
            else:
                self.index = self.index - self.posterALL
                if self.index < 0:
                    self.index = self.maxentry + self.index
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

    def gotoEnd(self):
        if self.ready is True:
            self.oldwallindex = self.wallindex
            self.wallindex = self.posterREST - 1
            if self.wallindex < 0:
                self.wallindex = 0
            self.pagecount = self.pagemax
            self.makePoster(self.pagecount - 1)
            self.index = self.maxentry - 1
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

    def controlMovies(self):
        if self.ready is True:
            content = self.contentlist[self.index]
            if content == 'Series:Top':
                self.session.open(MessageBox, _('Series Folder: No Info possible'), MessageBox.TYPE_ERROR)
                return
            self.movies = []
            if fileExists(self.database):
                f = open(self.database, 'r')
                for line in f:
                    if self.content in line and self.filter in line:
                        movieline = line.split(':::')
                        try:
                            self.movies.append((movieline[0], movieline[1], movieline[12]))
                        except IndexError:
                            pass

                if self.showfolder is True:
                    self.movies.append(_('<List of Movie Folder>'), config.plugins.moviebrowser.moviefolder.value + '...', default_backdrop)
                f.close()
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
            for root, dirs, files in os.walk(folder, topdown=False, onerror=None, followlinks=True):
                for name in dirs:
                    folder = os.path.join(root, name)
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
            if fileExists(self.database):
                f = open(self.database, 'r')
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
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 28), font=28, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 28), font=28, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                        else:
                            if backcolor is True:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 25), font=26, color=16777215, color_sel=16777215, backcolor_sel=back_color, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
                            else:
                                res.append(MultiContentEntryText(pos=(0, 0), size=(listwidth, 25), font=26, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.seasons[i]))
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
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
                self.session.nav.playService(self.oldService)
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserMetrix, self.index, self.content, self.filter)
        elif number == 2:
            if config.plugins.moviebrowser.lastmovie.value == 'yes':
                try:
                    movie = self.movielist[self.index]
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
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
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            self.sortDatabase()
            f = open(self.database, 'r')
            count = 0
            for line in f:
                if self.content in line and self.filter in line:
                    if movie in line:
                        self.index = count
                        break
                    count += 1

            f.close()
            self.makeMovies(self.filter)

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        # getPage(link).addCallback(name).addErrback(self.downloadError)
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            # self.session.openWithCallback(self.close, movieBrowserConfig)
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

    def exit(self):
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
                    f = open(self.lastfile, 'w')
                    f.write(movie)
                    f.close()
                except IndexError:
                    pass

            if config.plugins.moviebrowser.lastfilter.value == 'yes':
                f = open(self.lastfilter, 'w')
                f.write(self.filter)
                f.close()
            if config.plugins.moviebrowser.showtv.value == 'hide' or config.plugins.moviebrowser.m1v.value == 'yes':
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
        self.database = dbmovie
        self.blacklist = blacklistmovie
        self.updatelog = updatelog
        if self.renew is True:
            self.starttime = ''
            self.namelist.append(name)
            self.movielist.append(movie)
            self.datelist.append(date)
        else:
            self.makeUpdate()

    def makeUpdate(self):
        self.starttime = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        data = open(self.database).read()
        if fileExists(self.blacklist):
            blacklist = open(self.blacklist).read()
            alldata = data + blacklist
        else:
            alldata = data
        allfiles = ':::'
        count = 0
        folder = config.plugins.moviebrowser.moviefolder.value
        for root, dirs, files in os.walk(folder, topdown=False, onerror=None, followlinks=True):
            for name in files:
                count += 1
                if name.endswith('.ts') or name.endswith('.avi') or name.endswith('.divx') or name.endswith('.flv') or name.lower().endswith('.iso') or name.endswith('.m2ts') or name.endswith('.m4v') or name.endswith('.mov') or name.endswith('.mp4') or name.endswith('.mpg') or name.endswith('.mpeg') or name.endswith('.mkv') or name.endswith('.vob'):
                    filename = os.path.join(root, name)
                    allfiles = allfiles + filename + ':::'
                    movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', filename)
                    if search(movie, alldata) is None:
                        self.movielist.append(filename)
                        date = os.path.getmtime(filename)
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
            f = open(self.database, 'w')
            f.write(data)
            f.close()
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
                url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + series + self.language
                self.getTVDbData(url, '0')
            else:
                movie = transMOVIE(self.name)
                movie = sub('\\+[1-2][0-9][0-9][0-9]', '', movie)
                url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s' % (tmdb_api_key, movie + self.language)
                self.getTMDbData(url, '0', False)
        return

    def getTMDbData(self, url, tmdbid, renew):
        self.tmdbCount += 1
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            output = ''

        if search('"total_results":0', output) is not None:
            series = self.name + 'FIN'
            series = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('FIN', '', series)
            series = transSERIES(series)
            url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + series + self.language
            self.getTVDbData(url, '0')
        else:
            output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
            if tmdbid == '0':
                tmdbid = re.findall('"id":(.*?),', output)
                try:
                    tmdbid = tmdbid[0]
                except IndexError:
                    tmdbid = '0'

                name = re.findall('"title":"(.*?)"', output)
                backdrop = re.findall('"backdrop_path":"(.*?)"', output)
                year = re.findall('"release_date":"(.*?)"', output)
                poster = re.findall('"poster_path":"(.*?)"', output)
                rating = re.findall('"vote_average":(.*?),', output)
                try:
                    self.namelist[self.dbcount - 1] = name[0]
                except IndexError:
                    self.namelist[self.dbcount - 1] = self.name

                try:
                    self.backdroplist.append('https://image.tmdb.org/t/p/w1280' + backdrop[0])
                except IndexError:
                    self.backdroplist.append(default_backdrop)

                try:
                    self.posterlist.append('https://image.tmdb.org/t/p/w154' + poster[0])
                except IndexError:
                    self.posterlist.append(default_poster)

                url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdbid + self.language, tmdb_api_key)
                headers = {'Accept': 'application/json'}
                request = Request(url, headers=headers)
                try:
                    if pythonVer == 2:
                        output = urlopen(request, timeout=10).read()
                    else:
                        output = urlopen(request, timeout=10).read().decode('utf-8')
                except Exception:
                    output = ''

            plot = re.findall('"overview":"(.*?)","', output)
            if renew is True:
                output = sub('"belongs_to_collection":{.*?}', '', output)
                name = re.findall('"title":"(.*?)"', output)
                backdrop = re.findall('"backdrop_path":"(.*?)"', output)
                poster = re.findall('"poster_path":"(.*?)"', output)
            url = 'https://api.themoviedb.org/3/movie/%s?api_key=%s' % (tmdbid, tmdb_api_key)
            headers = {'Accept': 'application/json'}
            request = Request(url, headers=headers)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')
            except Exception:
                output = ''

            output = output.replace('&amp;', '&').replace('\\/', '/').replace('}', ',')
            output = sub('"belongs_to_collection":{.*?}', '', output)
            if not plot:
                plot = re.findall('"overview":"(.*?)","', output)
            genre = re.findall('"genres":[[]."id":[0-9]+,"name":"(.*?)"', output)
            genre2 = re.findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre3 = re.findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre4 = re.findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            genre5 = re.findall('"genres":[[]."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":".*?".,."id":[0-9]+,"name":"(.*?)"', output)
            country = re.findall('"iso_3166_1":"(.*?)"', output)
            runtime = re.findall('"runtime":(.*?),', output)
            if renew is True:
                year = re.findall('"release_date":"(.*?)"', output)
                rating = re.findall('"vote_average":(.*?),', output)
                if not backdrop:
                    backdrop = re.findall('"backdrop_path":"(.*?)"', output)
                if not poster:
                    poster = re.findall('"poster_path":"(.*?)"', output)
                try:
                    self.namelist[self.dbcount - 1] = name[0]
                except IndexError:
                    self.namelist[self.dbcount - 1] = self.name

                try:
                    self.backdroplist.append('https://image.tmdb.org/t/p/w1280' + backdrop[0])
                except IndexError:
                    self.backdroplist.append(default_backdrop)

                try:
                    self.posterlist.append('https://image.tmdb.org/t/p/w154' + poster[0])
                except IndexError:
                    self.posterlist.append(default_poster)

            url = 'https://api.themoviedb.org/3/movie/%s/casts?api_key=%s' % (tmdbid + self.language, tmdb_api_key)
            headers = {'Accept': 'application/json'}
            request = Request(url, headers=headers)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')
            except Exception:
                output = ''

            actor = re.findall('"name":"(.*?)"', output)
            actor2 = re.findall('"name":".*?"name":"(.*?)"', output)
            actor3 = re.findall('"name":".*?"name":".*?"name":"(.*?)"', output)
            actor4 = re.findall('"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor5 = re.findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor6 = re.findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            actor7 = re.findall('"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":".*?"name":"(.*?)"', output)
            director = re.findall('"job":"Director","name":"(.*?)"', output)
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
        agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
        request = Request(url, headers=agents)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
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
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                self.namelist.insert(self.dbcount - 1, name)
                self.movielist.insert(self.dbcount - 1, name)
                self.datelist.insert(self.dbcount - 1, str(datetime.datetime.now()))
                self.backdroplist.append(default_backdrop)
                self.posterlist.append(default_poster + '<episode>' + default_banner + '<episode>')
                self.makeDataEntry(self.dbcount - 1, False)
            else:
                self.backdroplist.append(default_backdrop)
                self.posterlist.append(default_poster)
                self.namelist[self.dbcount - 1] = self.name
                self.makeDataEntry(self.dbcount - 1, True)
        else:
            if seriesid == '0':
                seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
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
                url = 'https://www.thetvdb.com/api/%s/series/' + seriesid + '/default/' + season + '/' + episode + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
                agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
                request = Request(url, headers=agents)
                try:
                    if pythonVer == 2:
                        output = urlopen(request, timeout=10).read()
                    else:
                        output = urlopen(request, timeout=10).read().decode('utf-8')
                except Exception:
                    output = ''

                output = sub('\n', '', output)
                output = sub('&amp;', '&', output)
                episode = re.findall('<EpisodeName>(.*?)</EpisodeName>', output)
                year = re.findall('<FirstAired>([0-9]+)-', output)
                guest = re.findall('<GuestStars>[|](.*?)[|]</GuestStars>', output)
                director = re.findall('<Director>[|](.*?)[|]', output)
                if not director:
                    director = re.findall('<Director>(.*?)[|]', output)
                    if not director:
                        director = re.findall('<Director>(.*?)</Director>', output)
                plotfull = re.findall('<Overview>(.*?)</Overview>', output, re.S)
                rating = re.findall('<Rating>(.*?)</Rating>', output)
                eposter = re.findall('<filename>(.*?)</filename>', output)
            else:
                data = ''
                episode = []
                year = []
                guest = []
                director = []
                plotfull = []
                rating = []
                eposter = []
            url = 'https://www.thetvdb.com/api/%s/series/' + seriesid + '/' + config.plugins.moviebrowser.language.value + '.xml' % thetvdb_api_key
            agents = {'User-Agent': 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30)'}
            request = Request(url, headers=agents)
            try:
                if pythonVer == 2:
                    output = urlopen(request, timeout=10).read()
                else:
                    output = urlopen(request, timeout=10).read().decode('utf-8')
            except Exception:
                output = ''

            output = sub('\n', '', output)
            output = sub('&amp;', '&', output)
            output = sub('&quot;', '"', output)
            name = re.findall('<SeriesName>(.*?)</SeriesName>', output)
            runtime = re.findall('<Runtime>(.*?)</Runtime>', output)
            if not rating:
                rating = re.findall('<Rating>(.*?)</Rating>', output)
            actors = re.findall('<Actors>(.*?)</Actors>', output)
            actor = actor2 = actor3 = actor4 = actor5 = actor6 = actor7 = genre = genre2 = genre3 = genre4 = genre5 = []
            try:
                actor = re.findall('[|](.*?)[|]', actors[0])
                actor2 = re.findall('[|].*?[|](.*?)[|]', actors[0])
                actor3 = re.findall('[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor4 = re.findall('[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor5 = re.findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor6 = re.findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
                actor7 = re.findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                pass

            genres = re.findall('<Genre>(.*?)</Genre>', output)
            try:
                genre = re.findall('[|](.*?)[|]', genres[0])
                genre2 = re.findall('[|].*?[|](.*?)[|]', genres[0])
                genre3 = re.findall('[|].*?[|].*?[|](.*?)[|]', genres[0])
                genre4 = re.findall('[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
                genre5 = re.findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                pass
            if not year:
                year = re.findall('<FirstAired>([0-9]+)-', output)
            if not plotfull:
                plotfull = re.findall('<Overview>(.*?)</Overview>', output, re.S)
            backdrop = re.findall('<fanart>(.*?)</fanart>', output)
            poster = re.findall('<poster>(.*?)</poster>', output)
            if self.newseries is True:
                eposter = re.findall('<banner>(.*?)</banner>', output)
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

            if config.plugins.moviebrowser.language.value == 'de':
                country = 'DE'
            elif config.plugins.moviebrowser.language.value == 'es':
                country = 'ES'
            elif config.plugins.moviebrowser.language.value == 'it':
                country = 'ITA'
            elif config.plugins.moviebrowser.language.value == 'fr':
                country = 'FR'
            elif config.plugins.moviebrowser.language.value == 'ru':
                country = 'RUS'
            else:
                country = 'USA'
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
                self.backdroplist.append(default_backdrop)

            try:
                if self.newseries is True:
                    if not eposter:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + default_banner + '<episode>')
                    elif eposter[0] == '':
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + default_banner + '<episode>')
                    else:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
                elif not eposter:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0])
                else:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
            except IndexError:
                if self.newseries is True:
                    self.posterlist.append(default_poster + '<episode>' + default_banner + '<episode>')
                else:
                    self.posterlist.append(default_poster)

            self.makeDataEntry(self.dbcount - 1, False)
        return

    def makeDataEntry(self, count, content):
        if self.renew is False:
            f = open(self.database, 'a')
            try:
                if content is True:
                    self.moviecount += 1
                    data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Movie:Top:::unseen:::\n'
                elif self.newseries is True:
                    self.newseries = False
                    data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:Top:::unseen:::\n'
                else:
                    name = self.namelist[count] + 'FIN'
                    name = sub('\\([Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                    name = sub('FIN', '', name)
                    name = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', name)
                    data = open(self.database).read()
                    if search(name + '\\(', data) is None:
                        self.newseries = True
                    self.seriescount += 1
                    data = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:::unseen:::\n'
                f.write(data)
                if config.plugins.moviebrowser.download.value == 'update':
                    url = self.backdroplist[count]
                    backdrop = sub('.*?[/]', '', url)
                    backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
                    if fileExists(backdrop):
                        pass
                    else:
                        try:
                            headers = {'Accept': 'application/json'}
                            request = Request(url, headers=headers)
                            if pythonVer == 2:
                                output = urlopen(request).read()
                            else:
                                output = urlopen(request).read().decode('utf-8')
                            fbackdrop = open(backdrop, 'w')
                            fbackdrop.write(output)
                            fbackdrop.close()
                        except Exception:
                            pass

            except IndexError:
                pass

            f.close()
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
                    data = open(self.database).read()
                    if search(name + '.*?:::Series:Top:::unseen:::\n', data) is None:
                        self.newseries = True
                        self.renew = False
                    self.seriescount += 1
                    newdata = self.namelist[count] + ':::' + self.movielist[count] + ':::' + self.datelist[count] + ':::' + self.infolist[count][0] + ':::' + self.infolist[count][1] + ':::' + self.infolist[count][2] + ':::' + self.infolist[count][3] + ':::' + self.infolist[count][4] + ':::' + self.infolist[count][5] + ':::' + self.infolist[count][6] + ':::' + self.plotlist[count] + ':::' + self.posterlist[count] + ':::' + self.backdroplist[count] + ':::Series:::unseen:::'
            except IndexError:
                newdata = ''

            movie = self.movielist[count]
            movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
            data = open(self.database).read()
            if search(movie, data) is not None:
                for line in data.split('\n'):
                    if search(movie, line) is not None:
                        data = data.replace(line, newdata)

                f = open(self.database, 'w')
                f.write(data)
                f.close()
        if self.newseries is True:
            self.dbcount += 1
            self.dbcountmax += 1
            series = self.name + 'FIN'
            series = sub(' - .[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', series)
            series = sub('FIN', '', series)
            series = transSERIES(series)
            url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + series + self.language
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
                    url = 'https://www.thetvdb.com/api/GetSeries.php?seriesname=' + series + self.language
                    try:
                        self.getTVDbData(url, '0')
                    except RuntimeError:
                        return (1, self.orphaned, self.moviecount, self.seriescount)

                else:
                    movie = transMOVIE(self.name)
                    movie = sub('\\+[1-2][0-9][0-9][0-9]', '', movie)
                    url = 'https://api.themoviedb.org/3/search/movie?api_key=%s&query=%s' % (tmdb_api_key, movie + self.language)
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
            if self.renew is False:
                f = open(self.updatelog, 'a')
                f.write(result)
                f.close()
                return (found, orphaned, moviecount, seriescount)
            return True

    def sortDatabase(self):
        f = open(self.database, 'r')
        series = ''
        for line in f:
            if ':::Series:::' in line:
                series = series + line

        f.close()
        fseries = open(self.database + '.series', 'w')
        fseries.write(series)
        fseries.close()
        fseries = open(self.database + '.series', 'r')
        series = fseries.readlines()
        series.sort(key=lambda line: line.split(':::')[0])
        fseries.close()
        fseries = open(self.database + '.series', 'w')
        fseries.writelines(series)
        fseries.close()
        f = open(self.database, 'r')
        movies = ''
        for line in f:
            if ':::Series:::' not in line:
                movies = movies + line

        f.close()
        fmovies = open(self.database + '.movies', 'w')
        fmovies.write(movies)
        fmovies.close()
        fmovies = open(self.database + '.movies', 'r')
        lines = fmovies.readlines()
        fmovies.close()
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

        f = open(self.database + '.movies', 'w')
        f.writelines(lines)
        f.close()
        files = [self.database + '.movies', self.database + '.series']
        with open(self.database + '.sorted', 'w') as outfile:
            for name in files:
                with open(name) as infile:
                    outfile.write(infile.read())

        if fileExists(self.database + '.movies'):
            os.remove(self.database + '.movies')
        if fileExists(self.database + '.series'):
            os.remove(self.database + '.series')
        os.rename(self.database + '.sorted', self.database)


class movieControlList(Screen):

    def __init__(self, session, list, index, content):
        skin = skin_path + "movieControlList.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieControlList.xml"
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
        self['label'] = Label('= MovieCut')
        self['label2'] = Label('= CutListEditor')
        self['label3'] = Label('Info = ')
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions', 'ChannelSelectBaseActions', 'HelpActions', 'NumberActions'], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.zap,
            'prevBouquet': self.zap,
            'red': self.movieCut,
            'green': self.cutlistEditor,
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
                        res.append(MultiContentEntryText(pos=(0, 0), size=(1700, 30), font=28, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i][0]))
                    else:
                        series = sub('[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(MultiContentEntryText(pos=(0, 0), size=(1700, 30), font=28, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=series))
                else:
                    if self.content != ':::Series:::':
                        res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 25), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i][0]))
                    else:
                        series = sub('[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                        res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 25), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=series))

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
        if config.plugins.moviebrowser.showfolder.value == 'yes':
            totalMovies -= 1
        free = 'Free Space:'
        folder = 'Movie Folder'
        movies = 'Movies'
        series = 'Series'
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
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
                (_('Movie File Informations', 'info')),
                (_('Delete Movie File', 'delete')),
                (_('Blacklist Movie File', 'blacklist')),
                (_('Database Update Log', 'update')),
                (_('Database Timer Log', 'timer')),
                (_('Cleanup Cache Folder Log', 'cleanup'))
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
                size = os.path.getsize(moviefile)
                suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
                suffixIndex = 0
                while size > 1024:
                    suffixIndex += 1
                    size = size // 1024.0

                size = round(size, 2)
                size = str(size) + ' ' + suffixes[suffixIndex]
                date = os.path.getmtime(moviefile)
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
                for root, dirs, files in os.walk(folder, topdown=False, onerror=None, followlinks=True):
                    for name in dirs:
                        folder = os.path.join(root, name)
                        infotext = infotext + folder + '\n'

            else:
                size = os.path.getsize(moviefile)
                suffixes = ['B', 'KB', 'MB', 'GB', 'TB']
                suffixIndex = 0
                while size > 1024:
                    suffixIndex += 1
                    size = size // 1024.0

                size = round(size, 2)
                size = str(size) + ' ' + suffixes[suffixIndex]
                date = os.path.getmtime(moviefile)
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
            data = open(updatelog).read()
            self['log'].setText(data)
        elif choice == 'timer':
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open(timerlog).read()
            self['log'].setText(data)
        else:
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open(cleanuplog).read()
            self['log'].setText(data)
        return

    def cutlistEditor(self):
        if self.ready is True:
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/CutListEditor/plugin.pyo'):
                from Plugins.Extensions.CutListEditor.plugin import CutListEditor
                index = self['list'].getSelectedIndex()
                moviefile = self.list[index][1]
                if moviefile.endswith('.ts'):
                    service = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + moviefile)
                    if config.plugins.moviebrowser.m1v.value == 'no':
                        self.session.nav.stopService()
                    self.session.openWithCallback(self.cutlist_return, CutListEditor, service)
                self.session.open(MessageBox, _('\nThe CutListEditor plugin supports only records with the box.'), MessageBox.TYPE_ERROR)
            else:
                self.session.openWithCallback(self.CutListInstall, MessageBox, _('\nThe CutListEditor plugin is not installed.\n\nThe plugin can be installed automatically if it exists on the feed of your image. Search for the plugin now and install it if present on the feed?'), MessageBox.TYPE_YESNO)

    def cutlist_return(self):
        if config.plugins.moviebrowser.m1v.value == 'no':
            self.session.nav.stopService()
            self.session.nav.playService(self.oldService)
        else:
            index = self['list'].getSelectedIndex()
            backdropurl = self.list[index][2]
            backdrop = sub('.*?[/]', '', backdropurl)
            backdrop = config.plugins.moviebrowser.cachefolder.value + '/' + backdrop
            backdrop_m1v = backdrop.replace('.jpg', '.m1v')
            if fileExists(backdrop_m1v):
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)

    def movieCut(self):
        if self.ready is True:
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieCut/plugin.pyo'):
                from Plugins.Extensions.MovieCut.plugin import MovieCut
                index = self['list'].getSelectedIndex()
                moviefile = self.list[index][1]
                if moviefile.endswith('.ts'):
                    service = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + moviefile)
                    self.session.open(MovieCut, service)
                else:
                    self.session.open(MessageBox, _('\nThe MovieCut plugin supports only records with the box.'), MessageBox.TYPE_ERROR)
            else:
                self.session.openWithCallback(self.MovieCutInstall, MessageBox, _('\nThe MovieCut plugin is not installed.\n\nThe plugin can be installed automatically if it exists on the feed of your image. Search for the plugin now and install it if present on the feed?'), MessageBox.TYPE_YESNO)

    def CutListInstall(self, answer):
        if answer is True:
            self.container = eConsoleAppContainer()
            self.container.appClosed.append(self.finishedCutList)
            self.container.execute('opkg update && opkg install enigma2-plugin-extensions-cutlisteditor')

    def finishedCutList(self, retval):
        del self.container.appClosed[:]
        del self.container
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/CutListEditor/plugin.pyo'):
            self.session.openWithCallback(self.restartGUI, MessageBox, _('\nThe CutListEditor plugin was installed.\nPlease restart Enigma.'), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _('\nThe CutListEditor plugin is not present on the feed of your image.\n\nPlease install the CutListEditor plugin manually.'), MessageBox.TYPE_ERROR)

    def MovieCutInstall(self, answer):
        if answer is True:
            self.container = eConsoleAppContainer()
            self.container.appClosed.append(self.finishedMovieCut)
            self.container.execute('opkg update && opkg install enigma2-plugin-extensions-moviecut')

    def finishedMovieCut(self, retval):
        del self.container.appClosed[:]
        del self.container
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieCut/plugin.pyo'):
            self.session.openWithCallback(self.restartGUI, MessageBox, _('\nThe MovieCut plugin was installed.\nPlease restart Enigma.'), MessageBox.TYPE_YESNO)
        else:
            self.session.open(MessageBox, _('\nThe MovieCut plugin is not present on the feed of your image.\n\nPlease install the CutListEditor plugin manually.'), MessageBox.TYPE_ERROR)

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
                database = dbmovie
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                if fileExists(movie):
                    os.remove(movie)
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if search('[.]ts', movie) is not None:
                    eitfile = sub('[.]ts', '.eit', movie)
                    if fileExists(eitfile):
                        os.remove(eitfile)
                    if fileExists(movie + '.ap'):
                        os.remove(movie + '.ap')
                    if fileExists(movie + '.cuts'):
                        os.remove(movie + '.cuts')
                    if fileExists(movie + '.meta'):
                        os.remove(movie + '.meta')
                    if fileExists(movie + '.sc'):
                        os.remove(movie + '.sc')
                    if fileExists(movie + '_mp.jpg'):
                        os.remove(movie + '_mp.jpg')
                else:
                    subfile = sub(movie[-4:], '.sub', movie)
                    if fileExists(subfile):
                        os.remove(subfile)
                    srtfile = sub(movie[-4:], '.srt', movie)
                    if fileExists(srtfile):
                        os.remove(srtfile)
                data = open(database).read()
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

                f = open(database, 'w')
                f.write(data)
                f.close()
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
                database = dbmovie
                blacklist = blacklistmovie
                index = self['list'].getSelectedIndex()
                name = self.list[index][0]
                movie = self.list[index][1]
                movie = sub('\\(|\\)|\\[|\\]|\\+|\\?', '.', movie)
                if fileExists(blacklist):
                    fremove = open(blacklist, 'a')
                else:
                    fremove = open(blacklist, 'w')
                data = open(database).read()
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

                f = open(database, 'w')
                f.write(data)
                f.close()
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

    def exit(self):
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

        skin = skin_path + "movieDatabase.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieDatabase.xml"
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
        self.database = dbmovie
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
        if fileExists(self.database):
            count = 0
            index = 0
            f = open(self.database, 'r')
            for line in f:
                movieline = line.split(':::')
                poster = default_poster
                backdrop = default_backdrop
                media = '\n'
                name = movie = date = runtime = rating = director = actors = year = country = " "
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 30), font=28, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=name))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=name))
                self.listentries.append(res)

            self['list'].l.setList(self.listentries)
            self['list'].moveToIndex(index)
            self.selectList()
            self.ready = True
            totalMovies = len(self.list)
            database = _('Database')
            free = _('Free Space:')
            folder = _('Movie Folder')
            movies = _('Movies')
            if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
                movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(1200, 25), font=28, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list2[i]))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list2[i]))
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
        if newdata and newdata != '' and newdata != self.data:
            if self.first is True:
                self.first = False
                newdata = newdata + ':::'
                olddata = self.data + ':::'
            else:
                newdata = ':::' + newdata + ':::'
                olddata = ':::' + self.data + ':::'
            database = open(self.database).read()
            for line in database.split('\n'):
                if search(self.movie, line) is not None:
                    newline = line.replace(olddata, newdata)
                    database = database.replace(line, newline)

            f = open(self.database + '.new', 'w')
            f.write(database)
            f.close()
            os.rename(self.database + '.new', self.database)
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

    def exit(self):
        if self.hideflag is False:
            self.hideflag = True
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

        skin = skin_path + "moviesList.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/moviesList.xml"
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(810, 225), font=28, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
                    res.append(MultiContentEntryText(pos=(10, 13), size=(800, 45), font=28, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.titles[x]))
                    res.append(MultiContentEntryText(pos=(10, 54), size=(200, 45), font=28, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.year[x]))
                    res.append(MultiContentEntryText(pos=(10, 260), size=(200, 45), font=28, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(10 * round(float(self.rating[x]), 1)) // 10

                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(620, 125), font=24, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
                    res.append(MultiContentEntryText(pos=(5, 13), size=(610, 30), font=24, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.titles[x]))
                    res.append(MultiContentEntryText(pos=(5, 48), size=(200, 30), font=26, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.year[x]))
                    res.append(MultiContentEntryText(pos=(5, 48), size=(200, 30), font=26, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.country[x]))
                    rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(10 * round(float(self.rating[x]), 1)) // 10

            except (IndexError, ValueError):
                rating = 0

            try:
                if screenwidth.width() == 1920:
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 90), size=(350, 45), png=loadPNG(png)))
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(10, 90), size=(rating, 45), png=loadPNG(png2)))
                    res.append(MultiContentEntryText(pos=(410, 90), size=(50, 45), font=28, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.rating[x]))
                else:
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(210, 21), png=loadPNG(png)))
                    res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(rating, 21), png=loadPNG(png2)))
                    res.append(MultiContentEntryText(pos=(225, 84), size=(50, 21), font=26, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.rating[x]))
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
                    os.remove(self.banner1)
                if fileExists(self.banner2):
                    os.remove(self.banner2)
                if fileExists(self.banner3):
                    os.remove(self.banner3)
                if fileExists(self.banner4):
                    os.remove(self.banner4)
                self.close(current, self.choice)

    def updateMovie(self, choice):
        c = self['list'].getSelectedIndex()
        current = self.id[c]
        self.choice = choice and choice[1]
        if self.choice == 'movie':
            if fileExists(self.poster1):
                os.remove(self.poster1)
            if fileExists(self.poster2):
                os.remove(self.poster2)
            if fileExists(self.poster3):
                os.remove(self.poster3)
            if fileExists(self.poster4):
                os.remove(self.poster4)
            self.close(current, self.choice)
        elif self.choice == 'poster':
            url = 'https://api.themoviedb.org/3/movie/' + current + '/images?api_key=%s' % tmdb_api_key
            self.getTMDbPosters(url)
        elif self.choice == 'backdrop':
            url = 'https://api.themoviedb.org/3/movie/' + current + '/images?api_key=%s' % tmdb_api_key
            self.getTMDbBackdrops(url)

    def getTMDbPosters(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = re.sub('"backdrops".*?"posters"', '', output, flags=re.S)
        output = sub('"file_path":"', '"file_path":"https://image.tmdb.org/t/p/w154', output)
        self.banner = re.findall('"file_path":"(.*?)"', output)
        self.makeList()

    def getTMDbBackdrops(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTMDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output + 'FIN'
        output = re.sub('"posters".*?FIN', '', output, flags=re.S)
        output = sub('"file_path":"', '"file_path":"https://image.tmdb.org/t/p/w1280', output)
        self.banner = re.findall('"file_path":"(.*?)"', output)
        self.makeList()

    def updateSeries(self, choice):
        c = self['list'].getSelectedIndex()
        current = self.id[c]
        self.choice = choice and choice[1]
        if self.choice == 'series':
            if fileExists(self.poster1):
                os.remove(self.poster1)
            if fileExists(self.poster2):
                os.remove(self.poster2)
            if fileExists(self.poster3):
                os.remove(self.poster3)
            if fileExists(self.poster4):
                os.remove(self.poster4)
            self.close(current, self.choice)
        elif self.choice == 'banner':
            url = 'https://thetvdb.com/api/%s/series/' + current + '/banners.xml' % thetvdb_api_key
            self.getTVDbBanners(url)
        elif self.choice == 'backdrop':
            url = 'https://thetvdb.com/api/%s/series/' + current + '/banners.xml' % thetvdb_api_key
            self.getTVDbBackdrops(url)

    def getTVDbBanners(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = sub('<BannerPath>graphical', '<BannerPath>https://www.thetvdb.com/banners/graphical', output)
        self.banner = re.findall('<BannerPath>(.*?)</BannerPath>\n\\s+<BannerType>series</BannerType>', output)
        self.makeList()

    def getTVDbBackdrops(self, url):
        headers = {'Accept': 'application/json'}
        request = Request(url, headers=headers)
        try:
            if pythonVer == 2:
                output = urlopen(request, timeout=10).read()
            else:
                output = urlopen(request, timeout=10).read().decode('utf-8')
        except Exception:
            self.session.open(MessageBox, _('\nTheTVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = sub('<BannerPath>fanart', '<BannerPath>https://www.thetvdb.com/banners/fanart', output)
        self.banner = re.findall('<BannerPath>(.*?)</BannerPath>\n\\s+<BannerType>fanart</BannerType>', output)
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
                res.append(MultiContentEntryText(pos=(0, 0), size=(1265, 225), font=28, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
                self.imagelist.append(res)
                self['piclist'].l.setList(self.imagelist)
                self['piclist'].l.setItemHeight(225)
            else:
                res.append(MultiContentEntryText(pos=(0, 0), size=(710, 125), font=26, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
                self.imagelist.append(res)
                self['piclist'].l.setList(self.imagelist)
                self['piclist'].l.setItemHeight(125)

        self['piclist'].show()
        self.first = False
        self.ready = True

    def down(self):
        if self.ready is True:
            if self.first is True:
                try:
                    c = self['list'].getSelectedIndex()
                except IndexError:
                    return

                self['list'].down()
                if c + 1 == len(self.titles):
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

                elif c % 4 == 3:
                    try:
                        poster1 = self.poster[c + 1]
                        self.download(poster1, self.getPoster1)
                        self['poster1'].show()
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c + 2]
                        self.download(poster2, self.getPoster2)
                        self['poster2'].show()
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c + 3]
                        self.download(poster3, self.getPoster3)
                        self['poster3'].show()
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c + 4]
                        self.download(poster4, self.getPoster4)
                        self['poster4'].show()
                    except IndexError:
                        self['poster4'].hide()

            else:
                try:
                    c = self['piclist'].getSelectedIndex()
                except IndexError:
                    return

                self['piclist'].down()
                if c + 1 == len(self.titles):
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

                elif c % 4 == 3:
                    try:
                        banner1 = self.banner[c + 1]
                        self.download(banner1, self.getBanner1)
                        self['banner1'].show()
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c + 2]
                        self.download(banner2, self.getBanner2)
                        self['banner2'].show()
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c + 3]
                        self.download(banner3, self.getBanner3)
                        self['banner3'].show()
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c + 4]
                        self.download(banner4, self.getBanner4)
                        self['banner4'].show()
                    except IndexError:
                        self['banner4'].hide()

    def up(self):
        if self.ready is True:
            if self.first is True:
                try:
                    c = self['list'].getSelectedIndex()
                except IndexError:
                    return

                self['list'].up()
                if c == 0:
                    length = len(self.titles)
                    d = length % 4
                    if d == 0:
                        d = 4
                    try:
                        poster1 = self.poster[length - d]
                        self.download(poster1, self.getPoster1)
                        self['poster1'].show()
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[length - d + 1]
                        self.download(poster2, self.getPoster2)
                        self['poster2'].show()
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[length - d + 2]
                        self.download(poster3, self.getPoster3)
                        self['poster3'].show()
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[length - d + 3]
                        self.download(poster4, self.getPoster4)
                        self['poster4'].show()
                    except IndexError:
                        self['poster4'].hide()

                elif c % 4 == 0:
                    try:
                        poster1 = self.poster[c - 4]
                        self.download(poster1, self.getPoster1)
                        self['poster1'].show()
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c - 3]
                        self.download(poster2, self.getPoster2)
                        self['poster2'].show()
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c - 2]
                        self.download(poster3, self.getPoster3)
                        self['poster3'].show()
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c - 1]
                        self.download(poster4, self.getPoster4)
                        self['poster4'].show()
                    except IndexError:
                        self['poster4'].hide()

            else:
                try:
                    c = self['piclist'].getSelectedIndex()
                except IndexError:
                    return

                self['piclist'].up()
                if c == 0:
                    length = len(self.titles)
                    d = length % 4
                    if d == 0:
                        d = 4
                    try:
                        banner1 = self.banner[length - d]
                        self.download(banner1, self.getBanner1)
                        self['banner1'].show()
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[length - d + 1]
                        self.download(banner2, self.getBanner2)
                        self['banner2'].show()
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[length - d + 2]
                        self.download(banner3, self.getBanner3)
                        self['banner3'].show()
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[length - d + 3]
                        self.download(banner4, self.getBanner4)
                        self['banner4'].show()
                    except IndexError:
                        self['banner4'].hide()

                elif c % 4 == 0:
                    try:
                        banner1 = self.banner[c - 4]
                        self.download(banner1, self.getBanner1)
                        self['banner1'].show()
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c - 3]
                        self.download(banner2, self.getBanner2)
                        self['banner2'].show()
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c - 2]
                        self.download(banner3, self.getBanner3)
                        self['banner3'].show()
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c - 1]
                        self.download(banner4, self.getBanner4)
                        self['banner4'].show()
                    except IndexError:
                        self['banner4'].hide()

    def rightDown(self):
        if self.ready is True:
            if self.first is True:
                try:
                    c = self['list'].getSelectedIndex()
                except IndexError:
                    return

                self['list'].pageDown()
                length = len(self.titles)
                d = c % 4
                e = length % 4
                if e == 0:
                    e = 4
                if c + e >= length:
                    pass
                elif d == 0:
                    try:
                        poster1 = self.poster[c + 4]
                        self.download(poster1, self.getPoster1)
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c + 5]
                        self.download(poster2, self.getPoster2)
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c + 6]
                        self.download(poster3, self.getPoster3)
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c + 7]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        self['poster4'].hide()

                elif d == 1:
                    try:
                        poster1 = self.poster[c + 3]
                        self.download(poster1, self.getPoster1)
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c + 4]
                        self.download(poster2, self.getPoster2)
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c + 5]
                        self.download(poster3, self.getPoster3)
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c + 6]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        self['poster4'].hide()

                elif d == 2:
                    try:
                        poster1 = self.poster[c + 2]
                        self.download(poster1, self.getPoster1)
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c + 3]
                        self.download(poster2, self.getPoster2)
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c + 4]
                        self.download(poster3, self.getPoster3)
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c + 5]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        self['poster4'].hide()

                elif d == 3:
                    try:
                        poster1 = self.poster[c + 1]
                        self.download(poster1, self.getPoster1)
                    except IndexError:
                        self['poster1'].hide()

                    try:
                        poster2 = self.poster[c + 2]
                        self.download(poster2, self.getPoster2)
                    except IndexError:
                        self['poster2'].hide()

                    try:
                        poster3 = self.poster[c + 3]
                        self.download(poster3, self.getPoster3)
                    except IndexError:
                        self['poster3'].hide()

                    try:
                        poster4 = self.poster[c + 4]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        self['poster4'].hide()

            else:
                try:
                    c = self['piclist'].getSelectedIndex()
                except IndexError:
                    return

                self['piclist'].pageDown()
                length = len(self.titles)
                d = c % 4
                e = length % 4
                if e == 0:
                    e = 4
                if c + e >= length:
                    pass
                elif d == 0:
                    try:
                        banner1 = self.banner[c + 4]
                        self.download(banner1, self.getBanner1)
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c + 5]
                        self.download(banner2, self.getBanner2)
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c + 6]
                        self.download(banner3, self.getBanner3)
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c + 7]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        self['banner4'].hide()

                elif d == 1:
                    try:
                        banner1 = self.banner[c + 3]
                        self.download(banner1, self.getBanner1)
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c + 4]
                        self.download(banner2, self.getBanner2)
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c + 5]
                        self.download(banner3, self.getBanner3)
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c + 6]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        self['banner4'].hide()

                elif d == 2:
                    try:
                        banner1 = self.banner[c + 2]
                        self.download(banner1, self.getBanner1)
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c + 3]
                        self.download(banner2, self.getBanner2)
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c + 4]
                        self.download(banner3, self.getBanner3)
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c + 5]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        self['banner4'].hide()

                elif d == 3:
                    try:
                        banner1 = self.banner[c + 1]
                        self.download(banner1, self.getBanner1)
                    except IndexError:
                        self['banner1'].hide()

                    try:
                        banner2 = self.banner[c + 2]
                        self.download(banner2, self.getBanner2)
                    except IndexError:
                        self['banner2'].hide()

                    try:
                        banner3 = self.banner[c + 3]
                        self.download(banner3, self.getBanner3)
                    except IndexError:
                        self['banner3'].hide()

                    try:
                        banner4 = self.banner[c + 4]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        self['banner4'].hide()

    def leftUp(self):
        if self.ready is True:
            if self.first is True:
                try:
                    c = self['list'].getSelectedIndex()
                except IndexError:
                    return

                self['list'].pageUp()
                d = c % 4
                if c < 4:
                    pass
                elif d == 0:
                    try:
                        poster1 = self.poster[c - 4]
                        self.download(poster1, self.getPoster1)
                        poster2 = self.poster[c - 3]
                        self.download(poster2, self.getPoster2)
                        poster3 = self.poster[c - 2]
                        self.download(poster3, self.getPoster3)
                        poster4 = self.poster[c - 1]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 1:
                    try:
                        poster1 = self.poster[c - 5]
                        self.download(poster1, self.getPoster1)
                        poster2 = self.poster[c - 4]
                        self.download(poster2, self.getPoster2)
                        poster3 = self.poster[c - 3]
                        self.download(poster3, self.getPoster3)
                        poster4 = self.poster[c - 2]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 2:
                    try:
                        poster1 = self.poster[c - 6]
                        self.download(poster1, self.getPoster1)
                        poster2 = self.poster[c - 5]
                        self.download(poster2, self.getPoster2)
                        poster3 = self.poster[c - 4]
                        self.download(poster3, self.getPoster3)
                        poster4 = self.poster[c - 3]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 3:
                    try:
                        poster1 = self.poster[c - 7]
                        self.download(poster1, self.getPoster1)
                        poster2 = self.poster[c - 6]
                        self.download(poster2, self.getPoster2)
                        poster3 = self.poster[c - 5]
                        self.download(poster3, self.getPoster3)
                        poster4 = self.poster[c - 4]
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                self['poster1'].show()
                self['poster2'].show()
                self['poster3'].show()
                self['poster4'].show()
            else:
                try:
                    c = self['piclist'].getSelectedIndex()
                except IndexError:
                    return

                self['piclist'].pageUp()
                d = c % 4
                if c < 4:
                    pass
                elif d == 0:
                    try:
                        banner1 = self.banner[c - 4]
                        self.download(banner1, self.getBanner1)
                        banner2 = self.banner[c - 3]
                        self.download(banner2, self.getBanner2)
                        banner3 = self.banner[c - 2]
                        self.download(banner3, self.getBanner3)
                        banner4 = self.banner[c - 1]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        pass

                elif d == 1:
                    try:
                        banner1 = self.banner[c - 5]
                        self.download(banner1, self.getBanner1)
                        banner2 = self.banner[c - 4]
                        self.download(banner2, self.getBanner2)
                        banner3 = self.banner[c - 3]
                        self.download(banner3, self.getBanner3)
                        banner4 = self.banner[c - 2]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        pass

                elif d == 2:
                    try:
                        banner1 = self.banner[c - 6]
                        self.download(banner1, self.getBanner1)
                        banner2 = self.banner[c - 5]
                        self.download(banner2, self.getBanner2)
                        banner3 = self.banner[c - 4]
                        self.download(banner3, self.getBanner3)
                        banner4 = self.banner[c - 3]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        pass

                elif d == 3:
                    try:
                        banner1 = self.banner[c - 7]
                        self.download(banner1, self.getBanner1)
                        banner2 = self.banner[c - 6]
                        self.download(banner2, self.getBanner2)
                        banner3 = self.banner[c - 5]
                        self.download(banner3, self.getBanner3)
                        banner4 = self.banner[c - 4]
                        self.download(banner4, self.getBanner4)
                    except IndexError:
                        pass

                self['banner1'].show()
                self['banner2'].show()
                self['banner3'].show()
                self['banner4'].show()

    def gotoEnd(self):
        if self.ready is True:
            end = len(self.titles) - 1
            if end > 4:
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
        f = open(self.poster1, 'wb')
        f.write(output)
        f.close()
        self.showPoster1(self.poster1)

    def showPoster1(self, poster1):
        if fileExists(poster1):
            self["poster1"].instance.setPixmapFromFile(poster1)
            self['poster1'].show()
        return

    def getPoster2(self, output):
        f = open(self.poster2, 'wb')
        f.write(output)
        f.close()
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        if fileExists(poster2):
            self["poster2"].instance.setPixmapFromFile(poster2)
            self['poster2'].show()
        return

    def getPoster3(self, output):
        f = open(self.poster3, 'wb')
        f.write(output)
        f.close()
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        if fileExists(poster3):
            self["poster3"].instance.setPixmapFromFile(poster3)
            self['poster3'].show()
        return

    def getPoster4(self, output):
        f = open(self.poster4, 'wb')
        f.write(output)
        f.close()
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        if fileExists(poster4):
            self["poster4"].instance.setPixmapFromFile(poster4)
            self['poster4'].show()
        return

    def getBanner1(self, output):
        f = open(self.banner1, 'wb')
        f.write(output)
        f.close()
        self.showBanner1(self.banner1)

    def showBanner1(self, banner1):
        if fileExists(banner1):
            self["banner1"].instance.setPixmapFromFile(banner1)
            self['banner1'].show()
        return

    def getBanner2(self, output):
        f = open(self.banner2, 'wb')
        f.write(output)
        f.close()
        self.showBanner2(self.banner2)

    def showBanner2(self, banner2):
        if fileExists(banner2):
            self["banner2"].instance.setPixmapFromFile(banner2)
            self['banner2'].show()
        return

    def getBanner3(self, output):
        f = open(self.banner3, 'wb')
        f.write(output)
        f.close()
        self.showBanner3(self.banner3)

    def showBanner3(self, banner3):
        if fileExists(banner3):
            self["banner3"].instance.setPixmapFromFile(banner3)
            self['banner3'].show()
        return

    def getBanner4(self, output):
        f = open(self.banner4, 'wb')
        f.write(output)
        f.close()
        self.showBanner4(self.banner4)

    def showBanner4(self, banner4):
        if fileExists(banner4):
            self["banner4"].instance.setPixmapFromFile(banner4)
            self['banner4'].show()
        return

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        # getPage(link).addCallback(name).addErrback(self.downloadError)
        callInThread(threadGetPage, url=link, file=None, success=name, fail=self.downloadError)

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

    def exit(self):
        if fileExists(self.poster1):
            os.remove(self.poster1)
        if fileExists(self.poster2):
            os.remove(self.poster2)
        if fileExists(self.poster3):
            os.remove(self.poster3)
        if fileExists(self.poster4):
            os.remove(self.poster4)
        if fileExists(self.banner1):
            os.remove(self.banner1)
        if fileExists(self.banner2):
            os.remove(self.banner2)
        if fileExists(self.banner3):
            os.remove(self.banner3)
        if fileExists(self.banner4):
            os.remove(self.banner4)
        self.close(None, None)
        return


class filterList(Screen):

    def __init__(self, session, list, titel, filter, len, max):

        # if int(len) < 20:
            # listheight = int(len) * 25
            # screenheight = listheight + 48
            # screenheight = str(screenheight)
            # listheight = str(listheight)
        # else:
            # screenheight = '523'
            # listheight = '475'
        # if int(max) > 50:
            # screenwidth = '720'
            # listwidth = '700'
            # self.listwidth = 700
            # png = 'logoFilter4'
        # elif int(max) > 35:
            # screenwidth = '520'
            # listwidth = '500'
            # self.listwidth = 500
            # png = 'logoFilter3'
        # elif int(max) > 25:
            # screenwidth = '370'
            # listwidth = '350'
            # self.listwidth = 350
            # png = 'logoFilter2'
        # else:
            # screenwidth = '270'
            # listwidth = '250'
            # self.listwidth = 250
            # png = 'logoFilter'

        # self.dict = {
            # 'screenwidth': screenwidth,
            # 'screenheight': screenheight,
            # 'listwidth': listwidth,
            # 'listheight': listheight,
            # 'png': png
        # }

        skin = skin_path + "filterList.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/filterList.xml"
        # xskin = applySkinVars(skin, self.dict)
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(700, 25), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(500, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
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

    def exit(self):
        self.close(None)
        return


class filterSeasonList(Screen):

    def __init__(self, session, list, content):
        Screen.__init__(self, session)

        skin = skin_path + "filterSeasonList.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/filterSeasonList.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        self.hideflag = True
        self.content = content
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
            '4': self.resetFilter,
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(760, 30), font=26, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
                else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(510, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
                self.listentries.append(res)
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)
        totalSeasons = len(self.list)
        series = _('Series Episodes')
        free = _('Free Space:')
        folder = _('Movie Folder')
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
            try:
                stat = movieFolder
                freeSize = convert_size(float(stat.f_bfree * stat.f_bsize))
            except Exception as e:
                print(e)
                freeSize = "-?-"

            title = '%s %s (%s %s)' % (str(totalSeasons), series, str(freeSize), free)
            self.setTitle(title)
        else:
            title = '%s %s (%s offline)' % (str(totalSeasons), series, folder)
            self.setTitle(title)

    def ok(self):
        index = self['list'].getSelectedIndex()
        current = self.list[index]
        current = sub('Specials', '(S00', current)
        current = sub('specials', '(s00', current)
        current = sub('Season ', '(S', current)
        current = sub('season ', '(s', current)
        self.close(current)

    def resetFilter(self):
        self.close(self.content)

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

    def exit(self):
        self.close(None)
        return


class getABC(Screen):

    def __init__(self, session, ABC, XYZ):
        skin = skin_path + "getABC.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/getABC.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        if XYZ is True and ABC == 'ABC':
            self.field = 'WXYZ'
        else:
            self.field = ABC
        self['ABC'] = Label(self.field)
        self['actions'] = ActionMap(['OkCancelActions', 'ChannelSelectBaseActions', 'NumberActions'], {
            'cancel': self.quit,
            'ok': self.OK,
            'nextMarker': self.ABC,
            'prevMarker': self.WXYZ,
            '2': self._ABC,
            '3': self._DEF,
            '4': self._GHI,
            '5': self._JKL,
            '6': self._MNO,
            '7': self._PQRS,
            '8': self._TUV,
            '9': self._WXYZ
        })

        self.Timer = eTimer()
        self.Timer.callback.append(self.returnABC)
        self.Timer.start(2500, True)

    def ABC(self):
        self.Timer.start(2000, True)
        if self.field.startswith('A') or self.field.startswith('B') or self.field.startswith('C'):
            self.field = 'DEF'
        elif self.field.startswith('D') or self.field.startswith('E') or self.field.startswith('F'):
            self.field = 'GHI'
        elif self.field.startswith('G') or self.field.startswith('H') or self.field.startswith('I'):
            self.field = 'JKL'
        elif self.field.startswith('J') or self.field.startswith('K') or self.field.startswith('L'):
            self.field = 'MNO'
        elif self.field.startswith('M') or self.field.startswith('N') or self.field.startswith('O'):
            self.field = 'PQRS'
        elif self.field.startswith('P') or self.field.startswith('Q') or self.field.startswith('R') or self.field.startswith('S'):
            self.field = 'TUV'
        elif self.field.startswith('T') or self.field.startswith('U') or self.field.startswith('V'):
            self.field = 'WXYZ'
        elif self.field.startswith('W') or self.field.startswith('X') or self.field.startswith('Y') or self.field.startswith('Z'):
            self.field = 'ABC'
        self['ABC'].setText(self.field)

    def WXYZ(self):
        self.Timer.start(2000, True)
        if self.field.startswith('W') or self.field.startswith('X') or self.field.startswith('Y') or self.field.startswith('Z'):
            self.field = 'TUV'
        elif self.field.startswith('T') or self.field.startswith('U') or self.field.startswith('V'):
            self.field = 'PQRS'
        elif self.field.startswith('P') or self.field.startswith('Q') or self.field.startswith('R') or self.field.startswith('S'):
            self.field = 'MNO'
        elif self.field.startswith('M') or self.field.startswith('N') or self.field.startswith('O'):
            self.field = 'JKL'
        elif self.field.startswith('J') or self.field.startswith('K') or self.field.startswith('L'):
            self.field = 'GHI'
        elif self.field.startswith('G') or self.field.startswith('H') or self.field.startswith('I'):
            self.field = 'DEF'
        elif self.field.startswith('D') or self.field.startswith('E') or self.field.startswith('F'):
            self.field = 'ABC'
        elif self.field.startswith('A') or self.field.startswith('B') or self.field.startswith('C'):
            self.field = 'WXYZ'
        self['ABC'].setText(self.field)

    def _ABC(self):
        self.Timer.start(2000, True)
        if self.field != 'A' and self.field != 'B' and self.field != 'C':
            self.field = 'A'
        elif self.field == 'A':
            self.field = 'B'
        elif self.field == 'B':
            self.field = 'C'
        elif self.field == 'C':
            self.field = 'A'
        self['ABC'].setText(self.field)

    def _DEF(self):
        self.Timer.start(2000, True)
        if self.field != 'D' and self.field != 'E' and self.field != 'F':
            self.field = 'D'
        elif self.field == 'D':
            self.field = 'E'
        elif self.field == 'E':
            self.field = 'F'
        elif self.field == 'F':
            self.field = 'D'
        self['ABC'].setText(self.field)

    def _GHI(self):
        self.Timer.start(2000, True)
        if self.field != 'G' and self.field != 'H' and self.field != 'I':
            self.field = 'G'
        elif self.field == 'G':
            self.field = 'H'
        elif self.field == 'H':
            self.field = 'I'
        elif self.field == 'I':
            self.field = 'G'
        self['ABC'].setText(self.field)

    def _JKL(self):
        self.Timer.start(2000, True)
        if self.field != 'J' and self.field != 'K' and self.field != 'L':
            self.field = 'J'
        elif self.field == 'J':
            self.field = 'K'
        elif self.field == 'K':
            self.field = 'L'
        elif self.field == 'L':
            self.field = 'J'
        self['ABC'].setText(self.field)

    def _MNO(self):
        self.Timer.start(2000, True)
        if self.field != 'M' and self.field != 'N' and self.field != 'O':
            self.field = 'M'
        elif self.field == 'M':
            self.field = 'N'
        elif self.field == 'N':
            self.field = 'O'
        elif self.field == 'O':
            self.field = 'M'
        self['ABC'].setText(self.field)

    def _PQRS(self):
        self.Timer.start(2000, True)
        if self.field != 'P' and self.field != 'Q' and self.field != 'R' and self.field != 'S':
            self.field = 'P'
        elif self.field == 'P':
            self.field = 'Q'
        elif self.field == 'Q':
            self.field = 'R'
        elif self.field == 'R':
            self.field = 'S'
        elif self.field == 'S':
            self.field = 'P'
        self['ABC'].setText(self.field)

    def _TUV(self):
        self.Timer.start(2000, True)
        if self.field != 'T' and self.field != 'U' and self.field != 'V':
            self.field = 'T'
        elif self.field == 'T':
            self.field = 'U'
        elif self.field == 'U':
            self.field = 'V'
        elif self.field == 'V':
            self.field = 'T'
        self['ABC'].setText(self.field)

    def _WXYZ(self):
        self.Timer.start(2000, True)
        if self.field != 'W' and self.field != 'X' and self.field != 'Y' and self.field != 'Z':
            self.field = 'W'
        elif self.field == 'W':
            self.field = 'X'
        elif self.field == 'X':
            self.field = 'Y'
        elif self.field == 'Y':
            self.field = 'Z'
        elif self.field == 'Z':
            self.field = 'W'
        self['ABC'].setText(self.field)

    def OK(self):
        self.Timer.start(2000, True)
        if self.field == 'ABC':
            self.field = 'B'
        elif self.field == 'B':
            self.field = 'C'
        elif self.field == 'C':
            self.field = 'A'
        elif self.field == 'A':
            self.field = 'B'
        elif self.field == 'DEF':
            self.field = 'E'
        elif self.field == 'E':
            self.field = 'F'
        elif self.field == 'F':
            self.field = 'D'
        elif self.field == 'D':
            self.field = 'E'
        elif self.field == 'GHI':
            self.field = 'H'
        elif self.field == 'H':
            self.field = 'I'
        elif self.field == 'I':
            self.field = 'G'
        elif self.field == 'G':
            self.field = 'H'
        elif self.field == 'JKL':
            self.field = 'K'
        elif self.field == 'K':
            self.field = 'L'
        elif self.field == 'L':
            self.field = 'J'
        elif self.field == 'J':
            self.field = 'K'
        elif self.field == 'MNO':
            self.field = 'N'
        elif self.field == 'N':
            self.field = 'O'
        elif self.field == 'O':
            self.field = 'M'
        elif self.field == 'M':
            self.field = 'N'
        elif self.field == 'PQRS':
            self.field = 'Q'
        elif self.field == 'Q':
            self.field = 'R'
        elif self.field == 'R':
            self.field = 'S'
        elif self.field == 'S':
            self.field = 'P'
        elif self.field == 'P':
            self.field = 'Q'
        elif self.field == 'TUV':
            self.field = 'U'
        elif self.field == 'U':
            self.field = 'V'
        elif self.field == 'V':
            self.field = 'T'
        elif self.field == 'T':
            self.field = 'U'
        elif self.field == 'WXYZ':
            self.field = 'X'
        elif self.field == 'X':
            self.field = 'Y'
        elif self.field == 'Y':
            self.field = 'Z'
        elif self.field == 'Z':
            self.field = 'W'
        elif self.field == 'W':
            self.field = 'X'
        self['ABC'].setText(self.field)

    def returnABC(self):
        self.Timer.stop()
        self.close(self.field)

    def quit(self):
        self.Timer.stop()
        self.close(None)
        return


class switchScreen(Screen):

    def __init__(self, session, number, mode):
        skin = skin_path + "switchScreen.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/switchScreen.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

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
            self['label_select_1'].hide()
            self['label_select_2'].hide()
            self['label_select_3'].hide()
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

        self['actions'] = ActionMap(['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions'], {
            'ok': self.returnNumber,
            'cancel': self.quit,
            'down': self.next,
            'up': self.next,
            'red': self.next,
            '5': self.next
        })

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

    def returnNumber(self):
        self.Timer.stop()
        self.close(self.number)

    def quit(self):
        self.Timer.stop()
        self.close(None)
        return


class switchStart(Screen):

    def __init__(self, session, number):
        skin = skin_path + "switchStart.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/switchStart.xml"
        with open(skin, "r") as f:
            self.skin = f.read()
        Screen.__init__(self, session)
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
        self['actions'] = ActionMap(['OkCancelActions', 'NumberActions', 'ColorActions', 'DirectionActions', 'InfobarActions'], {
            'ok': self.returnNumber,
            'cancel': self.quit,
            'showMovies': self.next,
            'down': self.next,
            '5': self.next
        })
        self.Timer = eTimer()
        self.Timer.callback.append(self.returnNumber)
        self.Timer.start(4000, True)

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

    def returnNumber(self):
        self.Timer.stop()
        if self.number == 1:
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Movie:Top:::', ':::Movie:Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Movie:Top:::', ':::Movie:Top:::')
        elif self.number == 2:
            if config.plugins.moviebrowser.seriesstyle.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':::Series:Top:::', ':::Series:Top:::')
            elif config.plugins.moviebrowser.seriesstyle.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':::Series:Top:::', ':::Series:Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':::Series:Top:::', ':::Series:Top:::')
        elif self.number == 3:
            if config.plugins.moviebrowser.style.value == 'metrix':
                self.session.openWithCallback(self.close, movieBrowserMetrix, 0, ':Top:::', ':Top:::')
            elif config.plugins.moviebrowser.style.value == 'backdrop':
                self.session.openWithCallback(self.close, movieBrowserBackdrop, 0, ':Top:::', ':Top:::')
            else:
                self.session.openWithCallback(self.close, movieBrowserPosterwall, 0, ':Top:::', ':Top:::')

    def quit(self):
        self.close()


class helpScreen(Screen):

    def __init__(self, session):
        skin = skin_path + "helpScreen.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/helpScreen.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        self.setTitle(_('Movie Browser Key Assignment'))
        self['label'] = Label(_(': Update Database\n"     : Wikipedia Search\n     : Toggle Plugin Style\n     : Toggle hide/show plugin\nInfo Button: Toggle show/hide infos\nVideo Button: Update Database\nText Button: Edit Database\nStop Button: Mark movie as seen\nRadio Button: Delete/Blacklist movie\n<- -> Button: Go to first letter\nButton 1: CutListEditor/MovieCut/LogView\nButton 2: Renew infos on TMDb\nButton 3: Renew infos on TheTVDb\nButton 4: Hide/show seen movies\nButton 5: Toggle Movies/Series view\nButton 6: Movie Folder Selection\nButton 7: Movie Director Selection\nButton 8: Movie Actor Selection\nButton 9: Movie Genre Selection\nButton 0: Go to end of list'))
        self['actions'] = ActionMap(['OkCancelActions'], {
            'ok': self.close,
            'cancel': self.close
        }, -1)


class movieBrowserConfig(ConfigListScreen, Screen):

    def __init__(self, session):

        skin = skin_path + "movieBrowserConfig.xml"
        # if os.path.exists("/var/lib/dpkg/status"):
            # skin = skin_path + "DreamOS/movieBrowserConfig.xml"
        with open(skin, "r") as f:
            self.skin = f.read()

        Screen.__init__(self, session)
        
        self.onChangedEntry = []
        
        self.sortorder = config.plugins.moviebrowser.sortorder.value
        self.moviefolder = config.plugins.moviebrowser.moviefolder.value
        self.cachefolder = config.plugins.moviebrowser.cachefolder.value
        self.database = dbmovie
        self.m1v = config.plugins.moviebrowser.m1v.value
        # self.lang = config.plugins.moviebrowser.language.value
        self.timer_update = config.plugins.moviebrowser.timerupdate.value
        self.timer_hour = config.plugins.moviebrowser.timer.value[0]
        self.timer_min = config.plugins.moviebrowser.timer.value[1]
        self['save'] = Label(_('Save'))

        self['cancel'] = Label(_('Cancel'))
        self['plugin'] = Pixmap()
        self.ready = True

        # self.editListEntry = None        
        list = []
        # list.append(getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style))
        # list.append(getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle))
        # self.foldername = getConfigListEntry(_('Movie Folder:'), config.plugins.moviebrowser.moviefolder)
        # list.append(self.foldername)
        # list.append(getConfigListEntry(_('Cache Folder:'), config.plugins.moviebrowser.cachefolder))
        # list.append(getConfigListEntry(_('Movies or Series:'), config.plugins.moviebrowser.filter))
        # list.append(getConfigListEntry(_('Movies or Series Selection at Start:'), config.plugins.moviebrowser.showswitch))
        # list.append(getConfigListEntry(_('TMDb/TheTVDb Language:'), config.plugins.moviebrowser.language))
        # list.append(getConfigListEntry(_('Movie Sort Order:'), config.plugins.moviebrowser.sortorder))
        # list.append(getConfigListEntry(_('Show Backdrops:'), config.plugins.moviebrowser.backdrops))
        # list.append(getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v))
        # list.append(getConfigListEntry(_('Download new Backdrops:'), config.plugins.moviebrowser.download))
        # list.append(getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv))

        # list.append(getConfigListEntry(_('Show List of Movie Folder:'), config.plugins.moviebrowser.showfolder))

        # # list.append(getConfigListEntry(_('Plugin Sans Serif Font:'), config.plugins.moviebrowser.font))
        # # list.append(getConfigListEntry(_('Plugin Transparency:'), config.plugins.moviebrowser.transparency))
        # # list.append(getConfigListEntry(_('Posterwall/Backdrop Plugin Size:'), config.plugins.moviebrowser.plugin_size))
        # # list.append(getConfigListEntry(_('Full HD Skin Support:'), config.plugins.moviebrowser.fhd))
        # # list.append(getConfigListEntry(_('PayPal Info:'), config.plugins.moviebrowser.paypal))
        # # list.append(getConfigListEntry(_('Plugin Auto Update Check:'), config.plugins.moviebrowser.autocheck))

        # list.append(getConfigListEntry(_('Posterwall/Backdrop Show Plot:'), config.plugins.moviebrowser.plotfull))
        # list.append(getConfigListEntry(_('Posterwall/Backdrop Headline Color:'), config.plugins.moviebrowser.color))
        # list.append(getConfigListEntry(_('Metrix List Selection Color:'), config.plugins.moviebrowser.metrixcolor))

        # # list.append(getConfigListEntry(_("Settings TMDB ApiKey"), config.plugins.moviebrowser.data))  # , _("Settings TMDB ApiKey")))
        # # if config.plugins.moviebrowser.data.value is True:
        # list.append(getConfigListEntry(_("Load TMDB Apikey from /tmp/tmdbapikey.txt"), config.plugins.moviebrowser.api))  # , _("Load TMDB Apikey from /tmp/tmdbapikey.txt")))
        # list.append(getConfigListEntry(_("Signup on TMDB and input free personal ApiKey"), config.plugins.moviebrowser.txtapi))  # , _("Signup on TMDB and input free personal ApiKey")))
        # list.append(getConfigListEntry(_("Load TheTVDb Apikey from /tmp/thetvdbapikey.txt"), config.plugins.moviebrowser.tvdbapi))  # , _("Load TheTVDb Apikey from /tmp/thetvdbapikey.txt")))
        # list.append(getConfigListEntry(_("Signup on TheTVDb and input free personal ApiKey"), config.plugins.moviebrowser.txttvdbapi))  # , _("Signup on TheTVDb and input free personal ApiKey")))

        # list.append(getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie))
        # list.append(getConfigListEntry(_('Load last Selection/Filter on Start:'), config.plugins.moviebrowser.lastfilter))

        # list.append(getConfigListEntry(_('Update Database with Timer:'), config.plugins.moviebrowser.timerupdate))
        # list.append(getConfigListEntry(_('Timer Database Update:'), config.plugins.moviebrowser.timer))
        # list.append(getConfigListEntry(_('Hide Plugin during Update:'), config.plugins.moviebrowser.hideupdate))

        # list.append(getConfigListEntry(_('Reset Database:'), config.plugins.moviebrowser.reset))
        # list.append(getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup))
        # list.append(getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup))
        # list.append(getConfigListEntry(_('Restore Database:'), config.plugins.moviebrowser.restore))

        # list.append(getConfigListEntry(_('Select skin *Restart GUI Required:'), config.plugins.moviebrowser.skin))
        # list.append(getConfigListEntry(_('Start Plugin with Video Button:'), config.plugins.moviebrowser.videobutton))
        # list.append(getConfigListEntry(_('Plugin in Enigma Menu:'), config.plugins.moviebrowser.showmenu))

        ConfigListScreen.__init__(self, list, on_change=self.changedEntry)
        
        self.createSetup()
        
        self['actions'] = ActionMap(['SetupActions', 'VirtualKeyboardActions', 'ColorActions'], {
            'ok': self.keyRun,
            'showVirtualKeyboard': self.KeyText,
            'cancel': self.cancel,
            'red': self.cancel,
            'green': self.save
        }, -1)

        self.onLayoutFinish.append(self.UpdateComponents)

    def createSetup(self):
        self.editListEntry = None        
        list = []
        list.append(getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style))
        list.append(getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle))
        list.append(getConfigListEntry(_('Movie Folder:'), config.plugins.moviebrowser.moviefolder))
        list.append(getConfigListEntry(_('Cache Folder:'), config.plugins.moviebrowser.cachefolder))
        list.append(getConfigListEntry(_('Movies or Series:'), config.plugins.moviebrowser.filter))
        list.append(getConfigListEntry(_('Movies or Series Selection at Start:'), config.plugins.moviebrowser.showswitch))
        list.append(getConfigListEntry(_('TMDb/TheTVDb Language:'), config.plugins.moviebrowser.language))
        list.append(getConfigListEntry(_('Movie Sort Order:'), config.plugins.moviebrowser.sortorder))
        list.append(getConfigListEntry(_('Show Backdrops:'), config.plugins.moviebrowser.backdrops))
        list.append(getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v))
        list.append(getConfigListEntry(_('Download new Backdrops:'), config.plugins.moviebrowser.download))
        list.append(getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv))
        list.append(getConfigListEntry(_('Show List of Movie Folder:'), config.plugins.moviebrowser.showfolder))

        # self.foldername = getConfigListEntry(_('Movie Folder:'), config.plugins.moviebrowser.moviefolder)
        # list.append(self.foldername)
        # list.append(getConfigListEntry(_('Plugin Sans Serif Font:'), config.plugins.moviebrowser.font))
        # list.append(getConfigListEntry(_('Plugin Transparency:'), config.plugins.moviebrowser.transparency))
        # list.append(getConfigListEntry(_('Posterwall/Backdrop Plugin Size:'), config.plugins.moviebrowser.plugin_size))
        # list.append(getConfigListEntry(_('Full HD Skin Support:'), config.plugins.moviebrowser.fhd))
        # list.append(getConfigListEntry(_('PayPal Info:'), config.plugins.moviebrowser.paypal))
        # list.append(getConfigListEntry(_('Plugin Auto Update Check:'), config.plugins.moviebrowser.autocheck))

        list.append(getConfigListEntry(_('Posterwall/Backdrop Show Plot:'), config.plugins.moviebrowser.plotfull))
        list.append(getConfigListEntry(_('Posterwall/Backdrop Headline Color:'), config.plugins.moviebrowser.color))
        list.append(getConfigListEntry(_('Metrix List Selection Color:'), config.plugins.moviebrowser.metrixcolor))

        list.append(getConfigListEntry(_("Load TMDB Apikey from /tmp/tmdbapikey.txt"), config.plugins.moviebrowser.api))
        list.append(getConfigListEntry(_("Signup on TMDB and input free personal ApiKey"), config.plugins.moviebrowser.txtapi))
        list.append(getConfigListEntry(_("Load TheTVDb Apikey from /tmp/thetvdbapikey.txt"), config.plugins.moviebrowser.tvdbapi))
        list.append(getConfigListEntry(_("Signup on TheTVDb and input free personal ApiKey"), config.plugins.moviebrowser.txttvdbapi))

        list.append(getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie))
        list.append(getConfigListEntry(_('Load last Selection/Filter on Start:'), config.plugins.moviebrowser.lastfilter))

        list.append(getConfigListEntry(_('Update Database with Timer:'), config.plugins.moviebrowser.timerupdate))
        list.append(getConfigListEntry(_('Timer Database Update:'), config.plugins.moviebrowser.timer))
        list.append(getConfigListEntry(_('Hide Plugin during Update:'), config.plugins.moviebrowser.hideupdate))

        list.append(getConfigListEntry(_('Reset Database:'), config.plugins.moviebrowser.reset))
        list.append(getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup))
        list.append(getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup))
        list.append(getConfigListEntry(_('Restore Database:'), config.plugins.moviebrowser.restore))

        list.append(getConfigListEntry(_('Select skin *Restart GUI Required:'), config.plugins.moviebrowser.skin))
        list.append(getConfigListEntry(_('Start Plugin with Video Button:'), config.plugins.moviebrowser.videobutton))
        list.append(getConfigListEntry(_('Plugin in Enigma Menu:'), config.plugins.moviebrowser.showmenu))
        self["config"].list = list
        self["config"].l.setList(list)

    def UpdateComponents(self):
        current = self['config'].getCurrent()
        if current == getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style):
            png = ('%spic/setup/' + str(config.plugins.moviebrowser.style.value) + '.png') % str(skin_directory)
            if fileExists(png):
                self["plugin"].instance.setPixmapFromFile(png)
                self['plugin'].show()
        elif current == getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle):
            png2 = ('%spic/setup/' + str(config.plugins.moviebrowser.seriesstyle.value) + '.png') % str(skin_directory)    
            if fileExists(png2):
                self["plugin"].instance.setPixmapFromFile(png2)
                self['plugin'].show()
        # elif current == self.foldername:
            # self.session.openWithCallback(self.folderSelected, FolderSelection, self.moviefolder)
        elif current == getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v) or current == getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv):
            if config.plugins.moviebrowser.m1v.value == 'yes':
                config.plugins.moviebrowser.showtv.value = 'hide'
        elif current == getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie):
            if config.plugins.moviebrowser.showfolder.value == 'no' and config.plugins.moviebrowser.lastmovie.value == 'folder':
                config.plugins.moviebrowser.lastmovie.value = 'yes'
        elif current == getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup):
            if os.path.exists(self.cachefolder):
                if fileExists(self.database):
                    if config.plugins.moviebrowser.backup.value == 'yes':
                        data = open(self.database).read()
                        try:
                            os.makedirs(self.cachefolder + '/backup')
                        except OSError:
                            pass
                        f = open(self.cachefolder + '/backup/database', 'w')
                        f.write(data)
                        f.close()
                        self.session.open(MessageBox, _('\nDatabase backuped to %s') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                    else:
                        self.session.open(MessageBox, _('\nDatabase %s not found:\nMovie Browser Database Backup canceled.') % str(self.database), MessageBox.TYPE_ERROR)
                    # config.plugins.moviebrowser.backup.setValue('no')
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Backup canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        elif current == getConfigListEntry('Restore Database:', config.plugins.moviebrowser.restore):
            if os.path.exists(self.cachefolder):
                if config.plugins.moviebrowser.restore.value == 'yes':
                    if fileExists(self.cachefolder + '/backup/database'):
                        data = open(self.cachefolder + '/backup/database').read()
                        f = open(self.database, 'w')
                        f.write(data)
                        f.close()
                        self.session.open(MessageBox, _('\nDatabase restored from %s') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                    else:
                        self.session.open(MessageBox, _('\nDatabase Backup %s not found:\nMovie Browser Database Restore canceled.') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_ERROR)
                    # config.plugins.moviebrowser.restore.setValue('no')
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Restore canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        elif current == getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup):
            if os.path.exists(self.cachefolder):
                if config.plugins.moviebrowser.cleanup.value == 'yes':
                    if fileExists(self.database):
                        data = open(self.database).read()
                        data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
                        folder = self.cachefolder
                        count = 0
                        # if config.plugins.moviebrowser.language.value == 'de':
                            # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
                        # else:
                        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        for root, dirs, files in os.walk(folder, topdown=False, onerror=None):
                            for name in files:
                                shortname = sub('[.]jpg', '', name)
                                shortname = sub('[.]m1v', '', shortname)
                                if search(shortname, data) is None:
                                    filename = os.path.join(root, name)
                                    if fileExists(filename):
                                        os.remove(filename)
                                        count += 1
                        del data
                        if count == 0:
                            self.session.open(MessageBox, _('\nNo orphaned Backdrops or Posters found:\nYour Cache Folder is clean.'), MessageBox.TYPE_INFO, close_on_any_key=True)
                        else:
                            self.session.open(MessageBox, _('\nCleanup Cache Folder finished:\n%s orphaned Backdrops or Posters removed.') % str(count), MessageBox.TYPE_INFO, close_on_any_key=True)
                        end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        info = _('Start time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
                        f = open(cleanuplog, 'a')
                        f.write(info)
                        f.close()
                    else:
                        self.session.open(MessageBox, _('\nDatabase %s not found:\nCleanup Cache Folder canceled.') % str(self.database), MessageBox.TYPE_ERROR)
                    # config.plugins.moviebrowser.cleanup.setValue('no')
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nCleanup Cache Folder canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        return

    # def folderSelected(self, folder):
        # if folder is not None:
            # self.moviefolder = folder
            # config.plugins.moviebrowser.moviefolder.value = folder
            # config.plugins.moviebrowser.moviefolder.save()
        # return

    def keyRun(self):
        current = self['config'].getCurrent()
        if current == getConfigListEntry(_("Load TMDB Apikey from /tmp/tmdbapikey.txt"), config.plugins.moviebrowser.api):
            self.keyApi()
        elif current == getConfigListEntry(_("Load TheTVDb Apikey from /tmp/thetvdbapikey.txt"), config.plugins.moviebrowser.tvdbapi):
            self.tvdbkeyApi()
        else:
            self.save()

    def keyApi(self, answer=None):
        api = "/tmp/tmdbapikey.txt"
        if answer is None:
            if fileExists(api) and os.stat(api).st_size > 0:
                self.session.openWithCallback(self.keyApi, MessageBox, _("Import Api Key TMDB from\n/tmp/tmdbapikey.txt?"))
            else:
                self.mbox = self.session.open(MessageBox, (_("Missing %s !") % api), MessageBox.TYPE_INFO, timeout=4)
        elif answer:
            if fileExists(api) and os.stat(api).st_size > 0:
                with open(api, 'r') as f:
                    fpage = f.readline()
                    config.plugins.moviebrowser.txtapi.setValue(str(fpage))
                    config.plugins.moviebrowser.txtapi.save()
                    configfile.save()
                self.createSetup()
                self.mbox = self.session.open(MessageBox, (_("TMDB ApiKey Imported & Stored!")), MessageBox.TYPE_INFO, timeout=4)
            else:
                self.mbox = self.session.open(MessageBox, (_("Missing %s !") % api), MessageBox.TYPE_INFO, timeout=4)
        return

    def tvdbkeyApi(self, answer=None):
        thetvdbapikey = "/tmp/thetvdbapikey.txt"
        if answer is None:
            if fileExists(thetvdbapikey) and os.stat(thetvdbapikey).st_size > 0:
                self.session.openWithCallback(self.keyApi, MessageBox, _("Import Api Key TheTVDb from\n/tmp/thetvdbapikey.txt?"))
            else:
                self.mbox = self.session.open(MessageBox, (_("Missing %s !") % thetvdbapikey), MessageBox.TYPE_INFO, timeout=4)
        elif answer:
            if fileExists(thetvdbapikey) and os.stat(thetvdbapikey).st_size > 0:
                with open(thetvdbapikey, 'r') as d:
                    fpage2 = d.readline()
                    config.plugins.moviebrowser.txttvdbapi.setValue(str(fpage2))
                    config.plugins.moviebrowser.txttvdbapi.save()
                    configfile.save()
                self.createSetup()
                self.mbox = self.session.open(MessageBox, (_("TheTVDb ApiKey Imported & Stored!")), MessageBox.TYPE_INFO, timeout=4)
            else:
                self.mbox = self.session.open(MessageBox, (_("Missing %s !") % thetvdbapikey), MessageBox.TYPE_INFO, timeout=4)
        return

    def selectionChanged(self):
        self['status'].setText(self['config'].getCurrent()[0])

    def changedEntry(self):
        # self.item = self["config"].getCurrent()
        for x in self.onChangedEntry:
            x()
        try:
            if isinstance(self["config"].getCurrent()[1], ConfigYesNo) or isinstance(self["config"].getCurrent()[1], ConfigSelection) or isinstance(self["config"].getCurrent()[1], ConfigText):
                self.UpdateComponents()
        except:
            self.createSetup()
            pass

    def getCurrentEntry(self):
        return self["config"].getCurrent() and self["config"].getCurrent()[0] or ""

    def getCurrentValue(self):
        return self["config"].getCurrent() and str(self["config"].getCurrent()[1].getText()) or ""

    def createSummary(self):
        from Screens.Setup import SetupSummary
        return SetupSummary

    def save(self):
        if self.ready is True:
            self.ready = False
            if config.plugins.moviebrowser.sortorder.value != self.sortorder:
                if fileExists(self.database):
                    f = open(self.database, 'r')
                    series = ''
                    for line in f:
                        if ':::Series:::' in line:
                            series = series + line

                    f.close()
                    fseries = open(self.database + '.series', 'w')
                    fseries.write(series)
                    fseries.close()
                    fseries = open(self.database + '.series', 'r')
                    series = fseries.readlines()
                    series.sort(key=lambda line: line.split(':::')[0])
                    fseries.close()
                    fseries = open(self.database + '.series', 'w')
                    fseries.writelines(series)
                    fseries.close()
                    f = open(self.database, 'r')
                    movies = ''
                    for line in f:
                        if ':::Series:::' not in line:
                            movies = movies + line

                    f.close()
                    fmovies = open(self.database + '.movies', 'w')
                    fmovies.write(movies)
                    fmovies.close()
                    fmovies = open(self.database + '.movies', 'r')
                    lines = fmovies.readlines()
                    fmovies.close()
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

                    f = open(self.database + '.movies', 'w')
                    f.writelines(lines)
                    f.close()
                    files = [self.database + '.movies', self.database + '.series']
                    with open(self.database + '.sorted', 'w') as outfile:
                        for name in files:
                            with open(name) as infile:
                                outfile.write(infile.read())

                    if fileExists(self.database + '.movies'):
                        os.remove(self.database + '.movies')
                    if fileExists(self.database + '.series'):
                        os.remove(self.database + '.series')
                    os.rename(self.database + '.sorted', self.database)
            if config.plugins.moviebrowser.timerupdate.value == 'yes':
                if self.timer_hour != config.plugins.moviebrowser.timer.value[0] or self.timer_min != config.plugins.moviebrowser.timer.value[1] or self.timer_update == 'no':
                    if timerupdate.session is None:
                        timerupdate.saveSession(self.session)
                    timerupdate.restart()
            elif config.plugins.moviebrowser.timerupdate.value == 'no' and self.timer_update == 'yes':
                if timerupdate.session is None:
                    timerupdate.saveSession(self.session)
                timerupdate.stop()

            if config.plugins.moviebrowser.cachefolder.value != self.cachefolder:
                self.container = eConsoleAppContainer()
                self.container.appClosed.append(self.finished)
                newcache = sub('/cache', '', config.plugins.moviebrowser.cachefolder.value)
                self.container.execute("mkdir -p '%s' && cp -r '%s' '%s' && rm -rf '%s'" % (config.plugins.moviebrowser.cachefolder.value, self.cachefolder, newcache, self.cachefolder))
                self.cachefolder = config.plugins.moviebrowser.cachefolder.value
                config.plugins.moviebrowser.cachefolder.save()

            if config.plugins.moviebrowser.reset.value == 'yes':
                open(dbreset, 'w').close()
                config.plugins.moviebrowser.reset.value = 'no'
                config.plugins.moviebrowser.reset.save()

            if config.plugins.moviebrowser.backup.value == 'yes':
                config.plugins.moviebrowser.backup.setValue('no')
                config.plugins.moviebrowser.backup.save()

            if config.plugins.moviebrowser.restore.value == 'yes':
                config.plugins.moviebrowser.restore.setValue('no')
                config.plugins.moviebrowser.restore.save()
                
            if config.plugins.moviebrowser.cleanup.value == 'yes':
                config.plugins.moviebrowser.cleanup.setValue('no')
                config.plugins.moviebrowser.cleanup.save()                

            else:
                for x in self["config"].list:
                    x[1].save()
                configfile.save()
            self.exit()
        return

    def finished(self, retval):
        del self.container.appClosed[:]
        del self.container
        for x in self['config'].list:
            x[1].save()
        configfile.save()
        # self.exit()
        return

    def KeyText(self):
        from Screens.VirtualKeyBoard import VirtualKeyBoard
        current = self['config'].getCurrent()
        if current:
            self.session.openWithCallback(self.VirtualKeyBoardCallback, VirtualKeyBoard, title=self["config"].getCurrent()[0], text=self["config"].getCurrent()[1].value)

    def VirtualKeyBoardCallback(self, callback=None):
        if callback is not None and len(callback):
            self["config"].getCurrent()[1].value = callback
            self["config"].invalidate(self["config"].getCurrent())
        return

# why don't work
    def keySave(self):
        for i in range(0, len(config.plugins.moviebrowser)):
            # print('config list ', i)
            config.plugins.moviebrowser[i].save()
        ConfigListScreen.keySave(self)

    def cancel(self, answer=None):
        if answer is None:
            if self["config"].isChanged():
                self.session.openWithCallback(self.cancel, MessageBox, _("Really close without saving settings?"))
            else:
                self.exit()
        elif answer:
            for x in self["config"].list:
                x[1].cancel()
            self.exit()
        return

    def exit(self):
        if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
            number = 1
        elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
            number = 2
        else:
            number = 3
        if config.plugins.moviebrowser.showswitch.value == 'yes':
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


# class FolderSelection(Screen):

    # def __init__(self, session, folder):
        # skin = skin_path + "FolderSelection.xml"
        # # if os.path.exists("/var/lib/dpkg/status"):
            # # skin = skin_path + "DreamOS/FolderSelection.xml"
        # with open(skin, "r") as f:
            # self.skin = f.read()

        # Screen.__init__(self, session)
        # self['save'] = Label(_('Save'))
        # self['cancel'] = Label(_('Cancel'))
        # self['plugin'] = Pixmap()
        # noFolder = [
            # '/bin',
            # '/boot',
            # '/dev',
            # '/etc',
            # '/lib',
            # '/proc',
            # '/sbin',
            # '/sys'
        # ]
        # self['folderlist'] = FileList(folder, showDirectories=True, showFiles=False, inhibitDirs=noFolder)
        # self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {
            # 'ok': self.ok,
            # 'cancel': self.cancel,
            # 'right': self.right,
            # 'left': self.left,
            # 'down': self.down,
            # 'up': self.up,
            # 'red': self.cancel,
            # 'green': self.green
        # }, -1)

        # self.onLayoutFinish.append(self.pluginPic)

    # def pluginPic(self):
        # png = ('%spic/setup/' + str(config.plugins.moviebrowser.style.value) + '.png') % skin_directory
        # if fileExists(png):
            # self["plugin"].instance.setPixmapFromFile(png)
            # self['plugin'].show()
        # return

    # def ok(self):
        # if self['folderlist'].canDescent():
            # self['folderlist'].descent()

    # def right(self):
        # self['folderlist'].pageDown()

    # def left(self):
        # self['folderlist'].pageUp()

    # def down(self):
        # self['folderlist'].down()

    # def up(self):
        # self['folderlist'].up()

    # def green(self):
        # self.close(self['folderlist'].getSelection()[0])

    # def cancel(self):
        # self.close(None)
        # return


class timerUpdate():

    def __init__(self):
        self.session = None
        self.startTimer = eTimer()
        self.dailyTimer = eTimer()
        return

    def saveSession(self, session):
        self.session = session

    def start(self):
        self.startTimer.callback.append(self.daily)
        now = datetime.datetime.now()
        now = now.hour * 60 + now.minute
        start_time = config.plugins.moviebrowser.timer.value[0] * 60 + config.plugins.moviebrowser.timer.value[1]
        if now < start_time:
            start_time = start_time - now
        else:
            start_time = 1440 - now + start_time
        self.startTimer.start(start_time * 60 * 1000, True)
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('*******Movie Browser Database Update Timer*******\nInitial Update Timer started: %s\nTimer Value (min): %s\n') % (now, str(start_time))
        f = open(timerlog, 'a')
        f.write(info)
        f.close()

    def restart(self):
        self.startTimer.stop()
        if self.daily in self.startTimer.callback:
            self.startTimer.callback.remove(self.daily)
        self.dailyTimer.stop()
        if self.runUpdate in self.dailyTimer.callback:
            self.dailyTimer.callback.remove(self.runUpdate)
        self.start()

    def stop(self):
        self.startTimer.stop()
        if self.daily in self.startTimer.callback:
            self.startTimer.callback.remove(self.daily)
        self.dailyTimer.stop()
        if self.runUpdate in self.dailyTimer.callback:
            self.dailyTimer.callback.remove(self.runUpdate)
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer stopped: %s\n') % now
        f = open(timerlog, 'a')
        f.write(info)
        f.close()

    def daily(self):
        self.startTimer.stop()
        if self.daily in self.startTimer.callback:
            self.startTimer.callback.remove(self.daily)
        self.runUpdate()
        self.dailyTimer.callback.append(self.runUpdate)
        start_time = 1440
        self.dailyTimer.start(start_time * 60 * 1000, False)
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer started: %s\nTimer Value (min): %s\n') % (now, str(start_time))
        f = open(timerlog, 'a')
        f.write(info)
        f.close()

    def runUpdate(self):
        UpdateDatabase(False, '', '', '').showResult(True)
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Movie Database Update started: %s\n') % now
        f = open(timerlog, 'a')
        f.write(info)
        f.close()


def main(session, **kwargs):
    if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
        number = 1
    elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
        number = 2
    else:
        number = 3
    if config.plugins.moviebrowser.showswitch.value == 'yes':
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
    global infobarsession
    if config.plugins.moviebrowser.filter.value == ':::Movie:Top:::':
        number = 1
    elif config.plugins.moviebrowser.filter.value == ':::Series:Top:::':
        number = 2
    else:
        number = 3
    if config.plugins.moviebrowser.showswitch.value == 'yes':
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


infobarsession = None
timerupdate = timerUpdate()


def autostart(reason, **kwargs):
    global infobarsession
    if 'session' in kwargs:
        info = _('*******Movie Browser Database Update*******\n')
        f = open(updatelog, 'w')
        f.write(info)
        f.close()
        if config.plugins.moviebrowser.videobutton.value == 'yes':
            infobarsession = kwargs['session']
            from Screens.InfoBar import InfoBar
            InfoBar.showMovies = mainInfoBar
        if config.plugins.moviebrowser.timerupdate.value == 'yes':
            open(timerlog, 'w').close()
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
                f = open(updatelog, 'w')
                f.write(result)
                f.close()

        if os.path.exists(config.plugins.moviebrowser.cachefolder.value):
            if fileExists(dbmovie):
                data = open(dbmovie).read()
                data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
                folder = config.plugins.moviebrowser.cachefolder.value
                count = 0
                now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                for root, dirs, files in os.walk(folder, topdown=False, onerror=None):
                    for name in files:
                        shortname = sub('[.]jpg', '', name)
                        shortname = sub('[.]m1v', '', shortname)
                        if search(shortname, data) is None:
                            filename = os.path.join(root, name)
                            if fileExists(filename):
                                os.remove(filename)
                                count += 1
                del data
                end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                info = _('*******Cleanup Cache Folder*******\nStart time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
                f = open(cleanuplog, 'w')
                f.write(info)
                f.close()
    return


def Plugins(**kwargs):
    plugindesc = _('Manage your Movies & Series V.%s' % str(version))
    if config.plugins.moviebrowser.showmenu.value == 'no':
        return [
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main),
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main),
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)
                ]
    else:
        return [
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_MENU], fnc=menu),
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_PLUGINMENU], icon='plugin.png', fnc=main),
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_EXTENSIONSMENU], fnc=main),
                PluginDescriptor(name='Movie Browser', description=plugindesc, where=[PluginDescriptor.WHERE_SESSIONSTART], fnc=autostart)
                ]
