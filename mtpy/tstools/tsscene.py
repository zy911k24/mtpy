
from PyQt5.QtWidgets import QGraphicsScene

from PyQt5.QtGui import QPixmap

from PyQt5.QtCore import Qt

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvas
import matplotlib.pyplot as plt

from tsdata import TSData
from obspy.core.trace import Trace


class TSScene(QGraphicsScene):
    def __init__(self, width=14, height=12, numofchannel=4):
        super(TSScene, self).__init__()

        # set waveform windows
        figure = Figure()
        figure.set_size_inches(width, height)
        self.graphwidth = figure.dpi * width
        self.canvas = FigureCanvas(figure)
        self.addWidget(self.canvas)
        self.axesavailability = [True for i in range(numofchannel)]
        self.axes = []
        for i in range(numofchannel):
            self.axes.append(figure.add_subplot(str(numofchannel)+'1'+str(i+1)))

        # set backend data model
        self.data = None
        self.visibleWave = {}
        self.starttime = None
        self.endtime = None

        # prepare for user input
        self.downx = None
        self.wheelactive = False

    def setdata(self, filename: str):
        self.data = TSData(filename)

    def getlist(self):
        return self.data.getlist()

    def togglewave(self, wave: str, colorcode:int=0):
        print(self.visibleWave)
        if wave in self.visibleWave:
            axes = self.visibleWave[wave][0]
            lines = self.visibleWave[wave][1]
            self.removewave(axes, lines)
            self.visibleWave.pop(wave, None)
            self.axesavailability[self.axes.index(axes)] = True

        else:
            stream, wavename, starttime, endtime = self.data.getwaveform(wave, self.starttime, self.endtime)
            waveform = stream[0]
            axes, lines = self.displaywave(wavename, waveform)
            if axes is not None:
                self.visibleWave[wave] = (axes, lines, colorcode, starttime, endtime)

    def displaywave(self, wavename: str, waveform: Trace, colorcode: int=None):
        if True not in self.axesavailability:
            return None, None
        else:
            location = self.axesavailability.index(True)
            axes = self.axes[location]
            self.axesavailability[location] = False
            if colorcode is None:
                colorcode = 'C'+str(location%10)

            times = [waveform.meta['starttime']+t for t in waveform.times()]
            lines = axes.plot(times, waveform.data,linestyle="-", label=wavename, color=colorcode)
            axes.legend()
            self.downx = None

            self.canvas.draw()

            self.starttime = waveform.meta['starttime']
            self.endtime = waveform.meta['endtime']


            return axes, lines

    def removewave(self, axes: Axes, lines: Line2D):
        lines.pop(0).remove()
        axes.relim()
        axes.autoscale_view(True, True, True)
        axes.legend()
        self.canvas.draw()

    def timeshift(self, shift):
        shift = (self.endtime-self.starttime)*shift

        starttime = self.starttime + shift
        endtime = self.endtime + shift

        for wave in self.visibleWave:
            if starttime<self.visibleWave[wave][3]:
                starttime = self.starttime
            if endtime>self.visibleWave[wave][4]:
                endtime = self.endtime

        if starttime!=self.starttime and endtime!=self.endtime:
            self.starttime = starttime
            self.endtime = endtime
            tmplist = self.visibleWave.copy()
            for wave in tmplist:
                self.togglewave(wave)
                self.togglewave(wave, tmplist[wave][2])


    def timescale(self, delta):
        shift = (self.endtime - self.starttime) * -delta*0.1

        starttime = self.starttime + shift
        endtime = self.endtime - shift

        print(starttime, endtime,'='*8)

        for wave in self.visibleWave:
            if starttime<self.visibleWave[wave][3]:
                starttime = self.starttime
            if endtime>self.visibleWave[wave][4]:
                endtime = self.endtime

        print(starttime, endtime,'!'*8)

        if endtime-starttime<0.1:
            pass
        elif starttime==self.starttime and endtime==self.endtime:
            pass
        else:
            self.starttime = starttime
            self.endtime = endtime
            tmplist = self.visibleWave.copy()
            for wave in tmplist:
                self.togglewave(wave)
                self.togglewave(wave, tmplist[wave][1])

        self.wheelactive = False




    def mousePressEvent(self, event):
        super(TSScene, self).mousePressEvent(event)
        self.downx = event.scenePos().x()


    def mouseMoveEvent(self, event):
        if self.downx is not None:
            self.upx = event.scenePos().x()
            shift = float(self.downx - self.upx) / self.graphwidth
            self.timeshift(shift)
            self.downx=self.upx

    def mouseReleaseEvent(self, event):
        super(TSScene, self).mousePressEvent(event)
        self.downx = None

    def wheelEvent(self, event):
        super(TSScene, self).wheelEvent(event)

        delta = -event.delta() / 8 / 15

        if self.wheelactive==False:
            self.wheelactive = True
            self.timescale(delta)




    def exportwaveform(self, wavename, filename):
        print(wavename)
        print(list(self.visibleWave))
        if wavename in self.visibleWave:
            wave = self.visibleWave[wavename][0]
            stream = self.data.getwaveform(wave, self.starttime, self.endtime)
            print(type(stream),'type of stream')
            stream.write(filename+".mseed", format='MSEED', encoding=3, reclen=256)
        else:
            pass

