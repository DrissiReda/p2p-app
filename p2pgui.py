#!/usr/bin/python

# p2pgui.py

"""
Module implementing simple a simple p2p network.
"""

import os
import sys
import threading

from Tkinter import *
from random import *

from p2pfiler import *


class P2PGui(Frame):
    def __init__(self, firstpeer, hops=2, maxpeers=5, serverport=5678, master=None):
        Frame.__init__(self, master)
        self.grid()
        self.createWidgets()
        self.master.title("G4 P2P GUI port:%d" % serverport)
        self.p2peer = FilerPeer(maxpeers, serverport)

        self.bind("<Destroy>", self.__onDestroy)

        host, port = firstpeer.split(':')
        self.p2peer.buildpeers(host, int(port), hops=hops)
        self.updatePeerList()

        t = threading.Thread(target=self.p2peer.mainloop, args=[])
        t.start()

        self.p2peer.startstabilizer(self.p2peer.checklivepeers, 3)
#      self.p2peer.startstabilizer( self.onRefresh, 3 )
        self.after(3000, self.onTimer)

    def onTimer(self):
        self.onRefresh()
        self.after(3000, self.onTimer)
        # self.after_idle( self.onTimer )

    def __onDestroy(self, event):
        self.p2peer.shutdown = True

    def updatePeerList(self):
        if self.peerList.size() > 0:
            self.peerList.delete(0, self.peerList.size() - 1)
        for p in self.p2peer.getpeerids():
            self.peerList.insert(END, p)

    def updateFileList(self):
        if self.fileList.size() > 0:
            self.fileList.delete(0, self.fileList.size() - 1)
        for f in self.p2peer.files:
            p = self.p2peer.files[f]
            if p is not None:
                if not p[1]:
                    p[1] = '(local)'

            self.fileList.insert(END, "%s:%s" % (f, '(local)' if p is None else "%s" % p[1]))

    def createWidgets(self):
        """
        Set up the frame widgets
        """
        fileFrame = Frame(self)
        peerFrame = Frame(self)

        rebuildFrame = Frame(self)
        searchFrame = Frame(self)
        addfileFrame = Frame(self)
        getinfoFrame = Frame(self)
        pbFrame = Frame(self)

        fileFrame.grid(row=0, column=0, sticky=N+S)
        peerFrame.grid(row=0, column=1, sticky=N+S)
        pbFrame.grid(row=2, column=1)
        addfileFrame.grid(row=2)
        searchFrame.grid(row=3)
        rebuildFrame.grid(row=3, column=1)

        Label(fileFrame, text='Available Files').grid()
        Label(peerFrame, text='Peer List').grid()

        fileListFrame = Frame(fileFrame)
        fileListFrame.grid(row=1, column=0)
        fileScroll = Scrollbar(fileListFrame, orient=VERTICAL)
        fileScroll.grid(row=0, column=4, sticky=N+S+E+W)

        self.fileList = Listbox(fileListFrame, height=20, width=100,
                                yscrollcommand=fileScroll.set)
        # self.fileList.insert( END, 'a', 'b', 'c', 'd', 'e', 'f', 'g' )
        self.fileList.grid(row=0, column=0, columnspan= 4, sticky=N+S+E+W)
        fileScroll["command"] = self.fileList.yview

        self.fetchButton = Button(addfileFrame, text='Download',
                                  command=self.onFetch)
        self.addfileButton = Button(addfileFrame, text='Populate',
                                    command=self.onPopulate)
        self.delfileButton = Button(addfileFrame, text='Delete',
                                    command=self.onDelete)
        self.infofileButton = Button(addfileFrame, text='Info',
                                    command=self.onInfo)
        self.fetchButton.grid(row=0, column=0)
        self.addfileButton.grid(row=0, column=1)
        self.delfileButton.grid(row=0, column=2)
        self.infofileButton.grid(row=0, column=3)

        self.searchEntry = Entry(searchFrame, width=150)
        self.searchButton = Button(searchFrame, text='Search',
                                   command=self.onSearch)
        self.searchEntry.grid(row=0, column=0)
        self.searchButton.grid(row=0, column=1)

        peerListFrame = Frame(peerFrame)
        peerListFrame.grid(row=1, column=0)
        peerScroll = Scrollbar(peerListFrame, orient=VERTICAL)
        peerScroll.grid(row=0, column=1, sticky=N+S)

        self.peerList = Listbox(peerListFrame, height=20, width=30,
                                yscrollcommand=peerScroll.set)
        # self.peerList.insert( END, '1', '2', '3', '4', '5', '6' )
        self.peerList.grid(row=0, column=0, sticky=N+S)
        peerScroll["command"] = self.peerList.yview

        self.removeButton = Button(pbFrame, text='Unregister',
                                   command=self.onRemove)
        self.refreshButton = Button(pbFrame, text='Refresh',
                                    command=self.onRefresh)

        self.rebuildEntry = Entry(rebuildFrame, width=150)
        self.rebuildButton = Button(rebuildFrame, text='Register',
                                    command=self.onRebuild)
        self.removeButton.grid(row=0, column=0)
        self.refreshButton.grid(row=0, column=1)
        self.rebuildEntry.grid(row=0, column=0)
        self.rebuildButton.grid(row=0, column=1)

        # print "Done"

    def onPopulate(self):
        for file in os.listdir('.'):
            self.onAdd(file)

    def onAdd(self, file):
        # file = self.addfileEntry.get()
        if file.lstrip().rstrip():
            filename = file.lstrip().rstrip()
            self.p2peer.addlocalfile(filename, humansize(os.path.getsize(filename)))
        # self.addfileEntry.delete( 0, len(file) )

    def onSearch(self):
        key = self.searchEntry.get()
        self.searchEntry.delete(0, len(key))

        for p in self.p2peer.getpeerids():
            self.p2peer.sendtopeer(p,
                                   QUERY, "%s %s 4" % (self.p2peer.myid, key))

    def onFetch(self):
        sels = self.fileList.curselection()
        if len(sels) == 1:
            sel = self.fileList.get(sels[0]).split(':')
            if len(sel) > 2:  # fname:host:port
                fname, host, port = sel
                sel[1] = sel[1][1:]
                sel[2] = sel[2][:-1]
                print(sel)
                resp = self.p2peer.connectandsend(host[1:], port[:-1], FILEGET, fname)
                print(resp)
                if len(resp) and resp[0][0] == REPLY:
                    fd = file(fname, 'w')
                    fd.write(resp[0][1])
                    fd.close()
                    self.p2peer.files[fname] = None  # because it's local now

    def onDelete(self):
        sels = self.fileList.curselection()
        if len(sels) == 1:
            sel = self.fileList.get(sels[0]).split(':')
            if len(sel) > 2: # fname:host:port means remote
                print("Dude, leave people's files alone")
            else:
                self.p2peer.dellocalfile(sel[0])

    def onInfo(self):
        sels = self.fileList.curselection()
        if len(sels) == 1:
            sel = self.fileList.get(sels[0]).split(':')
            if len(sel) <= 3:
                text="File :"+sel[0]+" is \nsize :"+self.p2peer.files[sel[0]][0]
                toplevel = Toplevel()
                toplevel.title(sel[0]+" Properties")
                label1 = Label(toplevel, text=text, height=5, width=25)
                label1.pack()
                toplevel.focus_force()

    def onRemove(self):
        sels = self.peerList.curselection()
        if len(sels) == 1:
            peerid = self.peerList.get(sels[0])
            self.p2peer.sendtopeer(peerid, PEERQUIT, self.p2peer.myid)
            self.p2peer.removepeer(peerid)

    def onRefresh(self):
        self.updatePeerList()
        self.updateFileList()

    def onRebuild(self):
        if not self.p2peer.maxpeersreached():
            peerid = self.rebuildEntry.get()
            self.rebuildEntry.delete(0, len(peerid))
            peerid = peerid.lstrip().rstrip()
            try:
                host, port = peerid.split(':')
                # print "doing rebuild", peerid, host, port
                self.p2peer.buildpeers(host, port, hops=3)
            except:
                if self.p2peer.debug:
                    traceback.print_exc()
#         for peerid in self.p2peer.getpeerids():
#            host,port = self.p2peer.getpeer( peerid )

suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
def humansize(nbytes):
    i = 0
    while nbytes >= 1024 and i < len(suffixes)-1:
        nbytes /= 1024.
        i += 1
    f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
    return '%s %s' % (f, suffixes[i])
def main():
    if len(sys.argv) < 4:
        print ("Syntax: %s server-port max-peers peer-ip:port" % sys.argv[0])
        sys.exit(-1)

    serverport = int(sys.argv[1])
    maxpeers = sys.argv[2]
    peerid = sys.argv[3]
    app = P2PGui(firstpeer=peerid, maxpeers=maxpeers, serverport=serverport)
    app.mainloop()


# setup and run app
if __name__ == '__main__':
    main()
