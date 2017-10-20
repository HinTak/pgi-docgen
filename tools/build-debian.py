#!/usr/bin/python
# Copyright 2015 Christoph Reiter
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.

"""
Call these first:

* apt-file update
* sudo apt-get update

"""

import os
import sys
import subprocess
import shutil
import argparse
import requests
import time
from multiprocessing.pool import ThreadPool

import apt
import apt_pkg

from pgidocgen.debian import get_repo_girs, get_debug_packages_for_libs, \
    get_repo_typelibs
from pgidocgen.util import parse_gir_shared_libs


DEB_BLACKLIST = [
    "gir1.2-hkl-5.0",
    "gir1.2-totem-plparser-1.0",
]

BLACKLIST = [
    # old gtk
    "Gtk-2.0",
    "Gdk-2.0",
    "GdkX11-2.0",
    'MateDesktop-2.0',
    'PolkitGtkMate-1.0',
    'AtrilView-1.5.0',
    'AtrilDocument-1.5.0',
    'Eom-1.0',
    'Matekbd-1.0',

    # broken
    "Pluma-1.0",
    "Hkl-5.0",
    "Gcr-3",
    "GTop-2.0",
    "BraseroMedia-3.1",
    "FolksTelepathy-0.6",
    "Folks-0.6",
    "FolksEds-0.6",
    "Entangle-0.1",
    "Diodon-1.0",
    "Gee-0.8",
    "JSCore-3.0",
    "Skk-1.0",
    "SugarExt-1.0",
    "Meta-Muffin.0",
    "libisocodes-1.2.2",
    'Nice-0.1',
    "Geoclue-2.0",
    "Gtd-1.0",

    # hangs?
    'NMA-1.0',

    # criticals.. better skip
    "NMClient-1.0",
    "NMGtk-1.0",

    # depends on one of the above
    "Ganv-1.0",
    "DbusmenuGtk-0.4",
    "GcrUi-3",
    "Caja-2.0",
    "AppIndicator-0.1",
    "MatePanelApplet-4.0",
    "BraseroBurn-3.1",
    "v_sim-3.7",
    "FolksDummy-0.6",
    "Wnck-1.0",
]

