# -*- coding: utf-8 -*-
import os
import sys
import time
import wx
import glob
import traceback
import platform

# For the version checking
import urllib2
from threading import Thread

# Used to recurse subdirectories
import fnmatch

def flatten(list):
    """
    Internal function that flattens a N-D list.

    
    **Parameters:**

    * list: the N-D list that needs to be flattened.
    """

    res = []
    for item in list:
        if type(item) == ListType:
            res = res + flatten(item)
        elif item is not None:
            res = res + [item]
    return res


def unique(list):
    """
    Internal function, returning the unique elements in a list.

    
    **Parameters:**

    * list: the list for which we want the unique elements.
    """

    # Create a fake dictionary
    res = {}

    for item in list:
        # Loop over all the items in the list
        key, value = item
        if res.has_key(key):
            res[key].append(value)
        else:
            res[key] = [value]

    # Return the dictionary values (a list)    
    return res.items()


def now():
    """ Returns the current time formatted. """

    t = time.localtime(time.time())
    st = time.strftime("%d %B %Y @ %H:%M:%S", t)
    
    return st


def shortNow():
    """ Returns the current time formatted. """
    
    t = time.localtime(time.time())
    st = time.strftime("%H:%M:%S", t)

    return st


def FractSec(s):
    """
    Formats time as hh:mm:ss.

    
    **Parameters:**

    * s: the number of seconds.
    """
    
    min, s = divmod(s, 60)
    h, min = divmod(min, 60)
    return h, min, s


def GetFolderSize(exePath):
    """
    Returns the size of the executable distribution folder.

    
    **Parameters:**

    * exePath: the path of the distribution folder.
    """
    
    folderSize = numFiles = 0
    join, getsize = os.path.join, os.path.getsize
    # Recurse over all the folders and sub-folders    
    for path, dirs, files in os.walk(exePath):
        for file in files:
            # Get the file size
            filename = join(path, file)
            folderSize += getsize(filename)
            numFiles += 1

    if numFiles == 0:
        # No files found, has the executable ever been built?
        return "", ""
    
    folderSize = "%0.2f"%(folderSize/(1024*1024.0))
    numFiles = "%d"%numFiles

    return numFiles, folderSize


def RecurseSubDirs(directory, userDir, extensions):
    """
    Recurse one directory to include all the files and sub-folders in it.

    
    **Parameters:**

    * directory: the folder on which to recurse;
    * userDir: the directory chosen by the user;
    * extensions: the file extensions to be filtered.
    """

    config = []
    baseStart = os.path.basename(directory)

    normpath, join = os.path.normpath, os.path.join
    splitext, match = os.path.splitext, fnmatch.fnmatch
    
    # Loop over all the sub-folders in the top folder 
    for root, dirs, files in os.walk(directory):
        start = root.find(baseStart) + len(baseStart)
        dirName = userDir + root[start:]
        dirName = dirName.replace("\\", "/")
        paths = []
        # Loop over all the files
        for name in files:
            # Loop over all extensions
            for ext in extensions:
                if match(name, ext):
                    paths.append(normpath(join(root, name)))
                    break

        if paths:
            config.append((dirName, paths))

    return config

def GetAvailLocales(installDir):
    """
    Gets a list of the available locales that have been installed.
    Returning a list of strings that represent the
    canonical names of each language.
    
    
    **Returns:**

    *  list of all available local/languages available
    
    **Note:**

    *  from Editra.dev_tool
    """

    avail_loc = []
    langDir = installDir
    loc = glob.glob(os.path.join(langDir, "locale", "*"))
    for path in loc:
        the_path = os.path.join(path, "LC_MESSAGES", "GUI2Exe.mo")
        if os.path.exists(the_path):
            avail_loc.append(os.path.basename(path))
    return avail_loc


def GetLocaleDict(loc_list, opt=0):
    """
    Takes a list of cannonical locale names and by default returns a
    dictionary of available language values using the canonical name as
    the key. Supplying the Option OPT_DESCRIPT will return a dictionary
    of language id's with languages description as the key.
    
    
    **Parameters:**

    * loc_list: list of locals
    
    **Keywords:**

    * opt: option for configuring return data
    
    **Returns:**

    *  dict of locales mapped to wx.LANGUAGE_*** values
    
    **Note:**

    *  from Editra.dev_tool
    """
    lang_dict = dict()
    for lang in [x for x in dir(wx) if x.startswith("LANGUAGE")]:
        loc_i = wx.Locale(wx.LANGUAGE_DEFAULT).\
                          GetLanguageInfo(getattr(wx, lang))
        if loc_i:
            if loc_i.CanonicalName in loc_list:
                if opt == 1:
                    lang_dict[loc_i.Description] = getattr(wx, lang)
                else:
                    lang_dict[loc_i.CanonicalName] = getattr(wx, lang)
    return lang_dict


def GetLangId(installDir, lang_n):
    """
    Gets the ID of a language from the description string. If the
    language cannot be found the function simply returns the default language

    
    **Parameters:**

    * lang_n: Canonical name of a language
    
    **Returns:**

    *  wx.LANGUAGE_*** id of language
    
    **Note:**

    *  from Editra.dev_tool
    """
    
    lang_desc = GetLocaleDict(GetAvailLocales(installDir), 1)
    return lang_desc.get(lang_n, wx.LANGUAGE_DEFAULT)


def FormatTrace(etype, value, trace):
    """Formats the given traceback
    
    **Returns:**

    *  Formatted string of traceback with attached timestamp
    
    **Note:**

    *  from Editra.dev_tool
    """
    
    exc = traceback.format_exception(etype, value, trace)
    exc.insert(0, "*** %s ***%s" % (now(), os.linesep))
    return "".join(exc)


def EnvironmentInfo():
    """
    Returns a string of the systems information.
    
    
    **Returns:**

    *  System information string
    
    **Note:**

    *  from Editra.dev_tool
    """

    info = list()
    info.append("---- Notes ----")
    info.append("Please provide additional information about the crash here")
    info.extend(["", "", ""])
    info.append("---- System Information ----")
    info.append("Operating System: %s" % wx.GetOsDescription())
    if sys.platform == 'darwin':
        info.append("Mac OSX: %s" % platform.mac_ver()[0])
    info.append("Python Version: %s" % sys.version)
    info.append("wxPython Version: %s" % wx.version())
    info.append("wxPython Info: (%s)" % ", ".join(wx.PlatformInfo))
    info.append("Python Encoding: Default=%s  File=%s" % \
                (sys.getdefaultencoding(), sys.getfilesystemencoding()))
    info.append("wxPython Encoding: %s" % wx.GetDefaultPyEncoding())
    info.append("System Architecture: %s %s" % (platform.architecture()[0], \
                                                platform.machine()))
    info.append("Byte order: %s" % sys.byteorder)
    info.append("Frozen: %s" % str(getattr(sys, 'frozen', 'False')))
    info.append("---- End System Information ----")

    return os.linesep.join(info)