from PyQt6.QtGui import QImage,QColor
from lookup import ocr
for width in (192,256,384,512):
 for x in (278,292,308):
  im=QImage('/tmp/games-current.png').copy(max(0,x-width//2),51,width,24)
  for yy in range(24):
   for xx in range(width):
    im.setPixelColor(xx,yy,QColor('black' if im.pixelColor(xx,yy).lightness()<220 else 'white'))
  im.save('/tmp/local-games.png')
  r=ocr.recognize_image('/tmp/local-games.png',(min(x,width//2),12),fallback=False)
  print(width,x,r.selection,flush=True)
