#!/usr/bin/python
# -*- coding: utf-8 -*-

#20221204 Lululla edit: language, config, minor fix 
from . import _

from Components.ActionMap import ActionMap
from Components.config import config, configfile, ConfigClock, ConfigDirectory
from Components.config import ConfigSlider, ConfigSubsection, ConfigSelection
from Components.config import getConfigListEntry
from Components.ConfigList import ConfigListScreen
from Components.FileList import FileList
from Components.Label import Label
from Components.Language import language
from Components.MenuList import MenuList
from Components.MultiContent import MultiContentEntryText, MultiContentEntryPixmapAlphaTest
from Components.Pixmap import Pixmap, MultiPixmap
from Components.ProgressBar import ProgressBar
from Components.ScrollLabel import ScrollLabel
from Components.ServiceEventTracker import ServiceEventTracker
from enigma import addFont, eConsoleAppContainer, eListboxPythonMultiContent, ePoint
from enigma import eServiceReference, eTimer, getDesktop, gFont, iPlayableService
from enigma import iServiceInformation, loadPic, loadPNG
from enigma import RT_HALIGN_LEFT, RT_HALIGN_RIGHT, RT_HALIGN_CENTER, RT_VALIGN_CENTER, RT_WRAP
from Plugins.Plugin import PluginDescriptor
from re import search, sub
from Screens.ChannelSelection import ChannelSelection
from Screens.ChoiceBox import ChoiceBox
from Screens.InfoBar import MoviePlayer
from Screens.MessageBox import MessageBox
from Screens.Screen import Screen
from Screens.Standby import TryQuitMainloop
from Screens.VirtualKeyBoard import VirtualKeyBoard
from Tools.Directories import fileExists
from twisted.web.client import getPage, downloadPage
try:
    from urllib import unquote_plus
except:
    from urllib.parse import unquote_plus

try:
    from urllib2 import Request, urlopen
except:
    from urllib.request import urlopen, Request

try:
    from urlparse import parse_qs
except:
    from urllib.parse import parse_qs

import datetime
import os
import re

try:
    import statvfs
except:
    from os import statvfs

import sys

pythonVer = sys.version_info.major

config.plugins.moviebrowser = ConfigSubsection()
lang = language.getLanguage()[:2]
if lang == 'de':
    config.plugins.moviebrowser.language = ConfigSelection(default='de', choices=[
        ('de', 'Deutsch'),
        ('en', 'Englisch'),
        ('es', 'Spanisch'),
        ('it', 'Italienisch'),
        ('fr', 'Franz\xc3\xb6sisch'),
        ('ru', 'Russisch')
    ])

elif lang == 'es':
    config.plugins.moviebrowser.language = ConfigSelection(default='es', choices=[
        ('es', 'Espa\xc3\xb1ol'),
        ('de', 'Alem\xc3\xa1n'),
        ('en', 'Ingl\xc3\xa9s'),
        ('it', 'Italiano'),
        ('fr', 'Franc\xc3\xa9s'),
        ('ru', 'Ruso')
    ])

elif lang == 'it':
    config.plugins.moviebrowser.language = ConfigSelection(default='it', choices=[
        ('it', 'Italiano'),
        ('en', 'Inglese'),
        ('de', 'Tedesco'),
        ('es', 'Spagnolo'),
        ('fr', 'Francese'),
        ('ru', 'Russo')
    ])

elif lang == 'fr':
    config.plugins.moviebrowser.language = ConfigSelection(default='fr', choices=[
        ('fr', 'Fran\xc3\xa7ais'),
        ('de', 'Allemand'),
        ('en', 'Anglais'),
        ('es', 'Espagnol'),
        ('it', 'Italien'),
        ('ru', 'Russe')
    ])

elif lang == 'ru':
    config.plugins.moviebrowser.language = ConfigSelection(default='ru', choices=[
        ('ru', 'P\xd1\x83\xd1\x81\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9'),
        ('de', '\xd0\x9d\xd0\xb5\xd0\xbc\xd0\xb5\xd1\x86\xd0\xba\xd0\xb8\xd0\xb9'),
        ('en', '\xd0\x90\xd0\xbd\xd0\xb3\xd0\xbb\xd0\xb8\xd0\xb9\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9'),
        ('es', '\xd0\x98\xd1\x81\xd0\xbf\xd0\xb0\xd0\xbd\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9'),
        ('it', '\xd0\x98\xd1\x82\xd0\xb0\xd0\xbb\xd1\x8c\xd1\x8f\xd0\xbd\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9'),
        ('fr', '\xd1\x84\xd1\x80\xd0\xb0\xd0\xbd\xd1\x86\xd1\x83\xd0\xb7\xd1\x81\xd0\xba\xd0\xb8\xd0\xb9')
    ])

else:
    config.plugins.moviebrowser.language = ConfigSelection(default='en', choices=[
        ('en', 'English'),
        ('de', 'German'),
        ('es', 'Spanish'),
        ('it', 'Italian'),
        ('fr', 'French'),
        ('ru', 'Russian')
    ])

# if config.plugins.moviebrowser.language.value == 'de':
    # config.plugins.moviebrowser.filter = ConfigSelection(default=':::Movie:Top:::', choices=[(':::Movie:Top:::', 'Filme'), (':::Series:Top:::', 'Serien'), (':Top:::', 'Filme & Serien')])
    # config.plugins.moviebrowser.sortorder = ConfigSelection(default='date_reverse', choices=[
        # ('date_reverse', 'Film Erstellungsdatum Absteigend'),
        # ('date', 'Film Erstellungsdatum Aufsteigend'),
        # ('name', 'Film Titel A-Z'),
        # ('name_reverse', 'Film Titel Z-A'),
        # ('rating_reverse', 'Film Rating 10-0'),
        # ('rating', 'Film Rating 0-10'),
        # ('year_reverse', 'Film Erscheinungsdatum Absteigend'),
        # ('year', 'Film Erscheinungsdatum Aufsteigend'),
        # ('runtime_reverse', 'Film Laufzeit Absteigend'),
        # ('runtime', 'Film Laufzeit Aufsteigend'),
        # ('folder', 'Film Ordner Aufsteigend'),
        # ('folder_reverse', 'Film Ordner Absteigend')
    # ])

    # config.plugins.moviebrowser.backdrops = ConfigSelection(default='info', choices=[('info', 'Info Taste'), ('auto', 'Automatisch'), ('hide', 'Ausblenden')])
    # config.plugins.moviebrowser.m1v = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.download = ConfigSelection(default='update', choices=[('access', 'Beim ersten Zugriff'), ('update', 'Beim Datenbank Update')])
    # if config.plugins.moviebrowser.m1v.value == 'yes':
        # config.plugins.moviebrowser.showtv = ConfigSelection(default='hide', choices=[('show', 'Anzeigen'), ('hide', 'Ausblenden')])
    # else:
        # config.plugins.moviebrowser.showtv = ConfigSelection(default='show', choices=[('show', 'Anzeigen'), ('hide', 'Ausblenden')])
    # config.plugins.moviebrowser.showswitch = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.showmenu = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.videobutton = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.lastmovie = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein'), ('folder', 'Ordner Auswahl')])
    # config.plugins.moviebrowser.lastfilter = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.showfolder = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.autocheck = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
    # config.plugins.moviebrowser.paypal = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
    # config.plugins.moviebrowser.font = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
    # deskWidth = getDesktop(0).size().width()
    # if deskWidth >= 1280:
        # config.plugins.moviebrowser.plugin_size = ConfigSelection(default='full', choices=[('full', '1280x720'), ('normal', '1024x576')])
    # else:
        # config.plugins.moviebrowser.plugin_size = ConfigSelection(default='normal', choices=[('full', '1280x720'), ('normal', '1024x576')])
    # config.plugins.moviebrowser.fhd = ConfigSelection(default='no', choices=[('yes', 'Ja'), ('no', 'Nein')])
    # if config.plugins.moviebrowser.fhd.value == 'yes':
        # from enigma import eSize, gMainDC
    # config.plugins.moviebrowser.plotfull = ConfigSelection(default='hide', choices=[('hide', 'Info Taste'), ('show', 'Automatisch')])
    # config.plugins.moviebrowser.timerupdate = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
    # config.plugins.moviebrowser.hideupdate = ConfigSelection(default='yes', choices=[('yes', 'Ja'), ('no', 'Nein')])
    # config.plugins.moviebrowser.reset = ConfigSelection(default='no', choices=[('no', 'Nein'), ('yes', 'Ja')])
# else:
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
config.plugins.moviebrowser.autocheck = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])
config.plugins.moviebrowser.paypal = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])
config.plugins.moviebrowser.font = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])
deskWidth = getDesktop(0).size().width()
if deskWidth >= 1280:
    config.plugins.moviebrowser.plugin_size = ConfigSelection(default='full', choices=[('full', '1280x720'), ('normal', '1024x576')])
else:
    config.plugins.moviebrowser.plugin_size = ConfigSelection(default='normal', choices=[('full', '1280x720'), ('normal', '1024x576')])
config.plugins.moviebrowser.fhd = ConfigSelection(default='no', choices=[('yes', _('Yes')), ('no', _('No'))])
if config.plugins.moviebrowser.fhd.value == 'yes':
    from enigma import eSize, gMainDC
config.plugins.moviebrowser.plotfull = ConfigSelection(default='hide', choices=[('hide', _('Info Button')), ('show', _('Automatic'))])
config.plugins.moviebrowser.timerupdate = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])
config.plugins.moviebrowser.hideupdate = ConfigSelection(default='yes', choices=[('yes', _('Yes')), ('no', _('No'))])
config.plugins.moviebrowser.reset = ConfigSelection(default='no', choices=[('no', _('No')), ('yes', _('Yes'))])

config.plugins.moviebrowser.style = ConfigSelection(default='backdrop', choices=[('metrix', 'Metrix'), ('backdrop', 'Backdrop'), ('posterwall', 'Posterwall')])
config.plugins.moviebrowser.seriesstyle = ConfigSelection(default='metrix', choices=[('metrix', 'Metrix'), ('backdrop', 'Backdrop'), ('posterwall', 'Posterwall')])
config.plugins.moviebrowser.moviefolder = ConfigDirectory(default='/media/hdd/')
config.plugins.moviebrowser.cachefolder = ConfigSelection(default='/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/cache', choices=[('/media/usb/moviebrowser/cache', '/media/usb'), ('/media/hdd/moviebrowser/cache', '/media/hdd'), ('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/cache', 'Default')])
if config.plugins.moviebrowser.font.value == 'yes':
    try:
        addFont('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/font/Sans.ttf', 'Sans', 100, False)
    except Exception as ex:
        print(ex)
        addFont('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/font/Sans.ttf', 'Sans', 100, False, 0)

try:
    addFont('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/font/MetrixHD.ttf', 'Metrix', 100, False)
except Exception as ex:
    print(ex)
    addFont('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/font/MetrixHD.ttf', 'Metrix', 100, False, 0)

