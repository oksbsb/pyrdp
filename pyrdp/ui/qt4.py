#
# Copyright (c) 2014-2015 Sylvain Peyrefitte
# Copyright (c) 2018 GoSecure Inc.
#
# This file is part of rdpy.
#
# rdpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#

"""
Qt specific code

QRemoteDesktop is a widget use for render in rdpy
"""
from io import BytesIO

import rle
from PyQt4 import QtGui
from PyQt4.QtCore import QPoint
from PyQt4.QtGui import QColor

from pyrdp.logging import log


def RDPBitmapToQtImage(width, height, bitsPerPixel, isCompressed, data):
    """
    @summary: Bitmap transformation to Qt object
    @param width: width of bitmap
    @param height: height of bitmap
    @param bitsPerPixel: number of bit per pixel
    @param isCompressed: use RLE compression
    @param data: bitmap data
    """
    image = None
    #allocate
    
    if bitsPerPixel == 15:
        if isCompressed:
            buf = bytearray(width * height * 2)
            rle.bitmap_decompress(buf, width, height, data, 2)
            image = QtGui.QImage(buf, width, height, QtGui.QImage.Format_RGB555)
        else:
            image = QtGui.QImage(data, width, height, QtGui.QImage.Format_RGB555).transformed(QtGui.QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
    
    elif bitsPerPixel == 16:
        if isCompressed:
            buf = bytearray(width * height * 2)
            rle.bitmap_decompress(buf, width, height, data, 2)
            image = QtGui.QImage(buf, width, height, QtGui.QImage.Format_RGB16)
        else:
            image = QtGui.QImage(data, width, height, QtGui.QImage.Format_RGB16).transformed(QtGui.QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
    
    elif bitsPerPixel == 24:
        if isCompressed:
            buf = bytearray(width * height * 3)
            rle.bitmap_decompress(buf, width, height, data, 3)

            # This is a ugly patch because there is a bug in the 24bpp decompression in rle.c
            # where the red and the blue colors are inverted. Fixing this in python causes a performance
            # issue, but at least it shows the good colors.
            buf2 = BytesIO(buf)
            while buf2.tell() < len(buf2.getvalue()):
                pixel = buf2.read(3)
                buf[buf2.tell() - 3] = pixel[2]
                buf[buf2.tell() - 1] = pixel[0]

            image = QtGui.QImage(buf, width, height, QtGui.QImage.Format_RGB888)
        else:
            image = QtGui.QImage(data, width, height, QtGui.QImage.Format_RGB888).transformed(QtGui.QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
            
    elif bitsPerPixel == 32:
        if isCompressed:
            buf = bytearray(width * height * 4)
            rle.bitmap_decompress(buf, width, height, data, 4)
            image = QtGui.QImage(buf, width, height, QtGui.QImage.Format_RGB32)
        else:
            image = QtGui.QImage(data, width, height, QtGui.QImage.Format_RGB32).transformed(QtGui.QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
    elif bitsPerPixel == 8:
        if isCompressed:
            buf = bytearray(width * height * 1)
            rle.bitmap_decompress(buf, width, height, data, 1)
            buf2 = convert8bppTo16bpp(buf)
            image = QtGui.QImage(buf2, width, height, QtGui.QImage.Format_RGB16)
        else:
            buf2 = convert8bppTo16bpp(data)
            image = QtGui.QImage(buf2, width, height, QtGui.QImage.Format_RGB16).transformed(QtGui.QMatrix(1.0, 0.0, 0.0, -1.0, 0.0, 0.0))
    else:
        log.error("Receive image in bad format")
        image = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
    return image


def convert8bppTo16bpp(buf):
    """
    WARNING: The actual 8bpp images work by using a color palette, which this method does not use.
    This method instead tries to transform indices into colors. This results in a weird looking image,
    but it can still be useful to see whats happening ¯\_(ツ)_/¯
    """
    buf2 = bytearray(len(buf) * 2)
    i = 0
    for pixel in buf:
        r = (pixel & 0b11000000) >> 6
        g = (pixel & 0b00111000) >> 3
        b = (pixel & 0b00000111) >> 0
        buf2[i] = (b << 3)
        buf2[i + 1] = (g << 0) | (r << 5)
        i += 2

    return buf2


class QRemoteDesktop(QtGui.QWidget):
    """
    @summary: Qt display widget
    """
    def __init__(self, width, height):
        """
        @param width: {int} width of widget
        @param height: {int} height of widget
        """
        super(QRemoteDesktop, self).__init__()
        #set correct size
        self.resize(width, height)
        #bind mouse event
        self.setMouseTracking(True)
        #buffer image
        self._buffer = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
        self.mouseX = width / 2
        self.mouseY = height / 2


    def notifyImage(self, x, y, qimage, width, height):
        """
        @summary: Draw an image on the buffer.
        @param x: x position of new image
        @param y: y position of new image
        @param qimage: new QImage
        """
        #fill buffer image
        with QtGui.QPainter(self._buffer) as qp:
            qp.drawImage(x, y, qimage, 0, 0, width, height)
        #force update
        self.update()

    def setMousePosition(self, x, y):
        self.mouseX = x
        self.mouseY = y
        self.update()

    def resize(self, width, height):
        """
        @summary: override resize function
        @param width: {int} width of widget
        @param height: {int} height of widget
        """
        self._buffer = QtGui.QImage(width, height, QtGui.QImage.Format_RGB32)
        QtGui.QWidget.resize(self, width, height)
        
    def paintEvent(self, e):
        """
        @summary: Call when Qt renderer engine estimate that is needed
        @param e: QEvent
        """
        #draw in widget
        with QtGui.QPainter(self) as qp:
            qp.drawImage(0, 0, self._buffer)
            qp.setBrush(QColor.fromRgb(255, 255, 0, 180))
            qp.drawEllipse(QPoint(self.mouseX, self.mouseY), 5, 5)

    def clear(self):
        self._buffer = QtGui.QImage(self._buffer.width(), self._buffer.height(), QtGui.QImage.Format_RGB32)
        self.setMousePosition(self._buffer.width() // 2, self._buffer.height() // 2)
        self.repaint()