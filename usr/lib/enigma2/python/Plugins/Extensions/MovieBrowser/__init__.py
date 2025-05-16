# -*- coding: utf-8 -*-

from __future__ import absolute_import

from os import environ
from os.path import exists
from sys import version_info
import gettext

from Components.Language import language
from Tools.Directories import resolveFilename, SCOPE_PLUGINS

PluginLanguageDomain = "moviebrowser"
PluginLanguagePath = "Extensions/MovieBrowser/locale"

isDreambox = exists("/usr/bin/apt-get")
PY3 = version_info.major >= 3


def localeInit():
	if isDreambox:
		lang = language.getLanguage()[:2]
		environ["LANGUAGE"] = lang
	if PluginLanguageDomain and PluginLanguagePath:
		gettext.bindtextdomain(PluginLanguageDomain, resolveFilename(SCOPE_PLUGINS, PluginLanguagePath))


if isDreambox:
	def _(txt):
		return gettext.dgettext(PluginLanguageDomain, txt) if txt else ""
else:
	def _(txt):
		translated = gettext.dgettext(PluginLanguageDomain, txt)
		if translated:
			return translated
		else:
			print("[%s] fallback to default translation for %s" % (PluginLanguageDomain, txt))
			return gettext.gettext(txt)

localeInit()
language.addCallback(localeInit)
