# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from Foundation import NSPoint, NSMakePoint
from AppKit import NSView, NSColor, NSRectFill, NSBezierPath, NSAffineTransform
import traceback


class ShowAnchorCloud(ReporterPlugin):
    @objc.python_method
    def settings(self):
        self.menuName = "Show Anchor Cloud"
        self.skipMark = {}

    def matchingGlyphsAndAnchorsForAnchor(self, layer, anchor):
        anchorRoot = "_" + anchor.name
        font = layer.parent.parent
        allglyphs = font.glyphs
        glyphs = []
        for g in allglyphs:
            if not g.layers[layer.master.id]:
                continue
            l2 = g.layers[layer.master.id]
            otherAnchor = l2.anchors[anchorRoot]
            if not otherAnchor:
                continue
            glyphs.append((l2, otherAnchor))
        return glyphs

    def conditionalContextMenus(self):
        layer = Glyphs.font.selectedLayers[0]
        selectedAnchors = filter(lambda x: isinstance(x, GSAnchor), layer.selection)
        items = []
        for a in selectedAnchors:
            for (l2, otherAnchor) in self.matchingGlyphsAndAnchorsForAnchor(layer, a):
                if l2.parent.name in self.skipMark:
                    state = OFFSTATE
                else:
                    state = ONSTATE

                items.append(
                    {
                        "name": "Show " + l2.parent.name,
                        "state": state,
                        "action": self.sayHello
                        # "action": objc.selector(
                        #     lambda (self, sender): self.toggle(l2.parent.name)
                        # ),
                    }
                )
        return items

    def sayHello(self, sender):
        name = sender.title()[5:]
        print(name)
        if name in self.skipMark:
            del self.skipMark[name]
        else:
            self.skipMark[name] = True

    @objc.python_method
    def background(self, layer):
        selectedAnchors = filter(lambda x: isinstance(x, GSAnchor), layer.selection)
        if len(selectedAnchors) == 0:
            return
        try:
            NSColor.colorWithDeviceRed_green_blue_alpha_(0.2, 0.2, 0.2, 0.5).set()
            for a in selectedAnchors:
                for (l2, otherAnchor) in self.matchingGlyphsAndAnchorsForAnchor(
                    layer, a
                ):
                    if l2.parent.name in self.skipMark:
                        continue
                    anchorAnchorPos = NSPoint(
                        a.position.x - otherAnchor.position.x,
                        a.position.y - otherAnchor.position.y,
                    )
                    bez = NSBezierPath.bezierPath()
                    bez.appendBezierPath_(l2.bezierPath)

                    t = NSAffineTransform.transform()
                    t.translateXBy_yBy_(anchorAnchorPos.x, anchorAnchorPos.y)
                    bez.transformUsingAffineTransform_(t)
                    bez.fill()

        except:
            print("Oops!", sys.exc_info()[0], "occured.")
            traceback.print_exc(file=sys.stdout)
