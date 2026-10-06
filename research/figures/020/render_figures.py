"""Editable publication diagrams; no quantitative results are fabricated."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT=Path(__file__).parent
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.fonttype':'none','pdf.fonttype':42})
TEAL='#155e63'; BLUE='#365e91'; MUTED='#526372'
def canvas(title,subtitle):
    fig,ax=plt.subplots(figsize=(15,8.4));fig.subplots_adjust(left=.025,right=.975,bottom=.035,top=.965)
    ax.set(xlim=(0,15),ylim=(0,8));ax.axis('off')
    ax.text(.2,7.65,title,fontsize=21,weight='bold',color=TEAL)
    ax.text(.2,7.20,subtitle,color=MUTED,fontsize=11)
    return fig,ax
def box(ax,x,y,w,h,title,body,color=TEAL,dashed=False):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle='round,pad=0.035,rounding_size=0.1',linewidth=1.6,
        edgecolor=color,facecolor='#f4f8f8',linestyle='--' if dashed else '-'))
    ax.text(x+.15,y+h-.30,title,fontsize=12,weight='bold',color=color,va='top')
    ax.text(x+.15,y+h-.75,body,fontsize=10.5,color='#263943',va='top',linespacing=1.5)
def arrow(ax,a,b,text='',color=MUTED,rad=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=15,color=color,lw=1.5,connectionstyle=f'arc3,rad={rad}'))
    if text: ax.text((a[0]+b[0])/2,(a[1]+b[1])/2+.15,text,fontsize=9,ha='center',color=color)
def save(fig,name):
    for fmt in ['svg','pdf','png']:fig.savefig(OUT/(name+'.'+fmt),dpi=180,facecolor='white')
    plt.close(fig)

fig,ax=canvas('Skills Loop: evidence to reusable capability','System overview | Solid: implemented prototype. Dashed: proposed research extension. No outcome claim implied.')
items=[('1  Conversation events','Goal, outputs, failures\nSkill ID + version + hash'),('2  Revisable task traces','Rule-based association\nAttempts + corrections\nStable closure / reopen'),('3  Increment decisions','NEW / UPDATE\nSUPPORT / DEFER\nExact duplicate suppression'),('4  Bounded extraction','Freeze evidence + base\nReserve dispatch budget\nOpenClaw + chosen LLM')]
for i,(t,b) in enumerate(items):box(ax,.2+i*3.75,4.65,3.25,1.95,t,b)
for i in range(3):arrow(ax,(3.48+i*3.75,5.6),(3.90+i*3.75,5.6))
box(ax,11.45,1.70,3.25,1.95,'5  Candidate validation','SKILL.md + resources\nEvidence freshness\nVersion conflict checks')
box(ax,7.7,1.70,3.25,1.95,'6  Governed libraries','Personal acceptance\nOrganization submission\nReview before sharing')
box(ax,3.95,1.70,3.25,1.95,'7  Skill-conditioned agent','Read exact selected files\nExecute in workspace\nKeep outputs + read receipts')
box(ax,.2,1.70,3.25,1.95,'8  Feedback & evolution','Incremental correction\nVersioned update proposals\nRollback without erasure')
arrow(ax,(13.1,4.6),(13.1,3.7))
for x in [11.4,7.65,3.9]:arrow(ax,(x,2.65),(x-.45,2.65))
arrow(ax,(1.8,3.7),(1.8,4.6),'next experience')
box(ax,.2,.20,7,.95,'Research extension: utility-aware selection','Frequency / importance ranking and utility calibration are not yet implemented.',BLUE,True)
ax.text(7.7,.9,'Closure != success     Read receipt != compliance',fontsize=11,color=TEAL)
ax.text(7.7,.5,'No automatic organization authorization from clustering.',fontsize=10,color=MUTED)
save(fig,'01_lifecycle')

fig,ax=canvas('A correction revises evidence, not just the final answer','Illustrative task sequence | Outcomes remain UNKNOWN unless supported. Values here are states, not measurements.')
box(ax,.3,4.8,3.1,1.7,'t1  Initial task','Produce a sales report\nInitial period/refund rule')
box(ax,4,4.8,3.1,1.7,'t2  Task correction','Separate cross-period refunds\nKeep original attempt')
box(ax,7.7,4.8,3.1,1.7,'t3  Stable window','Seal revisable trace\nUNKNOWN is admissible')
box(ax,11.4,4.8,3.1,1.7,'t4  Skill proposal','NEW or attributed UPDATE\nFreeze revision + version')
for x in [3.45,7.15,10.85]:arrow(ax,(x,5.65),(x+.45,5.65))
box(ax,.3,2,4.3,1.75,'Evidence retained','Goal + attempts + corrections\nTechnical state separate from outcome\nRevision history remains inspectable')
box(ax,5.35,2,4.3,1.75,'Late feedback','Reopen task and supersede evidence\nInvalidate unpublished stale candidates\nDo not erase published history')
box(ax,10.4,2,4.1,1.75,'Reuse-aware decision','No delta -> SUPPORT\nOne used skill + delta -> UPDATE\nUnclear attribution -> DEFER')
arrow(ax,(5.5,4.75),(2.5,3.8));arrow(ax,(13,4.75),(12.4,3.8));arrow(ax,(10.35,2.85),(9.7,2.85))
arrow(ax,(7.5,3.8),(5.55,4.75),'re-open')
ax.text(.3,.9,'Not a universal semantic segmenter: implicit continuation and interleaved tasks remain research gaps.',color=MUTED)
save(fig,'02_trace_evolution')

fig,ax=canvas('Evaluation: measure downstream utility without leaking future feedback','Proposed protocol | No experiments or effect sizes are claimed in this diagram.')
box(ax,.3,4.85,4.3,1.65,'A  Earlier conversations','Discover / generate skills\nTune rules only on development data',BLUE,True)
box(ax,5.35,4.85,4.3,1.65,'B  Future task instances','Frozen generator and locked rubric\nSame agent, model and task resources',BLUE,True)
box(ax,10.4,4.85,4.1,1.65,'C  Unseen eligible users','Only reviewed organization skills\nNo private conversation transfer',BLUE,True)
arrow(ax,(4.65,5.65),(5.3,5.65),'time');arrow(ax,(9.7,5.65),(10.35,5.65),'transfer')
box(ax,.3,2.05,4.3,1.9,'Paired downstream comparison','No skill / strong baselines / ours\nObjective acceptance + blinded audit\nCluster-aware confidence intervals',BLUE,True)
box(ax,5.35,2.05,4.3,1.9,'Prequential evolution','Execute -> score -> receive feedback\nThen update for subsequent tasks\nCompare with the same frozen initial bank',BLUE,True)
box(ax,10.4,2.05,4.1,1.9,'Real-world pilot','Randomize teams / library namespaces\nLog all eligible tasks and spillover\nTask quality, labor, total lifecycle cost',BLUE,True)
for x in [2.5,7.5,12.5]:arrow(ax,(x,4.8),(x,4.0))
ax.text(.3,1.2,'Primary outcomes: task success | net human time | total cost per successful task',fontsize=13,weight='bold',color=BLUE)
ax.text(.3,.65,'Guardrails: useful-method retention | version regressions | latency | permission violations | deferred work',color=MUTED)
save(fig,'03_evaluation')
print('Rendered three diagrams as editable SVG, PDF and PNG.')