BUILD = ['AccountsService-1.0', 'Anjuta-3.0', 'AppIndicator3-0.1', 'Atk-1.0',
'Atspi-2.0', 'Cally-1.0', 'Caribou-1.0', 'Champlain-0.12', 'Cheese-3.0',
'Clutter-1.0', 'ClutterGdk-1.0', 'ClutterX11-1.0', 'Cogl-1.0', 'Cogl-2.0',
'CoglPango-1.0', 'ColorHug-1.0', 'Colord-1.0', 'ColordGtk-1.0', 'CryptUI-0.0',
'DBus-1.0', 'DBusGLib-1.0', 'Dbusmenu-0.4', 'DbusmenuGtk3-0.4', 'Dee-1.0',
'EBook-1.2', 'EBookContacts-1.2', 'EDataServer-1.2', 'EvinceDocument-3.0',
'EvinceView-3.0', 'Farstream-0.2', 'Fcitx-1.0', 'GConf-2.0', 'GData-0.0',
'GDesktopEnums-3.0', 'GES-1.0', 'GExiv2-0.10', 'GIRepository-2.0', 'GL-1.0',
'GLib-2.0', 'GMenu-3.0', 'GModule-2.0', 'GObject-2.0', 'GOffice-0.10',
'GSSDP-1.0', 'GUPnP-1.0', 'GUPnPAV-1.0', 'GUPnPDLNA-2.0', 'GUPnPDLNAGst-2.0',
'GUPnPIgd-1.0', 'GUdev-1.0', 'GUsb-1.0', 'GWeather-3.0', 'GXPS-0.1', 'Gck-1',
'Gda-5.0', 'Gdk-3.0', 'GdkPixbuf-2.0', 'GdkX11-3.0', 'Gdl-3', 'Gdm-1.0',
'GeocodeGlib-1.0', 'Gio-2.0', 'Gkbd-3.0', 'Gladeui-2.0', 'GnomeBluetooth-1.0',
'GnomeDesktop-3.0', 'GnomeKeyring-1.0', 'Goa-1.0', 'Gsf-1', 'Gst-1.0',
'GstAllocators-1.0', 'GstApp-1.0', 'GstAudio-1.0', 'GstBase-1.0',
'GstCheck-1.0', 'GstController-1.0', 'GstFft-1.0', 'GstNet-1.0',
'GstPbutils-1.0', 'GstRtp-1.0', 'GstRtsp-1.0', 'GstSdp-1.0', 'GstTag-1.0',
'GstVideo-1.0', 'Gtk-3.0', 'GtkChamplain-0.12', 'GtkClutter-1.0',
'GtkSource-3.0', 'GtkSpell-3.0', 'Gucharmap-2.90', 'IBus-1.0', 'Indicate-0.7',
'Itl-1.0', 'JavaScriptCore-3.0', 'Json-1.0', 'Keybinder-0.0', 'Libosinfo-1.0',
'LibvirtGConfig-1.0', 'LibvirtGLib-1.0', 'LibvirtGObject-1.0',
'LunarDate-2.0', 'MPID-3.0', 'Nautilus-3.0', 'Nemo-3.0', 'NetworkManager-1.0',
'Notify-0.7', 'PackageKitGlib-1.0', 'Pango-1.0', 'PangoCairo-1.0',
'PangoFT2-1.0', 'PangoXft-1.0', 'Peas-1.0', 'PeasGtk-1.0', 'Polkit-1.0',
'PolkitAgent-1.0', 'Poppler-0.18', 'RB-3.0', 'Rest-0.7', 'RestExtras-0.7',
'Rsvg-2.0', 'Secret-1', 'Soup-2.4', 'SoupGNOME-2.4', 'SpiceClientGLib-2.0',
'SpiceClientGtk-3.0', 'SugarGestures-1.0', 'TelepathyGLib-0.12',
'TelepathyLogger-0.2', 'TotemPlParser-1.0', 'UDisks-2.0', 'UMockdev-1.0',
'UPowerGlib-1.0', 'Vte-2.91', 'WebKit-3.0', 'Wnck-3.0', 'Xkl-1.0',
'Zeitgeist-2.0', 'Zpj-0.0', 'cairo-1.0', 'fontconfig-2.0', 'freetype2-2.0',
'libxml2-2.0', 'xfixes-4.0', 'xft-2.0', 'xlib-2.0', 'xrandr-1.3',
"CoglPango-2.0", "GFBGraph-0.2", "Guestfs-1.0", "HarfBuzz-0.0",
"InputPad-1.0", "Keybinder-3.0", "LightDM-1", "MateMenu-2.0", "OsmGpsMap-1.0",
"Totem-1.0", "Uhm-0.0", "AppStreamGlib-1.0", "CDesktopEnums-3.0", "CMenu-3.0",
"CinnamonDesktop-3.0", "ModemManager-1.0", "Evd-0.1", "Cattle-1.0",
"GCab-1.0", "GPaste-1.0", "GVnc-1.0", "GVncPulse-1.0", "Ggit-1.0",
"GtkVnc-2.0", "JavaScriptCore-4.0", "SocialWebClient-0.25", "WebKit2-4.0",
"WebKit2WebExtension-4.0", "NM-1.0", "GstGL-1.0", "GstInsertBin-1.0",
"GstMpegts-1.0", 'Anthy-9000', 'MediaArt-2.0', 'CoglGst-2.0',
'GstRtspServer-1.0', 'ClutterGst-3.0', 'Gom-1.0', 'Limba-1.0', 'Abi-3.0',
'Gnm-1.12', 'Libmsi-1.0', 'Vips-8.0', 'GooCanvas-2.0', 'GSound-1.0',
'Accounts-1.0', 'Signon-1.0', 'Fwupd-1.0', 'Grss-0.7', 'AppStream-1.0',
'Dfu-1.0', 'LibvirtSandbox-1.0', 'GrlNet-0.3', 'Grl-0.3', 'Hinawa-1.0',
'GstPlayer-1.0', 'LOKDocView-0.1', 'GrlPls-0.3', 'GoVirt-1.0', 'Cvc-1.0',
'Workrave-1.0', 'OSTree-1.0', 'Flatpak-1.0', 'Mx-2.0',
'GstTranscoder-1.0', 'GSystem-1.0', 'GMime-2.6', 'Budgie-1.0',
'GnomeAutoarGtk-0.1', 'GnomeAutoar-0.1', 'LangTag-0.6', 'Gspell-1',
'Urfkill-0.5', 'Bamf-3', 'Ufo-0.0', 'XApp-1.0', 'CScreensaver-1.0',
'GstBadAllocators-1.0', 'Gepub-0.5', 'Camel-1.2',
'Graphene-1.0', 'EDataServerUI-1.2', 'Template-1.0', 'Jsonrpc-1.0',
'Dazzle-1.0', 'BlockDev-2.0', 'Devhelp-3.0', 'GMime-3.0',
'AyatanaAppIndicator-0.1', 'AyatanaAppIndicator3-0.1', 'AvahiCore-0.6',
'TrackerMiner-2.0', 'Avahi-0.6', 'TrackerControl-2.0', 'Retro-0.12',
'AyatanaIdo3-0.4', 'Tracker-2.0', 'Fwupd-2.0',
]


