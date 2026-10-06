# -*- coding: utf-8 -*-
"""为 index.html 注入打印样式，生成 print.html"""
src = r"C:\Users\39835\Doubao\chats\2026-09-18\new-chat\skill-emergence-report\index.html"
dst = r"C:\Users\39835\Doubao\chats\2026-09-18\new-chat\skill-emergence-report\print.html"

with open(src, "r", encoding="utf-8") as f:
    html = f.read()

print_css = """
<style media="print">
@page { size: A4; margin: 13mm 12mm 14mm 12mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { background:#fff; color:#1a2536; font-size:10pt; line-height:1.6; }
.container { max-width:100%; padding:0; }
.hero { background:#fff; padding:20px 0 14px; border-bottom:2px solid #163f6e; }
.hero .kicker { margin-bottom:10px; }
.hero h1 { font-size:21pt; line-height:1.3; }
.hero .sub { font-size:11pt; margin-top:10px; }
.hero .meta { margin-top:14px; font-size:8.5pt; }
.thesis { padding:14px 0; }
.thesis p { font-size:9.5pt; line-height:1.7; }
section { padding:16px 0 2px; }
.sec-head { margin-bottom:10px; padding-bottom:8px; }
.sec-head h2 { font-size:15pt; }
h3.sub { font-size:11.5pt; margin:16px 0 8px; }
p { margin:6px 0; }
p.lead { font-size:10.5pt; }
.table-wrap { margin:10px 0; box-shadow:none; border-radius:4px; }
table { font-size:8.2pt; }
th { padding:6px 8px; font-size:7.8pt; }
td { padding:6px 8px; }
.callout { box-shadow:none; padding:10px 12px; margin:10px 0; break-inside:avoid; }
.flow { margin:14px 0 6px; }
.flow-in { padding:10px 12px; break-inside:avoid; }
.stage { box-shadow:none; padding:10px 12px 8px; break-inside:avoid; margin:0; }
.stage .name { font-size:11pt; }
.stage .desc { font-size:9pt; margin-top:5px; }
.stage .llm { font-size:8.6pt; margin-top:6px; }
.stage .art { font-size:8pt; padding:1px 6px; }
.spine { padding:5px 0; }
.spine .lbl { font-size:7.6pt; }
.risk { grid-template-columns:repeat(3,1fr); gap:10px; margin:12px 0; }
.risk-card { box-shadow:none; padding:12px; break-inside:avoid; }
.risk-card h4 { font-size:10pt; }
.risk-card p { font-size:8.4pt; }
.risk-card .fx { font-size:8pt; }
.llm-strip { grid-template-columns:repeat(4,1fr); gap:8px; margin:12px 0; }
.llm-card { box-shadow:none; padding:10px; break-inside:avoid; }
.llm-card h4 { font-size:9.5pt; }
.llm-card .row { font-size:8pt; }
.timeline li { padding:0 0 10px 24px; }
.timeline li .tl-t { font-size:9pt; }
.timeline li .tl-c { font-size:8.4pt; }
footer { margin-top:24px; padding:14px 0 20px; font-size:8pt; }
#q1,#q3,#q4,#q2,#q5,#appendix { break-before: page; }
* { box-shadow:none !important; }
</style>
"""

html = html.replace("</head>", print_css + "</head>", 1)

with open(dst, "w", encoding="utf-8") as f:
    f.write(html)
print("written:", dst, len(html))
