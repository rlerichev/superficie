from pivy.coin import SoComplexity
from superficie.animations import Animation
from superficie.base import MaterialNode
from superficie.nodes import Arrow


class Bundle2(MaterialNode):
    def __init__(self, curve3D, function, col, factor=1):
        """curve is something derived from Curve3D"""
        super(Bundle2,self).__init__()
        comp = SoComplexity()
        comp.value.setValue(.1)
        self.separator.addChild(comp)
        ## ============================
        points = curve3D.points
        pointsp = [curve3D[i] + function(t) * factor for i, t in enumerate(curve3D.domainPoints)]
        for p, pp in zip(points, pointsp):
            self.separator.addChild(Arrow(p, pp).root)

        self.animation = Animation(lambda num: self[num - 1].show(), (4000, 1, len(points)))

    def setMaterial(self, mat):
        for c in self.getChildren():
            c.material.ambientColor = mat.ambientColor
            c.material.diffuseColor = mat.diffuseColor
            c.material.specularColor = mat.specularColor
            c.material.shininess = mat.shininess

    def setHeadMaterial(self, mat):
        return
        for c in self.getChildren():
            c.head_material.ambientColor = mat.ambientColor
            c.head_material.diffuseColor = mat.diffuseColor
            c.head_material.specularColor = mat.specularColor
            c.head_material.shininess = mat.shininess

    def resetObjectForAnimation(self):
        self.hideAllArrows()

    def setRadius(self, r):
        for c in self.getChildren():
            c.setRadius(r)

    def setLengthFactor(self, factor):
        for c in filter(lambda c: isinstance(c, Arrow), self.getChildren()):
            c.setLengthFactor(factor)

    def hideAllArrows(self):
        for arrow in self.getChildren():
            arrow.hide()

    def setNumVisibleArrows(self, num):
        """set the number of arrow to show"""
        print "setNumVisibleArrows:", num