def check_typelibs(typelibs):
    cache = apt.Cache()
    cache.open(None)

    to_install = set()
    for package in typelibs:
        if package in DEB_BLACKLIST:
            continue
        if cache[package].candidate is None:
            continue
        if not cache[package].is_installed:
            to_install.add(package)

    cache.close()

    if to_install:
        print "Not all typelibs installed:\n"
        print "sudo apt install " + " ".join(sorted(to_install))
        raise SystemExit(1)


def compare_deb_packages(a, b):
    va = subprocess.check_output(["dpkg", "--field", a, "Version"]).strip()
    vb = subprocess.check_output(["dpkg", "--field", b, "Version"]).strip()
    return apt_pkg.version_compare(va, vb)


def _fetch(args):
    dest, uri = args
    for i in range(5):
        try:
            r = requests.get(uri)
        except requests.RequestException as e:
            time.sleep(i * i)
            continue
        break
    else:
        raise Exception(e)
    filename = uri.rsplit("/", 1)[-1]
    with open(os.path.join(dest, filename), "wb") as h:
        h.write(r.content)
    return uri


def fetch_girs(girs, dest):
    dest = os.path.abspath(dest)
    assert not os.path.exists(dest)

    tmp_root = os.path.join(dest, "temp_root")
    tmp_download = os.path.join(dest, "tmp_download")
    dst = os.path.join(dest, "gir-1.0")

    print "Download packages.."
    uris = []
    cache = apt.Cache()
    cache.open(None)
    # install anything that is a candidate or older
    # (is versions really ordered?)
    for name in girs:
        package = cache[name]
        ok = False
        for version in package.versions:
            if ok or package.candidate == version:
                ok = True
                if version.uri:
                    uris.append(version.uri)
    cache.close()

    os.makedirs(tmp_download)
    pool = ThreadPool(processes=10)
    for i, uri in enumerate(pool.imap_unordered(_fetch, [(tmp_download, u) for u in uris])):
        print("%d/%d" % (i+1, len(uris)), uri)
    pool.close()
    pool.join()

    print "Extracting packages.."

    # sort, so older girs get replaced
    entries = [os.path.join(tmp_download, e) for e in os.listdir(tmp_download)]
    entries.sort(cmp=compare_deb_packages)

    os.mkdir(dst)
    for path in entries:
        subprocess.check_call(["dpkg" , "-x", path, tmp_root])
        base_src = os.path.join(tmp_root, "usr", "share", "gir-1.0")
        if not os.path.isdir(base_src):
            continue
        for e in os.listdir(base_src):
            src = os.path.join(base_src, e)
            shutil.copy(src, dst)
        shutil.rmtree(tmp_root)