config.plugins.moviebrowser.transparency = ConfigSlider(default=255, limits=(100, 255))
config.plugins.moviebrowser.timer = ConfigClock(default=6 * 3600)
config.plugins.moviebrowser.cleanup = ConfigSelection(default='no', choices=[('no', '<Cleanup>'), ('no', '<Cleanup>')])
config.plugins.moviebrowser.backup = ConfigSelection(default='no', choices=[('no', '<Backup>'), ('no', '<Backup>')])
config.plugins.moviebrowser.restore = ConfigSelection(default='no', choices=[('no', '<Restore>'), ('no', '<Restore>')])
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
    skin = """
    <screen position="center,center" size="1280,720" flags="wfNoBorder" title="  ">
    <widget name="backdrop" position="0,0" size="1280,720" alphatest="on" transparent="0" zPosition="-2"/>
    <widget name="metrixback" position="40,25" size="620,670" alphatest="blend" transparent="1" zPosition="-1"/>
    <widget name="metrixback2" position="660,40" size="570,640" alphatest="blend" transparent="1" zPosition="-1"/>
    <widget name="audiotype" position="675,55" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>
    <widget name="videomode" position="765,55" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>
    <widget name="videocodec" position="825,55" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>
    <widget name="aspectratio" position="915,55" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>
    <widget name="ddd" position="675,55" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
    <widget name="ddd2" position="915,55" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="22"/>
    <widget render="Label" source="global.CurrentTime" position="1088,43" size="140,60" font="Metrix;50" foregroundColor="#FFFFFF" halign="left" transparent="1" zPosition="3">
        <convert type="ClockToText">Default</convert>
    </widget>
    <widget render="Label" source="global.CurrentTime" position="916,54" size="161,27" font="{font};15" foregroundColor="#BBBBBB" halign="right" transparent="1" zPosition="3">
        <convert type="ClockToText">Format:%A</convert>
    </widget>
    <widget render="Label" source="global.CurrentTime" position="916,81" size="161,29" font="{font};16" foregroundColor="#BBBBBB" halign="right" transparent="1" zPosition="3">
        <convert type="ClockToText">Format:%e. %B</convert>
    </widget>
    <widget name="menu" position="579,655" size="81,40" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="info" position="1149,640" size="81,40" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="help" position="50,655" size="30,29" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="pvr" position="240,655" size="30,29" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="text" position="430,655" size="30,29" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="yellow" position="50,649" size="30,46" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="red" position="240,649" size="30,46" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="green" position="430,649" size="30,46" alphatest="blend" transparent="1" zPosition="3"/>
    <widget name="text1" position="85,654" size="150,30" font="Metrix;22" transparent="1" zPosition="3"/>
    <widget name="text2" position="275,654" size="150,30" font="Metrix;22" transparent="1" zPosition="3"/>
    <widget name="text3" position="465,654" size="150,30" font="Metrix;22" transparent="1" zPosition="3"/>
    <widget name="label" position="80,47" size="540,43" font="Metrix;35" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="3"/>
    <widget name="label2" position="80,90" size="540,30" font="Metrix;22" foregroundColor="#BBBBBB" valign="center" transparent="1" zPosition="3"/>
    <widget name="label3" position="80,620" size="320,30" font="Metrix;22" foregroundColor="#BBBBBB" valign="center" transparent="1" zPosition="3"/>
    <widget name="list" position="80,125" size="540,490" transparent="1" zPosition="3"/>
    <widget name="plotname" position="70,55" size="560,30" font="Metrix;24" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="20"/>
    <widget name="plotfull" position="70,95" size="590,545" font="Metrix;24" foregroundColor="#FFFFFF" transparent="1" zPosition="20"/>
    <widget name="poster" position="722,210" size="150,225" zPosition="21" transparent="1" alphatest="on"/>
    <widget name="posterback" position="675,200" size="245,245" zPosition="20" transparent="1" alphatest="blend"/>
    <widget name="name" position="675,120" size="500,70" font="Metrix;28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="3"/>
    <widget name="seen" position="1175,120" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="3"/>
    <widget name="ratings" position="950,210" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="5"/>
    <widget name="ratingsback" position="950,210" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="6"/>
    <widget name="Director" position="950,250" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="8"/>
    <widget name="director" position="950,280" size="255,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="9"/>
    <widget name="Year" position="950,320" size="100,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="14"/>
    <widget name="year" position="950,350" size="100,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="15"/>
    <widget name="Country" position="1050,320" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="10"/>
    <widget name="country" position="1050,350" size="125,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="11"/>
    <widget name="Runtime" position="950,390" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="16"/>
    <widget name="runtime" position="950,420" size="125,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="17"/>
    <widget name="Genres" position="675,460" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="18"/>
    <widget name="genres" position="675,490" size="540,30" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>
    <widget name="Actors" position="675,530" size="125,30" font="Metrix;22" foregroundColor="#BBBBBB" transparent="1" zPosition="12"/>
    <widget name="actors" position="675,560" size="540,64" font="Metrix;22" foregroundColor="#FFFFFF" transparent="1" zPosition="13"/>
    <widget name="eposter" position="675,166" size="540,405" alphatest="on" transparent="1" zPosition="21"/>
    <widget name="banner" position="675,123" size="540,99" alphatest="on" transparent="1" zPosition="21"/>
    <widget name="episodes" position="675,233" size="540,410" scrollbarMode="showNever" transparent="1" zPosition="21"/>
    <widget name="seasons" position="675,233" size="540,410" scrollbarMode="showNever" transparent="1" zPosition="20"/>
</screen>

"""

    def __init__(self, session, index, content, filter):
        # f = open('/proc/stb/video/alpha', 'w')
        # f.write('%i' % config.plugins.moviebrowser.transparency.value)
        # f.close()
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(movieBrowserMetrix.skin, self.dict)
        Screen.__init__(self, session)
        self.fhd = False
        if config.plugins.moviebrowser.fhd.value == 'yes':
            if getDesktop(0).size().width() == 1920:
                self.fhd = True
                # try:
                    # gMainDC.getInstance().setResolution(1280, 720)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1280, 720))
                # except:
                    # import traceback
                    # traceback.print_exc()

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
        if config.plugins.moviebrowser.language.value == 'de':
            self.language = '&language=de'
        elif config.plugins.moviebrowser.language.value == 'es':
            self.language = '&language=es'
        elif config.plugins.moviebrowser.language.value == 'it':
            self.language = '&language=it'
        elif config.plugins.moviebrowser.language.value == 'fr':
            self.language = '&language=fr'
        elif config.plugins.moviebrowser.language.value == 'ru':
            self.language = '&language=ru'
        else:
            self.language = '&language=en'
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
        # if self.language == '&language=de':
            # self['Director'] = Label('Regie:')
            # self['Actors'] = Label('Darsteller:')
            # self['Year'] = Label('Jahr:')
            # self['Runtime'] = Label('Laufzeit:')
            # self['Country'] = Label('Land:')
            # self['text1'] = Label('Hilfe')
            # self['text2'] = Label(_('Update'))
            # self['text3'] = Label('Editieren')
        # else:
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
            'yellow': self.youTube,
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
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if config.plugins.moviebrowser.autocheck.value == 'yes':
            self.version = '3.7rc3'
            self.link = 'https://sites.google.com/site/kashmirplugins/home/movie-browser'

        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)
        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
        self.metrixBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/metrix_back.png'
        metrixBack = loadPic(self.metrixBackPNG, 620, 670, 3, 0, 0, 0)
        self.metrixBack2PNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/metrix_back2.png'
        metrixBack2 = loadPic(self.metrixBack2PNG, 570, 640, 3, 0, 0, 0)

        if metrixBack is not None and metrixBack2 is not None:
            self['metrixback'].instance.setPixmap(metrixBack)
            self['metrixback2'].instance.setPixmap(metrixBack2)
            self['metrixback'].show()
            self['metrixback2'].show()

        posterback = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/metrix_posterback.png'
        PosterBack = loadPic(posterback, 245, 245, 3, 0, 0, 0)
        self['posterback'].instance.setPixmap(PosterBack)
        self['posterback'].hide()
        key_menu = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_menu.png'
        key_info = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_info.png'
        key_help = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_help.png'
        key_pvr = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_pvr.png'
        key_text = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_text.png'
        key_yellow = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_yellow.png'
        key_red = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_red.png'
        key_green = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/key_green.png'
        Key_menu = loadPic(key_menu, 81, 40, 3, 0, 0, 0)
        Key_info = loadPic(key_info, 81, 40, 3, 0, 0, 0)
        Key_help = loadPic(key_help, 30, 29, 3, 0, 0, 0)
        Key_pvr = loadPic(key_pvr, 30, 29, 3, 0, 0, 0)
        Key_text = loadPic(key_text, 30, 29, 3, 0, 0, 0)
        Key_yellow = loadPic(key_yellow, 30, 46, 3, 0, 0, 0)
        Key_red = loadPic(key_red, 30, 46, 3, 0, 0, 0)
        Key_green = loadPic(key_green, 30, 46, 3, 0, 0, 0)
        self['menu'].instance.setPixmap(Key_menu)
        self['info'].instance.setPixmap(Key_info)
        self['help'].instance.setPixmap(Key_help)
        self['pvr'].instance.setPixmap(Key_pvr)
        self['text'].instance.setPixmap(Key_text)
        self['yellow'].instance.setPixmap(Key_yellow)
        self['red'].instance.setPixmap(Key_red)
        self['green'].instance.setPixmap(Key_green)
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
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.reset_return, MessageBox, 'Die Movie Browser Datenbank wird jetzt neu erstellt. Je nach Anzahl der Filme kann dies mehrere Minuten dauern.\n\nSollte sich das Plugin nach einigen Minuten automatisch beenden, starten Sie das Plugin erneut und f\xc3\xbchren Sie ein manuelles Datenbank Update durch (Video Taste).\n\nSoll die Datenbank jetzt erstellt werden?', MessageBox.TYPE_YESNO)
            # else:
                # self.session.openWithCallback(self.reset_return, MessageBox, 'The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?', MessageBox.TYPE_YESNO)
        # elif self.language == '&language=de':
            # self.session.openWithCallback(self.first_return, MessageBox, 'Bevor die Datenbank neu erstellt wird, \xc3\xbcberpr\xc3\xbcfen Sie Ihre Einstellungen im Setup des Plugins:\n\n- Kontrollieren Sie den Pfad zum Film Ordner\n- \xc3\x9cberpr\xc3\xbcfen Sie Ihre Spracheinstellung: TMDb/TheTVDb Sprache\n- \xc3\x84ndern Sie den Cache Ordner auf Ihre Festplatte.', MessageBox.TYPE_YESNO)
        # else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset', 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.close, movieBrowserConfig)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
                os.remove('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset')
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
                        except IndexError:
                            name = ' '

                        try:
                            filename = movieline[1]
                        except IndexError:
                            filename = ' '

                        try:
                            date = movieline[2]
                        except IndexError:
                            date = ' '

                        try:
                            runtime = movieline[3]
                        except IndexError:
                            runtime = ' '

                        try:
                            rating = movieline[4]
                        except IndexError:
                            rating = ' '

                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        try:
                            actors = movieline[6]
                        except IndexError:
                            actors = ' '

                        try:
                            genres = movieline[7]
                        except IndexError:
                            genres = ' '

                        try:
                            year = movieline[8]
                        except IndexError:
                            year = ' '

                        try:
                            country = movieline[9]
                        except IndexError:
                            country = ' '

                        try:
                            plotfull = movieline[10]
                        except IndexError:
                            plotfull = ' '

                        try:
                            poster = movieline[11]
                        except IndexError:
                            poster = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png'

                        try:
                            backdrop = movieline[12]
                        except IndexError:
                            backdrop = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png'

                        try:
                            content = movieline[13]
                        except IndexError:
                            content = 'Movie:Top'

                        try:
                            seen = movieline[14]
                        except IndexError:
                            seen = 'unseen'

                        try:
                            media = movieline[15]
                        except IndexError:
                            media = '\n'

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
                    # if self.language == '&language=de':
                        # self.namelist.append('<Liste der Film Ordner>')
                    # else:
                    self.namelist.append('<List of Movie Folder>')
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
            if self.backcolor is True:
                # if self.language == '&language=de':
                    # res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text='<Liste der Film Ordner>'))
                # else:
                    res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, backcolor_sel=self.back_color, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            # elif self.language == '&language=de':
                # res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text='<Liste der Film Ordner>'))
            else:
                res.append(MultiContentEntryText(pos=(0, 0), size=(540, 40), font=26, color=16777215, color_sel=16777215, flags=RT_HALIGN_LEFT | RT_VALIGN_CENTER, text=_('<List of Movie Folder>')))
            movies.append(res)
        self['list'].l.setList(movies)
        self['list'].l.setFont(26, gFont('Metrix', 26))
        self['list'].l.setItemHeight(35)
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
        # if self.language == '&language=de':
            # free = 'freier Speicher'
            # folder = 'Film Ordner'
            # movies = 'FILME'
            # series = 'SERIEN'
            # episodes = 'EPISODEN'
        # else:
        free = _('free Space')
        folder = _('Movie Folder')
        movies = _('MOVIES')
        series = _('SERIES')
        episodes = _('EPISODES')
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)

            if pythonVer == 2:
                freeSize = movieFolder[statvfs.F_BSIZE] * movieFolder[statvfs.F_BFREE] / 1024 / 1024 / 1024
            else:
                freeSize = movieFolder.f_bsize * movieFolder.f_bfree / 1024 / 1024 / 1024

            if self.content == ':::Movie:Top:::':
                titel = '%s %s' % (str(self.totalMovies), movies)
                titel2 = '(%s: %s GB %s)' % (folder, str(freeSize), free)
            elif self.content == ':::Series:Top:::':
                titel = '%s %s' % (str(self.totalMovies), series)
                titel2 = '(%s: %s GB %s)' % (folder, str(freeSize), free)
            elif self.content == ':::Series:::':
                titel = '%s %s' % (str(self.totalMovies), episodes)
                titel2 = '(%s: %s GB %s)' % (folder, str(freeSize), free)
            else:
                titel = '%s %s & %s' % (str(self.totalMovies), movies, series)
                titel2 = '(%s: %s GB %s)' % (folder, str(freeSize), free)
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
            # if self.language == '&language=de':
                # if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.openWithCallback(self.database_return, MessageBox, '\nMovie Browser Datenbank aktualisieren?', MessageBox.TYPE_YESNO)
                # elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.open(MessageBox, '\nFilm Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
                # else:
                    # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden:\nIhre Datenbank ist aktuell.', MessageBox.TYPE_INFO)
            # else:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            # if self.language == '&language=de':
                # if orphaned == 1:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.' % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
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
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif orphaned == 1:
                    # if seriescount == 0:
                        # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                    # elif moviecount == 0:
                        # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                    # else:
                        # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
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
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            # elif self.language == '&language=de':
                                # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nDas DVD Player Plugin ist nicht installiert.', MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    # elif self.language == '&language=de':
                        # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
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
                    # if self.language == '&language=de':
                        # self.session.open(MessageBox, '\nTMDb Film Update Fehler:\nSerien Ordner', MessageBox.TYPE_ERROR)
                    # else:
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
                url = 'https://api.themoviedb.org/3/search/movie?api_key=dfc629f7ff6936a269f8c5cdb194c890&query=' + name + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TMDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
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
        if self.language == '&language=de':
            titel = 'TMDb Ergebnisse'
        else:
            titel = 'TMDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TMDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == 'movie':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=dfc629f7ff6936a269f8c5cdb194c890' % new + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TheTVDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
            self.session.open(MessageBox, _('\nThe TVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
            output = sub('<poster>https://artworks.thetvdb.com/banners/_cache/</poster>', '<poster>https://www.thetvdb.com/wiki/skins/common/images/wiki.png</poster>', output)
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
                poster.append('https://www.thetvdb.com/wiki/skins/common/images/wiki.png')

            try:
                id.append(TVDbid[0])
            except IndexError:
                id.append('0')

            try:
                country.append(Country[0])
            except IndexError:
                country.append(' ')

        # if self.language == '&language=de':
            # titel = 'TheTVDb Ergebnisse'
        # else:
        titel = 'TheTVDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TheTVDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo The TVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
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
                url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
                # if self.language == '&language=de':
                    # if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                        # self.session.open(MessageBox, '\nDie Liste der Film Ordner kann nicht gel\xc3\xb6scht werden.', MessageBox.TYPE_ERROR)
                    # elif content == 'Series:Top':
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\nAlle %s Eintr\xc3\xa4ge werden aus der Datenbank, aber nicht aus dem Film Ordner gel\xc3\xb6scht.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                    # else:
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\n%s wird aus der Datenbank und aus dem Film Ordner gel\xc3\xb6scht!\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
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
                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.blacklist_return, MessageBox, '\n%s wird aus der Datenbank gel\xc3\xb6scht und in die Blacklist aufgenommen, so dass der Film bei zuk\xc3\xbcnftigen Datenbank Aktualisierungen ignoriert wird.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                # else:
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
        self['text1'].setText('YouTube')
        # if self.language == '&language=de':
            # self['text2'].setText('Ansichten')
        # else:
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
        # if self.language == '&language=de':
            # self['text1'].setText('Hilfe')
            # self['text2'].setText('Update')
            # self['text3'].setText('Editieren')
        # else:
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

    def makeEpisodes(self):
        try:
            posterurl = self.posterlist[self.index]
            if search('<episode>', posterurl) is not None:
                bannerurl = search('<episode>(.*?)<episode>', posterurl)
                bannerurl = bannerurl.group(1)
                banner = sub('.*?[/]', '', bannerurl)
                banner = config.plugins.moviebrowser.cachefolder.value + '/' + banner
                if fileExists(banner):
                    Banner = loadPic(banner, 540, 99, 3, 0, 0, 0)
                    if Banner is not None:
                        self['banner'].instance.setPixmap(Banner)
                        self['banner'].show()
                else:
                    if pythonVer == 3:
                        bannerurl = bannerurl.encode()

                    getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
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
        Banner = loadPic(banner, 540, 99, 3, 0, 0, 0)
        if Banner is not None:
            self['banner'].instance.setPixmap(Banner)
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
                    ePoster = loadPic(eposter, 540, 405, 3, 0, 0, 0)
                    if ePoster is not None:
                        self['eposter'].instance.setPixmap(ePoster)
                        self['eposter'].show()
                else:
                    if pythonVer == 3:
                        eposterurl = eposterurl.encode()
                    getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
        except IndexError:
            pass

        return

    def getEPoster(self, output, eposter):
        f = open(eposter, 'wb')
        f.write(output)
        f.close()
        ePoster = loadPic(eposter, 500, 375, 3, 0, 0, 0)
        if ePoster is not None:
            self['eposter'].instance.setPixmap(ePoster)
            self['eposter'].show()
        return

    def makePoster(self):
        try:
            posterurl = self.posterlist[self.index]
            posterurl = sub('<episode>.*?<episode>', '', posterurl)
            poster = sub('.*?[/]', '', posterurl)
            poster = config.plugins.moviebrowser.cachefolder.value + '/' + poster
            if fileExists(poster):
                Poster = loadPic(poster, 150, 225, 3, 0, 0, 0)
                if Poster is not None:
                    self['posterback'].show()
                    self['poster'].instance.setPixmap(Poster)
                    self['poster'].show()
            else:
                if pythonVer == 3:
                    posterurl = posterurl.encode()
                getPage(posterurl).addCallback(self.getPoster, poster).addErrback(self.downloadError)
        except IndexError:
            self['posterback'].hide()
            self['poster'].hide()

        return

    def getPoster(self, output, poster):
        f = open(poster, 'wb')
        f.write(output)
        f.close()
        Poster = loadPic(poster, 150, 225, 3, 0, 0, 0)
        if Poster is not None:
            self['posterback'].show()
            self['poster'].instance.setPixmap(Poster)
            self['poster'].show()
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
                        Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                        if Backdrop is not None:
                            self['backdrop'].instance.setPixmap(Backdrop)
                            self['backdrop'].show()
                            os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()

                        getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                elif fileExists(backdrop):
                    Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                    if Backdrop is not None:
                        self['backdrop'].instance.setPixmap(Backdrop)
                        self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()

                    getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        f = open(backdrop, 'wb')
        f.write(output)
        f.close()
        Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
        if Backdrop is not None:
            self['backdrop'].instance.setPixmap(Backdrop)
            self['backdrop'].show()
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                if Backdrop is not None:
                    self['backdrop'].instance.setPixmap(Backdrop)
                    self['backdrop'].show()
                    os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
        elif fileExists(backdrop):
            Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
            if Backdrop is not None:
                self['backdrop'].instance.setPixmap(Backdrop)
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
                # if self.language == '&language=de':
                    # self.session.open(MessageBox, 'Serien Ordner: Keine Info m\xc3\xb6glich', MessageBox.TYPE_ERROR)
                # else:
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
                    # if self.language == '&language=de':
                        # self.movies.append(('<Liste der Film Ordner>', config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
                    # else:
                    self.movies.append((_('<List of Movie Folder>'), config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
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
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.filter_return, filterList, self.folders, 'Film Ordner Auswahl', filter, len(self.folders), max)
            # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.genres, 'Genre Auswahl', filter, len(self.genres), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.actors, 'Darsteller Auswahl', filter, len(self.actors), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.directors, 'Regisseur Auswahl', filter, len(self.directors), max)
                # else:
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
                    res.append(MultiContentEntryText(pos=(0, 0), size=(540, 30), font=22, flags=RT_HALIGN_LEFT, text=self.seasons[i]))
                    list.append(res)

                self['episodes'].l.setList(list)
                self['episodes'].l.setItemHeight(30)
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

    def youTube(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                self.session.open(searchYouTube, name)
            except IndexError:
                pass

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserConfig)

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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

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
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
            self.close()


class movieBrowserBackdrop(Screen):
    skin = """
    <screen position="center,center" size="1024,576" flags="wfNoBorder" title="  ">
        <widget name="backdrop" position="0,0" size="1024,576" alphatest="on" transparent="0" zPosition="-2"/>
        <widget name="infoback" position="15,15" size="460,400" alphatest="blend" transparent="1" zPosition="-1"/>
        <widget name="plotfullback" position="549,15" size="460,400" alphatest="blend" transparent="1" zPosition="-1"/>
        <widget name="audiotype" position="719,15" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="videomode" position="809,15" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="videocodec" position="869,15" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="aspectratio" position="959,15" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="ddd" position="959,15" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="ddd2" position="659,15" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="name" position="25,16" size="400,55" font="{font};24" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="3"/>
        <widget name="seen" position="425,16" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="3"/>
        <widget name="Rating" position="25,70" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="4"/>
        <widget name="ratings" position="25,100" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="5"/>
        <widget name="ratingsback" position="25,100" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="6"/>
        <widget name="Director" position="25,140" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="8"/>
        <widget name="director" position="25,170" size="285,50" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="9"/>
        <widget name="Country" position="320,140" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="10"/>
        <widget name="country" position="320,170" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="11"/>
        <widget name="Actors" position="25,210" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="12"/>
        <widget name="actors" position="25,240" size="285,95" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="13"/>
        <widget name="Year" position="320,210" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="14"/>
        <widget name="year" position="320,240" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="15"/>
        <widget name="Runtime" position="320,280" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="16"/>
        <widget name="runtime" position="320,310" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="17"/>
        <widget name="Genres" position="25,350" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="18"/>
        <widget name="genres" position="25,380" size="440,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>
        <widget name="plotfull" position="559,22" size="440,390" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="20"/>
        <widget name="eposter" position="559,50" size="440,330" alphatest="on" transparent="1" zPosition="21"/>
        <widget name="banner" position="559,50" size="440,81" alphatest="on" transparent="1" zPosition="21"/>
        <widget name="episodes" position="559,137" size="440,250" scrollbarMode="showOnDemand" transparent="1" zPosition="21"/>
        <widget name="poster0" position="-42,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back0" position="0,426" size="50,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster1" position="55,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back1" position="55,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster2" position="152,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back2" position="152,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster3" position="249,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back3" position="249,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster4" position="346,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back4" position="346,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster5" position="443,352" size="138,207" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster6" position="586,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back6" position="586,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster7" position="683,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back7" position="683,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster8" position="780,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back8" position="780,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster9" position="877,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back9" position="877,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
        <widget name="poster10" position="974,426" size="92,138" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back10" position="974,426" size="92,138" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_back.png"/>
    </screen>


    """

    skinHD = """
     <screen position="center,center" size="1280,720" flags="wfNoBorder" title="  ">
        <widget name="backdrop" position="0,0" size="1280,720" alphatest="on" transparent="0" zPosition="-2"/>
        <widget name="infoback" position="25,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1"/>
        <widget name="plotfullback" position="730,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1"/>
        <widget name="audiotype" position="970,20" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="videomode" position="1060,20" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="videocodec" position="1120,20" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="aspectratio" position="1210,20" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="ddd" position="1210,20" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="ddd2" position="910,20" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
        <widget name="name" position="40,30" size="455,70" font="{font};28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="3"/>
        <widget name="seen" position="495,30" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="3"/>
        <widget name="Rating" position="40,100" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="4"/>
        <widget name="ratings" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="5"/>
        <widget name="ratingsback" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="6"/>
        <widget name="Director" position="40,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="8"/>
        <widget name="director" position="40,200" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="9"/>
        <widget name="Country" position="370,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="10"/>
        <widget name="country" position="370,200" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="11"/>
        <widget name="Actors" position="40,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="12"/>
        <widget name="actors" position="40,270" size="320,102" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="13"/>
        <widget name="Year" position="370,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="14"/>
        <widget name="year" position="370,270" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="15"/>
        <widget name="Runtime" position="370,310" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="16"/>
        <widget name="runtime" position="370,340" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="17"/>
        <widget name="Genres" position="40,380" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="18"/>
        <widget name="genres" position="40,410" size="500,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>
        <widget name="plotfull" position="745,40" size="500,393" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="20"/>
        <widget name="eposter" position="742,53" size="500,375" alphatest="on" transparent="1" zPosition="21"/>
        <widget name="banner" position="742,53" size="500,92" alphatest="on" transparent="1" zPosition="21"/>
        <widget name="episodes" position="742,151" size="500,270" scrollbarMode="showOnDemand" transparent="1" zPosition="21"/>
        <widget name="poster0" position="-65,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back0" position="0,535" size="35,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster1" position="40,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back1" position="40,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster2" position="145,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back2" position="145,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster3" position="250,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back3" position="250,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster4" position="355,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back4" position="355,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster5" position="460,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back5" position="460,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster6" position="565,455" size="150,225" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster7" position="720,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back7" position="720,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster8" position="825,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back8" position="825,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster9" position="930,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back9" position="930,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster10" position="1035,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back10" position="1035,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster11" position="1140,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back11" position="1140,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
        <widget name="poster12" position="1245,535" size="100,150" zPosition="21" transparent="1" alphatest="on"/>
        <widget name="poster_back12" position="1245,535" size="100,150" zPosition="22" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png"/>
    </screen>
    """

    def __init__(self, session, index, content, filter):
        # f = open('/proc/stb/video/alpha', 'w')
        # f.write('%i' % config.plugins.moviebrowser.transparency.value)
        # f.close()
        if config.plugins.moviebrowser.plugin_size.value == 'full':
            self.xd = False
            color = config.plugins.moviebrowser.color.value
            if config.plugins.moviebrowser.font.value == 'yes':
                font = 'Sans'
            else:
                font = 'Regular'
            self.dict = {
                'color': color,
                'font': font
            }
            self.skin = applySkinVars(movieBrowserBackdrop.skinHD, self.dict)
        else:
            self.xd = True
            color = config.plugins.moviebrowser.color.value
            if config.plugins.moviebrowser.font.value == 'yes':
                font = 'Sans'
            else:
                font = 'Regular'
            self.dict = {
                'color': color,
                'font': font
            }
            self.skin = applySkinVars(movieBrowserBackdrop.skin, self.dict)
        Screen.__init__(self, session)
        self.fhd = False
        if config.plugins.moviebrowser.fhd.value == 'yes':
            if getDesktop(0).size().width() == 1920:
                self.fhd = True
                # try:
                    # gMainDC.getInstance().setResolution(1280, 720)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1280, 720))
                # except:
                    # import traceback
                    # traceback.print_exc()

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
        if config.plugins.moviebrowser.language.value == 'de':
            self.language = '&language=de'
        elif config.plugins.moviebrowser.language.value == 'es':
            self.language = '&language=es'
        elif config.plugins.moviebrowser.language.value == 'it':
            self.language = '&language=it'
        elif config.plugins.moviebrowser.language.value == 'fr':
            self.language = '&language=fr'
        elif config.plugins.moviebrowser.language.value == 'ru':
            self.language = '&language=ru'
        else:
            self.language = '&language=en'
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
        # if self.language == '&language=de':
            # self['Director'] = Label('Regie:')
            # self['Actors'] = Label('Darsteller:')
            # self['Year'] = Label('Jahr:')
            # self['Runtime'] = Label('Laufzeit:')
            # self['Country'] = Label('Land:')
        # else:
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
        if self.xd is False:
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
            'yellow': self.youTube,
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
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if config.plugins.moviebrowser.autocheck.value == 'yes':
            self.version = '3.7rc3'
            self.link = 'https://sites.google.com/site/kashmirplugins/home/movie-browser'

        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)
        if self.xd is False:
            self.infoBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_backHD.png'
            InfoBack = loadPic(self.infoBackPNG, 525, 430, 3, 0, 0, 0)
        else:
            self.infoBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_back.png'
            InfoBack = loadPic(self.infoBackPNG, 460, 400, 3, 0, 0, 0)
        if InfoBack is not None:
            self['plotfullback'].instance.setPixmap(InfoBack)
            self['infoback'].instance.setPixmap(InfoBack)
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
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.reset_return, MessageBox, 'Die Movie Browser Datenbank wird jetzt neu erstellt. Je nach Anzahl der Filme kann dies mehrere Minuten dauern.\n\nSollte sich das Plugin nach einigen Minuten automatisch beenden, starten Sie das Plugin erneut und f\xc3\xbchren Sie ein manuelles Datenbank Update durch (Video Taste).\n\nSoll die Datenbank jetzt erstellt werden?', MessageBox.TYPE_YESNO)
            # else:
                self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        # elif self.language == '&language=de':
            # self.session.openWithCallback(self.first_return, MessageBox, 'Bevor die Datenbank neu erstellt wird, \xc3\xbcberpr\xc3\xbcfen Sie Ihre Einstellungen im Setup des Plugins:\n\n- Kontrollieren Sie den Pfad zum Film Ordner\n- \xc3\x9cberpr\xc3\xbcfen Sie Ihre Spracheinstellung: TMDb/TheTVDb Sprache\n- \xc3\x84ndern Sie den Cache Ordner auf Ihre Festplatte.', MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset', 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.close, movieBrowserConfig)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
                os.remove('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset')
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
                        except IndexError:
                            name = ' '

                        try:
                            filename = movieline[1]
                        except IndexError:
                            filename = ' '

                        try:
                            date = movieline[2]
                        except IndexError:
                            date = ' '

                        try:
                            runtime = movieline[3]
                        except IndexError:
                            runtime = ' '

                        try:
                            rating = movieline[4]
                        except IndexError:
                            rating = ' '

                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        try:
                            actors = movieline[6]
                        except IndexError:
                            actors = ' '

                        try:
                            genres = movieline[7]
                        except IndexError:
                            genres = ' '

                        try:
                            year = movieline[8]
                        except IndexError:
                            year = ' '

                        try:
                            country = movieline[9]
                        except IndexError:
                            country = ' '

                        try:
                            plotfull = movieline[10]
                        except IndexError:
                            plotfull = ' '

                        try:
                            poster = movieline[11]
                        except IndexError:
                            poster = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png'

                        try:
                            backdrop = movieline[12]
                        except IndexError:
                            backdrop = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png'

                        try:
                            content = movieline[13]
                        except IndexError:
                            content = 'Movie:Top'

                        try:
                            seen = movieline[14]
                        except IndexError:
                            seen = 'unseen'

                        try:
                            media = movieline[15]
                        except IndexError:
                            media = '\n'

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
                    # if self.language == '&language=de':
                        # self.namelist.append('<Liste der Film Ordner>')
                    # else:
                    self.namelist.append('<List of Movie Folder>')
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
            # if self.language == '&language=de':
                # if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.openWithCallback(self.database_return, MessageBox, '\nMovie Browser Datenbank aktualisieren?', MessageBox.TYPE_YESNO)
                # elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.open(MessageBox, '\nFilm Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
                # else:
                    # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden:\nIhre Datenbank ist aktuell.', MessageBox.TYPE_INFO)
            # else:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            # if self.language == '&language=de':
                # if orphaned == 1:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.' % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
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
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif orphaned == 1:
                    # if seriescount == 0:
                        # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                    # elif moviecount == 0:
                        # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                    # else:
                        # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
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
                        if self.xd is False:
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
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            # elif self.language == '&language=de':
                                # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nDas DVD Player Plugin ist nicht installiert.', MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    # elif self.language == '&language=de':
                        # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
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
                    # if self.language == '&language=de':
                        # self.session.open(MessageBox, '\nTMDb Film Update Fehler:\nSerien Ordner', MessageBox.TYPE_ERROR)
                    # else:
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
                url = 'https://api.themoviedb.org/3/search/movie?api_key=dfc629f7ff6936a269f8c5cdb194c890&query=' + name + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TMDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
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
        if self.language == '&language=de':
            titel = 'TMDb Ergebnisse'
        else:
            titel = 'TMDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TMDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == 'movie':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=dfc629f7ff6936a269f8c5cdb194c890' % new + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TheTVDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
            self.session.open(MessageBox, _('\nThe TVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
            output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>https://www.thetvdb.com/wiki/skins/common/images/wiki.png</poster>', output)
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
                poster.append('https://www.thetvdb.com/wiki/skins/common/images/wiki.png')

            try:
                id.append(TVDbid[0])
            except IndexError:
                id.append('0')

            try:
                country.append(Country[0])
            except IndexError:
                country.append(' ')

        # if self.language == '&language=de':
            # titel = 'TheTVDb Ergebnisse'
        # else:
        titel = 'TheTVDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TheTVDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo The TVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
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
                url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
                # if self.language == '&language=de':
                    # if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                        # self.session.open(MessageBox, '\nDie Liste der Film Ordner kann nicht gel\xc3\xb6scht werden.', MessageBox.TYPE_ERROR)
                    # elif content == 'Series:Top':
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\nAlle %s Eintr\xc3\xa4ge werden aus der Datenbank, aber nicht aus dem Film Ordner gel\xc3\xb6scht.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                    # else:
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\n%s wird aus der Datenbank und aus dem Film Ordner gel\xc3\xb6scht!\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
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
                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.blacklist_return, MessageBox, '\n%s wird aus der Datenbank gel\xc3\xb6scht und in die Blacklist aufgenommen, so dass der Film bei zuk\xc3\xbcnftigen Datenbank Aktualisierungen ignoriert wird.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                # else:
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
            if self.xd is False:
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
                        if self.xd is False:
                            Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
                        else:
                            Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
                        if Banner is not None:
                            self['banner'].instance.setPixmap(Banner)
                            self['banner'].show()
                    else:
                        if pythonVer == 3:
                            bannerurl = bannerurl.encode()
                        getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
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
                            if self.xd is False:
                                Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
                            else:
                                Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
                            if Banner is not None:
                                self['banner'].instance.setPixmap(Banner)
                                self['banner'].show()
                        else:
                            if pythonVer == 3:
                                bannerurl = bannerurl.encode()
                            getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
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
                        if self.xd is False:
                            ePoster = loadPic(eposter, 500, 375, 3, 0, 0, 0)
                        else:
                            ePoster = loadPic(eposter, 440, 330, 3, 0, 0, 0)
                        if ePoster is not None:
                            self['eposter'].instance.setPixmap(ePoster)
                            self['eposter'].show()
                    else:
                        if pythonVer == 3:
                            eposterurl = eposterurl.encode()
                        getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
                else:
                    self.toggleCount = 2
                    self['eposter'].hide()
                    self['plotfull'].show()
            except IndexError:
                pass

        return

    def getEPoster(self, output, eposter):
        f = open(eposter, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            ePoster = loadPic(eposter, 500, 375, 3, 0, 0, 0)
        else:
            ePoster = loadPic(eposter, 440, 330, 3, 0, 0, 0)
        if ePoster is not None:
            self['plotfull'].hide()
            self['eposter'].instance.setPixmap(ePoster)
            self['eposter'].show()
        return

    def getBanner(self, output, banner):
        f = open(banner, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
        else:
            Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
        if Banner is not None:
            self['plotfull'].hide()
            self['banner'].instance.setPixmap(Banner)
            self['banner'].show()
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
                    if self.xd is False:
                        if x == 6:
                            Poster = loadPic(poster, 150, 225, 3, 0, 0, 0)
                        else:
                            Poster = loadPic(poster, 100, 150, 3, 0, 0, 0)
                    elif x == 5:
                        Poster = loadPic(poster, 138, 207, 3, 0, 0, 0)
                    else:
                        Poster = loadPic(poster, 92, 138, 3, 0, 0, 0)
                    if Poster is not None:
                        self['poster' + str(x)].instance.setPixmap(Poster)
                        self['poster' + str(x)].show()
                else:
                    if pythonVer == 3:
                        posterurl = posterurl.encode()

                    getPage(posterurl).addCallback(self.getPoster, x, poster).addErrback(self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        return

    def getPoster(self, output, x, poster):
        f = open(poster, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            if x == 6:
                Poster = loadPic(poster, 150, 225, 3, 0, 0, 0)
            else:
                Poster = loadPic(poster, 100, 150, 3, 0, 0, 0)
        elif x == 5:
            Poster = loadPic(poster, 138, 207, 3, 0, 0, 0)
        else:
            Poster = loadPic(poster, 92, 138, 3, 0, 0, 0)
        if Poster is not None:
            self['poster' + str(x)].instance.setPixmap(Poster)
            self['poster' + str(x)].show()
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
                        if self.xd is False:
                            Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                        else:
                            Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                        if Backdrop is not None:
                            self['backdrop'].instance.setPixmap(Backdrop)
                            self['backdrop'].show()
                            os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()

                        getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                elif fileExists(backdrop):
                    if self.xd is False:
                        Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                    else:
                        Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                    if Backdrop is not None:
                        self['backdrop'].instance.setPixmap(Backdrop)
                        self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()

                    getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        f = open(backdrop, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
        else:
            Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
        if Backdrop is not None:
            self['backdrop'].instance.setPixmap(Backdrop)
            self['backdrop'].show()
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                if self.xd is False:
                    Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                else:
                    Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                if Backdrop is not None:
                    self['backdrop'].instance.setPixmap(Backdrop)
                    self['backdrop'].show()
                    os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
        elif fileExists(backdrop):
            if self.xd is False:
                Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
            else:
                Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
            if Backdrop is not None:
                self['backdrop'].instance.setPixmap(Backdrop)
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
                # if self.language == '&language=de':
                    # self.session.open(MessageBox, 'Serien Ordner: Keine Info m\xc3\xb6glich', MessageBox.TYPE_ERROR)
                # else:
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
                    # if self.language == '&language=de':
                        # self.movies.append(('<Liste der Film Ordner>', config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
                    # else:
                    self.movies.append(('<List of Movie Folder>', config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
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
                if self.xd is False:
                    self.posterindex = 6
                else:
                    self.posterindex = 5
                self.makeMovies(self.filter)
            else:
                self.filterseen = False
                self.filter = self.content
                self.index = 0
                self.toggleCount = 0
                if self.xd is False:
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
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.filter_return, filterList, self.folders, 'Film Ordner Auswahl', filter, len(self.folders), max)
            # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.genres, 'Genre Auswahl', filter, len(self.genres), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.actors, 'Darsteller Auswahl', filter, len(self.actors), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.directors, 'Regisseur Auswahl', filter, len(self.directors), max)
                # else:
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
                if self.xd is False:
                    listwidth = 500
                else:
                    listwidth = 440
                idx = 0
                for x in self.seasons:
                    idx += 1

                for i in range(idx):
                    try:
                        res = ['']
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
            if self.xd is False:
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
                if self.xd is False:
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
                if self.xd is False:
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
                if self.xd is False:
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

    def youTube(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                self.session.open(searchYouTube, name)
            except IndexError:
                pass

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()

        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserConfig)

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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

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
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
            self.close()


class movieBrowserPosterwall(Screen):

    def __init__(self, session, index, content, filter):
        # f = open('/proc/stb/video/alpha', 'w')
        # f.write('%i' % config.plugins.moviebrowser.transparency.value)
        # f.close()
        if config.plugins.moviebrowser.plugin_size.value == 'full':
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
            if self.xd is False:
                self.positionlist.append((posX - 13, posY - 15))
            else:
                self.positionlist.append((posX - 8, posY - 10))
            skincontent += '<widget name="poster' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-4" transparent="1" alphatest="on" />'
            skincontent += '<widget name="poster_back' + str(x) + '" position="' + str(posX) + ',' + str(posY) + '" size="' + str(self.picX) + ',' + str(self.picY) + '" zPosition="-3" transparent="1" alphatest="blend" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/poster_backHD.png" />'

        skin = """
        <screen position="center,center" size="1024,576" flags="wfNoBorder" title="  ">
            <widget name="backdrop" position="0,0" size="1024,576" alphatest="on" transparent="0" zPosition="-5"/>
            <widget name="infoback" position="5,500" size="1014,71" alphatest="blend" transparent="1" zPosition="2"/>
            <widget name="ratings_up" position="55,505" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>
            <widget name="ratingsback_up" position="55,505" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>
            <widget name="audiotype" position="15,530" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="videomode" position="105,530" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="videocodec" position="165,530" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="aspectratio" position="255,530" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ddd" position="15,530" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ddd2" position="315,530" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ratings" position="55,524" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>
            <widget name="ratingsback" position="55,524" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>
            <widget name="name" position="325,500" size="374,71" font="{font};26" foregroundColor="#FFFFFF" halign="center" valign="center" transparent="1" zPosition="5"/>
            <widget name="seen" position="700,516" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="6"/>
            <widget name="runtime" position="764,500" size="120,71" font="{font};24" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="7"/>
            <widget name="country" position="889,500" size="55,71" font="{font};24" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="8"/>
            <widget name="year" position="949,500" size="60,71" font="{font};24" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="9"/>
            <widget name="2infoback" position="15,15" size="460,400" alphatest="blend" transparent="1" zPosition="-1"/>
            <widget name="2name" position="25,16" size="400,55" font="{font};24" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="13"/>
            <widget name="2seen" position="425,16" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="13"/>
            <widget name="2Rating" position="25,70" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="14"/>
            <widget name="2ratings" position="25,100" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="15"/>
            <widget name="2ratingsback" position="25,100" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="16"/>
            <widget name="2Director" position="25,140" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="18"/>
            <widget name="2director" position="25,170" size="285,50" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>
            <widget name="2Country" position="320,140" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="20"/>
            <widget name="2country" position="320,170" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="21"/>
            <widget name="2Actors" position="25,210" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="22"/>
            <widget name="2actors" position="25,240" size="285,95" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="23"/>
            <widget name="2Year" position="320,210" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="24"/>
            <widget name="2year" position="320,240" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="25"/>
            <widget name="2Runtime" position="320,280" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="26"/>
            <widget name="2runtime" position="320,310" size="125,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="27"/>
            <widget name="2Genres" position="25,350" size="125,25" font="{font};20" halign="left" foregroundColor="{color}" transparent="1" zPosition="28"/>
            <widget name="2genres" position="25,380" size="440,25" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="29"/>
            <widget name="plotfullback" position="549,15" size="460,400" alphatest="blend" transparent="1" zPosition="-1"/>
            <widget name="plotfull" position="559,22" size="440,390" font="{font};20" foregroundColor="#FFFFFF" transparent="1" zPosition="30"/>
            <widget name="eposter" position="559,50" size="440,330" alphatest="on" transparent="1" zPosition="30"/>
            <widget name="banner" position="559,50" size="440,81" alphatest="on" transparent="1" zPosition="30"/>
            <widget name="episodes" position="559,137" size="440,250" scrollbarMode="showOnDemand" transparent="1" zPosition="30"/>
            <widget name="frame" position="7,-4" size="122,180" zPosition="-2" alphatest="on"/>"' + skincontent + '
        </screen>
        """

        skinHD = """
        <screen position="center,center" size="1280,720" flags="wfNoBorder" title="  ">
            <widget name="backdrop" position="0,0" size="1280,720" alphatest="on" transparent="0" zPosition="-5"/>
            <widget name="infoback" position="5,620" size="1270,95" alphatest="blend" transparent="1" zPosition="2"/>
            <widget name="ratings_up" position="65,641" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>
            <widget name="ratingsback_up" position="65,641" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>
            <widget name="audiotype" position="25,672" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolby.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dolbyplus.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dts.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dtshd.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mp2.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="videomode" position="115,672" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/1080.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/720.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/480.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="videocodec" position="175,672" size="80,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/h264.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/mpeg2.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/divx.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/flv.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/dvd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="aspectratio" position="265,672" size="50,38" pixmaps="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/16_9.png,/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/4_3.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ddd" position="25,672" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ddd2" position="325,672" size="50,38" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ddd.png" transparent="1" alphatest="blend" zPosition="21"/>
            <widget name="ratings" position="65,657" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="3"/>
            <widget name="ratingsback" position="65,657" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="4"/>
            <widget name="name" position="335,620" size="610,95" font="{font};28" foregroundColor="#FFFFFF" valign="center" halign="center" transparent="1" zPosition="5"/>
            <widget name="seen" position="950,643" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="6"/>
            <widget name="runtime" position="1000,620" size="120,95" font="{font};26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="7"/>
            <widget name="country" position="1125,620" size="60,95" font="{font};26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="8"/>
            <widget name="year" position="1190,620" size="65,95" font="{font};26" foregroundColor="#FFFFFF" halign="right" valign="center" transparent="1" zPosition="9"/>
            <widget name="2infoback" position="25,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1"/>
            <widget name="2name" position="40,30" size="455,70" font="{font};28" foregroundColor="#FFFFFF" valign="center" transparent="1" zPosition="13"/>
            <widget name="2seen" position="495,30" size="40,40" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/seen.png" transparent="1" alphatest="on" zPosition="13"/>
            <widget name="2Rating" position="40,100" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="14"/>
            <widget name="2ratings" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png" borderWidth="0" orientation="orHorizontal" transparent="1" zPosition="15"/>
            <widget name="2ratingsback" position="40,130" size="210,21" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png" alphatest="on" zPosition="16"/>
            <widget name="2Director" position="40,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="18"/>
            <widget name="2director" position="40,200" size="320,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="19"/>
            <widget name="2Country" position="370,170" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="20"/>
            <widget name="2country" position="370,200" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="21"/>
            <widget name="2Actors" position="40,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="22"/>
            <widget name="2actors" position="40,270" size="320,102" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="23"/>
            <widget name="2Year" position="370,240" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="24"/>
            <widget name="2year" position="370,270" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="25"/>
            <widget name="2Runtime" position="370,310" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="26"/>
            <widget name="2runtime" position="370,340" size="125,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="27"/>
            <widget name="2Genres" position="40,380" size="125,28" font="{font};22" halign="left" foregroundColor="{color}" transparent="1" zPosition="28"/>
            <widget name="2genres" position="40,410" size="500,28" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="29"/>
            <widget name="plotfullback" position="730,25" size="525,430" alphatest="blend" transparent="1" zPosition="-1"/>
            <widget name="plotfull" position="745,40" size="500,393" font="{font};22" foregroundColor="#FFFFFF" transparent="1" zPosition="30"/>
            <widget name="eposter" position="742,53" size="500,375" alphatest="on" transparent="1" zPosition="30"/>
            <widget name="banner" position="742,53" size="500,92" alphatest="on" transparent="1" zPosition="30"/>
            <widget name="episodes" position="742,151" size="500,270" scrollbarMode="showOnDemand" transparent="1" zPosition="30"/>
            <widget name="frame" position="7,-9" size="160,230" zPosition="-2" alphatest="on"/>"' + skincontent + '
        </screen>
        """
        if self.xd is False:
            color = config.plugins.moviebrowser.color.value
            if config.plugins.moviebrowser.font.value == 'yes':
                font = 'Sans'
            else:
                font = 'Regular'
            self.dict = {
                'color': color,
                'font': font
            }
            self.skin = applySkinVars(skinHD, self.dict)
        else:
            color = config.plugins.moviebrowser.color.value
            if config.plugins.moviebrowser.font.value == 'yes':
                font = 'Sans'
            else:
                font = 'Regular'
            self.dict = {
                'color': color,
                'font': font
            }
            self.skin = applySkinVars(skin, self.dict)
        Screen.__init__(self, session)
        self.fhd = False
        if config.plugins.moviebrowser.fhd.value == 'yes':
            if getDesktop(0).size().width() == 1920:
                self.fhd = True
                # try:
                    # gMainDC.getInstance().setResolution(1280, 720)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1280, 720))
                # except:
                    # import traceback
                    # traceback.print_exc()

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
        if config.plugins.moviebrowser.language.value == 'de':
            self.language = '&language=de'
        elif config.plugins.moviebrowser.language.value == 'es':
            self.language = '&language=es'
        elif config.plugins.moviebrowser.language.value == 'it':
            self.language = '&language=it'
        elif config.plugins.moviebrowser.language.value == 'fr':
            self.language = '&language=fr'
        elif config.plugins.moviebrowser.language.value == 'ru':
            self.language = '&language=ru'
        else:
            self.language = '&language=en'
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
        # if self.language == '&language=de':
            # self['2Director'] = Label('Regie:')
            # self['2Actors'] = Label('Darsteller:')
            # self['2Year'] = Label('Jahr:')
            # self['2Runtime'] = Label('Laufzeit:')
            # self['2Country'] = Label('Land:')
        # else:
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
            'yellow': self.youTube,
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
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        self.lastfilter = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/filter'
        self.lastfile = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/last'
        self.onLayoutFinish.append(self.onLayoutFinished)

    def onLayoutFinished(self):
        if config.plugins.moviebrowser.autocheck.value == 'yes':
            self.version = '3.7rc3'
            self.link = 'https://sites.google.com/site/kashmirplugins/home/movie-browser'

        if fileExists(self.database):
            size = os.path.getsize(self.database)
            if size < 10:
                os.remove(self.database)
        if self.xd is False:
            self.infoBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_backHD.png'
            self.infosmallBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_small_backHD.png'
            InfoBack = loadPic(self.infoBackPNG, 525, 430, 3, 0, 0, 0)
            InfoSmallBack = loadPic(self.infosmallBackPNG, 1270, 95, 3, 0, 0, 0)
        else:
            self.infoBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_back.png'
            self.infosmallBackPNG = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/info_small_back.png'
            InfoBack = loadPic(self.infoBackPNG, 460, 400, 3, 0, 0, 0)
            InfoSmallBack = loadPic(self.infosmallBackPNG, 1014, 71, 3, 0, 0, 0)
        if InfoBack is not None and InfoSmallBack is not None:
            self['infoback'].instance.setPixmap(InfoSmallBack)
            self['2infoback'].instance.setPixmap(InfoBack)
            self['plotfullback'].instance.setPixmap(InfoBack)
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
        if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.reset_return, MessageBox, 'Die Movie Browser Datenbank wird jetzt neu erstellt. Je nach Anzahl der Filme kann dies mehrere Minuten dauern.\n\nSollte sich das Plugin nach einigen Minuten automatisch beenden, starten Sie das Plugin erneut und f\xc3\xbchren Sie ein manuelles Datenbank Update durch (Video Taste).\n\nSoll die Datenbank jetzt erstellt werden?', MessageBox.TYPE_YESNO)
            # else:
            self.session.openWithCallback(self.reset_return, MessageBox, _('The Movie Browser Database will be rebuild now. Depending on the number of your Movies this can take several minutes.\n\nIf the plugin terminates after a few minutes, restart the plugin and make a manual Database Update (Video button).\n\nRebuild the Database now?'), MessageBox.TYPE_YESNO)
        # elif self.language == '&language=de':
            # self.session.openWithCallback(self.first_return, MessageBox, 'Bevor die Datenbank neu erstellt wird, \xc3\xbcberpr\xc3\xbcfen Sie Ihre Einstellungen im Setup des Plugins:\n\n- Kontrollieren Sie den Pfad zum Film Ordner\n- \xc3\x9cberpr\xc3\xbcfen Sie Ihre Spracheinstellung: TMDb/TheTVDb Sprache\n- \xc3\x84ndern Sie den Cache Ordner auf Ihre Festplatte.', MessageBox.TYPE_YESNO)
        else:
            self.session.openWithCallback(self.first_return, MessageBox, _('Before the Database will be rebuild, check your settings in the setup of the plugin:\n\n- Check the path to the Movie Folder\n- Check your TMDb/TheTVDb Language\n- Change the Cache Folder to your hard disk drive.'), MessageBox.TYPE_YESNO)

    def first_return(self, answer):
        if answer is True:
            open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset', 'w').close()
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.session.openWithCallback(self.close, movieBrowserConfig)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
            self.close()

    def reset_return(self, answer):
        if answer is True:
            self.reset = True
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset'):
                os.remove('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset')
            if fileExists(self.blacklist):
                os.remove(self.blacklist)
            open(self.database, 'w').close()
            self.makeMovieBrowserTimer = eTimer()
            self.resetTimer = eTimer()
            self.resetTimer.callback.append(self.database_return(True))
            self.resetTimer.start(500, True)
        else:
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
                        movieline = line.split(':::')
                        try:
                            name = movieline[0]
                            name = sub('[Ss][0]+[Ee]', 'Special ', name)
                        except IndexError:
                            name = ' '

                        try:
                            filename = movieline[1]
                        except IndexError:
                            filename = ' '

                        try:
                            date = movieline[2]
                        except IndexError:
                            date = ' '

                        try:
                            runtime = movieline[3]
                        except IndexError:
                            runtime = ' '

                        try:
                            rating = movieline[4]
                        except IndexError:
                            rating = ' '

                        try:
                            director = movieline[5]
                        except IndexError:
                            director = ' '

                        try:
                            actors = movieline[6]
                        except IndexError:
                            actors = ' '

                        try:
                            genres = movieline[7]
                        except IndexError:
                            genres = ' '

                        try:
                            year = movieline[8]
                        except IndexError:
                            year = ' '

                        try:
                            country = movieline[9]
                        except IndexError:
                            country = ' '

                        try:
                            plotfull = movieline[10]
                        except IndexError:
                            plotfull = ' '

                        try:
                            poster = movieline[11]
                        except IndexError:
                            poster = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png'

                        try:
                            backdrop = movieline[12]
                        except IndexError:
                            backdrop = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png'

                        try:
                            content = movieline[13]
                        except IndexError:
                            content = 'Movie:Top'

                        try:
                            seen = movieline[14]
                        except IndexError:
                            seen = 'unseen'

                        try:
                            media = movieline[15]
                        except IndexError:
                            media = '\n'

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
                    # if self.language == '&language=de':
                        # self.namelist.append('<Liste der Film Ordner>')
                    # else:
                    self.namelist.append('<List of Movie Folder>')
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
        return

    def updateDatabase(self):
        if self.ready is True:
            # if self.language == '&language=de':
                # if os.path.exists(config.plugins.moviebrowser.moviefolder.value) and os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.openWithCallback(self.database_return, MessageBox, '\nMovie Browser Datenbank aktualisieren?', MessageBox.TYPE_YESNO)
                # elif os.path.exists(config.plugins.moviebrowser.cachefolder.value):
                    # self.session.open(MessageBox, '\nFilm Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.moviefolder.value), MessageBox.TYPE_ERROR)
                # else:
                    # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Aktualisierung abgebrochen.' % str(config.plugins.moviebrowser.cachefolder.value), MessageBox.TYPE_ERROR)
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden:\nIhre Datenbank ist aktuell.', MessageBox.TYPE_INFO)
            # else:
            self.session.open(MessageBox, _('\nNo new Movies or Series found:\nYour Database is up to date.'), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif found == 0:
            # if self.language == '&language=de':
                # if orphaned == 1:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\nKeine neuen Filme oder Serien gefunden.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % str(orphaned), MessageBox.TYPE_INFO)
            if orphaned == 1:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entry deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            else:
                self.session.open(MessageBox, _('\nNo new Movies or Series found.\n%s orphaned Database Entries deleted.') % str(orphaned), MessageBox.TYPE_INFO)
            self.makeMovies(self.filter)
        elif orphaned == 0:
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.' % str(moviecount), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.' % str(seriescount), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.' % (str(moviecount), str(seriescount)), MessageBox.TYPE_INFO)
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
            # if self.language == '&language=de':
                # if moviecount == 1 and seriescount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0 and orphaned == 1:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 1 and seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Film in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 1 and moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serie in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif orphaned == 1:
                    # if seriescount == 0:
                        # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                    # elif moviecount == 0:
                        # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                    # else:
                        # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaister Datenbank Eintrag gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif seriescount == 0:
                    # self.session.open(MessageBox, '\n%s Filme in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(orphaned)), MessageBox.TYPE_INFO)
                # elif moviecount == 0:
                    # self.session.open(MessageBox, '\n%s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
                # else:
                    # self.session.open(MessageBox, '\n%s Filme und %s Serien in die Datenbank importiert.\n%s verwaiste Datenbank Eintr\xc3\xa4ge gel\xc3\xb6scht.' % (str(moviecount), str(seriescount), str(orphaned)), MessageBox.TYPE_INFO)
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
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                    elif filename.endswith('.iso') or filename.endswith('.ISO'):
                        if os.path.exists('/usr/lib/enigma2/python/Plugins/Extensions/DVDPlayer/'):
                            from Plugins.Extensions.DVDPlayer.plugin import DVDPlayer
                            if fileExists(filename):
                                self.session.open(DVDPlayer, dvd_filelist=[filename])
                            # elif self.language == '&language=de':
                                # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
                            else:
                                self.session.open(MessageBox, _('\nMovie file %s not available.') % filename, MessageBox.TYPE_ERROR)
                        # elif self.language == '&language=de':
                            # self.session.open(MessageBox, '\nDas DVD Player Plugin ist nicht installiert.', MessageBox.TYPE_ERROR)
                        else:
                            self.session.open(MessageBox, _('\nDVD Player Plugin not installed.'), MessageBox.TYPE_ERROR)
                    elif fileExists(filename):
                        sref = eServiceReference('4097:0:0:0:0:0:0:0:0:0:' + filename)
                        sref.setName(self.namelist[self.index])
                        self.session.open(MoviePlayer, sref)
                    # elif self.language == '&language=de':
                        # self.session.open(MessageBox, '\nFilmdatei %s nicht verf\xc3\xbcgbar.' % filename, MessageBox.TYPE_ERROR)
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
                    # if self.language == '&language=de':
                        # self.session.open(MessageBox, '\nTMDb Film Update Fehler:\nSerien Ordner', MessageBox.TYPE_ERROR)
                    # else:
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
                url = 'https://api.themoviedb.org/3/search/movie?api_key=dfc629f7ff6936a269f8c5cdb194c890&query=' + name + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TMDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
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
        # if self.language == '&language=de':
            # titel = 'TMDb Ergebnisse'
        # else:
        titel = 'TMDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TMDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo TMDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
        else:
            self.session.openWithCallback(self.makeTMDbUpdate, moviesList, titel, rating, year, titles, poster, id, country, True, False)

    def makeTMDbUpdate(self, new, select):
        if new is not None:
            if select == 'movie':
                movie = self.movielist[self.index]
                date = self.datelist[self.index]
                url = 'https://api.themoviedb.org/3/movie/%s?api_key=dfc629f7ff6936a269f8c5cdb194c890' % new + self.language
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDer TheTVDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
            self.session.open(MessageBox, _('\nThe TVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
            return

        output = output.replace('&amp;', '&')
        seriesid = re.findall('<seriesid>(.*?)</seriesid>', output)
        for x in range(len(seriesid)):
            url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + seriesid[x] + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
            output = sub('<poster>https://www.thetvdb.com/banners/_cache/</poster>', '<poster>https://www.thetvdb.com/wiki/skins/common/images/wiki.png</poster>', output)
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
                poster.append('https://www.thetvdb.com/wiki/skins/common/images/wiki.png')

            try:
                id.append(TVDbid[0])
            except IndexError:
                id.append('0')

            try:
                country.append(Country[0])
            except IndexError:
                country.append(' ')

        # if self.language == '&language=de':
            # titel = 'TheTVDb Ergebnisse'
        # else:
        titel = 'TheTVDb Results'
        if not titles:
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nKeine TheTVDb Ergebnisse f\xc3\xbcr %s.' % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
            # else:
            self.session.open(MessageBox, _('\nNo The TVDb Results for %s.') % self.name, MessageBox.TYPE_INFO, close_on_any_key=True)
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
                url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + new + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
                # if self.language == '&language=de':
                    # if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                        # self.session.open(MessageBox, '\nDie Liste der Film Ordner kann nicht gel\xc3\xb6scht werden.', MessageBox.TYPE_ERROR)
                    # elif content == 'Series:Top':
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\nAlle %s Eintr\xc3\xa4ge werden aus der Datenbank, aber nicht aus dem Film Ordner gel\xc3\xb6scht.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                    # else:
                        # self.session.openWithCallback(self.delete_return, MessageBox, '\n%s wird aus der Datenbank und aus dem Film Ordner gel\xc3\xb6scht!\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
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
                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.blacklist_return, MessageBox, '\n%s wird aus der Datenbank gel\xc3\xb6scht und in die Blacklist aufgenommen, so dass der Film bei zuk\xc3\xbcnftigen Datenbank Aktualisierungen ignoriert wird.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                # else:
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
            if self.xd is False:
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
            if self.xd is False:
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
        if self.xd is False:
            PlotFull = loadPic(self.infoBackPNG, 525, 430, 3, 0, 0, 0)
        else:
            PlotFull = loadPic(self.infoBackPNG, 460, 400, 3, 0, 0, 0)
        if PlotFull is not None:
            self['plotfullback'].instance.setPixmap(PlotFull)
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
                        if self.xd is False:
                            Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
                        else:
                            Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
                        if Banner is not None:
                            self['banner'].instance.setPixmap(Banner)
                            self['banner'].show()
                    else:
                        if pythonVer == 3:
                            bannerurl = bannerurl.encode()
                        getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
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
                            if self.xd is False:
                                Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
                            else:
                                Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
                            if Banner is not None:
                                self['banner'].instance.setPixmap(Banner)
                                self['banner'].show()
                        else:
                            if pythonVer == 3:
                                bannerurl = bannerurl.encode()
                            getPage(bannerurl).addCallback(self.getBanner, banner).addErrback(self.downloadError)
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
                        if self.xd is False:
                            ePoster = loadPic(eposter, 500, 375, 3, 0, 0, 0)
                        else:
                            ePoster = loadPic(eposter, 440, 330, 3, 0, 0, 0)
                        if ePoster is not None:
                            self['eposter'].instance.setPixmap(ePoster)
                            self['eposter'].show()
                    else:
                        if pythonVer == 3:
                            eposterurl = eposterurl.encode()
                        getPage(eposterurl).addCallback(self.getEPoster, eposter).addErrback(self.downloadError)
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
        if self.xd is False:
            ePoster = loadPic(eposter, 500, 375, 3, 0, 0, 0)
        else:
            ePoster = loadPic(eposter, 440, 330, 3, 0, 0, 0)
        if ePoster is not None:
            self['plotfull'].hide()
            self['eposter'].instance.setPixmap(ePoster)
            self['eposter'].show()
        return

    def getBanner(self, output, banner):
        f = open(banner, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            Banner = loadPic(banner, 500, 92, 3, 0, 0, 0)
        else:
            Banner = loadPic(banner, 440, 81, 3, 0, 0, 0)
        if Banner is not None:
            self['plotfull'].hide()
            self['banner'].instance.setPixmap(Banner)
            self['banner'].show()
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
                    if self.xd is False:
                        Poster = loadPic(poster, 133, 200, 3, 0, 0, 0)
                    else:
                        Poster = loadPic(poster, 106, 160, 3, 0, 0, 0)
                    if Poster is not None:
                        self['poster' + str(x)].instance.setPixmap(Poster)
                        self['poster' + str(x)].show()
                else:
                    if pythonVer == 3:
                        posterurl = posterurl.encode()

                    getPage(posterurl).addCallback(self.getPoster, x, poster).addErrback(self.downloadError)
            except IndexError:
                self['poster' + str(x)].hide()

        self['poster_back' + str(self.wallindex)].hide()
        return

    def getPoster(self, output, x, poster):
        f = open(poster, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            Poster = loadPic(poster, 133, 200, 3, 0, 0, 0)
        else:
            Poster = loadPic(poster, 106, 160, 3, 0, 0, 0)
        if Poster is not None:
            self['poster' + str(x)].instance.setPixmap(Poster)
            self['poster' + str(x)].show()
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
                if self.xd is False:
                    Poster = loadPic(poster, 160, 230, 3, 0, 0, 0)
                else:
                    Poster = loadPic(poster, 122, 180, 3, 0, 0, 0)
                if Poster is not None:
                    self['frame'].instance.setPixmap(Poster)
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
                        if self.xd is False:
                            Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                        else:
                            Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                        if Backdrop is not None:
                            self['backdrop'].instance.setPixmap(Backdrop)
                            self['backdrop'].show()
                            os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                    else:
                        if pythonVer == 3:
                            backdropurl = backdropurl.encode()
                        getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
                        os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
                elif fileExists(backdrop):
                    if self.xd is False:
                        Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                    else:
                        Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                    if Backdrop is not None:
                        self['backdrop'].instance.setPixmap(Backdrop)
                        self['backdrop'].show()
                else:
                    if pythonVer == 3:
                        backdropurl = backdropurl.encode()
                    getPage(backdropurl).addCallback(self.getBackdrop, backdrop, index).addErrback(self.downloadError)
        except IndexError:
            self['backdrop'].hide()

        return

    def getBackdrop(self, output, backdrop, index):
        f = open(backdrop, 'wb')
        f.write(output)
        f.close()
        if self.xd is False:
            Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
        else:
            Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
        if Backdrop is not None:
            self['backdrop'].instance.setPixmap(Backdrop)
            self['backdrop'].show()
        return

    def showDefaultBackdrop(self):
        backdrop = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.png'
        backdrop_m1v = config.plugins.moviebrowser.cachefolder.value + '/default_backdrop.m1v'
        if config.plugins.moviebrowser.m1v.value == 'yes':
            if fileExists(backdrop_m1v):
                self['backdrop'].hide()
                os.popen("/usr/bin/showiframe '%s'" % backdrop_m1v)
            elif fileExists(backdrop):
                if self.xd is False:
                    Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
                else:
                    Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
                if Backdrop is not None:
                    self['backdrop'].instance.setPixmap(Backdrop)
                    self['backdrop'].show()
                    os.popen('/usr/bin/showiframe /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/no.m1v')
        elif fileExists(backdrop):
            if self.xd is False:
                Backdrop = loadPic(backdrop, 1280, 720, 3, 0, 0, 0)
            else:
                Backdrop = loadPic(backdrop, 1024, 576, 3, 0, 0, 0)
            if Backdrop is not None:
                self['backdrop'].instance.setPixmap(Backdrop)
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
                # if self.language == '&language=de':
                    # self.session.open(MessageBox, 'Serien Ordner: Keine Info m\xc3\xb6glich', MessageBox.TYPE_ERROR)
                # else:
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
                    # if self.language == '&language=de':
                        # self.movies.append(('<Liste der Film Ordner>', config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
                    # else:
                    self.movies.append(('<List of Movie Folder>', config.plugins.moviebrowser.moviefolder.value + '...', 'https://sites.google.com/site/kashmirplugins/home/movie-browser/default_backdrop.png'))
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
            # if self.language == '&language=de':
                # self.session.openWithCallback(self.filter_return, filterList, self.folders, 'Film Ordner Auswahl', filter, len(self.folders), max)
            # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.genres, 'Genre Auswahl', filter, len(self.genres), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.actors, 'Darsteller Auswahl', filter, len(self.actors), max)
                # else:
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

                # if self.language == '&language=de':
                    # self.session.openWithCallback(self.filter_return, filterList, self.directors, 'Regisseur Auswahl', filter, len(self.directors), max)
                # else:
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
                if self.xd is False:
                    listwidth = 500
                else:
                    listwidth = 440
                idx = 0
                for x in self.seasons:
                    idx += 1

                for i in range(idx):
                    try:
                        res = ['']
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

    def youTube(self):
        if self.ready is True:
            try:
                name = self.namelist[self.index]
                name = name + 'FIN'
                name = sub(' - [Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('[Ss][0-9]+[Ee][0-9]+.*?FIN', '', name)
                name = sub('FIN', '', name)
                self.session.open(searchYouTube, name)
            except IndexError:
                pass

    def getIndex(self, list):
        return list.getSelectedIndex()

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()

        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def config(self):
        if self.ready is True:
            config.usage.on_movie_stop.value = self.movie_stop
            config.usage.on_movie_eof.value = self.movie_eof
            self.topseries = False
            self.session.openWithCallback(self.close, movieBrowserConfig)

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
            # count = 4
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.plugins.moviebrowser.transparency.value * count / 40))
                # f.close()

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
            # if self.fhd is True:
                # try:
                    # gMainDC.getInstance().setResolution(1920, 1080)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1920, 1080))
                # except:
                    # import traceback
                    # traceback.print_exc()

            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
        if config.plugins.moviebrowser.language.value == 'de':
            self.language = '&language=de'
        elif config.plugins.moviebrowser.language.value == 'es':
            self.language = '&language=es'
        elif config.plugins.moviebrowser.language.value == 'it':
            self.language = '&language=it'
        elif config.plugins.moviebrowser.language.value == 'fr':
            self.language = '&language=fr'
        elif config.plugins.moviebrowser.language.value == 'ru':
            self.language = '&language=ru'
        else:
            self.language = '&language=en'
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
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
        self.updatelog = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/update.log'
        if self.renew is True:
            self.starttime = ''
            self.namelist.append(name)
            self.movielist.append(movie)
            self.datelist.append(date)
        else:
            self.makeUpdate()

    def makeUpdate(self):
        # if self.language == '&language=de':
            # self.starttime = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
        # else:
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
                url = 'https://api.themoviedb.org/3/search/movie?api_key=dfc629f7ff6936a269f8c5cdb194c890&query=' + movie + self.language
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
                    self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png')

                try:
                    self.posterlist.append('https://image.tmdb.org/t/p/w154' + poster[0])
                except IndexError:
                    self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png')

                url = 'https://api.themoviedb.org/3/movie/%s?api_key=dfc629f7ff6936a269f8c5cdb194c890' % tmdbid + self.language
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
            url = 'https://api.themoviedb.org/3/movie/%s?api_key=dfc629f7ff6936a269f8c5cdb194c890' % tmdbid
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
                    self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png')

                try:
                    self.posterlist.append('https://image.tmdb.org/t/p/w154' + poster[0])
                except IndexError:
                    self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png')

            url = 'https://api.themoviedb.org/3/movie/%s/casts?api_key=dfc629f7ff6936a269f8c5cdb194c890' % tmdbid + self.language
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

            try:
                actors = actor[0]
            except IndexError:
                actors = ' '

            try:
                actors = actors + ', ' + actor2[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor3[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor4[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor5[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor6[0]
            except IndexError:
                pass

            if len(actors) < 95:
                try:
                    actors = actors + ', ' + actor7[0]
                except IndexError:
                    pass

            res.append(actors)
            try:
                genres = genre[0]
            except IndexError:
                genres = ' '

            try:
                genres = genres + ', ' + genre2[0]
            except IndexError:
                pass

            try:
                genres = genres + ', ' + genre3[0]
            except IndexError:
                pass

            try:
                genres = genres + ', ' + genre4[0]
            except IndexError:
                pass

            try:
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
                self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png')
                self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png' + '<episode>' + 'https://sites.google.com/site/kashmirplugins/home/movie-browser/' + 'default_banner.png' + '<episode>')
                self.makeDataEntry(self.dbcount - 1, False)
            else:
                self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png')
                self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png')
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
                url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + seriesid + '/default/' + season + '/' + episode + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
            url = 'https://www.thetvdb.com/api/D19315B88B2DE21F/series/' + seriesid + '/' + config.plugins.moviebrowser.language.value + '.xml'
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
            try:
                actor = re.findall('[|](.*?)[|]', actors[0])
            except IndexError:
                actor = []

            try:
                actor2 = re.findall('[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor2 = []

            try:
                actor3 = re.findall('[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor3 = []

            try:
                actor4 = re.findall('[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor4 = []

            try:
                actor5 = re.findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor5 = []

            try:
                actor6 = re.findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor6 = []

            try:
                actor7 = re.findall('[|].*?[|].*?[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', actors[0])
            except IndexError:
                actor7 = []

            genres = re.findall('<Genre>(.*?)</Genre>', output)
            try:
                genre = re.findall('[|](.*?)[|]', genres[0])
            except IndexError:
                genre = []

            try:
                genre2 = re.findall('[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                genre2 = []

            try:
                genre3 = re.findall('[|].*?[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                genre3 = []

            try:
                genre4 = re.findall('[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                genre4 = []

            try:
                genre5 = re.findall('[|].*?[|].*?[|].*?[|].*?[|](.*?)[|]', genres[0])
            except IndexError:
                genre5 = []

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

            try:
                actors = actor[0]
            except IndexError:
                actors = ' '

            try:
                actors = actors + ', ' + actor2[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor3[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor4[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor5[0]
            except IndexError:
                pass

            try:
                actors = actors + ', ' + actor6[0]
            except IndexError:
                pass

            if len(actors) < 95:
                try:
                    actors = actors + ', ' + actor7[0]
                except IndexError:
                    pass

            res.append(actors)
            try:
                genres = genre[0]
            except IndexError:
                genres = ' '

            try:
                genres = genres + ', ' + genre2[0]
            except IndexError:
                pass

            try:
                genres = genres + ', ' + genre3[0]
            except IndexError:
                pass

            try:
                genres = genres + ', ' + genre4[0]
            except IndexError:
                pass

            try:
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
                self.backdroplist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png')

            try:
                if self.newseries is True:
                    if not eposter:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://sites.google.com/site/kashmirplugins/home/movie-browser/' + 'default_banner.png' + '<episode>')
                    elif eposter[0] == '':
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://sites.google.com/site/kashmirplugins/home/movie-browser/' + 'default_banner.png' + '<episode>')
                    else:
                        self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
                elif not eposter:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0])
                else:
                    self.posterlist.append('https://www.thetvdb.com/banners/_cache/' + poster[0] + '<episode>' + 'https://www.thetvdb.com/banners/' + eposter[0] + '<episode>')
            except IndexError:
                if self.newseries is True:
                    self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png' + '<episode>' + 'https://sites.google.com/site/kashmirplugins/home/movie-browser/' + 'default_banner.png' + '<episode>')
                else:
                    self.posterlist.append('https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png')

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
                    url = 'https://api.themoviedb.org/3/search/movie?api_key=dfc629f7ff6936a269f8c5cdb194c890&query=' + movie + self.language
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
        # if self.language == '&language=de':
            # endtime = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
            # result = 'Startzeit: %s\nEndzeit: %s\nGescannte Dateien insgesamt: %s\nTheTVDb Datenbank Anfragen: %s\nTMDb Datenbank Anfragen: %s\nVerwaiste Filme/Serien: %s\nNeue Serien: %s\nNeue Filme: %s\n\n' % (self.starttime, endtime, self.fileCount, self.tvdbCount, self.tmdbCount, orphaned, seriescount, moviecount)
        # else:
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
            # if self.language == '&language=de':
                # self.session.open(MessageBox, '\nDatenbank Fehler: Eintrag ohne Laufzeit', MessageBox.TYPE_ERROR)
            # else:
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
    skin = """
    <screen position="center,center" size="730,545" title=" ">
        <ePixmap position="0,0" size="730,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logoList.png" zPosition="1"/>
        <ePixmap position="10,5" size="18,18" pixmap="skin_default/buttons/red.png" alphatest="blend" zPosition="2"/>
        <ePixmap position="10,27" size="18,18" pixmap="skin_default/buttons/green.png" alphatest="blend" zPosition="2"/>
        <ePixmap position="702,27" size="18,18" pixmap="skin_default/buttons/yellow.png" alphatest="blend" zPosition="2"/>
        <widget name="label" position="34,5" size="120,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2"/>
        <widget name="label2" position="34,27" size="120,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2"/>
        <widget name="label3" position="576,27" size="120,20" font="{font};16" foregroundColor="#000000" backgroundColor="#FFFFFF" halign="right" transparent="1" zPosition="2"/>
        <widget name="list" position="10,60" size="710,475" scrollbarMode="showOnDemand" zPosition="1"/>
        <widget name="log" position="10,60" size="710,475" font="{font};20" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, list, index, content):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(movieControlList.skin, self.dict)
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
                if self.content != ':::Series:::':
                    res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i][0]))
                else:
                    series = sub('[Ss][0]+[Ee]', 'Special ', self.list[i][0])
                    res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=series))
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
        # if self.lang == 'de':
            # free = 'freier Speicher'
            # folder = 'Film Ordner'
            # movies = 'Filme'
            # series = 'Serien'
        # else:
        free = 'free Space'
        folder = 'Movie Folder'
        movies = 'Movies'
        series = 'Series'
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
            if pythonVer == 2:
                freeSize = movieFolder[statvfs.F_BSIZE] * movieFolder[statvfs.F_BFREE] / 1024 / 1024 / 1024
            else:
                freeSize = movieFolder.f_bsize * movieFolder.f_bfree / 1024 / 1024 / 1024

            if self.content == ':::Movie:Top:::':
                title = '%s %s (%s GB %s)' % (str(totalMovies), movies, str(freeSize), free)
            elif self.content == ':::Series:::' or self.content == ':::Series:Top:::':
                title = '%s %s (%s GB %s)' % (str(totalMovies), series, str(freeSize), free)
            else:
                title = '%s %s & %s (%s GB %s)' % (str(totalMovies), movies, series, str(freeSize), free)
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
            # if self.lang == 'de':
                # loglist = [
                    # ('Film Datei Informationen', 'info'),
                    # ('Film Datei l\xc3\xb6schen', 'delete'),
                    # ('Film Datei blacklisten', 'blacklist'),
                    # ('Datenbank Update Log', 'update'),
                    # ('Datenbank Timer Log', 'timer'),
                    # ('Cleanup Cache Ordner Log', 'cleanup')
                # ]
            # else:
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
                    size = size / 1024.0

                size = round(size, 2)
                size = str(size) + ' ' + suffixes[suffixIndex]
                date = os.path.getmtime(moviefile)
                date = str(datetime.datetime.fromtimestamp(date))
                service = eServiceReference('1:0:0:0:0:0:0:0:0:0:' + moviefile)
                from enigma import eServiceCenter
                info = eServiceCenter.getInstance().info(service)
                name = info.getName(service)
                event = info.getEvent(service)
                duration = '%d min' % (event.getDuration() / 60)
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
                    size = size / 1024.0

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
            data = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/update.log').read()
            self['log'].setText(data)
        elif choice == 'timer':
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log').read()
            self['log'].setText(data)
        else:
            self.log = True
            self['log'].show()
            self['list'].hide()
            data = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/cleanup.log').read()
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
                # elif self.lang == 'de':
                    # self.session.open(MessageBox, '\nDas CutListEditor Plugin unterst\xc3\xbctzt nur Aufnahmen mit der Box.', MessageBox.TYPE_ERROR)
                # else:
                self.session.open(MessageBox, _('\nThe CutListEditor plugin supports only records with the box.'), MessageBox.TYPE_ERROR)
            # elif self.lang == 'de':
                # self.session.openWithCallback(self.CutListInstall, MessageBox, '\nDas CutListEditor Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden installiert werden?', MessageBox.TYPE_YESNO)
            # else:
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
                # elif self.lang == 'de':
                    # self.session.open(MessageBox, '\nDas MovieCut Plugin unterst\xc3\xbctzt nur Aufnahmen mit der Box.', MessageBox.TYPE_ERROR)
                else:
                    self.session.open(MessageBox, _('\nThe MovieCut plugin supports only records with the box.'), MessageBox.TYPE_ERROR)
            # elif self.lang == 'de':
                # self.session.openWithCallback(self.MovieCutInstall, MessageBox, '\nDas MovieCut Plugin ist nicht installiert.\n\nDas Plugin kann automatisch installiert werden, wenn es auf dem Feed ihres Images vorhanden ist.\n\nSoll das Plugin jetzt auf dem Feed gesucht und wenn vorhanden installiert werden?', MessageBox.TYPE_YESNO)
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
            # if self.lang == 'de':
                # self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas CutListEditor Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
            # else:
            self.session.openWithCallback(self.restartGUI, MessageBox, _('\nThe CutListEditor plugin was installed.\nPlease restart Enigma.'), MessageBox.TYPE_YESNO)
        # elif self.lang == 'de':
            # self.session.open(MessageBox, '\nDas CutListEditor Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das CutListEditor Plugin manuell.', MessageBox.TYPE_ERROR)
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
            # if self.lang == 'de':
                # self.session.openWithCallback(self.restartGUI, MessageBox, '\nDas MovieCut Plugin wurde installiert.\nBitte starten Sie Enigma neu.', MessageBox.TYPE_YESNO)
            # else:
            self.session.openWithCallback(self.restartGUI, MessageBox, _('\nThe MovieCut plugin was installed.\nPlease restart Enigma.'), MessageBox.TYPE_YESNO)
        # elif self.lang == 'de':
            # self.session.open(MessageBox, '\nDas MovieCut Plugin ist nicht auf dem Feed ihres Images vorhanden.\n\nBitte installieren Sie das CutListEditor Plugin manuell.', MessageBox.TYPE_ERROR)
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
            # if self.lang == 'de':
                # if movie == config.plugins.moviebrowser.moviefolder.value + '...':
                    # self.session.open(MessageBox, '\nDie Liste der Film Ordner kann nicht gel\xc3\xb6scht werden.', MessageBox.TYPE_ERROR)
                # elif name == movie:
                    # self.session.openWithCallback(self.delete_return, MessageBox, '\nAlle %s Eintr\xc3\xa4ge werden aus der Datenbank, aber nicht aus dem Film Ordner gel\xc3\xb6scht.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
                # else:
                    # self.session.openWithCallback(self.delete_return, MessageBox, '\n%s wird aus der Datenbank und aus dem Film Ordner gel\xc3\xb6scht!\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
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
                database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
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
            # movie = self.list[index][1]
            # if self.lang == 'de':
                # self.session.openWithCallback(self.blacklist_return, MessageBox, '\n%s wird aus der Datenbank gel\xc3\xb6scht und in die Blacklist aufgenommen, so dass der Film bei zuk\xc3\xbcnftigen Datenbank Aktualisierungen ignoriert wird.\n\nWollen Sie fortfahren?' % name, MessageBox.TYPE_YESNO)
            # else:
            self.session.openWithCallback(self.blacklist_return, MessageBox, _('\nThis will delete %s from the Database and put it on the Blacklist, so the Movie will be ignored by future Database Updates.\n\nDo you want to continue?') % name, MessageBox.TYPE_YESNO)
        except IndexError:
            pass

    def blacklist_return(self, answer):
        if answer is True:
            self.ready = False
            try:
                database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
                blacklist = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/blacklist'
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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
    skin = """
     <screen position="center,center" size="730,325" title=" ">
        <ePixmap position="0,0" size="730,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logo.png" zPosition="1"/>
        <widget name="list" position="10,38" size="710,275" scrollbarMode="showOnDemand" zPosition="1"/>
        <widget name="list2" position="10,38" size="710,275" scrollbarMode="showOnDemand" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, movie):
        Screen.__init__(self, session)
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
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
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
                try:
                    name = movieline[0]
                    name = sub('[Ss][0]+[Ee]', 'Special ', name)
                except IndexError:
                    name = ' '

                try:
                    movie = movieline[1]
                    if movie == self.movie:
                        index = count
                except IndexError:
                    movie = ' '

                try:
                    date = movieline[2]
                except IndexError:
                    date = ' '

                try:
                    runtime = movieline[3]
                except IndexError:
                    runtime = ' '

                try:
                    rating = movieline[4]
                except IndexError:
                    rating = ' '

                try:
                    director = movieline[5]
                except IndexError:
                    director = ' '

                try:
                    actors = movieline[6]
                except IndexError:
                    actors = ' '

                try:
                    genres = movieline[7]
                except IndexError:
                    genres = ' '

                try:
                    year = movieline[8]
                except IndexError:
                    year = ' '

                try:
                    country = movieline[9]
                except IndexError:
                    country = ' '

                try:
                    poster = movieline[11]
                except IndexError:
                    poster = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_poster.png'

                try:
                    backdrop = movieline[12]
                except IndexError:
                    backdrop = 'https://sites.google.com/site/kashmirplugins/home/movie-browser' + '/default_backdrop.png'

                try:
                    media = movieline[15]
                except IndexError:
                    media = '\n'

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
                res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=name))
                self.listentries.append(res)

            self['list'].l.setList(self.listentries)
            self['list'].moveToIndex(index)
            self.selectList()
            self.ready = True
            totalMovies = len(self.list)
            # if self.lang == 'de':
                # database = 'Datenbank'
                # free = 'freier Speicher'
                # folder = 'Film Ordner'
                # movies = 'Filme'
            # else:
            database = _('Database')
            free = _('free Space')
            folder = _('Movie Folder')
            movies = _('Movies')
            if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
                movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
                if pythonVer == 2:
                    freeSize = movieFolder[statvfs.F_BSIZE] * movieFolder[statvfs.F_BFREE] / 1024 / 1024 / 1024
                else:
                    freeSize = movieFolder.f_bsize * movieFolder.f_bfree / 1024 / 1024 / 1024
                title = '%s Editor: %s %s (%s GB %s)' % (database, str(totalMovies), movies, str(freeSize), free)
                self.setTitle(title)
            else:
                title = '%s Editor: %s %s (%s offline)' % (database, str(totalMovies), movies, folder)
                self.setTitle(title)

    def makeList2(self):
        # if self.lang == 'de':
            # self.list2 = []
            # self.list2.append('Film: ' + self.namelist[self.index])
            # self.list2.append('Rating: ' + self.ratinglist[self.index])
            # self.list2.append('Regisseur: ' + self.directorlist[self.index])
            # self.list2.append('Land: ' + self.countrylist[self.index])
            # self.list2.append('Darsteller: ' + self.actorslist[self.index])
            # self.list2.append('Jahr: ' + self.yearlist[self.index])
            # self.list2.append('Laufzeit: ' + self.runtimelist[self.index])
            # self.list2.append('Genres: ' + self.genreslist[self.index])
            # if self.medialist[self.index] != '\n':
                # self.list2.append('MediaInfo: ' + self.medialist[self.index])
                # self.mediainfo = True
            # else:
                # self.mediainfo = False
            # self.list2.append('Poster: ' + self.posterlist[self.index])
            # self.list2.append('Backdrop: ' + self.backdroplist[self.index])
        # else:
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
                res.append(MultiContentEntryText(pos=(0, 0), size=(710, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list2[i]))
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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # self.hideflag = True
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
        if self.actlist == 'list':
            if self.change is True:
                self.close(True)
            else:
                self.close(False)
        elif self.actlist == 'list2':
            self.selectList()


class moviesList(Screen):
    skin = """
    <screen position="center,center" size="730,538" title=" ">
        <ePixmap position="0,0" size="730,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logo.png" zPosition="1"/>
        <widget name="poster1" position="10,33" size="80,120" alphatest="blend" zPosition="1"/>
        <widget name="poster2" position="10,158" size="80,120" alphatest="blend" zPosition="1"/>
        <widget name="poster3" position="10,283" size="80,120" alphatest="blend" zPosition="1"/>
        <widget name="poster4" position="10,408" size="80,120" alphatest="blend" zPosition="1"/>
        <widget name="list" position="100,33" size="620,500" scrollbarMode="showNever" zPosition="1"/>
        <widget name="banner1" position="10,33" size="710,120" alphatest="blend" zPosition="1"/>
        <widget name="banner2" position="10,158" size="710,120" alphatest="blend" zPosition="1"/>
        <widget name="banner3" position="10,283" size="710,120" alphatest="blend" zPosition="1"/>
        <widget name="banner4" position="10,408" size="710,120" alphatest="blend" zPosition="1"/>
        <widget name="piclist" position="10,33" size="710,500" scrollbarMode="showNever" transparent="1" zPosition="0"/>
    </screen>
    """

    def __init__(self, session, titel, rating, year, titles, poster, id, country, movie, top):
        Screen.__init__(self, session)
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
            res.append(MultiContentEntryText(pos=(0, 0), size=(620, 125), font=24, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
            try:
                res.append(MultiContentEntryText(pos=(5, 13), size=(610, 30), font=24, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.titles[x]))
            except IndexError:
                pass

            try:
                res.append(MultiContentEntryText(pos=(5, 48), size=(50, 25), font=20, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.year[x]))
            except IndexError:
                pass

            try:
                res.append(MultiContentEntryText(pos=(55, 48), size=(560, 25), font=20, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.country[x]))
            except IndexError:
                pass

            try:
                rating = int(10 * round(float(self.rating[x]), 1)) * 2 + int(10 * round(float(self.rating[x]), 1)) // 10
            except (IndexError, ValueError):
                rating = 0

            png = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings_back.png'
            if fileExists(png):
                res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(210, 21), png=loadPNG(png)))
            png2 = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/ratings.png'
            if fileExists(png2):
                res.append(MultiContentEntryPixmapAlphaTest(pos=(5, 84), size=(rating, 21), png=loadPNG(png2)))
            try:
                res.append(MultiContentEntryText(pos=(225, 84), size=(50, 25), font=20, backcolor_sel=16777215, color_sel=0, color=16777215, flags=RT_HALIGN_LEFT, text=self.rating[x]))
            except IndexError:
                pass

            self.movielist.append(res)

        self['list'].l.setList(self.movielist)
        self['list'].l.setItemHeight(125)
        self.ready = True

    def ok(self):
        if self.ready is True:
            if self.first is True:
                if self.movie is True:
                    # if self.language == 'de':
                        # choicelist = [('Update Film', 'movie'), ('Update Poster', 'poster'), ('Update Backdrop', 'backdrop')]
                        # self.session.openWithCallback(self.updateMovie, ChoiceBox, title='Update Film', list=choicelist)
                    # else:
                    choicelist = [('Update Movie', _('movie')), ('Update Poster', _('poster')), ('Update Backdrop', _('backdrop'))]
                    self.session.openWithCallback(self.updateMovie, ChoiceBox, title='Update Movie', list=choicelist)
                # elif self.language == 'de':
                    # if self.top is True:
                        # choicelist = [('Update Banner', 'banner'), ('Update Backdrop', 'backdrop')]
                        # self.session.openWithCallback(self.updateSeries, ChoiceBox, title='Update Serie', list=choicelist)
                    # else:
                        # choicelist = [('Update Serie', 'series')]
                        # self.session.openWithCallback(self.updateSeries, ChoiceBox, title='Update Serie', list=choicelist)
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
            url = 'https://api.themoviedb.org/3/movie/' + current + '/images?api_key=dfc629f7ff6936a269f8c5cdb194c890'
            self.getTMDbPosters(url)
        elif self.choice == 'backdrop':
            url = 'https://api.themoviedb.org/3/movie/' + current + '/images?api_key=dfc629f7ff6936a269f8c5cdb194c890'
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
            # if self.language == 'de':
                # self.session.open(MessageBox, '\nDer TMDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
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
            # if self.language == 'de':
                # self.session.open(MessageBox, '\nDer TMDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
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
            url = 'https://thetvdb.com/api/D19315B88B2DE21F/series/' + current + '/banners.xml'
            self.getTVDbBanners(url)
        elif self.choice == 'backdrop':
            url = 'https://thetvdb.com/api/D19315B88B2DE21F/series/' + current + '/banners.xml'
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
            # if self.language == 'de':
                # self.session.open(MessageBox, '\nDer TheTVDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
            self.session.open(MessageBox, _('\nThe TVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
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
            # if self.language == 'de':
                # self.session.open(MessageBox, '\nDer TheTVDb API Server ist nicht erreichbar.', MessageBox.TYPE_ERROR)
            # else:
            self.session.open(MessageBox, _('\nThe TVDb API Server is not reachable.'), MessageBox.TYPE_ERROR)
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
            res.append(MultiContentEntryText(pos=(0, 0), size=(710, 125), font=24, backcolor_sel=16777215, flags=RT_HALIGN_LEFT, text=''))
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
        currPic = loadPic(poster1, 80, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster1'].instance.setPixmap(currPic)
        return

    def getPoster2(self, output):
        f = open(self.poster2, 'wb')
        f.write(output)
        f.close()
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        currPic = loadPic(poster2, 80, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster2'].instance.setPixmap(currPic)
        return

    def getPoster3(self, output):
        f = open(self.poster3, 'wb')
        f.write(output)
        f.close()
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        currPic = loadPic(poster3, 80, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster3'].instance.setPixmap(currPic)
        return

    def getPoster4(self, output):
        f = open(self.poster4, 'wb')
        f.write(output)
        f.close()
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        currPic = loadPic(poster4, 80, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster4'].instance.setPixmap(currPic)
        return

    def getBanner1(self, output):
        f = open(self.banner1, 'wb')
        f.write(output)
        f.close()
        self.showBanner1(self.banner1)

    def showBanner1(self, banner1):
        currPic = loadPic(banner1, 710, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['banner1'].instance.setPixmap(currPic)
        return

    def getBanner2(self, output):
        f = open(self.banner2, 'wb')
        f.write(output)
        f.close()
        self.showBanner2(self.banner2)

    def showBanner2(self, banner2):
        currPic = loadPic(banner2, 710, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['banner2'].instance.setPixmap(currPic)
        return

    def getBanner3(self, output):
        f = open(self.banner3, 'wb')
        f.write(output)
        f.close()
        self.showBanner3(self.banner3)

    def showBanner3(self, banner3):
        currPic = loadPic(banner3, 710, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['banner3'].instance.setPixmap(currPic)
        return

    def getBanner4(self, output):
        f = open(self.banner4, 'wb')
        f.write(output)
        f.close()
        self.showBanner4(self.banner4)

    def showBanner4(self, banner4):
        currPic = loadPic(banner4, 710, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['banner4'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def zap(self):
        servicelist = self.session.instantiateDialog(ChannelSelection)
        self.session.execDialog(servicelist)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
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
    skin = """
    <screen position="center,center" size="{screenwidth},{screenheight}" title=" ">
        <ePixmap position="0,0" size="{screenwidth},28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/{png}.png" zPosition="1"/>
        <widget name="list" position="10,38" size="{listwidth},{listheight}" scrollbarMode="showOnDemand" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, list, titel, filter, len, max):
        if int(len) < 20:
            listheight = int(len) * 25
            screenheight = listheight + 48
            screenheight = str(screenheight)
            listheight = str(listheight)
        else:
            screenheight = '523'
            listheight = '475'
        if int(max) > 50:
            screenwidth = '720'
            listwidth = '700'
            self.listwidth = 700
            png = 'logoFilter4'
        elif int(max) > 35:
            screenwidth = '520'
            listwidth = '500'
            self.listwidth = 500
            png = 'logoFilter3'
        elif int(max) > 25:
            screenwidth = '370'
            listwidth = '350'
            self.listwidth = 350
            png = 'logoFilter2'
        else:
            screenwidth = '270'
            listwidth = '250'
            self.listwidth = 250
            png = 'logoFilter'

        self.dict = {
            'screenwidth': screenwidth,
            'screenheight': screenheight,
            'listwidth': listwidth,
            'listheight': listheight,
            'png': png
        }

        self.skin = applySkinVars(filterList.skin, self.dict)
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
                res.append(MultiContentEntryText(pos=(0, 0), size=(self.listwidth, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
        self.close(None)
        return


class filterSeasonList(Screen):
    skin = """
    <screen position="center,center" size="530,523" title=" ">
        <ePixmap position="0,0" size="530,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logoConfig.png" zPosition="1"/>
        <widget name="list" position="10,38" size="510,475" scrollbarMode="showOnDemand" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, list, content):
        Screen.__init__(self, session)
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
                res.append(MultiContentEntryText(pos=(0, 0), size=(510, 25), font=20, color=16777215, backcolor_sel=16777215, color_sel=0, flags=RT_HALIGN_CENTER | RT_VALIGN_CENTER, text=self.list[i]))
                self.listentries.append(res)
            except IndexError:
                pass

        self['list'].l.setList(self.listentries)
        totalSeasons = len(self.list)
        # if config.plugins.moviebrowser.language.value == 'de':
            # series = 'Serien Episoden'
            # free = 'freier Speicher'
            # folder = 'Film Ordner'
        # else:
        series = _('Series Episodes')
        free = _('free Space')
        folder = _('Movie Folder')
        if os.path.exists(config.plugins.moviebrowser.moviefolder.value):
            movieFolder = os.statvfs(config.plugins.moviebrowser.moviefolder.value)
            if pythonVer == 2:
                freeSize = movieFolder[statvfs.F_BSIZE] * movieFolder[statvfs.F_BFREE] / 1024 / 1024 / 1024
            else:
                freeSize = movieFolder.f_bsize * movieFolder.f_bfree / 1024 / 1024 / 1024

            title = '%s %s (%s GB %s)' % (str(totalSeasons), series, str(freeSize), free)
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
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
        self.close(None)
        return


class getABC(Screen):
    skin = """
    <screen position="center,center" size="190,60" backgroundColor="#000000" flags="wfNoBorder" title=" ">
        <widget name="ABC" position="0,0" size="190,60" font="{font};34" halign="center" valign="center" transparent="1" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, ABC, XYZ):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(getABC.skin, self.dict)
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
    skin = """
    <screen position="center,center" size="300,300" flags="wfNoBorder" title=" ">
        <widget name="label_1" position="0,0" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_2" position="0,100" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_3" position="0,200" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_1" position="0,0" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_2" position="0,100" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_3" position="0,200" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="select_1" position="0,0" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
        <widget name="select_2" position="0,100" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
        <widget name="select_3" position="0,200" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
    </screen>
    """

    def __init__(self, session, number, mode):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(switchScreen.skin, self.dict)
        Screen.__init__(self, session)
        self['select_1'] = Pixmap()
        self['select_2'] = Pixmap()
        self['select_3'] = Pixmap()
        self['select_1'].hide()
        self['select_2'].hide()
        self['select_3'].hide()
        if mode == 'content':
            # if config.plugins.moviebrowser.language.value == 'de':
                # self['label_1'] = Label('FILME')
                # self['label_2'] = Label('SERIEN')
                # self['label_3'] = Label('FILME & SERIEN')
                # self['label_select_1'] = Label('FILME')
                # self['label_select_2'] = Label('SERIEN')
                # self['label_select_3'] = Label('FILME & SERIEN')
            # else:
            self['label_1'] = Label(_('MOVIES'))
            self['label_2'] = Label(_('SERIES'))
            self['label_3'] = Label(_('MOVIES & SERIES'))
            self['label_select_1'] = Label(_('MOVIES'))
            self['label_select_2'] = Label(_('SERIES'))
            self['label_select_3'] = Label(_('MOVIES & SERIES'))
            self['label_select_1'].hide()
            self['label_select_2'].hide()
            self['label_select_3'].hide()
        else:
            self['label_1'] = Label(_('METRIX'))
            self['label_2'] = Label(_('BACKDROP'))
            self['label_3'] = Label(_('POSTERWALL'))
            self['label_select_1'] = Label(_('METRIX'))
            self['label_select_2'] = Label(_('BACKDROP'))
            self['label_select_3'] = Label(_('POSTERWALL'))
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
    skin = """
    <screen position="center,center" size="300,300" flags="wfNoBorder" title=" ">
        <widget name="label_1" position="0,0" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_2" position="0,100" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_3" position="0,200" size="300,100" font="{font};32" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_1" position="0,0" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_2" position="0,100" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="label_select_3" position="0,200" size="300,100" font="{font};32" backgroundColor="#D9D9D9" foregroundColor="#000000" halign="center" valign="center" transparent="1" zPosition="1"/>
        <widget name="select_1" position="0,0" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
        <widget name="select_2" position="0,100" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
        <widget name="select_3" position="0,200" size="300,100" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/browser/menu_select.png" transparent="1" alphatest="blend" zPosition="-1"/>
    </screen>
    """

    def __init__(self, session, number):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(switchStart.skin, self.dict)
        Screen.__init__(self, session)
        self.fhd = False
        if config.plugins.moviebrowser.fhd.value == 'yes':
            if getDesktop(0).size().width() == 1920:
                self.fhd = True
                # try:
                    # gMainDC.getInstance().setResolution(1280, 720)
                    # desktop = getDesktop(0)
                    # desktop.resize(eSize(1280, 720))
                # except:
                    # import traceback
                    # traceback.print_exc()

        self['select_1'] = Pixmap()
        self['select_2'] = Pixmap()
        self['select_3'] = Pixmap()
        self['select_1'].hide()
        self['select_2'].hide()
        self['select_3'].hide()
        # if config.plugins.moviebrowser.language.value == 'de':
            # self['label_1'] = Label('FILME')
            # self['label_2'] = Label('SERIEN')
            # self['label_3'] = Label('FILME & SERIEN')
            # self['label_select_1'] = Label('FILME')
            # self['label_select_2'] = Label('SERIEN')
            # self['label_select_3'] = Label('FILME & SERIEN')
        # else:
        self['label_1'] = Label(_('MOVIES'))
        self['label_2'] = Label(_('SERIES'))
        self['label_3'] = Label(_('MOVIES & SERIES'))
        self['label_select_1'] = Label(_('MOVIES'))
        self['label_select_2'] = Label(_('SERIES'))
        self['label_select_3'] = Label(_('MOVIES & SERIES'))
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
        # if self.fhd is True:
            # try:
                # gMainDC.getInstance().setResolution(1920, 1080)
                # desktop = getDesktop(0)
                # desktop.resize(eSize(1920, 1080))
            # except:
                # import traceback
                # traceback.print_exc()

        self.close()


class searchYouTube(Screen):
    skin = """
    <screen position="center,center" size="1000,560" title=" ">
        <ePixmap position="0,0" size="1000,50" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/youtube.png" zPosition="1"/>
        <ePixmap position="10,6" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/buttons/blue.png" alphatest="blend" zPosition="2"/>
        <ePixmap position="10,26" size="18,18" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/buttons/yellow.png" alphatest="blend" zPosition="2"/>
        <widget name="label" position="34,6" size="200,20" font="Regular;16" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2"/>
        <widget name="label2" position="34,26" size="200,20" font="Regular;16" foregroundColor="#697178" backgroundColor="#FFFFFF" halign="left" transparent="1" zPosition="2"/>
        <widget render="Label" source="global.CurrentTime" position="740,0" size="240,50" font="{font};24" foregroundColor="#697279" backgroundColor="#FFFFFF" halign="right" valign="center" zPosition="2">
            <convert type="ClockToText">Format:%H:%M:%S</convert>
        </widget>
        <widget name="poster1" position="10,55" size="215,120" alphatest="blend" zPosition="1"/>
        <widget name="poster2" position="10,180" size="215,120" alphatest="blend" zPosition="1"/>
        <widget name="poster3" position="10,305" size="215,120" alphatest="blend" zPosition="1"/>
        <widget name="poster4" position="10,430" size="215,120" alphatest="blend" zPosition="1"/>
        <widget name="list" position="235,55" size="755,500" scrollbarMode="showOnDemand" zPosition="1"/>
    </screen>
    """

    def __init__(self, session, name):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(searchYouTube.skin, self.dict)
        Screen.__init__(self, session)
        self.name = name + ' Trailer'
        self.link = 'https://www.youtube.com/results?filters=video&search_query=' + self.name.replace(' ', '%20').replace('\xc3\x83\xe2\x80\x9e', 'Ae').replace('\xc3\x83\xe2\x80\x93', 'Oe').replace('\xc3\x83\xc5\x93', 'Ue').replace('\xc3\x83\xc5\xb8', 'ss').replace('\xc3\x83\xc2\xa4', 'ae').replace('\xc3\x83\xc2\xb6', 'oe').replace('\xc3\x83\xc2\xbc', 'ue').replace('\xc3\x84', 'Ae').replace('\xc3\x96', 'Oe').replace('\xc3\x9c', 'Ue').replace('\xc3\xa4', 'ae').replace('\xc3\xb6', 'oe').replace('\xc3\xbc', 'ue')
        # if config.plugins.moviebrowser.language.value == 'de':
            # self.titel = 'YouTube Trailer Suche | Seite '
        # elif config.plugins.moviebrowser.language.value == 'es':
            # self.titel = 'YouTube Trailer Busqueda | Pagina '
        # elif config.plugins.moviebrowser.language.value == 'it':
            # self.titel = 'YouTube Trailer Ricerca | Pagina '
        # elif config.plugins.moviebrowser.language.value == 'fr':
            # self.titel = 'YouTube Trailer Recherche | Page '
        # elif config.plugins.moviebrowser.language.value == 'ru':
            # self.titel = 'YouTube Trailer \xd0\xbf\xd0\xbe\xd0\xb8\xd1\x81\xd0\xba | \xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x86\xd0\xb0 '
        # else:
        self.titel = _('YouTube Trailer Search | Page ')
        self.poster = []
        self.trailer_id = []
        self.trailer_list = []
        self.localhtml = '/tmp/youtube.html'
        self.poster1 = '/tmp/youtube1.jpg'
        self.poster2 = '/tmp/youtube2.jpg'
        self.poster3 = '/tmp/youtube3.jpg'
        self.poster4 = '/tmp/youtube4.jpg'
        self['poster1'] = Pixmap()
        self['poster2'] = Pixmap()
        self['poster3'] = Pixmap()
        self['poster4'] = Pixmap()
        self.ready = False
        self.hideflag = True
        self.count = 1
        self['list'] = ItemList([])
        self['label'] = Label(_('= Hide'))
        self['label2'] = Label(_('= YouTube Search'))
        self['actions'] = ActionMap([
            'OkCancelActions',
            'DirectionActions',
            'ColorActions',
            'ChannelSelectBaseActions',
            'HelpActions',
            'NumberActions',
            'MovieSelectionActions'
        ], {
            'ok': self.ok,
            'cancel': self.exit,
            'right': self.rightDown,
            'left': self.leftUp,
            'down': self.down,
            'up': self.up,
            'nextBouquet': self.nextPage,
            'prevBouquet': self.prevPage,
            'yellow': self.search,
            'blue': self.hideScreen,
            '0': self.gotoEnd,
            '1': self.gotoFirst,
            'showEventInfo': self.showHelp,
        }, -1)
        if config.plugins.moviebrowser.metrixcolor.value == '0x00000000':
            self.backcolor = False
        else:
            self.backcolor = True
            self.back_color = int(config.plugins.moviebrowser.metrixcolor.value, 16)
        self.makeTrailerTimer = eTimer()
        self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))
        self.makeTrailerTimer.start(500, True)

    def makeTrailerList(self, string):
        self.setTitle(self.titel + str(self.count))
        output = open(self.localhtml, 'r').read()
        startpos = output.find('class="section-list">')
        endpos = output.find('\n</ol>\n\n')
        bereich = output[startpos:endpos]
        bereich = sub('</a>', '', bereich)
        bereich = sub('<b>', '', bereich)
        bereich = sub('</b>', '', bereich)
        bereich = sub('<wbr>', '', bereich)
        bereich = sub('</li><li>', ' \xc2\xb7 ', bereich)
        bereich = sub('&quot;', "'", bereich)
        bereich = transHTML(bereich)
        self.poster = re.findall('i.ytimg.com/(.*?)default.jpg', bereich)
        self.trailer_id = re.findall('<h3 class="yt-lockup-title.*?"><a href="/watch.v=(.*?)"', bereich)
        self.trailer_titel = re.findall('<h3 class="yt-lockup-title.*?"><a href=".*?">(.*?)<', bereich)
        trailer_time = re.findall('<span class="accessible-description" id="description-id.*?: (.*?)</span>', bereich)
        trailer_info = re.findall('<ul class="yt-lockup-meta-info">(.*?)</div>(.*?)</div>', bereich)
        for x in range(len(self.trailer_id)):
            res = ['']
            if self.backcolor is True:
                res.append(MultiContentEntryText(pos=(0, 0), size=(755, 125), font=24, backcolor_sel=self.back_color, text=''))
            try:
                res.append(MultiContentEntryText(pos=(5, 13), size=(730, 30), font=24, color=16777215, flags=RT_HALIGN_LEFT, text=self.trailer_titel[x]))
            except IndexError:
                pass

            try:
                res.append(MultiContentEntryText(pos=(5, 48), size=(75, 25), font=20, color=16777215, flags=RT_HALIGN_RIGHT, text=trailer_time[x] + ' \xc2\xb7 '))
            except IndexError:
                pass

            try:
                info = sub('<.*?>', '', trailer_info[x][0])
                res.append(MultiContentEntryText(pos=(85, 48), size=(650, 25), font=20, color=16777215, flags=RT_HALIGN_LEFT, text=info))
            except IndexError:
                pass

            try:
                desc = sub('<.*?>', '', trailer_info[x][1])
                res.append(MultiContentEntryText(pos=(5, 75), size=(730, 50), font=20, color=16777215, flags=RT_HALIGN_LEFT | RT_WRAP, text=desc))
            except IndexError:
                pass

            self.trailer_list.append(res)

        self['list'].l.setList(self.trailer_list)
        self['list'].l.setItemHeight(125)
        self['list'].moveToIndex(0)
        self.ready = True
        try:
            poster1 = 'https://i.ytimg.com/' + self.poster[0] + 'default.jpg'
            self.download(poster1, self.getPoster1)
            self['poster1'].show()
        except IndexError:
            self['poster1'].hide()

        try:
            poster2 = 'https://i.ytimg.com/' + self.poster[1] + 'default.jpg'
            self.download(poster2, self.getPoster2)
            self['poster2'].show()
        except IndexError:
            self['poster2'].hide()

        try:
            poster3 = 'https://i.ytimg.com/' + self.poster[2] + 'default.jpg'
            self.download(poster3, self.getPoster3)
            self['poster3'].show()
        except IndexError:
            self['poster3'].hide()

        try:
            poster4 = 'https://i.ytimg.com/' + self.poster[3] + 'default.jpg'
            self.download(poster4, self.getPoster4)
            self['poster4'].show()
        except IndexError:
            self['poster4'].hide()

    def ok(self):
        if self.ready is True:
            try:
                c = self['list'].getSelectedIndex()
                trailer_id = self.trailer_id[c]
                trailer_titel = self.trailer_titel[c]
                trailer_url = self.getTrailerURL(trailer_id)
                if trailer_url is not None:
                    sref = eServiceReference(4097, 0, trailer_url)
                    sref.setName(trailer_titel)
                    self.session.open(MoviePlayer, sref)
                else:
                    self.session.open(MessageBox, '\nVideo not available', MessageBox.TYPE_ERROR)
            except IndexError:
                pass

        return

    def getTrailerURL(self, trailer_id):
        header = {
            'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100627 Firefox/3.6.6',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5'
        }

        VIDEO_FMT_PRIORITY_MAP = {
            '38': 3,
            '37': 1,
            '22': 2,
            '35': 5,
            '18': 4,
            '34': 6
        }

        trailer_url = None
        watch_url = 'https://www.youtube.com/watch?v=%s&gl=US&hl=en' % trailer_id
        watchrequest = Request(watch_url, None, header)
        try:
            urlopen(watchrequest).read()
        except Exception:
            return trailer_url

        for el in ['&el=embedded', '&el=detailpage', '&el=vevo', '']:
            info_url = 'https://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (trailer_id, el)
            request = Request(info_url, None, header)
            try:
                if pythonVer == 2:
                    infopage = urlopen(request).read()
                else:
                    infopage = urlopen(request).read().decode('utf-8')

                videoinfo = parse_qs(infopage)
                if ('url_encoded_fmt_stream_map' or 'fmt_url_map') in videoinfo:
                    break
            except Exception:
                return trailer_url

        if ('url_encoded_fmt_stream_map' or 'fmt_url_map') not in videoinfo:
            return trailer_url
        else:
            video_fmt_map = {}
            fmt_infomap = {}
            if 'url_encoded_fmt_stream_map' in videoinfo:
                tmp_fmtUrlDATA = videoinfo['url_encoded_fmt_stream_map'][0].split(',')
            else:
                tmp_fmtUrlDATA = videoinfo['fmt_url_map'][0].split(',')
            for fmtstring in tmp_fmtUrlDATA:
                fmturl = fmtid = ''
                if 'url_encoded_fmt_stream_map' in videoinfo:
                    try:
                        for arg in fmtstring.split('&'):
                            if arg.find('=') >= 0:
                                key, value = arg.split('=')
                                if key == 'itag':
                                    if len(value) > 3:
                                        value = value[:2]
                                    fmtid = value
                                elif key == 'url':
                                    fmturl = value

                        if fmtid != '' and fmturl != '' and "fmtid" in VIDEO_FMT_PRIORITY_MAP:
                            video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid, 'fmturl': unquote_plus(fmturl)}
                            fmt_infomap[int(fmtid)] = '%s' % unquote_plus(fmturl)
                        fmturl = fmtid = ''
                    except:
                        return trailer_url

                else:
                    fmtid, fmturl = fmtstring.split('|')

                if "fmtid" in VIDEO_FMT_PRIORITY_MAP and fmtid != '':
                    video_fmt_map[VIDEO_FMT_PRIORITY_MAP[fmtid]] = {'fmtid': fmtid, 'fmturl': unquote_plus(fmturl)}
                    fmt_infomap[int(fmtid)] = unquote_plus(fmturl)

            if video_fmt_map and len(video_fmt_map):
                best_video = video_fmt_map[sorted(video_fmt_map.iterkeys())[0]]
                trailer_url = '%s' % best_video['fmturl'].split(';')[0]
            return trailer_url

    def search(self):
        if self.ready is True:
            # if config.plugins.moviebrowser.language.value == 'de':
                # self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Suche:', text=self.name)
            # elif config.plugins.moviebrowser.language.value == 'es':
                # self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Busqueda:', text=self.name)
            # elif config.plugins.moviebrowser.language.value == 'it':
                # self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Ricerca:', text=self.name)
            # elif config.plugins.moviebrowser.language.value == 'fr':
                # self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer Recherche:', text=self.name)
            # elif config.plugins.moviebrowser.language.value == 'ru':
                # self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title='YouTube Trailer \xd0\xbf\xd0\xbe\xd0\xb8\xd1\x81\xd0\xba:', text=self.name)
            # else:
                self.session.openWithCallback(self.searchReturn, VirtualKeyBoard, title=_('YouTube Trailer Search:'), text=self.name)

    def searchReturn(self, name):
        if name and name != '':
            self.name = name
            self.link = 'https://www.youtube.com/results?filters=video&search_query=' + self.name.replace(' ', '%20').replace('\xc3\x84', 'Ae').replace('\xc3\x96', 'Oe').replace('\xc3\x9c', 'Ue').replace('\xc3\xa4', 'ae').replace('\xc3\xb6', 'oe').replace('\xc3\xbc', 'ue')
            self.count = 1
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(self.link, self.makeTrailerList))

    def nextPage(self):
        if self.ready is True:
            self.count += 1
            if self.count >= 10:
                self.count = 9
            link = self.link + '&page=' + str(self.count)
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(link, self.makeTrailerList))

    def prevPage(self):
        if self.ready is True:
            self.count -= 1
            if self.count <= 0:
                self.count = 1
            link = self.link + '&page=' + str(self.count)
            self.poster = []
            self.trailer_id = []
            self.trailer_list = []
            self.makeTrailerTimer.callback.append(self.downloadFullPage(link, self.makeTrailerList))

    def down(self):
        if self.ready is True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                pass

            self['list'].down()
            if c + 1 == len(self.trailer_id):
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[0] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[1] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[3] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

            elif c % 4 == 3:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 1] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

    def up(self):
        if self.ready is True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                pass

            self['list'].up()
            if c == 0:
                length = len(self.trailer_list)
                d = length % 4
                if d == 0:
                    d = 4
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[length - d] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[length - d + 1] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[length - d + 2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[length - d + 3] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

            elif c % 4 == 0:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                    self['poster1'].show()
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                    self['poster2'].show()
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                    self['poster3'].show()
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c - 1] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                    self['poster4'].show()
                except IndexError:
                    self['poster4'].hide()

    def rightDown(self):
        if self.ready is True:
            try:
                c = self['list'].getSelectedIndex()
            except IndexError:
                pass

            self['list'].pageDown()
            length = len(self.trailer_list)
            d = c % 4
            e = length % 4
            if e == 0:
                e = 4
            if c + e >= length:
                pass
            elif d == 0:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 6] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 7] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 1:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 6] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 2:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 5] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

            elif d == 3:
                try:
                    poster1 = 'https://i.ytimg.com/' + self.poster[c + 1] + 'default.jpg'
                    self.download(poster1, self.getPoster1)
                except IndexError:
                    self['poster1'].hide()

                try:
                    poster2 = 'https://i.ytimg.com/' + self.poster[c + 2] + 'default.jpg'
                    self.download(poster2, self.getPoster2)
                except IndexError:
                    self['poster2'].hide()

                try:
                    poster3 = 'https://i.ytimg.com/' + self.poster[c + 3] + 'default.jpg'
                    self.download(poster3, self.getPoster3)
                except IndexError:
                    self['poster3'].hide()

                try:
                    poster4 = 'https://i.ytimg.com/' + self.poster[c + 4] + 'default.jpg'
                    self.download(poster4, self.getPoster4)
                except IndexError:
                    self['poster4'].hide()

    def leftUp(self):
        if self.ready is True:
            try:
                c = self['list'].getSelectedIndex()
                self['list'].pageUp()
                d = c % 4
                if c < 4:
                    pass
                elif d == 0:
                    try:
                        poster1 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                        self.download(poster1, self.getPoster1)
                        poster2 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                        self.download(poster2, self.getPoster2)
                        poster3 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                        self.download(poster3, self.getPoster3)
                        poster4 = 'https://i.ytimg.com/' + self.poster[c - 1] + 'default.jpg'
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 1:
                    try:
                        poster1 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                        self.download(poster1, self.getPoster1)
                        poster2 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                        self.download(poster2, self.getPoster2)
                        poster3 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                        self.download(poster3, self.getPoster3)
                        poster4 = 'https://i.ytimg.com/' + self.poster[c - 2] + 'default.jpg'
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 2:
                    try:
                        poster1 = 'https://i.ytimg.com/' + self.poster[c - 6] + 'default.jpg'
                        self.download(poster1, self.getPoster1)
                        poster2 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                        self.download(poster2, self.getPoster2)
                        poster3 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                        self.download(poster3, self.getPoster3)
                        poster4 = 'https://i.ytimg.com/' + self.poster[c - 3] + 'default.jpg'
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                elif d == 3:
                    try:
                        poster1 = 'https://i.ytimg.com/' + self.poster[c - 7] + 'default.jpg'
                        self.download(poster1, self.getPoster1)
                        poster2 = 'https://i.ytimg.com/' + self.poster[c - 6] + 'default.jpg'
                        self.download(poster2, self.getPoster2)
                        poster3 = 'https://i.ytimg.com/' + self.poster[c - 5] + 'default.jpg'
                        self.download(poster3, self.getPoster3)
                        poster4 = 'https://i.ytimg.com/' + self.poster[c - 4] + 'default.jpg'
                        self.download(poster4, self.getPoster4)
                    except IndexError:
                        pass

                self['poster1'].show()
                self['poster2'].show()
                self['poster3'].show()
                self['poster4'].show()
            except IndexError:
                pass

    def gotoEnd(self):
        if self.ready is True:
            end = len(self.trailer_list) - 1
            if end > 4:
                self['list'].moveToIndex(end)
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
        currPic = loadPic(poster1, 215, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster1'].instance.setPixmap(currPic)
        return

    def getPoster2(self, output):
        f = open(self.poster2, 'wb')
        f.write(output)
        f.close()
        self.showPoster2(self.poster2)

    def showPoster2(self, poster2):
        currPic = loadPic(poster2, 215, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster2'].instance.setPixmap(currPic)
        return

    def getPoster3(self, output):
        f = open(self.poster3, 'wb')
        f.write(output)
        f.close()
        self.showPoster3(self.poster3)

    def showPoster3(self, poster3):
        currPic = loadPic(poster3, 215, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster3'].instance.setPixmap(currPic)
        return

    def getPoster4(self, output):
        f = open(self.poster4, 'wb')
        f.write(output)
        f.close()
        self.showPoster4(self.poster4)

    def showPoster4(self, poster4):
        currPic = loadPic(poster4, 215, 120, 3, 0, 0, 0)
        if currPic is not None:
            self['poster4'].instance.setPixmap(currPic)
        return

    def download(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        getPage(link).addCallback(name).addErrback(self.downloadError)

    def downloadError(self, output):
        pass

    def downloadFullPage(self, link, name):
        if pythonVer == 3:
            link = link.encode()
        downloadPage(link, self.localhtml).addCallback(name).addErrback(self.downloadPageError)

    def downloadPageError(self, output):
        try:
            error = output.getErrorMessage()
            self.session.open(MessageBox, _('\nThe YouTube Server is not reachable:\n%s') % error, MessageBox.TYPE_ERROR)
        except AttributeError:
            self.session.open(MessageBox, _('\nThe YouTube Server is not reachable.'), MessageBox.TYPE_ERROR)

        self.close()

    def showHelp(self):
        # if config.plugins.moviebrowser.language.value == 'de':
            # self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Seite\nGelb = Neue YouTube Suche', MessageBox.TYPE_INFO, close_on_any_key=True)
        # elif config.plugins.moviebrowser.language.value == 'es':
            # self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Pagina\nAmarillo = Nueva Busqueda de YouTube', MessageBox.TYPE_INFO, close_on_any_key=True)
        # elif config.plugins.moviebrowser.language.value == 'it':
            # self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Pagina\nGiallo = Nuova YouTube Ricerca', MessageBox.TYPE_INFO, close_on_any_key=True)
        # elif config.plugins.moviebrowser.language.value == 'fr':
            # self.session.open(MessageBox, '\n%s' % 'Bouquet = +- Page\nJaune = Nouvelle YouTube Recherche', MessageBox.TYPE_INFO, close_on_any_key=True)
        # elif config.plugins.moviebrowser.language.value == 'ru':
            # self.session.open(MessageBox, '\n%s' % 'Bouquet = +- \xd1\x81\xd1\x82\xd1\x80\xd0\xb0\xd0\xbd\xd0\xb8\xd1\x86\xd0\xb0\n\xd0\x96\xd0\xb5\xd0\xbb\xd1\x82\xd1\x8b\xd0\xb9 = \xd0\x9d\xd0\xbe\xd0\xb2\xd1\x8b\xd0\xb9 YouTube \xd0\xbf\xd0\xbe\xd0\xb8\xd1\x81\xd0\xba', MessageBox.TYPE_INFO, close_on_any_key=True)
        # else:
        self.session.open(MessageBox, _('\n%s' % 'Bouquet = +- Page\nYellow = New YouTube Search'), MessageBox.TYPE_INFO, close_on_any_key=True)

    def hideScreen(self):
        if self.hideflag is True:
            self.hideflag = False
            # count = 40
            # while count > 0:
                # count -= 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

        else:
            self.hideflag = True
            # count = 0
            # while count < 40:
                # count += 1
                # f = open('/proc/stb/video/alpha', 'w')
                # f.write('%i' % (config.av.osd_alpha.value * count / 40))
                # f.close()

    def exit(self):
        # if self.hideflag is False:
            # f = open('/proc/stb/video/alpha', 'w')
            # f.write('%i' % config.av.osd_alpha.value)
            # f.close()
        if fileExists(self.localhtml):
            os.remove(self.localhtml)
        if fileExists(self.poster1):
            os.remove(self.poster1)
        if fileExists(self.poster2):
            os.remove(self.poster2)
        if fileExists(self.poster3):
            os.remove(self.poster3)
        if fileExists(self.poster4):
            os.remove(self.poster4)
        self.close()


class ItemList(MenuList):
    def __init__(self, items, enableWrapAround=True):
        MenuList.__init__(self, items, enableWrapAround, eListboxPythonMultiContent)
        if config.plugins.moviebrowser.font.value == 'yes':
            self.l.setFont(26, gFont('Sans', 26))
            self.l.setFont(24, gFont('Sans', 24))
            self.l.setFont(22, gFont('Sans', 22))
            self.l.setFont(20, gFont('Sans', 20))
        else:
            self.l.setFont(26, gFont('Regular', 26))
            self.l.setFont(24, gFont('Regular', 24))
            self.l.setFont(22, gFont('Regular', 22))
            self.l.setFont(20, gFont('Regular', 20))


class helpScreen(Screen):
    skin = """
    <screen position="center,center" size="512,512" flags="wfNoBorder" title=" ">
        <ePixmap position="0,0" size="515,512" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/help.png" alphatest="on" transparent="0" zPosition="0"/>
        <ePixmap position="120,50" size="18,18" pixmap="skin_default/buttons/yellow.png" alphatest="blend" zPosition="3"/>
        <ePixmap position="120,71" size="18,18" pixmap="skin_default/buttons/green.png" alphatest="blend" zPosition="3"/>
        <ePixmap position="120,92" size="18,18" pixmap="skin_default/buttons/red.png" alphatest="blend" zPosition="3"/>
        <ePixmap position="120,113" size="18,18" pixmap="skin_default/buttons/blue.png" alphatest="blend" zPosition="3"/>
        <widget name="label" position="120,48" size="415,420" font="{font};18" transparent="1" zPosition="2"/>
    </screen>
    """

    def __init__(self, session):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(helpScreen.skin, self.dict)
        Screen.__init__(self, session)
        # if config.plugins.moviebrowser.language.value == 'de':
            # self.setTitle('Movie Browser Tastenbelegung')
            # self['label'] = Label('     : YouTube Film Trailer\n     : Wikipedia Suche\n     : Wechsel Plugin Ansicht\n     : Plugin aus-/einblenden\nInfo Taste: Infos ein-/ausblenden\nVideo Taste: Update Datenbank\nText Taste: Editiere Datenbank\nStop Taste: Markiere Film als gesehen\nRadio Taste: L\xc3\xb6sche/Blacklist Film\n<- -> Taste: Gehe zu Anfangsbuchstabe\nTaste 1: CutListeditor/MovieCut/LogView\nTaste 2: Erneuere Infos auf TMDb\nTaste 3: Erneuere Infos auf TheTVDb\nTaste 4: Gesehene Filme aus-/einblenden\nTaste 5: Wechsel Filme/Serien Ansicht\nTaste 6: Film Ordner Auswahl\nTaste 7: Film Regisseur Auswahl\nTaste 8: Film Darsteller Auswahl\nTaste 9: Film Genre Auswahl\nTaste 0: Gehe an das Ende der Liste')
        # elif config.plugins.moviebrowser.language.value == 'es':
            # self.setTitle('Movie Browser Asignacion de Teclas')
            # self['label'] = Label('     : YouTube Pelicula Trailer\n     : Wikipedia Buscar\n     : Cambiar Plugin Estilo\n     : Ocultar/mostrar plugin\nInfo Boton: Ocultar/mostrar info\nVideo Boton: Actualizar Database\nText Boton: Editar Database\nStop Boton: Marcar Pelicula se ve\nRadio Boton: Borrar/Blacklist Pelicula\n<- -> Boton: Ir a primera letra\nBoton 1: CutListEditor/MovieCut/LogView\nBoton 2: Renovar infos en TMDb\nBoton 3: Renovar infos en TheTVDb\nBoton 4: Ocultar/mostrar peliculas vistas\nBoton 5: Cambiar Pelicula/Serie vista\nBoton 6: Pelicula Carpeta seleccion\nBoton 7: Pelicula Director seleccion\nBoton 8: Pelicula Actor seleccion\nBoton 9: Pelicula Genre seleccion\nBoton 0: Ir al final de la lista')
        # else:
        self.setTitle(_('Movie Browser Key Assignment'))
        self['label'] = Label(_('     : YouTube Movie Trailer\n     : Wikipedia Search\n     : Toggle Plugin Style\n     : Toggle hide/show plugin\nInfo Button: Toggle show/hide infos\nVideo Button: Update Database\nText Button: Edit Database\nStop Button: Mark movie as seen\nRadio Button: Delete/Blacklist movie\n<- -> Button: Go to first letter\nButton 1: CutListEditor/MovieCut/LogView\nButton 2: Renew infos on TMDb\nButton 3: Renew infos on TheTVDb\nButton 4: Hide/show seen movies\nButton 5: Toggle Movies/Series view\nButton 6: Movie Folder Selection\nButton 7: Movie Director Selection\nButton 8: Movie Actor Selection\nButton 9: Movie Genre Selection\nButton 0: Go to end of list'))

        self['actions'] = ActionMap(['OkCancelActions'], {
            'ok': self.close,
            'cancel': self.close
        }, -1)


class movieBrowserConfig(ConfigListScreen, Screen):
    skin = """
    <screen position="center,center" size="1100,666" backgroundColor="#20000000" title="Movie Browser Setup">
        <ePixmap position="13,2" size="530,25" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logoConfig.png" alphatest="blend" zPosition="1" />
        <eLabel position="9,32" size="1050,3" backgroundColor="green" />
        <!--
        <ePixmap position="9,37" size="512,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/seperator.png" alphatest="off" zPosition="1" />
        -->
        <widget name="config" position="12,38" size="1068,314" itemHeight="45" scrollbarMode="showOnDemand" zPosition="1" />
        <eLabel position="9,359" size="1050,3" backgroundColor="green" />
        <!--
        <ePixmap position="9,344" size="1090,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/seperator.png" alphatest="off" zPosition="1" />
        -->
        <widget name="save" position="597,550" size="125,30" font="Regular; 24" halign="left" transparent="1" zPosition="1" />
        <widget name="cancel" position="838,550" size="125,30" font="Regular; 24" halign="left" transparent="1" zPosition="1" />
        <ePixmap position="560,550" size="30,30" pixmap="skin_default/buttons/green.png" alphatest="blend" zPosition="1" />
        <ePixmap position="810,550" size="30,30" pixmap="skin_default/buttons/red.png" alphatest="blend" zPosition="1" />
        <widget name="plugin" position="4,374" size="512,288" alphatest="blend" zPosition="1" />
    </screen>
    """

    def __init__(self, session):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(movieBrowserConfig.skin, self.dict)
        Screen.__init__(self, session)
        self.sortorder = config.plugins.moviebrowser.sortorder.value
        self.moviefolder = config.plugins.moviebrowser.moviefolder.value
        self.cachefolder = config.plugins.moviebrowser.cachefolder.value
        self.database = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'
        self.m1v = config.plugins.moviebrowser.m1v.value
        self.lang = config.plugins.moviebrowser.language.value
        self.timer_update = config.plugins.moviebrowser.timerupdate.value
        self.timer_hour = config.plugins.moviebrowser.timer.value[0]
        self.timer_min = config.plugins.moviebrowser.timer.value[1]
        # if self.lang == 'de':
            # self['save'] = Label('Speichern')
            # self['cancel'] = Label('Abbrechen')
        # else:
        self['save'] = Label(_('Save'))
        self['cancel'] = Label(_('Cancel'))
        self['plugin'] = Pixmap()
        self.ready = True
        list = []
        # if self.lang == 'de':
            # list.append(getConfigListEntry('Filme Ansicht:', config.plugins.moviebrowser.style))
            # list.append(getConfigListEntry('Serien Ansicht:', config.plugins.moviebrowser.seriesstyle))
            # self.foldername = getConfigListEntry('Film Ordner:', config.plugins.moviebrowser.moviefolder)
            # list.append(self.foldername)
            # list.append(getConfigListEntry('Cache Ordner:', config.plugins.moviebrowser.cachefolder))
            # list.append(getConfigListEntry('Filme oder Serien:', config.plugins.moviebrowser.filter))
            # list.append(getConfigListEntry('Filme oder Serien Auswahl beim Start:', config.plugins.moviebrowser.showswitch))
            # list.append(getConfigListEntry('TMDb/TheTVDb Sprache:', config.plugins.moviebrowser.language))
            # list.append(getConfigListEntry('Film Sortierung:', config.plugins.moviebrowser.sortorder))
            # list.append(getConfigListEntry('Zeige Backdrops:', config.plugins.moviebrowser.backdrops))
            # list.append(getConfigListEntry('Download neue Backdrops:', config.plugins.moviebrowser.download))
            # list.append(getConfigListEntry('Benutze m1v Backdrops:', config.plugins.moviebrowser.m1v))
            # list.append(getConfigListEntry('Zeige TV im Hintergrund (no m1v):', config.plugins.moviebrowser.showtv))
            # list.append(getConfigListEntry('Plugin im Enigma Men\xc3\xbc:', config.plugins.moviebrowser.showmenu))
            # list.append(getConfigListEntry('Plugin Sans Serif Schrift:', config.plugins.moviebrowser.font))
            # list.append(getConfigListEntry('Starte Plugin mit Video Taste:', config.plugins.moviebrowser.videobutton))
            # list.append(getConfigListEntry('Gehe zum letzten Film beim Start:', config.plugins.moviebrowser.lastmovie))
            # list.append(getConfigListEntry('Lade letzte Auswahl/Filter beim Start:', config.plugins.moviebrowser.lastfilter))
            # list.append(getConfigListEntry('Zeige Liste der Film Ordner:', config.plugins.moviebrowser.showfolder))
            # list.append(getConfigListEntry('Plugin Transparenz:', config.plugins.moviebrowser.transparency))
            # list.append(getConfigListEntry('Posterwall/Backdrop Plugin Gr\xc3\xb6\xc3\x9fe:', config.plugins.moviebrowser.plugin_size))
            # list.append(getConfigListEntry('Posterwall/Backdrop Filmbeschreibung:', config.plugins.moviebrowser.plotfull))
            # list.append(getConfigListEntry('Posterwall/Backdrop Farbe \xc3\x9cberschriften:', config.plugins.moviebrowser.color))
            # list.append(getConfigListEntry('Metrix Liste Farbe Auswahl:', config.plugins.moviebrowser.metrixcolor))
            # list.append(getConfigListEntry('Plugin Auto Update Check:', config.plugins.moviebrowser.autocheck))
            # list.append(getConfigListEntry('Aktualisiere Datenbank mit Timer:', config.plugins.moviebrowser.timerupdate))
            # list.append(getConfigListEntry('Timer Datenbank Aktualisierung:', config.plugins.moviebrowser.timer))
            # list.append(getConfigListEntry('Plugin w\xc3\xa4hrend Aktualisierung ausblenden:', config.plugins.moviebrowser.hideupdate))
        # else:
        list.append(getConfigListEntry(_('Movies Style:'), config.plugins.moviebrowser.style))
        list.append(getConfigListEntry(_('Series Style:'), config.plugins.moviebrowser.seriesstyle))
        self.foldername = getConfigListEntry(_('Movie Folder:'), config.plugins.moviebrowser.moviefolder)
        list.append(self.foldername)
        list.append(getConfigListEntry(_('Cache Folder:'), config.plugins.moviebrowser.cachefolder))
        list.append(getConfigListEntry(_('Movies or Series:'), config.plugins.moviebrowser.filter))
        list.append(getConfigListEntry(_('Movies or Series Selection at Start:'), config.plugins.moviebrowser.showswitch))
        list.append(getConfigListEntry(_('TMDb/TheTVDb Language:'), config.plugins.moviebrowser.language))
        list.append(getConfigListEntry(_('Movie Sort Order:'), config.plugins.moviebrowser.sortorder))
        list.append(getConfigListEntry(_('Show Backdrops:'), config.plugins.moviebrowser.backdrops))
        list.append(getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v))
        list.append(getConfigListEntry(_('Download new Backdrops:'), config.plugins.moviebrowser.download))
        list.append(getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv))
        list.append(getConfigListEntry(_('Plugin in Enigma Menu:'), config.plugins.moviebrowser.showmenu))
        list.append(getConfigListEntry(_('Plugin Sans Serif Font:'), config.plugins.moviebrowser.font))
        list.append(getConfigListEntry(_('Start Plugin with Video Button:'), config.plugins.moviebrowser.videobutton))
        list.append(getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie))
        list.append(getConfigListEntry(_('Load last Selection/Filter on Start:'), config.plugins.moviebrowser.lastfilter))
        list.append(getConfigListEntry(_('Show List of Movie Folder:'), config.plugins.moviebrowser.showfolder))
        list.append(getConfigListEntry(_('Plugin Transparency:'), config.plugins.moviebrowser.transparency))
        list.append(getConfigListEntry(_('Posterwall/Backdrop Plugin Size:'), config.plugins.moviebrowser.plugin_size))
        list.append(getConfigListEntry(_('Posterwall/Backdrop Show Plot:'), config.plugins.moviebrowser.plotfull))
        list.append(getConfigListEntry(_('Posterwall/Backdrop Headline Color:'), config.plugins.moviebrowser.color))
        list.append(getConfigListEntry(_('Metrix List Selection Color:'), config.plugins.moviebrowser.metrixcolor))
        list.append(getConfigListEntry(_('Plugin Auto Update Check:'), config.plugins.moviebrowser.autocheck))
        list.append(getConfigListEntry(_('Update Database with Timer:'), config.plugins.moviebrowser.timerupdate))
        list.append(getConfigListEntry(_('Timer Database Update:'), config.plugins.moviebrowser.timer))
        list.append(getConfigListEntry(_('Hide Plugin during Update:'), config.plugins.moviebrowser.hideupdate))
        list.append(getConfigListEntry(_('Full HD Skin Support:'), config.plugins.moviebrowser.fhd))
        list.append(getConfigListEntry(_('PayPal Info:'), config.plugins.moviebrowser.paypal))
        list.append(getConfigListEntry(_('Reset Database:'), config.plugins.moviebrowser.reset))
        list.append(getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup))
        list.append(getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup))
        list.append(getConfigListEntry(_('Restore Database:'), config.plugins.moviebrowser.restore))
        ConfigListScreen.__init__(self, list, on_change=self.UpdateComponents)
        self['actions'] = ActionMap(['SetupActions', 'ColorActions'], {
            'ok': self.save,
            'cancel': self.cancel,
            'red': self.cancel,
            'green': self.save
        }, -1)

        self.onLayoutFinish.append(self.UpdateComponents)

    def UpdateComponents(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/' + config.plugins.moviebrowser.style.value + '.png'
        if fileExists(png):
            PNG = loadPic(png, 512, 288, 3, 0, 0, 0)
            if PNG is not None:
                self['plugin'].instance.setPixmap(PNG)
        current = self['config'].getCurrent()
        if current == self.foldername:
            self.session.openWithCallback(self.folderSelected, FolderSelection, self.moviefolder)
        # elif current == getConfigListEntry('Use m1v Backdrops:', config.plugins.moviebrowser.m1v) or current == getConfigListEntry('Benutze m1v Backdrops:', config.plugins.moviebrowser.m1v) or current == getConfigListEntry('Show TV in Background (no m1v):', config.plugins.moviebrowser.showtv) or current == getConfigListEntry('Zeige TV im Hintergrund (no m1v):', config.plugins.moviebrowser.showtv):
        elif current == getConfigListEntry(_('Use m1v Backdrops:'), config.plugins.moviebrowser.m1v) or current == getConfigListEntry(_('Show TV in Background (no m1v):'), config.plugins.moviebrowser.showtv):
            if config.plugins.moviebrowser.m1v.value == 'yes':
                config.plugins.moviebrowser.showtv.value = 'hide'
        # elif current == getConfigListEntry('Goto last Movie on Start:', config.plugins.moviebrowser.lastmovie) or current == getConfigListEntry('Gehe zum letzten Film beim Start:', config.plugins.moviebrowser.lastmovie):
        elif current == getConfigListEntry(_('Goto last Movie on Start:'), config.plugins.moviebrowser.lastmovie):

           if config.plugins.moviebrowser.showfolder.value == 'no' and config.plugins.moviebrowser.lastmovie.value == 'folder':
                config.plugins.moviebrowser.lastmovie.value = 'yes'
        elif current == getConfigListEntry(_('PayPal Info:'), config.plugins.moviebrowser.paypal):
            import time
            from Screens.InputBox import PinInput
            self.pin = int(time.strftime('%d%m'))
            self.session.openWithCallback(self.returnPin, PinInput, pinList=[self.pin], triesEntry=config.ParentalControl.retries.servicepin)
        elif current == getConfigListEntry(_('Backup Database:'), config.plugins.moviebrowser.backup):
            if os.path.exists(self.cachefolder):
                if fileExists(self.database):
                    data = open(self.database).read()
                    try:
                        os.makedirs(self.cachefolder + '/backup')
                    except OSError:
                        pass

                    f = open(self.cachefolder + '/backup/database', 'w')
                    f.write(data)
                    f.close()
                    # if self.lang == 'de':
                        # self.session.open(MessageBox, '\nDatenbank gesichert nach %s' % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                    # else:
                    self.session.open(MessageBox, _('\nDatabase backuped to %s') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                # elif self.lang == 'de':
                    # self.session.open(MessageBox, '\nDatenbank %s nicht gefunden:\nMovie Browser Datenbank Backup abgebrochen.' % str(self.database), MessageBox.TYPE_ERROR)
                else:
                    self.session.open(MessageBox, _('\nDatabase %s not found:\nMovie Browser Database Backup canceled.') % str(self.database), MessageBox.TYPE_ERROR)
            # elif self.lang == 'de':
                # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Backup abgebrochen.' % str(self.cachefolder), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Backup canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        elif current == getConfigListEntry('Restore Database:', config.plugins.moviebrowser.restore):
            if os.path.exists(self.cachefolder):
                if fileExists(self.cachefolder + '/backup/database'):
                    data = open(self.cachefolder + '/backup/database').read()
                    f = open(self.database, 'w')
                    f.write(data)
                    f.close()
                    # if self.lang == 'de':
                        # self.session.open(MessageBox, '\nDatenbank zur\xc3\xbcckgespielt von %s' % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                    # else:
                    self.session.open(MessageBox, _('\nDatabase restored from %s') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_INFO, close_on_any_key=True)
                # elif self.lang == 'de':
                    # self.session.open(MessageBox, '\nDatenbank Backup %s nicht gefunden:\nMovie Browser Datenbank Wiederherstellung abgebrochen.' % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_ERROR)
                else:
                    self.session.open(MessageBox, _('\nDatabase Backup %s not found:\nMovie Browser Database Restore canceled.') % str(self.cachefolder + '/backup/database'), MessageBox.TYPE_ERROR)
            # elif self.lang == 'de':
                # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nMovie Browser Datenbank Wiederherstellung abgebrochen.' % str(self.cachefolder), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nMovie Browser Database Restore canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        elif current == getConfigListEntry(_('Cleanup Cache Folder:'), config.plugins.moviebrowser.cleanup):
            if os.path.exists(self.cachefolder):
                if fileExists(self.database):
                    data = open(self.database).read()
                    data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
                    folder = self.cachefolder
                    count = 0
                    if config.plugins.moviebrowser.language.value == 'de':
                        now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
                    else:
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
                        # if self.lang == 'de':
                            # self.session.open(MessageBox, '\nKeine verwaisten Backdrops oder Poster gefunden:\nIhr Cache Ordner ist sauber.', MessageBox.TYPE_INFO, close_on_any_key=True)
                        # else:
                        self.session.open(MessageBox, _('\nNo orphaned Backdrops or Posters found:\nYour Cache Folder is clean.'), MessageBox.TYPE_INFO, close_on_any_key=True)
                    # elif self.lang == 'de':
                        # self.session.open(MessageBox, '\nCache Ordner Bereinigung beendet:\n%s verwaiste Backdrops oder Poster entfernt.' % str(count), MessageBox.TYPE_INFO, close_on_any_key=True)
                    else:
                        self.session.open(MessageBox, _('\nCleanup Cache Folder finished:\n%s orphaned Backdrops or Posters removed.') % str(count), MessageBox.TYPE_INFO, close_on_any_key=True)
                    # if config.plugins.moviebrowser.language.value == 'de':
                        # end = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
                        # info = 'Startzeit: %s\nEndzeit: %s\nVerwaiste Backdrops/Poster entfernt: %s\n\n' % (now, end, str(count))
                    # else:
                    end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                    info = _('Start time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
                    f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/cleanup.log', 'a')
                    f.write(info)
                    f.close()
                # elif self.lang == 'de':
                    # self.session.open(MessageBox, '\nDatenbank %s nicht gefunden:\nCache Ordner Bereinigung abgebrochen.' % str(self.database), MessageBox.TYPE_ERROR)
                else:
                    self.session.open(MessageBox, _('\nDatabase %s not found:\nCleanup Cache Folder canceled.') % str(self.database), MessageBox.TYPE_ERROR)
            # elif self.lang == 'de':
                # self.session.open(MessageBox, '\nCache Ordner %s ist nicht erreichbar:\nCache Ordner Bereinigung abgebrochen.' % str(self.cachefolder), MessageBox.TYPE_ERROR)
            else:
                self.session.open(MessageBox, _('\nCache Folder %s not reachable:\nCleanup Cache Folder canceled.') % str(self.cachefolder), MessageBox.TYPE_ERROR)
        return

    def folderSelected(self, folder):
        if folder is not None:
            self.moviefolder = folder
            config.plugins.moviebrowser.moviefolder.value = folder
            config.plugins.moviebrowser.moviefolder.save()
        return

    def returnPin(self, pin):
        if pin:
            config.plugins.moviebrowser.paypal.value = 'no'
            config.plugins.moviebrowser.paypal.save()
            configfile.save()
        else:
            config.plugins.moviebrowser.paypal.value = 'yes'
            config.plugins.moviebrowser.paypal.save()

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
                        # if self.lang == 'de':
                            # self.session.open(MessageBox, '\nDatenbank Fehler: Eintrag ohne Laufzeit', MessageBox.TYPE_ERROR)
                        # else:
                        self.session.open(MessageBox, '\nDatabase Error: Entry without runtime', MessageBox.TYPE_ERROR)

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
            if config.plugins.moviebrowser.reset.value == 'yes':
                open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/reset', 'w').close()
                config.plugins.moviebrowser.reset.value = 'no'
                config.plugins.moviebrowser.reset.save()
            if config.plugins.moviebrowser.cachefolder.value != self.cachefolder:
                self.container = eConsoleAppContainer()
                self.container.appClosed.append(self.finished)
                newcache = sub('/cache', '', config.plugins.moviebrowser.cachefolder.value)
                self.container.execute("mkdir -p '%s' && cp -r '%s' '%s' && rm -rf '%s'" % (config.plugins.moviebrowser.cachefolder.value, self.cachefolder, newcache, self.cachefolder))
                self.cachefolder = config.plugins.moviebrowser.cachefolder.value
                config.plugins.moviebrowser.cachefolder.save()
            else:
                for x in self['config'].list:
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

        self.exit()

    def cancel(self):
        for x in self['config'].list:
            x[1].cancel()

        self.exit()

    def exit(self):
        if self.m1v == 'no' and config.plugins.moviebrowser.m1v.value == 'yes':
            config.plugins.moviebrowser.transparency.value = 200
            config.plugins.moviebrowser.transparency.save()
            configfile.save()
        elif self.m1v == 'yes' and config.plugins.moviebrowser.m1v.value == 'no':
            config.plugins.moviebrowser.transparency.value = 255
            config.plugins.moviebrowser.transparency.save()
            configfile.save()
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


class FolderSelection(Screen):
    skin = """
        <screen position="center,center" size="530,525" backgroundColor="#20000000" title="Movie Browser Setup">
        <ePixmap position="0,0" size="530,28" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/logoConfig.png" alphatest="blend" zPosition="1"/>
        <ePixmap position="9,37" size="512,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/seperator.png" alphatest="off" zPosition="1"/>
        <widget name="folderlist" position="9,38" size="512,150" itemHeight="25" scrollbarMode="showOnDemand" zPosition="1"/>
        <ePixmap position="9,189" size="512,1" pixmap="/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/seperator.png" alphatest="off" zPosition="1"/>
        <widget name="save" position="150,198" size="125,20" font="{font};18" halign="left" transparent="1" zPosition="1"/>
        <widget name="cancel" position="365,198" size="125,20" font="{font};18" halign="left" transparent="1" zPosition="1"/>
        <ePixmap position="125,199" size="18,18" pixmap="skin_default/buttons/green.png" alphatest="blend" zPosition="1"/>
        <ePixmap position="340,199" size="18,18" pixmap="skin_default/buttons/red.png" alphatest="blend" zPosition="1"/>
        <widget name="plugin" position="9,228" size="512,288" alphatest="blend" zPosition="1"/>
        </screen>
    """

    def __init__(self, session, folder):
        if config.plugins.moviebrowser.font.value == 'yes':
            font = 'Sans'
        else:
            font = 'Regular'
        self.dict = {'font': font}
        self.skin = applySkinVars(FolderSelection.skin, self.dict)
        Screen.__init__(self, session)
        lang = config.plugins.moviebrowser.language.value
        # if lang == 'de':
            # self['save'] = Label('Speichern')
            # self['cancel'] = Label('Abbrechen')
        # else:
        self['save'] = Label(_('Save'))
        self['cancel'] = Label(_('Cancel'))
        self['plugin'] = Pixmap()
        noFolder = [
            '/bin',
            '/boot',
            '/dev',
            '/etc',
            '/lib',
            '/proc',
            '/sbin',
            '/sys'
        ]
        self['folderlist'] = FileList(folder, showDirectories=True, showFiles=False, inhibitDirs=noFolder)
        self['actions'] = ActionMap(['OkCancelActions', 'DirectionActions', 'ColorActions'], {
            'ok': self.ok,
            'cancel': self.cancel,
            'right': self.right,
            'left': self.left,
            'down': self.down,
            'up': self.up,
            'red': self.cancel,
            'green': self.green
        }, -1)

        self.onLayoutFinish.append(self.pluginPic)

    def pluginPic(self):
        png = '/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/pic/setup/' + config.plugins.moviebrowser.style.value + '.png'
        if fileExists(png):
            PNG = loadPic(png, 512, 288, 3, 0, 0, 0)
            if PNG is not None:
                self['plugin'].instance.setPixmap(PNG)
        return

    def ok(self):
        if self['folderlist'].canDescent():
            self['folderlist'].descent()

    def right(self):
        self['folderlist'].pageDown()

    def left(self):
        self['folderlist'].pageUp()

    def down(self):
        self['folderlist'].down()

    def up(self):
        self['folderlist'].up()

    def green(self):
        self.close(self['folderlist'].getSelection()[0])

    def cancel(self):
        self.close(None)
        return


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
        # if config.plugins.moviebrowser.language.value == 'de':
            # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
            # info = '*******Movie Browser Datenbank Update Timer*******\nInitial Update Timer gestartet: %s\nTimer Wert (min): %s\n' % (now, str(start_time))
        # else:
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('*******Movie Browser Database Update Timer*******\nInitial Update Timer started: %s\nTimer Value (min): %s\n') % (now, str(start_time))
        f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log', 'a')
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
        # if config.plugins.moviebrowser.language.value == 'de':
            # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
            # info = 'Datenbank Update Timer gestoppt: %s\n' % now
        # else:
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer stopped: %s\n') % now
        f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log', 'a')
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
        # if config.plugins.moviebrowser.language.value == 'de':
            # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
            # info = 'Datenbank Update Timer gestartet: %s\nTimer Wert (min): %s\n' % (now, str(start_time))
        # else:
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Database Update Timer started: %s\nTimer Value (min): %s\n') % (now, str(start_time))
        f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log', 'a')
        f.write(info)
        f.close()

    def runUpdate(self):
        UpdateDatabase(False, '', '', '').showResult(True)
        # if config.plugins.moviebrowser.language.value == 'de':
            # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
            # info = 'Film Datenbank Update gestartet: %s\n' % now
        # else:
        now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        info = _('Movie Database Update started: %s\n') % now
        f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log', 'a')
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
        # if config.plugins.moviebrowser.language.value == 'de':
            # info = '*******Movie Browser Datenbank Update*******\n'
        # else:
        info = _('*******Movie Browser Database Update*******\n')
        f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/update.log', 'w')
        f.write(info)
        f.close()
        if config.plugins.moviebrowser.videobutton.value == 'yes':
            infobarsession = kwargs['session']
            from Screens.InfoBar import InfoBar
            InfoBar.showMovies = mainInfoBar
        if config.plugins.moviebrowser.timerupdate.value == 'yes':
            open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/timer.log', 'w').close()
            session = kwargs['session']
            timerupdate.saveSession(session)
            try:
                timerupdate.start()
            except:
                error = sys.exc_info()[1]
                errortype = sys.exc_info()[0]
                # if config.plugins.moviebrowser.language.value == 'de':
                    # now = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
                    # result = '*******Movie Browser Datenbank Update*******\nUhrzeit: %s\nFehler: %s\nGrund: %s' % (now, str(errortype), str(error))
                # else:
                now = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                result = _('*******Movie Browser Database Update*******\nTime: %s\nError: %s\nReason: %s') % (now, str(errortype), str(error))
                print(result)
                f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/update.log', 'w')
                f.write(result)
                f.close()

        if os.path.exists(config.plugins.moviebrowser.cachefolder.value):
            if fileExists('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database'):
                data = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/db/database').read()
                data = data + ':::default_folder.png:::default_poster.png:::default_banner.png:::default_backdrop.png:::default_backdrop.m1v:::database:::'
                folder = config.plugins.moviebrowser.cachefolder.value
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
                # if config.plugins.moviebrowser.language.value == 'de':
                    # end = str(datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
                    # info = '*******Cleanup Cache Ordner*******\nStartzeit: %s\nEndzeit: %s\nVerwaiste Backdrops/Poster entfernt: %s\n\n' % (now, end, str(count))
                # else:
                end = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                info = _('*******Cleanup Cache Folder*******\nStart time: %s\nEnd time: %s\nOrphaned Backdrops/Posters removed: %s\n\n') % (now, end, str(count))
                f = open('/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/log/cleanup.log', 'w')
                f.write(info)
                f.close()
    return


def Plugins(**kwargs):
    # lang = language.getLanguage()[:2]
    # if lang == 'de':
        # plugindesc = 'Film & Serien Verwaltung'
    # else:
    plugindesc = _('Manage your Movies & Series')
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
