"""Reproducible publication figures and Chinese research-concept PDF. No model calls."""
from pathlib import Path
import re, html, math, subprocess, json
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer,
    PageBreak, Table, TableStyle, KeepTogether, Flowable, CondPageBreak)
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon, Circle
from reportlab.graphics import renderPDF, renderSVG
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
REPORTS = ROOT/'research/reports'
OUT = ROOT/'output/pdf'
QA = ROOT/'tmp/pdfs/025'
for p in (HERE,OUT,QA): p.mkdir(parents=True,exist_ok=True)
for n,f in [('CJK','msyh.ttc'),('CJKB','msyhbd.ttc'),('Latin','arial.ttf')]:
    pdfmetrics.registerFont(TTFont(n,'C:/Windows/Fonts/'+f))
pdfmetrics.registerFontFamily('CJK',normal='CJK',bold='CJKB',italic='CJK',boldItalic='CJKB')
NAVY='#15334B'; BLUE='#23669A'; TEAL='#167E7A'; GOLD='#A87725'; RED='#AB4A48'; GRAY='#637381'
PALE='#EDF4FA'; GREEN='#EAF5F1'; ROSE='#FAEFEE'; WHITE='#FFFFFF'

def txt(d,x,y,t,size=16,color=NAVY,bold=False,anchor='start'):
    d.add(String(x,y,t,fontName='CJKB' if bold else 'CJK',fontSize=size,
                 fillColor=colors.HexColor(color),textAnchor=anchor))
def box(d,x,y,w,h,title,lines=(),accent=BLUE,fill=PALE,dashed=False):
    d.add(Rect(x,y,w,h,rx=10,ry=10,fillColor=colors.HexColor(fill),
      strokeColor=colors.HexColor(accent),strokeWidth=1.2,strokeDashArray=[5,4] if dashed else None))
    txt(d,x+15,y+h-29,title,17,accent,True)
    for i,t in enumerate(lines): txt(d,x+15,y+h-55-i*23,t,14)
def arrow(d,x1,y1,x2,y2,color=GRAY,dashed=False):
    d.add(Line(x1,y1,x2,y2,strokeColor=colors.HexColor(color),strokeWidth=1.5,
               strokeDashArray=[5,4] if dashed else None))
    a=math.atan2(y2-y1,x2-x1); l=8
    pts=[x2,y2,x2-l*math.cos(a-.45),y2-l*math.sin(a-.45),x2-l*math.cos(a+.45),y2-l*math.sin(a+.45)]
    d.add(Polygon(pts,fillColor=colors.HexColor(color),strokeColor=None))
def base(h,label,subtitle):
    d=Drawing(720,h)
    d.add(Rect(0,0,720,h,fillColor=colors.white,strokeColor=None))
    txt(d,12,h-23,label,19,NAVY,True)
    txt(d,12,h-49,subtitle,13,GRAY)
    return d

figs={}
d=base(440,'01  SkillsLoop：从执行到下一次复用','蓝色：确定性控制  ·  绿色：模型执行与封装  ·  金色：人工采纳与授权')
box(d,12,265,212,100,'执行与事实采集',['会话 / 选定版本 / 工具','读取回执 / 文件产物'])
box(d,254,265,212,100,'可修订任务',['引用与词法关联','稳定封口 / 重开 / hash'])
box(d,496,265,212,100,'轨迹聚类与路由',['NEW：complete-link','UPDATE：实际技能版本'])
arrow(d,224,315,254,315);arrow(d,466,315,496,315)
box(d,496,100,212,107,'分析、合并与应用',['成功 / 失败 / 未知分析','Patch → 官方封装'],TEAL,GREEN)
box(d,254,100,212,107,'技能治理',['个人采纳 / 组织提审','审核发布 / 版本历史'],GOLD,'#FBF4E7')
box(d,12,100,212,107,'新任务消费',['读取所选技能版本','执行并登记交付'],TEAL,GREEN)
arrow(d,602,265,602,207);arrow(d,496,153,466,153);arrow(d,254,153,224,153)
arrow(d,117,207,117,265,TEAL)
txt(d,143,234,'反馈回流',13,TEAL)
txt(d,12,51,'已跑通：构造销售数据 + 真实模型；未证明：企业效果、无效减少、成本下降。',14)
txt(d,12,24,'已实现来源检查与局部修改；重要性排序、语义防退化仍需研究。',14,GRAY)
figs['01_lifecycle']=d