def fetch_girs_cached():
    temp_data = os.path.join(
        os.path.dirname(os.path.realpath(__file__)), "_temp_data_dir")
    if not os.path.exists(temp_data):
        print "find girs.."
        girs = get_repo_girs()
        print "fetch and extract debian packages.."
        fetch_girs(girs, temp_data)
    return temp_data


def get_gir_shared_libraries(gir_dir, can_build):
    all_libs = set()
    for entry in os.listdir(gir_dir):
        name, ext = os.path.splitext(entry)
        if name not in can_build:
            continue
        libs = parse_gir_shared_libs(os.path.join(gir_dir, entry))
        all_libs.update(libs)
    return all_libs


def check_debug_packages(gir_dir, can_build):
    shared_libs = get_gir_shared_libraries(gir_dir, can_build)
    debug_packages = get_debug_packages_for_libs(shared_libs)

    cache = apt.Cache()
    cache.open(None)
    to_install = set()
    for package in sorted(debug_packages):
        if not cache[package].is_installed:
            if package.startswith(("libwebkit", "libjavascriptcore")):
                # 5GB of debug data.. nope
                continue
            if package in DEB_BLACKLIST:
                continue
            to_install.add(package)
    cache.close()

    if to_install:
        print "Not all debug packages installed:\n"
        print "sudo apt install " + " ".join(sorted(to_install))
        raise SystemExit(1)


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument('--devhelp', action='store_true')
    args = parser.parse_args(argv[1:])

    print "[don't forget to apt-file update/apt-get update!]"

    print "searching for typelibs.."
    typelibs = get_repo_typelibs()
    print "searching for uninstalled typelibs"
    check_typelibs(typelibs)

    data_dir = fetch_girs_cached()
    gir_dir = os.path.join(data_dir, "gir-1.0")
    gir_list = [os.path.splitext(e)[0] for e in os.listdir(gir_dir)]

    typelib_ns = set()
    for namespaces in typelibs.itervalues():
        typelib_ns.update(namespaces)

    print "Missing gir files: %r" % sorted(typelib_ns - set(gir_list))
    print "Missing typelib files: %r" % sorted(set(gir_list) - typelib_ns)
    can_build = sorted(set(gir_list) & typelib_ns)
    print "%d ready to build" % len(can_build)

    assert not (set(BLACKLIST) & set(BUILD))

    unknown_build = set(BLACKLIST) - set(can_build)
    assert not unknown_build, unknown_build
    can_build = set(can_build) - set(BLACKLIST)
    print "%d ready to build after blacklisting" % len(can_build)

    print "searching for debug packages.."
    check_debug_packages(gir_dir, can_build)

    unknown_build = set(BUILD) - set(can_build)
    assert not unknown_build, unknown_build
    missing_build = set(can_build) - set(BUILD)
    assert not missing_build, missing_build

    os.environ["XDG_DATA_DIRS"] = data_dir

    subprocess.check_call(
        ["python", "./pgi-docgen.py", "_docs"] + BUILD)
    subprocess.check_call(
        ["python", "./pgi-docgen-build.py", "_docs", "_docs/_build"])

    if args.devhelp:
        subprocess.check_call(
            ["python", "./pgi-docgen-build.py", "--devhelp",
             "_docs", "_docs/_build_devhelp"])


if __name__ == "__main__":
    main(sys.argv)
