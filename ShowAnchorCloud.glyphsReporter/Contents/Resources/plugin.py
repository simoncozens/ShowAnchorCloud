# encoding: utf-8
from __future__ import division, print_function, unicode_literals
import objc
from GlyphsApp import *
from GlyphsApp.plugins import *
from Foundation import NSPoint
from AppKit import NSColor, NSBezierPath, NSAffineTransform
import traceback


class ShowAnchorCloud(ReporterPlugin):
    @objc.python_method
    def settings(self):
        self.name = "Show Anchor Cloud"
        self.menuName = "Anchor Cloud"
        self.skipMark = {}

    @objc.python_method
    def matchingLayersAndAnchorsForSelection(self, layer):
        selectedAnchors = [
            (x, self.getAnchorRoot(x))
            for x in layer.selection
            if isinstance(x, GSAnchor)
        ]
        if not selectedAnchors:
            return []

        font = layer.parent.parent
        glyphs = font.glyphs

        ret = []
        for glyph in glyphs:
            if otherLayer := glyph.layers[layer.associatedMasterId]:
                for anchor, anchorRoot in selectedAnchors:
                    if anchorRoot and (otherAnchor := otherLayer.anchors[anchorRoot]):
                        ret.append((anchor, otherLayer, otherAnchor))
        return ret

    @objc.python_method
    def getAnchorRoot(self, anchor):
        anchorName = anchor.name
        # Skip mark anchors
        if anchorName.startswith("_"):
            return None
        # If it is a ligature anchor, remove the suffix
        if "_" in anchorName:
            anchorName = anchorName.split("_")[0]
        # If it is a contextual anchor, remove the astrisk
        if anchorName.startswith("*"):
            anchorName = anchorName[1:]
            # If it has a suffix, remove it
            if "." in anchorName:
                anchorName = anchorName.split(".")[0]
        anchorRoot = "_" + anchorName
        return anchorRoot

    def conditionalContextMenus(self):
        layer = self.activeLayer()
        items = []
        for _, otherLayer, _ in self.matchingLayersAndAnchorsForSelection(layer):
            if otherLayer.parent.name in self.skipMark:
                state = OFFSTATE
            else:
                state = ONSTATE

            items.append(
                {
                    "name": "Show " + otherLayer.parent.name,
                    "state": state,
                    "action": self.toggleMark_,
                    # "action": objc.selector(
                    #     lambda (self, sender): self.toggle(l2.parent.name)
                    # ),
                }
            )
        items.append({"name": "Clear all marks", "action": self.clearAll_})
        items.append({"name": "Show all marks", "action": self.showAll_})
        return items

    def clearAll_(self, sender):
        layer = self.activeLayer()
        for _, otherLayer, _ in self.matchingLayersAndAnchorsForSelection(layer):
            self.skipMark[otherLayer.parent.name] = True
        Glyphs.redraw()

    def showAll_(self, sender):
        layer = self.activeLayer()
        for _, otherLayer, _ in self.matchingLayersAndAnchorsForSelection(layer):
            if otherLayer.parent.name in self.skipMark:
                del self.skipMark[otherLayer.parent.name]
        Glyphs.redraw()

    def toggleMark_(self, sender):
        name = sender.title()[5:]
        if name in self.skipMark:
            del self.skipMark[name]
        else:
            self.skipMark[name] = True
        Glyphs.redraw()

    @objc.python_method
    def background(self, layer):
        try:
            matchingLayersAndAnchors = self.matchingLayersAndAnchorsForSelection(layer)
            if not matchingLayersAndAnchors:
                return
            NSColor.colorWithDeviceWhite_alpha_(0, 0.2).set()
            for anchor, otherLayer, otherAnchor in matchingLayersAndAnchors:
                if otherLayer.parent.name in self.skipMark:
                    continue
                anchorAnchorPos = NSPoint(
                    anchor.position.x - otherAnchor.position.x,
                    anchor.position.y - otherAnchor.position.y,
                )
                bez = NSBezierPath.bezierPath()
                bez.appendBezierPath_(otherLayer.completeBezierPath)

                t = NSAffineTransform.transform()
                t.translateXBy_yBy_(anchorAnchorPos.x, anchorAnchorPos.y)
                bez.transformUsingAffineTransform_(t)
                bez.fill()
        except:
            print("Oops!", sys.exc_info()[0], "occured.")
            traceback.print_exc(file=sys.stdout)

    def shouldDrawAccentCloudForLayer_(self, layer):
        return layer != self.activeLayer()
