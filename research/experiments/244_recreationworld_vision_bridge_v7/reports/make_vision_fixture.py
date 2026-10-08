import io,base64,json,secrets
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]; nonce=''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))
im=Image.new('RGB',(480,150),'white'); ImageDraw.Draw(im).text((35,35),nonce,font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',60),fill='black'); b=io.BytesIO(); im.save(b,format='PNG')
(ROOT/'reports/vision_fixture.json').write_text(json.dumps({'expected':nonce,'image':{'type':'image','source':{'type':'base64','media_type':'image/png','data':base64.b64encode(b.getvalue()).decode()}}}))
