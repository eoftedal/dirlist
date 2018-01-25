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
    # For shortened file sizes we need to ensure the reported size is >= actual size
    if (vs.endswith("K")):
        return int( (float(vs.replace("K", ""))+0.1)*1024 )
    if (vs.endswith("M")):
        return int( (float(vs.replace("M", ""))+0.1)*1024*1024 )
    if (vs.endswith("G")):
        return int( (float(vs.replace("G", ""))+0.1)*1024*1024*1024 )
    return int(vs)

def parseindex(index):
    if ('<hr></th></tr>' in index):
        return parseapacheindex(index)
    if ('<hr><pre><a ' in index or '<pre><img' in index):
        return parsepreindex(index)
    raise FuseOSError(errno.EACCES)

def parseapacheindex(index):
    files_and_folders = [x for x in re.findall(r'<tr>.*?alt="([^"]+)".*?<td><a href="[^"]+">([^<]+).*?<td[^>]*>([^<&]*).*?<td[^>]*>([0-9.KMG]*)', index, re.MULTILINE) if x[0] != "[PARENTDIR]"]
    result = []
    for f in files_and_folders:
        print(f)
        st_mode = 33024
        st_nlink = 1
        if (f[0] == "[DIR]"):
            st_mode = S_IFDIR | 0o500
            st_nlink = 2
        dt = now
        if (f[2].strip() != "-" and f[2].strip() != ""):
            dt = int(mktime(parser.parse(f[2].strip()).timetuple()))
        size = 0
        if (f[3].strip() != ""):
            size = tosize(f[3].strip())
        name = f[1].decode('utf-8').encode('utf-8').replace("/","")
        result.append(dict(name=name, attrs=dict(st_mode=st_mode, st_ctime=dt, st_mtime=dt, st_atime=dt, st_nlink=st_nlink, st_size=size)))
    return result

def parsepreindex(index):
    index = re.search(r'<pre>(<a href="../">../|.*">Parent Directory)</a>((\r|\n|.)*)</pre>', index, re.MULTILINE).group(2)
    files_and_folders = [x for x in re.findall(r'<a href="[^"]+">([^<]+)</a> +([a-zA-Z0-9\-: ]*?) {2,}([0-9\-.]*[KGM]?)', index, re.MULTILINE)]
    result = []
    for f in files_and_folders:
        st_mode = 33024
        st_nlink = 1
        if (f[2] == "-" or f[0].endswith("/")):
            st_mode = S_IFDIR | 0o500
            st_nlink = 2
        dt = now
        if (f[1].strip() != "-" and f[1].strip() != ""):
            dt = int(mktime(parser.parse(f[1].strip()).timetuple()))
        size = 0
        if (f[2].strip() != '' and f[2].strip() != '-'):
            size = tosize(f[2].strip())
        name = f[0].decode('utf-8').encode('utf-8').replace("/","")
        result.append(dict(name=name, attrs=dict(st_mode=st_mode, st_ctime=dt, st_mtime=dt, st_atime=dt, st_nlink=st_nlink, st_size=size)))
    return result

now = time()

class Xxe(LoggingMixIn, Operations):

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
        headers = { 'Range': "bytes=" + str(offset) + "-" + str(offset+size), }
        req = urllib2.Request(self.uri + path, None, headers)
        resp = urllib2.urlopen(req)
        if (resp.getcode() != 206):
            raise FuseOSError(errno.EACCES)
        contl = int(resp.info().getheader('content-length'))
        return resp.read(contl)

    def readdir(self, path, fh):
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

    fuse = FUSE(Xxe(argv[1]), argv[2], foreground=True, nothreads=True)
