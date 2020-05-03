#!/usr/bin/env python2

from stat import S_ISDIR,ST_MODE,S_ISREG
from os import getcwd,listdir,lstat,path
from sys import argv,exit
from operator import itemgetter
from argparse import ArgumentParser

usage = """Inode counter -- use this to find subfolders using excessive inodes.
If any directory contains 5% or more of total calculated inodes, it will be shown.
If any subdirectories contain 10% or more, they will be shown."""

parser = ArgumentParser(description=usage)
parser.add_argument("-p", "--path", dest='target', help='Path to start the search')
target = parser.parse_args().target

if not target:#target is optional, if not given setting target to current working directory
    target=getcwd()

if path.isfile(target):
    print target + " is a file not a directory"
    exit(2)


try: 
    listdir(target)
except OSError:
    print "Could not open " + target
    exit(2)


directories = []
table = []
tl = []
current_dir_id = 1
parent_dir_id = 0
total=0
account_total=0

    
for f in listdir(target):
    pathname = path.join(target, f)
    mode = lstat(pathname)[ST_MODE]

    if S_ISDIR(mode):
        directories.append([current_dir_id,0,pathname])
        current_dir_id += 1
        account_total += 1
    elif S_ISREG(mode):
        account_total += 1


#This loop treats 'directories' as a stack containing a list of directories that have yet
#to be scanned for inode count.  The for loop counts inodes for the currently investigated
#directory.  table at the end of this loop contains the unique id for the directory,
#the id of its parent, path of directory, and inode count for that
#directory(not including suddirs yet)
while(len(directories) > 0): #keep going while directories haven't been processed
    new_parent_dir_id,parent_dir_id,dir=directories.pop()
    count = 0
    for f in listdir(dir):
        pathname = path.join(dir, f)
        mode = lstat(pathname)[ST_MODE]
        if S_ISDIR(mode):
            directories.append([current_dir_id,new_parent_dir_id,pathname])
            current_dir_id += 1
            count += 1
        elif S_ISREG(mode):
            count += 1
    table.append([new_parent_dir_id,parent_dir_id,dir,count])
    
#Print out directories with a disproportionate amount of inodes.
for i in range(len(table)):
    account_total += table[i][3]
print 'Total inodes is:', account_total
table = sorted(table, key=itemgetter(3), reverse=True)
count=0

if len(table) == 0:
    print 'Um, no subdirectories?'
    exit(0)
elif table[count][3]>0.05*account_total:
    print "\n-------Directories with a large number of file/directories-------"

while (count<len(table) and table[count][3]>0.05*account_total):
    S = '%2.1f%%'%(float(table[count][3])/account_total*100)
    print table[count][2],table[count][3],S
    count+=1

if count==0:
    print "\n------------!!No large inode using directories found!!-----------"


table = sorted(table, key=itemgetter(1))
parent_dir_id = table[len(table)-1][1]

#Now taking that table utilizing the directory ids to sum up inodes of suddirs to parent
#inodes.  When the number of inodes exceed some limit store that path for display later.
#Continue on until table is completely processed.
#Note: I reused the directories list to store final output.  It was empty after above loop.

#The order of table doesn't change in the following loop. Using this static list is about
#6x faster than generating it every time when the initial table is large.
static_list=[]
for x in table:
    static_list.append(x[0])


#Copying the initial self-contained inodes count to a second column.
#Going to decrement table[3] when reporting inodes by the amount reported.
#table[3] is also used for the reporting limit.
#This significantly reduces the amount of directories reported
for i in range(len(table)):
    table[i].append(table[i][3])

limit = account_total/10 #report directories that contain more the 10% of total.
print "\n---Locating directories holding more than 10% of total inodes----"
while (len(table) > 0):
    inspect = table.pop()
    static_list.pop()
    if inspect[1] == 0:
        tl.append([inspect[2],inspect[4]])
    if inspect[3] >= limit:
        directories.append([inspect[2],inspect[3],inspect[4]]) #storing for later report
        if inspect[1] != 0:#can't update the parent of the starting directory
            index=static_list.index(inspect[1])#find location of parent
            table[index][3] -= inspect[3]#decrement inode count by amount of reported dir.
    if inspect[3] != inspect[4]:#this directory has reported subdirs
        if inspect[1] != 0:
            index=static_list.index(inspect[1])
            table[index][3] -= (inspect[4]-inspect[3])#passing up the reported amount
    if inspect[1] == parent_dir_id:
        total += inspect[4]
    if len(table)>0: #hate this logic, but duplicate code more.
        if table[len(table)-1][1] != parent_dir_id:
            index=static_list.index(parent_dir_id)
            table[index][3] += total
            table[index][4] += total
            total=0
            parent_dir_id=table[len(table)-1][1]

exception = False

#yay. print out the final results
directories = sorted(directories, key=itemgetter(0), reverse=True)
if len(directories)==0:
    print "Wow!! I didn't find anything to report. Must be a lot of folders here"

while (len(directories) > 0):
    item = directories.pop()
    if item[1] == item[2]:
        print item[0],item[1]
    else:
        exception = True
        print item[0],item[1],item[2]

if (exception):
    print '\nNOTE: The above lines with two numbers are excluding and including the already reported subdirs inode count'

tl = sorted(tl, key=itemgetter(1))
count = 0
print "\n-----Largest inode usage directories at the script's target-----"
while (len(tl) > 0 and count < 20):
    item = tl.pop()
    print item[0],item[1]
    count += 1
