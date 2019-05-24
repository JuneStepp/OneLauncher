#!/usr/bin/env python
# coding=utf-8
###########################################################################
# Name:   ProgressMonitor
# Author: Lynx3d
# Date:   19th November 2013
#
# Patching prgress analyzer for the Linux/OS X based launcher
# for the game Lord of the Rings Online
#
# Based on a script by SNy <SNy@bmx-chemnitz.de>
# Python port of PyLotRO by AJackson <ajackson@bcs.org.uk>
#
# (C) 2009 AJackson <ajackson@bcs.org.uk>
#
# This file is part of PyLotRO
#
# PyLotRO is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# PyLotRO is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PyLotRO.  If not, see <http://www.gnu.org/licenses/>.
###########################################################################

import re


class ProgressMonitor:
    def __init__(self, logWindow=None):
        self.uiLog = logWindow
        self._re_filestat = re.compile(
            r'^.*?files to patch: ([\d]+) bytes to download: ([\d]+)')
        self._re_datastat = re.compile(
            r'^.*?data patches: ([\d]+) bytes to download: ([\d]+)')
        self.reset()

    def reset(self):
        self.stateFunc = self.handlePatchMain

        self.fileCount = -1
        self.fileBytes = -1
        self.dataCount = -1
        self.dataBytes = -1
        self.currentLine = ''
        self.currentPos = 0
        self.currentFileNum = 0
        self.currentIterNum = 0
        self._fileTotalDots = 0
        self._fileDots = 0
        self._dataTotalDots = 0

        if self.uiLog:
            self.uiLog.progressBar.reset()

    def parseOutput(self, text):
        # split the output in lines
        text_lines = (self.currentLine + text).splitlines()
        linePos = -1
        for line in text_lines:
            if linePos < 0:
                linePos = self.currentPos
            else:
                linePos = 0
            newPos = self.stateFunc(line, linePos)

            # if nothing is returned, assume the whole line has been parsed or discarded
            if newPos:
                linePos = newPos
            else:
                linePos = len(line)
            #print(line, linePos)

        # copy current line to buffer unless input ends with newline char
        if text[-1] == '\n':
            self.currentLine = ''
            self.currentPos = 0
        else:
            self.currentLine = text_lines[-1]
            self.currentPos = linePos

    def handlePatchMain(self, text, offset):
        res = self._re_filestat.match(text)
        if res:
            # file patching is checked again before data patching starts, don't overwrite
            if self.fileCount < 0:
                self.fileCount = int(res.group(1))
                self.fileBytes = int(res.group(2))
                #print("Files: %d, Bytes: %d"%(self.fileCount, self.fileBytes))
                if self.uiLog and self.fileCount > 1:
                    self.uiLog.progressBar.setMaximum(self.fileCount)
                    self.uiLog.progressBar.setValue(0)
            self.stateFunc = self.handlePatchFiles

        res = self._re_datastat.match(text)
        if res:
            self.dataCount = int(res.group(1))
            self.dataBytes = int(res.group(2))
            #print("Iterations: %d, Bytes: %d"%(self.dataCount, self.dataBytes))
            if self.uiLog and self.dataCount > 1:
                self.uiLog.progressBar.setMaximum(self.dataCount)
                self.uiLog.progressBar.setValue(0)
            self.stateFunc = self.handlePatchData

    def handlePatchFiles(self, text, offset):
        if text.startswith('Downloading '):
            self.currentFileNum += 1
            filename = text.split()[1].strip('.')
            #print('Downloading %s (%d/%d)'%(filename, self.currentFileNum, self.fileCount))
            pos = len('Downloading ') + len(filename)
            #print('text[%d] = %s'%(pos, text[pos]))
            self.stateFunc = self.handleFileDownload
            return self.stateFunc(text, pos)

        elif text.startswith('File patching complete'):
            self.stateFunc = self.handlePatchMain

    def handlePatchData(self, text, offset):
        if text.startswith('Downloading '):
            self.currentIterNum += 1
            filename = text.split()[1].strip('.')
            #print('Patching %s (%d/%d)'%(filename, self.currentIterNum, self.dataCount))
            pos = len('Downloading ') + len(filename)
            #print('text[%d] = %s'%(pos, text[pos]))
            self.stateFunc = self.handleDataDownload
            return self.stateFunc(text, pos)

        elif text.startswith('Data patching complete'):
            self.stateFunc = self.handlePatchMain

    def handleFileDownload(self, text, offset):
        idx = offset
        while idx < len(text):
            if text[idx] == '.':
                self._fileTotalDots += 1
                self._fileDots += 1
            else:
                self.stateFunc = self.handlePatchFiles
                if self.uiLog:
                    self.uiLog.progressBar.setValue(self.currentFileNum)
                # print('%d dots' % self._fileDots)
                self._fileDots = 0
                return self.stateFunc(text, idx)
            idx += 1

        return idx

    def handleDataDownload(self, text, offset):
        idx = offset
        while idx < len(text):
            if text[idx] == '.':
                self._dataTotalDots += 1
                #self._fileDots += 1
            else:
                self.stateFunc = self.handlePatchData
                if self.uiLog:
                    self.uiLog.progressBar.setValue(self.currentIterNum)
                return self.stateFunc(text, idx)
                #print('%d dots' % self._fileDots)
                #self._fileDots = 0
            idx += 1

        return idx
