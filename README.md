DirList
-------

A fuse file system driver for mounting nginx and apache directory indexes as folders.

How to use
----------

Prerequisites: vagrant + virtualbox/vmware

```
git clone https://github.com/eoftedal/dirlist.git
cd dirlist
vagrant up
vagrant ssh
sudo bash

nohup python dirlist.py https://nginx.org/packages/ mount 2>&1 > nohup.out &

cd mount
ls
```