d=base(510,'02  生成之前先决策','一次学习派发可能包含多次底层模型请求；四种路由不是四次模型调用。')
box(d,140,382,440,65,'稳定轨迹：方法材料 / 可诊断失败依据',[],BLUE)
box(d,140,279,440,65,'使用关系：未使用 / 单一版本 / 不明确',[],BLUE)
arrow(d,360,382,360,344)
box(d,12,157,210,80,'NEW',['未使用已有技能'])
box(d,255,157,210,80,'UPDATE / SUPPORT',['纠正或失败 / 无增量'])
box(d,498,157,210,80,'DEFER',['无方法 / 归因不明'],GRAY,'#F0F3F5')
arrow(d,245,279,116,237);arrow(d,360,279,360,237);arrow(d,477,279,603,237)
arrow(d,580,415,656,415,GRAY);arrow(d,656,415,656,237,GRAY)
txt(d,590,430,'否',13,GRAY)
box(d,12,26,453,80,'去重 → 聚类 → 等待吸收 → 冻结',['同owner / 同基准；最多8条；单例到期处理'],TEAL,GREEN)
arrow(d,116,157,116,106);arrow(d,360,157,360,106)
txt(d,499,100,'重复 → SUPPORT',14,GRAY)
txt(d,499,73,'过期 → DEFER',14,GRAY)
txt(d,499,46,'额度不足 → 排队',14,GRAY)
figs['02_routing']=d

d=base(430,'03  一条任务，多个修订','示例中的金额仅用于说明任务关系；状态封口不表示业务成功。')
for x,title,lines,ac,fill in [(12,'初次尝试',['汇总销售','错误：跨期退款混扣'],RED,ROSE),
 (253,'用户纠正',['跨期退款单列','保留原任务目标'],BLUE,PALE),
 (494,'修正版交付',['保存当前证据快照','结果允许 UNKNOWN'],TEAL,GREEN)]:
    box(d,x,245,214,100,title,lines,ac,fill)
arrow(d,226,295,253,295);arrow(d,467,295,494,295)
box(d,12,75,214,101,'旧候选失效',['源hash不再一致','不能继续采纳'],RED,ROSE)
box(d,253,75,214,101,'稳定封口',['修订 r → r+1','冻结新候选输入'])
box(d,494,75,214,101,'后续复用与纠正',['读取技能 v1','新条件 → 更新候选'],TEAL,GREEN)
arrow(d,601,245,601,176);arrow(d,494,123,467,123);arrow(d,253,123,226,123)
txt(d,12,28,'任一来源修订阻止旧候选入库；同池其他材料释放后重新归纳。',14,GRAY)
figs['03_revision']=d

d=base(430,'06  三个实验，三个不同问题','保持时间隔离：先执行并评分，再释放反馈更新；不把未来答案带入生成。')
box(d,12,227,215,117,'E1  沉淀质量',['全部合格会话','无效数量 / 方法保留','生成与审核总开销'])
box(d,252,227,215,117,'E2  未来任务',['未见任务与输入','业务成功 / 个人偏好','强摘要与经验检索对照'])
box(d,492,227,215,117,'E3  连续演化',['共同初始技能库','更新分支 vs 冻结分支','新收益 / 旧能力退化'])
arrow(d,227,285,252,285);arrow(d,467,285,492,285)
box(d,12,87,695,86,'跨实验共同约束',['固定消费者与信息口径；模型内部请求 / tokens / 失败 / 人工均计入成本。'],TEAL,GREEN)
txt(d,12,35,'工业证据另需真实员工试点、授权范围、运行周期与净人工时间。此图没有结果数值。',14,GRAY)
figs['04_evaluation']=d

