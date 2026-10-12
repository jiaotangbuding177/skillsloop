"""Explicit reconstructed INITIAL converter input, not the repaired target.

Same-source original AI describes swapped wrap_a href/text groups and an image
regex that assumes src precedes alt. Both defects deliberately remain here.
No original publisher package identity/version is asserted; no network calls.
"""
import argparse,html,re
from pathlib import Path

def wrap_a(match):
    # Original described initial defect: group1 is href, group2 is text.
    txt=match.group(1)
    href=match.group(2)
    return '<a href="'+html.escape(href,quote=True)+'" style="color:#576b95">'+txt+'</a>'

def style_links(content):
    return re.sub(r'<a\s+href="([^"]+)">(.*?)</a>',wrap_a,content,flags=re.S)

def style_images(content):
    # Original described initial defect: alt-before-src does not match.
    return re.sub(r'<img\s+src="([^"]+)"\s+alt="([^"]*)"\s*/?>',
                  r'<img src="\1" alt="\2" style="max-width:100%;height:auto" />',content)

def convert_markdown(markdown):
    def inline(text):
        text=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',lambda m:'<a href="'+m.group(2)+'">'+m.group(1)+'</a>',text)
        return re.sub(r'\*\*(.*?)\*\*',r'<strong>\1</strong>',text)
    blocks=[]
    for line in markdown.splitlines():
        if line.startswith('## '):blocks.append('<h2>'+inline(line[3:])+'</h2>')
        elif line.startswith('# '):blocks.append('<h1>'+inline(line[2:])+'</h1>')
        elif line.strip():blocks.append(line if line.lstrip().startswith('<') else '<p>'+inline(line)+'</p>')
    return style_images(style_links('\n'.join(blocks)))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('input');parser.add_argument('--out',required=True);a=parser.parse_args()
    output=Path(a.out);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(convert_markdown(Path(a.input).read_text('utf8')),'utf8')
    print('HTML written')
if __name__=='__main__':main()
