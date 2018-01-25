DirList
-------

A fuse file system driver for nginx and apache directory indexes.

How to use
----------

Prerequisites: vagrant + virtualbox/vmware

```
git clone https://github.com/eoftedal/dirlist.git
cd dirlist
vagrant up
vagrant ssh
sudo bash

python dirlist.py https://nginx.org/packages/ mount
```
And then from a second shell:
```
vagrant ssh
sudo bash
cd mount
ls
```
