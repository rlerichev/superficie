#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pivy.coin import *
try:
    from pivy.quarter import QuarterWidget
    Quarter = True
except ImportError:
    from pivy.gui.soqt import *
    Quarter = False


from PyQt4 import QtGui, QtCore, uic
from types import FunctionType
from random import random
import operator
from util import partial,  conecta, intervalPartition, Range, malla, wrap
from base import GraphicObject
from gui import Slider
from Equation import createVars
import logging
## TODO: el código necesita averiguar qué símbolos están definidos
## en el bloque que llama a *Plot3D, para que este código
## use las funciones ya definidas, y no tener que definirlas aquí
from math import *



log = logging.getLogger("Mesh")
log.setLevel(logging.DEBUG)

def bindFreeVariables(func, dvals={}):
    dvals.update(globals())
    f = FunctionType(func.func_code, dvals, closure=func.func_closure)
    f.func_defaults = func.func_defaults
    return f

def getFreeVariables(func):
    nargs = func.func_code.co_argcount
    vars1 = []
    while 1:
        try:
            d = dict(zip(vars1,[random() for j in vars1]))
            f = bindFreeVariables(func, d)
            args = [random() for j in range(nargs)]
            val = f(*args)
            break
        except NameError, error:
            freevar = error.args[0].split(" ")[2].replace("'","")
            ## this occurs when func has an inner function with
            ## free variables
            if freevar in vars1:
                raise NameError, error
            vars1.append(freevar)
    return vars1



def genVarsVals(vars, args):
    return ";".join([v+"="+str(a) for v, a in zip(vars, args)])
        
class Quad(object):
    def __init__(self, func=None, nx = 10, ny = 10):
        self.function= func
        self.coords = SoCoordinate3()
        self.mesh = wrap(SoQuadMesh())
        self.getMesh().verticesPerColumn = nx
        self.getMesh().verticesPerRow = ny
        nb = SoNormalBinding()
        nb.value = SoNormalBinding.PER_VERTEX_INDEXED
        ## ============================
        self.scale = SoScale()
        self.linesetX = wrap(SoLineSet(),False)
        self.linesetY = wrap(SoLineSet(),False)
        self.linesetYcoor = SoCoordinate3()
        self.lineColor = SoMaterial()
        self.lineColor.diffuseColor = (1,0,0)
        ## ============================
        self.root = SoSeparator()
        self.root.addChild(nb)
        self.root.addChild(self.scale)
        self.root.addChild(self.coords)
        self.root.addChild(self.mesh)
        self.root.addChild(self.lineColor)
        self.root.addChild(self.linesetX)
        self.root.addChild(self.linesetYcoor)
        self.root.addChild(self.linesetY)

    def getMesh(self):
        return self.mesh[0]
    def getLineSetX(self):
        return self.linesetX[0]
    def getLineSetY(self):
        return self.linesetY[0]

    def getVerticesPerColumn(self):
        return self.getMesh().verticesPerColumn.getValue()

    def getVerticesPerRow(self):
        return self.getMesh().verticesPerRow.getValue()
        
