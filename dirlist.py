#!/usr/bin/env python
# encoding=utf8
from __future__ import print_function, absolute_import, division

import logging

import errno
from sys import argv, exit
from time import time
from time import mktime
from datetime import datetime
import urllib2
import re
from stat import S_IFDIR, S_IFLNK, S_IFREG
from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
from dateutil import parser
import sys

reload(sys)
sys.setdefaultencoding('utf8')


def tosize(vs):
    if (vs == "" or vs == "-"):
        return 0
    # For shortened file sizes we need to ensure the reported size is >= actual size
    # to avoid copy operations truncating the downloaded file
    if (vs.endswith("K")):
        return int( (float(vs.replace("K", ""))+0.1)*1024 )
    if (vs.endswith("M")):
        return int( (float(vs.replace("M", ""))+0.1)*1024*1024 )
    if (vs.endswith("G")):
        return int( (float(vs.replace("G", ""))+0.1)*1024*1024*1024 )
    return int(vs)

def todate(dt):
    d = now
    if (dt.strip() != "" and dt.strip() != "-"):
        d = int(mktime(parser.parse(dt.strip()).timetuple()))
    return d

def parseindex(index):
    files = parseindextofiles(index)
    print(files)
    return [dict(
        name=f["filename"],
        attrs=dict(
            st_mode=(S_IFDIR | 0o500) if f["dir"] else 33024,
            st_ctime=f["date"],
            st_mtime=f["date"],
            st_atime=f["date"],
            st_nlink=2 if f["dir"] else 1,
            st_size=f["size"],
        ),
    ) for f in files]

def parseindextofiles(index):
    if ('<hr></th></tr>' in index):
        return parseapacheindex(index)
    if ('<tbody><tr><td><a href="../">Parent directory/</a></td><td>-</td><td>-</td></tr>' in index):
        return parsenginxfancyindex(index)
    if ('<hr><pre><a ' in index or '<pre><img' in index):
        return parsepreindex(index)
    raise FuseOSError(errno.EACCES)

def parsenginxfancyindex(index):
    index = re.search(r'<tbody><tr><td><a href="../">Parent directory/</a></td><td>-</td><td>-</td></tr>((\r|\n|.)*)</tbody>', index, re.MULTILINE).group(1)
    # <tr><td><a href="rall/">rall/</a></td><td>-</td><td>27-Jan-2018 20:47</td></tr>
    files_and_folders = [x for x in re.findall(r'<tr><td><a href="[^"]+">([^<]+)</a></td><td>([^<]+)</td><td>([^<]+)</td></tr>', index, re.MULTILINE) if x[0] != "[PARENTDIR]"]
    result = []
    for f in files_and_folders:
        dir = True if f[0].endswith("/") else False
        date = todate(f[2])
        size = tosize(f[1].strip())
        name = f[0].decode('utf-8').encode('utf-8').replace("/","")
        result.append(dict(filename=name, dir=dir, size=size, date=date))
    return result


def parseapacheindex(index):
    files_and_folders = [x for x in re.findall(r'<tr>.*?alt="([^"]+)".*?<td><a href="[^"]+">([^<]+).*?<td[^>]*>([^<&]*).*?<td[^>]*> *([0-9.KMG]*)', index, re.MULTILINE) if x[0] != "[PARENTDIR]"]
    result = []
    for f in files_and_folders:
        dir = True if (f[0] == "[DIR]") else False
        date = todate(f[2])
        size = tosize(f[3].strip())
        name = f[1].decode('utf-8').encode('utf-8').replace("/","")
        result.append(dict(filename=name, dir=dir, size=size, date=date))
    return result

def parsepreindex(index):
    index = re.search(r'<pre>(<a href="../">../|.*">Parent Directory)</a>((\r|\n|.)*)</pre>', index, re.MULTILINE).group(2)
    files_and_folders = [x for x in re.findall(r'<a href="[^"]+">([^<]+)</a> +([a-zA-Z0-9\-: ]*?) {2,}([0-9\-.]*[KGM]?)', index, re.MULTILINE)]
    result = []
    for f in files_and_folders:
        dir = True if (f[2] == "-" or f[0].endswith("/")) else False
        date = todate(f[1])
        size = tosize(f[2].strip())
        name = f[0].decode('utf-8').encode('utf-8').replace("/","")
        result.append(dict(filename=name, dir=dir, size=size, date=date))
    return result

now = time()

class DirList(LoggingMixIn, Operations):

    def create_ino(self):
        self.ino += 1
        return self.ino

    def __init__(self, uri, path='.'):
        self.uri = uri
        self.ino = 1
        self.cache = { "/": dict(st_mode=(S_IFDIR | 0o755), st_ino=1, st_ctime=now, st_mtime=now, st_atime=now, st_nlink=2) }
        self.root = path

    def chmod(self, path, mode):
        raise FuseOSError(errno.EACCES)

    def chown(self, path, uid, gid):
        raise FuseOSError(errno.EACCES)

    def create(self, path, mode):
       raise FuseOSError(errno.EACCES)

    def destroy(self, path):
        print("bye bye")

    def getattr(self, path, fh=None):
        return self.cache[path]

    def mkdir(self, path, mode):
        raise FuseOSError(errno.EACCES)

    def read(self, path, size, offset, fh):
        headers = { 'Range': "bytes=" + str(offset) + "-" + str(offset+size-1), }
        req = urllib2.Request(self.uri + path, None, headers)
        resp = urllib2.urlopen(req)
        if (resp.getcode() != 206):
            if (resp.getcode() == 416):
                return ""
            raise FuseOSError(errno.EACCES)
        contl = int(resp.info().getheader('content-length'))
        return resp.read(contl)

    def readdir(self, path, fh):
        print(self.uri + path)
        response = urllib2.urlopen(self.uri + path) 
        if (response.getcode() != 200):
            raise FuseOSError(errno.EACCES)
        html = response.read()
        result = parseindex(html)
        for f in result:
            key = (path + "/" + f["name"]).replace('//', '/')
            f["attrs"]["st_ino"] = self.create_ino()
            self.cache[key] = f["attrs"]
        names = [x["name"] for x in result]
        return ['.', '..'] + [name.replace("/","").encode('utf-8')
                              for name in names if name != "/"]

    def readlink(self, path):
        raise FuseOSError(errno.EINVAL)

    def rename(self, old, new):
        raise FuseOSError(errno.EACCES)

    def rmdir(self, path):
        raise FuseOSError(errno.EACCES)

    def symlink(self, target, source):
        raise FuseOSError(errno.EACCES)

    def truncate(self, path, length, fh=None):
        raise FuseOSError(errno.EACCES)

    def unlink(self, path):
        raise FuseOSError(errno.EACCES)

    def utimens(self, path, times=None):
        raise FuseOSError(errno.EACCES)

    def write(self, path, data, offset, fh):
        raise FuseOSError(errno.EACCES)


if __name__ == '__main__':
    if len(argv) != 3:
        print('usage: %s <uri> <mountpoint>' % argv[0])
        exit(1)

    logging.basicConfig(level=logging.DEBUG)

    fuse = FUSE(DirList(argv[1]), argv[2], foreground=True, nothreads=True)
