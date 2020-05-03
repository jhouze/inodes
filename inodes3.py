#!/usr/bin/env python3

from stat import S_ISDIR,ST_MODE,S_ISREG
from os import getcwd,listdir,lstat,path
from sys import argv,exit
from operator import itemgetter
from argparse import ArgumentParser

directories = []
table = []
tl = []
current_dir_id = 1
parent_dir_id = 0
total=0
account_total=0


usage = """Inode counter -- use this to find subfolders using excessive inodes.
If any single directory contains 5%(default) or more of total calculated inodes, it will be shown.
If any directory including its subdirectories contain 10%(default) or more, they will be shown."""

parser = ArgumentParser(description=usage)
parser.add_argument("-p", "--path", dest='target', default=getcwd(), help='Path to start the search') #using dest='path' would conflict with the os.path import, d'oh.
parser.add_argument("-s", "--single", dest='single', default='5', help="Report any single diretory holding more than this, default is 5%%, %%optional")
parser.add_argument("-a", "--amassed", dest='amassed', default='10', help="Report any directory when including it's subdirectories is holding more than this, default is 10%%, %%optional")

target = parser.parse_args().target
single = float(parser.parse_args().single.strip('%'))
amassed = float(parser.parse_args().amassed.strip('%'))

if single < 0.5:
    exit("Refusing to accept less than 0.5% for single argument")
elif single >= 99.999:
    exit("Lower the single argument vaule")
else:
    single=single/100

if amassed < 1.0:
    exit("Refusing to accept less than 1.0% for amassed argument")
elif amassed >= 99.999:
    exit("Lower the amassed argument vaule")
else:
    amassed=amassed/100


if path.isfile(target):
    print(f"{target} is a file not a directory")
    exit(2)

try: 
    listdir(target)
except OSError:
    print(f"Could not open {target}")
    exit(2)
    
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
#to be scaned for inode count.  The for loop counts inodes for the currently investigated
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
print(f"Total inodes is: {account_total}")
table = sorted(table, key=itemgetter(3), reverse=True)
count=0

if len(table) == 0:
    print('Um, no subdirectories?')
    exit(0)
elif table[count][3]>single*account_total:
    print(f"\n-------Directories with more than {single*100:.2f}% of total calculated inodes.-------")

while (count<len(table) and table[count][3]>single*account_total):
    S = '%2.1f%%'%(float(table[count][3])/account_total*100)
    print(table[count][2],table[count][3],S)
    count+=1

if count==0:
    print("\n------------!!No large inode using directories found!!-----------")


table = sorted(table, key=itemgetter(1))
parent_dir_id = table[len(table)-1][1]

#Now taking that table utilising the directory ids to sum up inodes of suddirs to parent
#inodes.  When the number of inodes exceed some limit store that path for display later.
#Continue on until table is completly processed.
#Note: I reused the directories list to store final output.  It was empty after above loop.

#The order of table doesn't change in the following loop. Using this static list is about
#6x faster than generating it every time when the initial table is large.
static_list=[]
for x in table:
    static_list.append(x[0])


#Copying the initial self contained inodes count to a second column.
#Going to decrement table[3] when reporting inodes by the amount reported.
#table[3] is also used for the reporting limit.
#This significantly reduces the amount of directories reported
for i in range(len(table)):
    table[i].append(table[i][3])

limit = account_total*amassed #report direcories that contain more the 10% of total.
print(f"\n---Locating directories holding more than {amassed*100:.2f}% of total inodes----")
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
    print("Wow!! I didn't find anything to report. Try lowering amassed argument")

while (len(directories) > 0):
    item = directories.pop()
    if item[1] == item[2]:
        S = '%2.1f%%'%(float(item[1])/account_total*100)
        print(item[0],item[1],S)
    else:
        exception = True
        S = '%2.1f%%'%(float(item[1])/account_total*100)
        T = '%2.1f%%'%(float(item[2])/account_total*100)
        print(f"{item[0]} ({item[1]} {S}) ({item[2]} {T})")
        
if (exception):
    print('\nNOTE: The above lines with two (value %) are excluding and including the already reported subdirs inode count')

tl = sorted(tl, key=itemgetter(1))
count = 0
print("\n-----Largest inode usage directories at the script's target-----")
while (len(tl) > 0 and count < 10):
    item = tl.pop()
    print(item[0],item[1])
    count += 1
