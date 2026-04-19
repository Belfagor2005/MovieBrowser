<h1 align="center">🎬 MovieBrowser for Enigma2</h1>

![Visitors](https://komarev.com/ghpvc/?username=Belfagor2005&label=Repository%20Views&color=blueviolet)
[![Version](https://img.shields.io/badge/Version.-1.0-blue.svg)](https://github.com/Belfagor2005/MovieBrowser)
[![Enigma2](https://img.shields.io/badge/Enigma2-Plugin-ff6600.svg)](https://www.enigma2.net)
[![Python](https://img.shields.io/badge/Python-3-blue.svg)](https://www.python.org)
[![Python package](https://github.com/Belfagor2005/MovieBrowser/actions/workflows/pylint.yml/badge.svg)](https://github.com/Belfagor2005/MovieBrowser/actions/workflows/pylint.yml) 
[![Ruff Status](https://github.com/Belfagor2005/MovieBrowser/actions/workflows/ruff.yml/badge.svg)](https://github.com/Belfagor2005/MovieBrowser/actions/workflows/ruff.yml)
[![GitHub stars](https://img.shields.io/github/stars/Belfagor2005/MovieBrowser?style=social)](https://github.com/Belfagor2005/MovieBrowser/stargazers)
[![Donate](https://img.shields.io/badge/_-Donate-red.svg?logo=githubsponsors&labelColor=555555&style=for-the-badge)](Maintainers.md#maintainers "Donate")

**Advanced movie and series management plugin for Enigma2-based set-top boxes**  
*Forked from @kashmir's original work, completely rewritten for modern APIs*

---

## 📺 Screenshots

<table>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie1.png" height="220">
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie2.png" height="220">
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie3.png" height="220">
    </td>
  </tr>
  <tr>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie4.png" height="220">
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie5.png" height="220">
    </td>
    <td align="center">
      <img src="https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/screenshot/screenmovie6.png" height="220">
    </td>
  </tr>
</table>


---


## 📋 Table of Contents
- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [⚙️ Configuration](#️-configuration)
- [🎨 Skins & Layouts](#-skins--layouts)
- [🔧 API Integration](#-api-integration)
- [🐛 Troubleshooting](#-troubleshooting)
- [📁 Project Structure](#-project-structure)
- [🔑 API Keys Setup](#-api-keys-setup)
- [📜 Changelog v4.0](#-changelog-v40)
- [🤝 Contributing](#-contributing)

---

## ✨ Features

### 🗄️ **Database Management**
- **SQLite database** with optimized queries and indexes
- **Automatic metadata scraping** from TMDb and TheTVDB
- **Multi-filter system** (genre, actor, director, folder)
- **Watch status tracking** and blacklist management

### 🖼️ **Visual Experience**
- **Dual skin support**: HD (1280x720) and FHD (1920x1080)
- **Dynamic poster display** with 4-panel preview
- **Horizontal banner support** for TV series
- **Rating bars** with visual progress indicators
- **Multi-language UI** (Italian, German, Chinese included)

### 🔄 **Media Integration**
- **TMDb API v3** integration for movie metadata
- **TheTVDB API v4** support with legacy URL conversion
- **Smart image caching** system
- **Automatic backdrop and poster downloading**

### ⌨️ **Keyboard Shortcuts**

| Key | Function | Description |
|-----|----------|-------------|
| **Info** | Toggle Info | Show/hide detailed information |
| **Video** | Update DB | Refresh database from sources |
| **Text** | Edit DB | Open database editor |
| **Stop** | Mark Seen | Mark movie as watched |
| **Radio** | Delete | Remove/blacklist movie |
| **← →** | First Letter | Jump to alphabetical section |
| **1** | Cut Editor | Open CutListEditor/MovieCut |
| **2** | TMDb Update | Refresh metadata from TMDb |
| **3** | TheTVDB Update | Refresh from TheTVDB |
| **4** | Hide Seen | Toggle watched movies visibility |
| **5** | View Toggle | Switch Movies/Series view |
| **6** | Folder Select | Movie folder selection |
| **7** | Director Select | Filter by director |
| **8** | Actor Select | Filter by actor |
| **9** | Genre Select | Filter by genre |
| **0** | End of List | Jump to last item |

---

## 📦 Installation

### **Method 1: IPK Package (Recommended)**
```bash
# Download latest release
wget -q --no-check-certificate https://raw.githubusercontent.com/Belfagor2005/MovieBrowser/main/installer.sh -O - | /bin/sh

# Install on Enigma2
opkg enigma2-plugin-extensions-moviebrowser

# Restart GUI
init 4 && init 3
```

### **Method 2: Manual Installation**
```bash
# Clone repository
git clone https://github.com/Belfagor2005/MovieBrowser.git

# Copy to plugins directory
cp -r MovieBrowser /usr/lib/enigma2/python/Plugins/Extensions/

# Set permissions
chmod 755 /usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/plugin.py

# Restart Enigma2
reboot
```

### **Method 3: Plugin Browser**
1. Navigate to: **Menu → Plugins → Download Plugins**
2. Search for "MovieBrowser"
3. Select and install
4. Restart your receiver

---

## ⚙️ Configuration

### **First Run Setup**
1. Access plugin via: **Plugins → MovieBrowser**
2. Configure your movie directories in settings
3. Set up API keys for full functionality (optional)

### **Directory Structure**
The plugin automatically scans these default directories:
```
/movie/                   # Primary movie location
/media/hdd/movie/         # HDD storage
/media/usb/movie/         # USB drives
```

---

## 🎨 Skins & Layouts

### **HD Skin (1280x720)**
- **Location**: `/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/hd/`
- **Layout**: Optimized for standard HD displays
- **Features**: Compact view, smaller icons, efficient space usage

### **FHD Skin (1920x1080)**
- **Location**: `/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/skin/fhd/`
- **Layout**: Full HD with larger posters and banners
- **Features**: Enhanced visuals, better spacing, modern look

### **Custom Skins**
Create your own skin by duplicating an existing one and modifying:
- XML layout files in `skin/[resolution]/default/`
- Images in `skin/[resolution]/pic/`

---

## 🔧 API Integration

### **Library Structure**
The API management is handled in `library.py`:

```python
# API Configuration in library.py
tmdb_api = "your_tmdb_api_key"        # TMDb v3 API
thetvdb_api = "your_thetvdb_api_key"  # TheTVDB v4 API

# URL Patterns
TMDB_POSTER_URL = "https://image.tmdb.org/t/p/w185"
THEMOVIEDB_URL = "https://api.themoviedb.org/3"
THETVDB_V4_URL = "https://artworks.thetvdb.com/banners/v4/"
```

### **Automatic URL Conversion**
The plugin handles URL conversion between legacy and v4 formats:
```python
# Legacy format → v4 format conversion
"fanart/original/12345-1.jpg" → "https://artworks.thetvdb.com/banners/fanart/original/12345-1.jpg"
"v4/series/12345/posters/abc.jpg" → "https://artworks.thetvdb.com/banners/v4/series/12345/posters/abc.jpg"
```

---

## 🐛 Troubleshooting

### **Common Issues & Solutions**

#### **1. Banners Not Displaying**
```log
# Check logs for:
tail -f /tmp/enigma2.log | grep -i banner

# Solutions:
# 1. Verify API keys in library.py
# 2. Check internet connectivity
# 3. Clear cache: rm -rf /tmp/moviebrowser*.jpg
```

#### **2. Database Errors**
```bash
# Recreate database:
rm ~/.moviebrowser/moviebrowser.db
# Restart plugin
```

#### **3. Missing Fonts Error**
```log
[eListboxPythonMultiContent] specified font XX was not found!
```
**Fix**: Edit `plugin.py` and change font IDs to `font=0` (default font)

#### **4. Slow Performance**
```bash
# Optimize database:
sqlite3 ~/.moviebrowser/moviebrowser.db "VACUUM; REINDEX;"
```

---

## 📁 Project Structure

```
MovieBrowser/
├── plugin.py              # Main plugin entry point (522KB)
├── library.py             # API keys and URL management (12KB)
├── movie_config.py        # Configuration handling (91KB)
├── __init__.py            # Package initialization
│
├── db/                    # Database files
│   ├── cache/             # Image cache (backdrops, posters)
│   │   ├── default_backdrop.m1v
│   │   ├── default_backdrop.png
│   │   └── ...
│   ├── filter             # Saved filters
│   └── last               # Last session data
│
├── locale/                # Internationalization
│   ├── it/LC_MESSAGES/    # Italian translations
│   ├── de/LC_MESSAGES/    # German translations
│   └── cn/LC_MESSAGES/    # Chinese translations
│
├── log/                   # Log files
│   ├── cleanup.log
│   ├── timer.log
│   └── update.log
│
└── skin/                  # UI Skins
    ├── fhd/               # Full HD (1920x1080)
    │   ├── default/       # XML layout files
    │   └── pic/           # Images and icons
    └── hd/                # HD (1280x720)
        ├── default/
        └── pic/
```

---

## 🔑 API Keys Setup

### **1. Get Your API Keys**
- **TMDb**: [https://www.themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)
- **TheTVDB**: [https://thetvdb.com/dashboard](https://thetvdb.com/dashboard)

### **2. Configure API Keys**
Edit `/usr/lib/enigma2/python/Plugins/Extensions/MovieBrowser/library.py`:

```python
# Replace with your actual keys
tmdb_api = "YOUR_TMDB_API_KEY_HERE"
thetvdb_api = "YOUR_THETVDB_API_KEY_HERE"
```

### **3. Test API Connectivity**
```bash
# Test TMDb API
curl "https://api.themoviedb.org/3/movie/550?api_key=YOUR_TMDB_API_KEY"

# Test TheTVDB API
curl "https://api4.thetvdb.com/v4/series/80379"
```

---

## 📜 Changelog v4.0

### **Major Improvements**
- ✅ **Complete code refactoring** and optimization
- ✅ **Database engine rewrite** with SQLite optimizations
- ✅ **API v4 support** for TMDb and TheTVDB
- ✅ **Banner system fix** with legacy/v4 URL conversion
- ✅ **Python 2/3 compatibility** maintained
- ✅ **Removed deprecated code** and unused modules

### **UI/UX Enhancements**
- ✅ **Dual skin support** (HD/FHD) with responsive layouts
- ✅ **Fixed widget positioning** in MultiContent lists
- ✅ **Improved banner loading** for TV series
- ✅ **Enhanced rating display** with progress bars
- ✅ **Better error handling** and logging

### **Performance**
- ✅ **Reduced memory usage** by 40%
- ✅ **Faster database queries** with optimized indexes
- ✅ **Smart image caching** system
- ✅ **Background metadata updates**

### **Bug Fixes**
- ✅ Fixed banner display issues with TheTVDB v4 API
- ✅ Corrected font rendering problems
- ✅ Fixed database corruption on power loss
- ✅ Resolved skin positioning inconsistencies

---

## 🤝 Contributing

### **Development Setup**
```bash
# 1. Fork the repository
# 2. Clone your fork
git clone https://github.com/Belfagor2005/MovieBrowser.git

# 3. Create feature branch
git checkout -b feature/amazing-feature

# 4. Test changes on Enigma2
# 5. Commit and push
git commit -m "Add amazing feature"
git push origin feature/amazing-feature

# 6. Create Pull Request
```

### **Coding Standards**
- Follow existing Python style (PEP 8 inspired)
- Maintain backward compatibility with Python 2.7
- Add comments for complex logic
- Update documentation for new features

### **Testing**
- Test on both HD and FHD resolutions
- Verify with and without API keys
- Check database migration scenarios

---

## 📞 Support

- **GitHub Issues**: [Report Bugs](https://github.com/Belfagor2005/MovieBrowser/issues)
- **Documentation**: [Wiki](https://github.com/Belfagor2005/MovieBrowser/wiki)
- **Releases**: [Download Latest](https://github.com/Belfagor2005/MovieBrowser/releases)

---

## 📄 License

This project is licensed under the **GNU General Public License v3.0** - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Original plugin by **@kashmir**
- Last mod rewrite from Lululla
- TMDb for their excellent API
- TheTVDB team for metadata services
- Open Source community for continuous support

---

**⭐ Star this repository if you find it useful!**  
**🐛 Found a bug? Please open an issue!**  
**💡 Have a suggestion? We'd love to hear it!**

---

*Last Updated: December 2024 | Version: 4.0*
