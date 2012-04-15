from PyQt4 import QtGui
from superficie.nodes.arrow import Arrow
from superficie.nodes.line import Line

from superficie.viewer.MinimalViewer import MinimalViewer

if __name__ == "__main__":
    import sys


    x = [(0,0,0),(1,0,0)]
    y = [(0,0,0),(0,1,0)]
    z = [(0,0,0),(0,0,1)]
    lx = Line(x, width=5).setColor((1,0,0))
    ly = Line(y, width=7).setColor((0,1,0))
    lz = Line(z, width=5).setColor((0,0,1))

    ob = Arrow((0,.05,0),(1,.05,0))
    ob.toText()
    ob2 = Arrow(*y).setWidthFactor(.5)
    ob3 = Arrow(*z)

    app = QtGui.QApplication(sys.argv)
    viewer = MinimalViewer()
    viewer.root.addChild(ob.root)
    viewer.root.addChild(ob2.root)
    viewer.root.addChild(ob3.root)
    viewer.root.addChild(lx.root)
    viewer.root.addChild(ly.root)
    viewer.root.addChild(lz.root)

    viewer.resize(400, 400)
    viewer.show()
    viewer.viewAll()

    sys.exit(app.exec_())