class Mesh(GraphicObject):
    def __init__(self, rangeX=(0,1,40),  rangeY=(0,1,40), name="",visible = False, parent = None):
        GraphicObject.__init__(self,visible,parent)
        self.name = name
        ## ============================
        self.sHints = SoShapeHints()
        self.sHints.vertexOrdering = SoShapeHints.COUNTERCLOCKWISE
        self.sHints.creaseAngle = 0.0
        self.addChild(self.sHints)
        ## ============================
        self.quads = {}
        self.parameters = {}
        self.rangeX = Range(*rangeX)
        self.rangeY = Range(*rangeY)
        ## ============================
        layout  =  QtGui.QVBoxLayout()
        self.widget = QtGui.QWidget()
        self.widget.setLayout(layout)
        if self.name != "":
            layout.addWidget(QtGui.QLabel("<center><h1>%s</h1></center>" % self.name))
            
    def getGui(self):
        return self.widget

    def addWidget(self,widget):
        self.widget.layout().addWidget(widget)
        
    def __len__(self):
        return len(self.rangeX) * len(self.rangeY)

    def setMeshVisible(self, visible):
        if visible:
            val = SO_SWITCH_ALL
        else:
            val = SO_SWITCH_NONE
        for quad in self.quads.values():
            quad.mesh.whichChild = val

    def setLinesVisible(self, visible):
        if visible:
            val = SO_SWITCH_ALL
        else:
            val = SO_SWITCH_NONE
        for quad in self.quads.values():
            quad.linesetX.whichChild = val
            quad.linesetY.whichChild = val

    def setMeshDiffuseColor(self,val):
        for quad in self.quads.values():
            quad.lineColor.diffuseColor = val

    def setScaleFactor(self,vec3):
        for quad in self.quads.values():
            quad.scale.scaleFactor = vec3

    def setVerticesPerColumn(self,n):
        for quad in self.quads.values():
            quad.getMesh().verticesPerColumn = int(round(n))
            
    def checkReturnValue(self, func, val):
        if not operator.isSequenceType(val) or len(val) != 3:
            raise TypeError, "function %s does not produces a 3-tuple" % func
    
    def getParametersValues(self):
        return dict((par.name, par.getValue()) for par in self.parameters.values())
    
    def addQuad(self,func,col=None):
        nargs = func.func_code.co_argcount
        freevars = set(getFreeVariables(func))
        if nargs < 2:
            raise TypeError, "function %s needs at least 2 arguments" % func
        quad = Quad(func, len(self.rangeX), len(self.rangeY))
        ## only add new names
        oldnames = set(self.parameters.keys())
        newvars = freevars - oldnames
        for v in sorted(newvars):
            self.addParameter((v, 0, 1, 0))
        ## ============================
        ## test the return value
        d = self.getParametersValues()
        fbind = bindFreeVariables(func, d)
        val = fbind(1, 1)
        self.checkReturnValue(func, val)
        ## ============================
        self.quads[func] = quad
#        self.root.addChild(quad.root)
#        self.separator.addChild(quad.root)
        self.addChild(quad)
        
    def updateParameters(self):
        d = self.getParametersValues()
        for func,quad in self.quads.items():
            quad.function = bindFreeVariables(func, d)
        
    def updateAll(self, val = 0):
        if hasattr(self,"parameters"):
            self.updateParameters()
            self.updateMesh()

    def updateMesh(self):
        for quad in self.quads.values():
            vertices = range(len(self))
            malla(vertices, quad.function, 
                self.rangeX.min, self.rangeX.dt, len(self.rangeX),
                self.rangeY.min, self.rangeY.dt, len(self.rangeY))
            quad.coords.point.setValues(0,len(vertices),vertices)
            vpc = quad.getVerticesPerColumn()
            vpr = quad.getVerticesPerRow()
            lstX = [vpr for i in range(vpc)]
            lstY = [vpc for i in range(vpr)]
            quad.getLineSetX().numVertices.setValues(lstX)
            ## we need the "transpose of the first list
            verticesY = []
            for i in range(vpr):
                for j in range(vpc):
                    verticesY.append(vertices[j*vpr+i])
            quad.linesetYcoor.point.setValues(0,len(verticesY),verticesY)
            quad.getLineSetY().numVertices.setValues(lstY)
            
    def addParameter(self, rangep=('w', 0, 1, 0), qlabel = None):
        ## rangep = (name, vmin, vmax, vini)
        ##        | (name, vmin, vmax)
        if len(rangep) == 3:
            rangep += rangep[1:2]
        sliderNpoints = 20
        rangep += (sliderNpoints,)
        ## ============================
        slider = Slider(rangep=rangep, func=self.updateAll)
        self.addWidget(slider)
        self.parameters[slider.name] = slider
        ## ============================
        if qlabel != None:
            if not (type(qlabel) == list or type(qlabel) == tuple):
                qlabel = [qlabel]
            slider.qlabel = qlabel
            for lab in qlabel:
                conecta(slider, QtCore.SIGNAL("labelChanged(float)"), lab.setParamValue)
        ## ============================
        return slider

    def getParameter(self, name):
        return self.parameters[name]
        
    def setRange(self, name, rangep):
        if name == "x":
            pass
        elif name == "y":
            pass
        else:
            self.getParameter(name).updateRange(rangep)
            
    def addEqn(self, eqn):
        layout = QtGui.QHBoxLayout()
        layout.setMargin(0)
        layout.setSpacing(0)
        w = QtGui.QWidget()
        w.setLayout(layout)
        layout.addStretch()
        ## ============================
        eqn.eval(layout)
        ## ============================
        layout.addStretch()
        self.widget.layout().insertWidget(1,w,0, QtCore.Qt.AlignTop)



