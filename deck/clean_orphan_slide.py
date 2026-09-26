"""Remove the orphaned demo-flow slide part (slide13.xml / rId18) left in the
package when the slide was deleted from the slide list but not garbage-collected.
Produces a clean 12-slide deck so downstream cloning doesn't collide on partnames.
"""
import re
import shutil
import zipfile

SRC = "/tmp/deck_backup_12slide.pptx"
OUT = "/Users/srihari.a/febar/Medical-OmniChannel-Analytics-FE/deck/Medical_Omnichannel_Daiichi_Deck.pptx"

ORPHAN_PART = "ppt/slides/slide13.xml"
ORPHAN_RELS = "ppt/slides/_rels/slide13.xml.rels"
DROP = {ORPHAN_PART, ORPHAN_RELS}

zin = zipfile.ZipFile(SRC, "r")
tmp = OUT + ".tmp"
zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)

for item in zin.infolist():
    if item.filename in DROP:
        continue
    data = zin.read(item.filename)
    if item.filename == "ppt/_rels/presentation.xml.rels":
        txt = data.decode("utf-8")
        # drop the <Relationship ... Target="slides/slide13.xml"/> entry
        txt = re.sub(r'<Relationship[^>]*Target="slides/slide13\.xml"[^>]*/>', "", txt)
        data = txt.encode("utf-8")
    elif item.filename == "[Content_Types].xml":
        txt = data.decode("utf-8")
        txt = re.sub(r'<Override[^>]*PartName="/ppt/slides/slide13\.xml"[^>]*/>', "", txt)
        data = txt.encode("utf-8")
    zout.writestr(item, data)

zin.close()
zout.close()
shutil.move(tmp, OUT)

# verify
from pptx import Presentation
p = Presentation(OUT)
print("clean deck slides:", len(p.slides))
parts = sorted(zipfile.ZipFile(OUT).namelist())
slideparts = [n for n in parts if re.match(r"ppt/slides/slide\d+\.xml$", n)]
print("slide parts:", len(slideparts), slideparts)
