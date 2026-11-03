import subprocess
from lookup import ocr
point=(292,63)
path='/tmp/games-current.png'
print('baseline',ocr.recognize_image(path,point))
from PyQt6.QtGui import QImage
for width in (128,192,256):
    local='/tmp/games-local.png'
    QImage(path).copy(292-width//2,47,width,32).save(local)
    print('local',width,ocr.recognize_image(local,(width//2,16)))
for light in (False,True):
    png,tr=ocr._prepare_image(path,point,2,'never',light_text=light)
    for mode in (6,11,7):
        p=subprocess.run(['tesseract','stdin','stdout','-l','eng','--psm',str(mode),'tsv'],input=png,capture_output=True)
        words=ocr.parse_tsv(p.stdout,tr)
        print(light,mode,[(w.text,w.confidence,w.box) for w in words if w.box[1]<90],ocr.select_word(words,point))
