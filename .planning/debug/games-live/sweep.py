import subprocess
from PyQt6.QtGui import QImage,QColor
from lookup import ocr
for h in (20,24,32):
 for threshold in (None,160,180,200,220):
  im=QImage('/tmp/games-current.png').copy(196,63-h//2,192,h)
  if threshold:
   for y in range(h):
    for x in range(192):
     c=im.pixelColor(x,y)
     im.setPixelColor(x,y,QColor('black' if c.lightness()<threshold else 'white'))
  im.save('/tmp/local-games.png')
  png,tr=ocr._prepare_image('/tmp/local-games.png',(96,h//2),2,'never')
  for mode in (6,7,11):
   p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(mode),'tsv'],input=png,capture_output=True)
   words=ocr.parse_tsv(p.stdout,tr)
   print(h,threshold,mode,[(w.text,round(w.confidence),w.box) for w in words],flush=True)
