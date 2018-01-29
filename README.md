DirList
-------

A fuse file system driver for mounting nginx and apache directory indexes as folders.

## How to use


### With vagrant

Prerequisites: vagrant + virtualbox/vmware

```
git clone https://github.com/eoftedal/dirlist.git
cd dirlist
vagrant up
vagrant ssh
sudo bash

nohup python dirlist.py <uri> mount 2>&1 > nohup.out &

cd mount
ls
```

### With docker

Prerequisites: docker installed and running

```
git clone https://github.com/eoftedal/dirlist.git
cd dirlist
docker build . -t dirlist
docker run --device=/dev/fuse --cap-add SYS_ADMIN -i -t -v $(pwd):/app/dirlist dirlist /bin/bash
nohup python dirlist.py <uri> mount 2>&1 > nohup.out &

cd mount
ls
```

### Without vagrant or docker

Prequisites:
* Install `python`, `python-pip` and `libfuse2` (with `apt-get` or similar)

```
git clone https://github.com/eoftedal/dirlist.git
cd dirlist
pip install fusepy
pip install python-dateutil
mkdir mount

nohup python dirlist.py <uri> mount 2>&1 > nohup.out &

cd mount
ls
```


## Example:

```
root@minimal-xenial:~# ls -l mount/
total 0
root@minimal-xenial:~# nohup python dirlist.py https://nginx.org/packages/ mount 2>&1 > nohup.out &
[1] 3199
root@minimal-xenial:~# ls -l mount/
total 0
dr-x------ 2 root root 0 Dec  1  2011 aix
dr-x------ 2 root root 0 Sep 22  2011 centos
dr-x------ 2 root root 0 Mar 23  2012 debian
dr-x------ 2 root root 0 Dec 15  2011 keys
dr-x------ 2 root root 0 Mar 27  2013 mainline
dr-x------ 2 root root 0 May 26  2015 old
dr-x------ 2 root root 0 Mar 15  2012 opensuse
dr-x------ 2 root root 0 Oct 14  2011 rhel
dr-x------ 2 root root 0 Nov 21  2014 sles
dr-x------ 2 root root 0 Mar 23  2012 ubuntu
root@minimal-xenial:~#
```
![demo](demo.gif)
