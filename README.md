# inodes
python scripts to find inode hogs

This was written while I was at HostGator. It was published on their repository, so I have seen the output printed elsewhere. My shift lead at the time, Sam Foster, contributed a small bit of cleanup. It was written almost entirely exclusively in my off time. I was trying to come up with much better response than something like

```
for i in `find . -mindepth 1 -maxdepth 1 -type d`; do echo -n "$i " && find $i | wc -l; done | sort -k2 -nr | head
```

, cd into directory, and repeat could produce. First thing it attempts to print is any directory contains 5% or more of the total inodes below the search path. Second print any directories including sub directories which contain 10% or more will be shown. The last thing printed is basically the same thing as the for loop above.

Usage help from python3.6+ version of script.

```
usage: inodes3.py [-h] [-p TARGET] [-s SINGLE] [-a AMASSED]

Inode counter -- use this to find subfolders using excessive inodes. If any
single directory contains 5%(default) or more of total calculated inodes, it
will be shown. If any directory including its subdirectories contain
10%(default) or more, they will be shown.

optional arguments:
  -h, --help            show this help message and exit
  -p TARGET, --path TARGET
                        Path to start the search
  -s SINGLE, --single SINGLE
                        Report any single directory holding more than this,
                        default is 5%, %optional
  -a AMASSED, --amassed AMASSED
                        Report any directory when including it's
                        subdirectories is holding more than this, default is
                        10%, %optional
```

Sample output:

```
Total inodes is: 11942

-------Directories with a large number of file/directories-------
/home/jhouze/.cache/mozilla/firefox/h9tdth8d.default-default/cache2/entries 1429 12.0%
/home/jhouze/.cache/google-chrome/Default/Cache 847 7.1%
/home/jhouze/.config/google-chrome/Default/Extensions/hdokiejnpimakedhajhdlcegeplioahd/4.44.0.1_0 609 5.1%

---Locating directories holding more than 10% of total inodes----
/home/jhouze/.cache 1227 2656
/home/jhouze/.cache/mozilla/firefox/h9tdth8d.default-default/cache2/entries 1429
/home/jhouze/.config/google-chrome/Default/Extensions 1371 2911
/home/jhouze/.config/google-chrome/Default/Extensions/hdokiejnpimakedhajhdlcegeplioahd/4.44.0.1_0 1540
/home/jhouze/aws 1195 5138
/home/jhouze/aws/dist/awscli/examples 3943

NOTE: The above lines with two numbers are excluding and including the already reported subdirs inode count

-----Largest inode usage directories at the script's target-----
/home/jhouze/aws 5138
/home/jhouze/.config 3452
/home/jhouze/.cache 2656
/home/jhouze/Desktop 306
/home/jhouze/.mozilla 177
/home/jhouze/.local 104
/home/jhouze/roles 19
/home/jhouze/test 16
```

Without any further ado, the code with python2 and python3 syntax are over at my [github](https://github.com/jhouze/inodes). The python 2 version is less feature complete.