d=base(545,'04  轨迹小模块：关联、修订、封口','消息、工具结果、产物引用共同进入hash；隐含语义关联仍是边界。')
box(d,12,404,222,69,'输入轮次或执行更新',[])
box(d,266,404,442,69,'关联优先级',['原taskId → replyTo → 明确续作 → 新请求'])
arrow(d,234,437,266,437)
box(d,266,278,442,83,'hash变化：修订 r+1',['旧候选STALE；同池其他来源重新排队'])
arrow(d,487,404,487,361)
box(d,12,265,222,100,'歧义 / 噪声 / 维护',['记录分类与原因','不强行关联任务'],GRAY,'#F0F3F5')
arrow(d,266,420,180,365,GRAY)
box(d,266,152,442,81,'状态：OPEN → SETTLING',['无RUNNING；等待稳定期或空闲阈值'])
arrow(d,487,278,487,233)
box(d,266,31,442,79,'SEALED：进入候选决策',['verification 仍可为 UNKNOWN'],TEAL,GREEN)
arrow(d,487,152,487,110)
arrow(d,266,68,244,68,BLUE);arrow(d,244,68,244,320,BLUE);arrow(d,244,320,266,320,BLUE)
txt(d,22,175,'迟到纠正重开',14,BLUE)
figs['05_trace_control']=d

d=base(510,'05  多轨迹分析与Patch归纳','一次学习派发内分角色分析；小池一次归纳；宿主实际应用修改。')
box(d,12,302,213,117,'A+  成功分析器',['结果依据 / 稳定步骤','条件与引用','不把运行结束当成功'],TEAL,GREEN)
box(d,253,302,213,117,'A-  失败分析器',['现象 / 原因 / 修正','检查产物与验证依据','未验证原因 → 延期'],RED,ROSE)
box(d,495,302,213,117,'A?  未知结果',['明确用户规则可提议','不补造成功标签','保留不确定性'],BLUE,PALE)
box(d,160,167,400,84,'逐轨迹Patch → 多对一归纳',['重复合并 / 互补保留 / 冲突延期'],TEAL,GREEN)
arrow(d,118,302,230,251);arrow(d,360,302,360,251);arrow(d,602,302,490,251)
box(d,12,38,330,82,'宿主校验并应用',['引用 / 全提议覆盖 / hash / 唯一锚点'])
box(d,377,38,331,82,'官方封装 → 原审批流程',['SKILL.md / 附件 / .skill'],GOLD,'#FBF4E7')
arrow(d,360,167,177,120);arrow(d,342,78,377,78)
txt(d,12,10,'来源可审计不等于语义正确；未知原因不升级为已验证经验。',12,GRAY)
figs['06_proposed_compiler']=d

for name,d in figs.items():
    renderPDF.drawToFile(d,str(HERE/(name+'.pdf')))
    renderSVG.drawToFile(d,str(HERE/(name+'.svg')))
    svg=HERE/(name+'.svg')
    data=svg.read_text(encoding='utf-8').replace('font-family: CJK;',"font-family: 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif;").replace('font-family: CJKB;',"font-family: 'Microsoft YaHei', 'Noto Sans CJK SC', sans-serif; font-weight: 700;")
    svg.write_text(data,encoding='utf-8')

source=REPORTS/'022_论文概念文档.md'
text=source.read_text(encoding='utf-8').replace('<ama-doc>','').replace('</ama-doc>','')

# --- Chinese publication layout ---
PAGE=(595.276,841.89); M=47; CW=PAGE[0]-2*M
styles={
 'body':ParagraphStyle('body',fontName='CJK',fontSize=9.5,leading=16.1,textColor=colors.HexColor(NAVY),spaceAfter=7,wordWrap='CJK'),
 'h1':ParagraphStyle('h1',fontName='CJKB',fontSize=21,leading=30,spaceAfter=18,textColor=colors.HexColor(NAVY),keepWithNext=True,wordWrap='CJK'),
 'h2':ParagraphStyle('h2',fontName='CJKB',fontSize=17,leading=25,spaceBefore=3,spaceAfter=15,textColor=colors.HexColor(BLUE),keepWithNext=True,wordWrap='CJK'),
 'h3':ParagraphStyle('h3',fontName='CJKB',fontSize=11.6,leading=19,spaceBefore=12,spaceAfter=7,textColor=colors.HexColor(TEAL),keepWithNext=True,wordWrap='CJK'),
 'cell':ParagraphStyle('cell',fontName='CJK',fontSize=8.2,leading=13,wordWrap='CJK',textColor=colors.HexColor(NAVY)),
 'th':ParagraphStyle('th',fontName='CJKB',fontSize=8.4,leading=13,wordWrap='CJK',textColor=colors.white),
 'quote':ParagraphStyle('quote',fontName='CJK',fontSize=9,leading=15,spaceAfter=12,borderPadding=10,backColor=colors.HexColor(PALE),wordWrap='CJK'),
 'code':ParagraphStyle('code',fontName='CJK',fontSize=8.2,leading=12.5,wordWrap='CJK',spaceAfter=0),
 'caption':ParagraphStyle('caption',fontName='CJK',fontSize=8.4,leading=13,textColor=colors.HexColor(GRAY),spaceAfter=10,wordWrap='CJK')}

