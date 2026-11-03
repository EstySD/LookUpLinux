import sys, subprocess
sys.path.insert(0, '/home/lookup07/lookup-preview-0.2.1-1793721877/lookup-source')
from lookup import ocr
from PyQt6.QtGui import QImage
from PyQt6.QtCore import QBuffer, QIODevice
path='/tmp/home-ocr-before.png'
print('baseline', ocr.recognize_image(path,(360,262)))
for w,h in [(96,24),(128,32),(192,48)]:
    image=QImage(path).copy(360-w//2,262-h//2,w,h)
    from PyQt6.QtGui import QColor
    for yy in range(h):
        for xx in range(w):
            c=image.pixelColor(xx,yy)
            image.setPixelColor(xx,yy,QColor('black' if min(c.red(),c.green(),c.blue())>140 else 'white'))
    buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG')
    for invert in ['auto','never']:
        png,tr=ocr._prepare_image(bytes(buffer.data()),(w//2,h//2),2,invert)
        for psm in [6,11,7]:
            p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(psm),'tsv'],input=png,capture_output=True)
            words=ocr.parse_tsv(p.stdout,tr)
            print(w,h,invert,psm,[(x.text,round(x.confidence,1),x.box) for x in words],ocr.select_word(words,(w//2,h//2)))