class ParametricPlot3D(Mesh):
    def __init__(self, funcs, rangeX=(0,1,40), rangeY=(0,1,40), name = '', eq = None,visible = True, parent = None):
        Mesh.__init__(self,rangeX=rangeX,rangeY=rangeY,name=name,visible=visible,parent=parent)
        if not type(funcs) in (list, tuple):
            funcs = [funcs]
        for fn in funcs:
            self.addQuad(fn)

        ## ============================
#        if eq != None:
#            self.addEqn(eq)
        ## ============================

class Plot3D(ParametricPlot3D):
    def __init__(self, funcs, rangeX=(0,1,40), rangeY=(0,1,40), name = '', eq = None,visible = True, parent = None):
        ParametricPlot3D.__init__(self,funcs,rangeX=rangeX,rangeY=rangeY,name=name,visible=visible,parent=parent)
        
    def checkReturnValue(self, func, val):
        if not operator.isNumberType(val):
            raise TypeError, "function %s does not produces a number" % func
        
    def updateParameters(self):
        d = self.getParametersValues()
        for func,quad in self.quads.items():
            f2 = bindFreeVariables(func, d)
            quad.function = lambda x, y: (x, y, f2(x, y))

            
class RevolutionPlot3D(ParametricPlot3D):
    def __init__(self, funcs, rangeX=(0,1,40), rangeY=(0,2*pi,40), name = '', eq = None,visible = True, parent = None):
        ParametricPlot3D.__init__(self,funcs,rangeX=rangeX,rangeY=rangeY,name=name,visible=visible,parent=parent)
        
    def checkReturnValue(self, func, val):
        if not operator.isNumberType(val):
            raise TypeError, "function %s does not produces a number" % func
            
    def updateParameters(self):
        d = self.getParametersValues()
        for func,quad in self.quads.items():
            fz = bindFreeVariables(func, d)
            quad.function = lambda r,t: (r*cos(t), r*sin(t),fz(r,t))

class RevolutionParametricPlot3D(ParametricPlot3D):
    def __init__(self, funcs, rangeX=(0,1,40), rangeY=(0,1,40), name = '', eq = None,visible = True, parent = None):
        ParametricPlot3D.__init__(self,funcs,rangeX=rangeX,rangeY=rangeY,name=name,visible=visible,parent=parent)

    def updateParameters(self):
        d = self.getParametersValues()
        for func,quad in self.quads.items():
            g = bindFreeVariables(func, d)
            def fn(r,t):
                R,T,Z = g(r,t)
                return(R*cos(T),R*sin(T),Z)
            quad.function = fn

if __name__ == "__main__":
    from util import  main
    from math import  cos,  sin,  pi
    from Viewer import Viewer
    import sys

    app = QtGui.QApplication(sys.argv)
    visor = Viewer()
    visor.createChapter()
    ## ============================
#    visor.createPage()
#    m = Mesh((-1, 1, 20), (-1, 1, 20))
#    m.addQuad(lambda x, y:(x,y,   v*x**2 - w*y**2))
#    m.addQuad(lambda x, y:(x,y, - x**2 - y**2))
#    visor.addChild(m)
    ## ============================
    visor.createPage()
    pp = ParametricPlot3D(lambda x,y:(x,y, a*x**2 + b*y**2),(-1,1),(-1,1),visible=True)

    for t in intervalPartition((0, 3, 6)):
        pp.addQuad(lambda x,y,t=t:(x,y, x**2 + b*y**2 + t))

    pp.setRange("a", (-1, 1, 0))
    pp.setRange("b", (-1, 1, 0))
    visor.addChild(pp)
    ## ============================
    visor.createPage()
    p2 = Plot3D(lambda x,y:a*x**2 - y**2,(-1,1),(-1,1),visible=True)
    ## si el parámetro no se define explícitamente, el resultado es equivalente
    ## a esto:
    ## p2.setRange("a", (0, 1, 0))
    visor.addChild(p2)
    ## ============================
    visor.createPage()
    p3 = RevolutionPlot3D(lambda r,t: r**2 ,(.1,1),(.1,2*pi), name="p3",visible=True)
    r, t = createVars(["r", "t"])
    p3.addEqn(t == r**2)
    visor.addChild(p3)
    ## ============================
    visor.lucesBlanca.on = False
    visor.lucesColor.whichChild = SO_SWITCH_ALL
    ## ============================    
    visor.whichPage = 0
    visor.resize(400, 400)
    visor.show()
    visor.chaptersStack.show()

    if Quarter:
        sys.exit(app.exec_())
    else:
        SoQt.mainLoop()
    