def inline(t):
    t=t.replace('—','-').replace('–','-').replace('\u2011','-')
    # Escape first, then constrained markup to keep arbitrary source safe.
    t=html.escape(t)
    t=re.sub(r'\[\[([0-9]+)\]\]\((https?://[^)]+)\)',r'<link href="\2" color="#23669A">[\1]</link>',t)
    def link(m):
        label,url=m.group(1),m.group(2)
        return f'<link href="{url}" color="#23669A">{label}</link>' if url.startswith('http') else label
    t=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,t)
    t=re.sub(r'\*\*(.+?)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'`([^`]+)`',r'<font color="#23669A">\1</font>',t)
    return t
def p(t,key='body'): return Paragraph(inline(t),styles[key])
class Figure(Flowable):
    def __init__(self,d):
        Flowable.__init__(self);self.d=d;self.width=CW;self.height=d.height*CW/d.width;self.keepWithNext=True
    def draw(self):
        self.canv.saveState();self.canv.scale(CW/self.d.width,CW/self.d.width);renderPDF.draw(self.d,self.canv,0,0);self.canv.restoreState()
class Cover(Flowable):
    def __init__(self): Flowable.__init__(self);self.width=CW;self.height=675
    def draw(self):
        c=self.canv
        c.setFillColor(colors.HexColor(TEAL));c.rect(0,643,53,5,fill=1,stroke=0)
        c.setFont('Latin',12);c.setFillColor(colors.HexColor(BLUE));c.drawString(0,616,'SKILLSLOOP  /  RESEARCH CONCEPT 03')
        c.setFont('CJKB',28);c.setFillColor(colors.HexColor(NAVY))
        for i,t in enumerate(['从会话修订','到可复用能力']):c.drawString(0,549-i*43,t)
        c.setFont('CJK',14);c.drawString(0,456,'面向企业个性化智能体的技能涌现与持续演化')
        c.setFont('Latin',10);c.setFillColor(colors.HexColor(GRAY))
        for i,t in enumerate(['From Conversational Revisions to Reusable Skills:',
                            'Personalized Skill Emergence and Evolution for Enterprise Agents']):c.drawString(0,426-i*16,t)
        c.setStrokeColor(colors.HexColor('#D6E1E9'));c.line(0,376,CW,376)
        items=[('01','全链路与技术机制','轨迹聚类、成功/失败分析、Patch归纳与真实复用'),
               ('02','WWW Industry 技术对标','四篇论文的方法与证据；当前原型的真实边界'),
               ('03','研究推进路线','原创机制候选、E1/E2/E3与完整论文大纲')]
        for i,(n,t,s) in enumerate(items):
            y=330-i*78;c.setFont('Latin',18);c.setFillColor(colors.HexColor(TEAL));c.drawString(0,y,n)
            c.setFont('CJKB',13);c.setFillColor(colors.HexColor(NAVY));c.drawString(43,y+1,t)
            c.setFont('CJK',10);c.setFillColor(colors.HexColor(GRAY));c.drawString(43,y-21,s)
        c.setFillColor(colors.HexColor(PALE));c.roundRect(0,29,CW,91,8,fill=1,stroke=0)
        c.setFont('CJKB',10);c.setFillColor(colors.HexColor(BLUE));c.drawString(15,95,'证据状态 / 2026-09-24')
        c.setFont('CJK',9.6)
        for i,t in enumerate(['构造数据的真实模型闭环已通过；尚无企业效果对照实验。',
                             '聚类、分角色分析和局部修改已接入；收益仍待评估。',
                             '概念讨论稿 v3，不作为投稿终稿或已证明创新的声明。']):c.drawString(15,74-i*17,t)

class Doc(BaseDocTemplate):
    def __init__(self,path):
        super().__init__(str(path),pagesize=PAGE,leftMargin=M,rightMargin=M,topMargin=56,bottomMargin=48,
                         title='SkillsLoop：论文概念、技术机制与Industry评估',author='SkillsLoop Research')
        self.addPageTemplates(PageTemplate('normal',[Frame(M,48,CW,PAGE[1]-104,leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=self.decorate))
    def decorate(self,c,doc):
        if doc.page==1:return
        c.saveState();c.setFont('Latin',8);c.setFillColor(colors.HexColor(GRAY));c.drawString(M,PAGE[1]-31,'SKILLSLOOP / TECHNICAL CONCEPT & INDUSTRY ASSESSMENT')
        c.setStrokeColor(colors.HexColor('#D6E1E9'));c.line(M,PAGE[1]-40,PAGE[0]-M,PAGE[1]-40)
        c.setFont('CJK',8);c.drawString(M,27,'研究讨论稿 v3 · 2026-09-24');c.setFont('Latin',9);c.drawRightString(PAGE[0]-M,27,f'{doc.page:02d}');c.restoreState()
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name=='h2':
            title=f.getPlainText();key='section-'+str(self.page)+'-'+str(len(title))
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(title,key,0,False)
            self.notify('TOCEntry',(0,title,self.page,key))

toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc',fontName='CJK',fontSize=10,leading=20,spaceAfter=5,textColor=colors.HexColor(NAVY),wordWrap='CJK')]
story=[Cover(),PageBreak(),p('阅读导航','h1'),p('正文区分原型事实、待实现机制与论文证据。第八、十、十一节适合技术审阅；第九、十二节及附录适合安排后续研究。'),Spacer(1,14),toc,PageBreak()]
lines=text.splitlines();i=0;started=False
while i<len(lines):
    line=lines[i].strip()
    if not started:
        if line.startswith('## 一、'):started=True
        else:i+=1;continue
    if not line or line=='---':i+=1;continue
    if line.startswith('## '):
        major=any(line.startswith('## '+k) for k in ('一、','四、','八、','九、','十、','附录A','附录B'))
        if major and story and not isinstance(story[-1],PageBreak):story.append(PageBreak())
        elif not major:story.extend([CondPageBreak(155),Spacer(1,18)])
        story.append(p(line[3:],'h2'));i+=1;continue
    if line.startswith('### '):story.append(p(line[4:],'h3'));i+=1;continue
    if line.startswith('!['):
        match=re.search(r'/([^/]+)\.svg',line)
        if match and match.group(1) in figs:story += [Spacer(1,7),Figure(figs[match.group(1)]),Spacer(1,6)]
        i+=1;continue
    if line.startswith('```'):
        i+=1;cl=[]
        while i<len(lines) and not lines[i].startswith('```'):
            cl.append(Paragraph(html.escape(lines[i]).replace(' ','&#160;'),styles['code']));i+=1
        block=Table([[x] for x in cl],colWidths=[CW]);block.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor(PALE)),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2)]))
        story.extend([block,Spacer(1,10)]);i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            cells=[v.strip() for v in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r'[-: ]+',c) for c in cells):rows.append(cells)
            i+=1
        n=len(rows[0]);weights=[1]*n
        if n==4:weights=[.78,1.22,1,1.1]
        if n==3:weights=[.85,1.1,1.15]
        widths=[CW*w/sum(weights) for w in weights]
        data=[[p(c,'th' if ri==0 else 'cell') for c in row] for ri,row in enumerate(rows)]
        table=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor(NAVY)),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F8'),colors.white]),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),8),('BOTTOMPADDING',(0,0),(-1,-1),8),('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor(NAVY)),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#D6E1E9'))]))
        story.extend([table,Spacer(1,12)]);continue
    if line.startswith('> '):story.append(p(line[2:],'quote'));i+=1;continue
    if line.startswith('- '):line='• '+line[2:]
    key='caption' if re.match(r'^(\*\*)?图[1-6]',line) else 'body'
    story.append(p(line,key));i+=1
pdf=OUT/'skillsloop_concept_and_technical_assessment.pdf'
Doc(pdf).multiBuild(story)
reader=PdfReader(str(pdf));texts=[pg.extract_text() or '' for pg in reader.pages]
assert len(texts)>10 and all(len(t)>30 for t in texts)
assert all(q in '\n'.join(texts) for q in ['8.3','10.2','E1','E2','E3','35','498,204'])
(QA/'text_audit.json').write_text(json.dumps({'pages':len(texts),'chars':[len(t) for t in texts],'figures':list(figs),'source':str(source),'pdf':str(pdf)},ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'pdf':str(pdf),'pages':len(texts),'figures':len(figs)},ensure_ascii=False))
