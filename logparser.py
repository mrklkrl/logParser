# ***********************************************************************************************
# Log Parser
# Filename : logparser.py
# Author: Mike Cole
# Description : This script looks at all .log files in a specified directory and outputs a single
#               .csv file that maps them to a single timeline. 
# 
# Dependencies: python 2.7
# Usage : python logparser.py path/to/logfile/directory
# 
# It accepts log files of the following form. designed to be used with "serial" logging app
#
# ---------- 2019-11-20 20:02:00 -0600: Logging Started ----------
#
# 11-20 20:56:16.443: 00:58:44: log text ...
# 11-20 22:43:21.167: 02:45:48: more log text...
#
# ***********************************************************************************************

import glob
import os
import csv
import sys
import datetime
import threading

##################################################################################

def createCSV(columns, timestamps, csvFileName):
    with open (csvFileName, 'w+') as csvfile:
        csvwriter = csv.writer(csvfile)

        for i in range(len(timestamps) + 1):
            row = []
            if(i != 0):
                row.append(timestamps[i - 1])
            else:
                # the first row is headers only and "timestamps" is the first column
                row.append("timestamps")
            for column in columns:
                row.append(column[i])
            csvwriter.writerow(row)

##################################################################################

# checks to see if beginning of line matches format DD-MM HH:MM:SS.MSX TODO: replace with strptime()
def getDateTime(line):
    if(line.strip()):
        time = line.split(' ')[1]
        if(len(time.split(":")) == 4):
            hour = time.split(":")[0]
            minute = time.split(":")[1]
            second = time.split(":")[2].split(".")[0]
            microsecond = time.split(":")[2].split(".")[1]
            if(datetime.time(int(hour), int(minute), int(second), int(microsecond))):
                stamp = line.split(' ')[0] + " " + line.split(' ')[1]
                return stamp
            else:
                return 0
        else:
            return 0

##################################################################################
    
def getTimestamps(logFilePaths):
    timestamps = []
    # parse files to get timestamps
    for logFilePath in logFilePaths:
        logFile = open(logFilePath, 'r')
        lines = logFile.readlines()
        for line in lines:     
            stamp = getDateTime(line)
            # append all valid timestamps to the array
            if(stamp != 0 and stamp != None):
                timestamps.append(stamp)
        logFile.close()
    
    # remove duplicate timestamps and sort
    timestamps = list(dict.fromkeys(timestamps))
    timestamps.sort()
    
    return timestamps

##################################################################################

def constructAndAppendColumnToList(logFilePath, timestamps, columns, header):
    column = []
    logFile = open(logFilePath, "r")
    lines = logFile.readlines()
    dex = 0
    for line in lines:
        line = line.replace('\n',"")
        lines[dex] = line
        dex += 1

    # the top of each column has the filename. parse out any parent directories
    column.append(header.split("/")[-1])

    # zero the row
    for stamp in timestamps:
        column.append("")
    
    # find the index of the corresponding timestamp for each line in the file
    for i in range(len(column) - 1):
        if(i < len(lines)):
            line = lines[i]
            if line != '':
                try:
                    stamp = getDateTime(line)
                    index = timestamps.index(stamp)
                    if(column[index + 1] != ''):
                        column[index + 1] = column[index + 1] + " ~~ " + line
                    else:
                        column.insert(index + 1, line)
                except ValueError:
                    column[i + 1] = line
                    pass
    logFile.close()
 
    # pretty sure lists are threadsafe, but lock em just to be sure
    lock = threading.Lock()
    lock.acquire()
    columns.append(column)
    lock.release()

##################################################################################

def getColumns(logFilePaths, timestamps):
    columns = []
    threads = []
    
    # parse files in parallel
    i = 0
    for logFilePath in logFilePaths:
        threadName = logFilePath
        threads.append(threading.Thread(target=constructAndAppendColumnToList, name=threadName, args=(logFilePath, timestamps, columns, threadName)))
        i += 1
    
    for thread in threads:
        thread.start()
    # synchronizes threads
    for thread in threads:
        thread.join()
    return columns

##################################################################################

def parseLogs(logFilePaths, csvFileName):
    timestamps = getTimestamps(logFilePaths)
    columns = getColumns(logFilePaths, timestamps)
    createCSV(columns, timestamps, csvFileName)

##################################################################################

def main ():
    # default logfile base path and csv file name
    logFileBasePath = ""
    csvFileName = "Log.csv"

    # parsing command line args
    numArgs = len (sys.argv) - 1
    if(numArgs == 0):
        print ("ERROR: You must specify the path to a directory of logfiles")
        return
    elif(numArgs > 1):
        print ("ERROR: Too many arguments")
        return
    else:
        # appending slash to path if not already there
        arg = sys.argv[1]
        if(arg[len (arg) - 1] != "/"):
            arg = arg + "/"
        logFileBasePath = arg

        # csv file will be placed adjacent to the logs, and will be named the name of its containing folder
        csvFileName = logFileBasePath + os.path.splitext (os.path.basename (os.path.dirname (logFileBasePath)))[0] + ".csv"
        
    logFilePaths = glob.glob (logFileBasePath + "*.log")
    if(len (logFilePaths) == 0):
        print ("ERROR: No logfiles found at: ", logFileBasePath)
        return
    else:
        parseLogs(logFilePaths, csvFileName )

main ()