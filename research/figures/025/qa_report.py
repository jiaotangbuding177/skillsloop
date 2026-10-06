from pathlib import Path
from PIL import Image, ImageDraw
from pypdf import PdfReader
root=Path(__file__).resolve().parents[3]
p=root/'tmp/pdfs/025'
files=sorted(p.glob('final-*.png'))
for start in range(0,len(files),6):
    canvas=Image.new('RGB',(1200,1180),'#DDE5EB')
    for k,f in enumerate(files[start:start+6]):
        im=Image.open(f).convert('RGB');im.thumbnail((380,550))
        x,y=(k%3)*400+10,(k//3)*590
        canvas.paste(im,(x,y+25));ImageDraw.Draw(canvas).text((x,y+5),f.stem,fill='black')
    canvas.save(p/f'contact-{start//6+1}.png')
reader=PdfReader(str(root/'output/pdf/skillsloop_concept_and_technical_assessment.pdf'))
for i,page in enumerate(reader.pages):
    text=page.extract_text() or ''
    print(i+1, len(text), text[80:145].replace('\n',' / '))
