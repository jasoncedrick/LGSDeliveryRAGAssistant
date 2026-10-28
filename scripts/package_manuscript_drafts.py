"""Build review PDF and editable LaTeX fragments from evidence-based draft Markdown.

No model calls, source changes, or institutional submission occur here.
Run with the bundled Python containing reportlab.
"""
import json
import re
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/manuscript-closeout-20261028'
d = json.loads((OUT / 'evidence_tables.json').read_text(encoding='utf-8'))
names = {'hit_at_k':'Hit@3', 'mrr_at_k':'MRR@3', 'faithfulness':'Faithfulness',
         'context_precision':'Context precision', 'context_recall':'Context recall', 'answer_relevancy':'Answer relevancy'}

def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |'] +
                     ['| '+' | '.join(map(str,r))+' |' for r in rows])

human = d['human']
insert = {
 'AUTOMATED_PRIMARY_TABLE':table(['Metric','Matched queries','A','B','C'],
     [[names[r['metric']],r['n']]+[f"{r[c]:.4f}" for c in 'ABC'] for r in d['primary_automated']]),
 'RECONCILED_TABLE':table(['Metric','Matched queries','A','B','C'],
     [[names[r['metric']],r['matched_queries']]+[f"{float(r[c]):.4f}" for c in 'ABC'] for r in d['current_reconciled_retrieval']]),
 'HUMAN_DESCRIPTIVE_TABLE':table(['Module / dimension','Config','Scores','Mean','Median'],
     [[r['module']+' '+r['dimension'],r['configuration'],r['rating_count'],f"{r['mean']:.4f}",f"{r['median']:.0f}"]
      for r in human['descriptives'] if r['language']=='all']),
 'RELIABILITY_TABLE':table(['Dimension','Outputs','Alpha','95% interval'],
     [[r['module']+' '+r['dimension'],r['unique_outputs'],f"{r['ordinal_alpha']:.4f}",f"[{r['ci95_low']:.4f}, {r['ci95_high']:.4f}]"] for r in human['reliability']]),
 'COMPARISON_TABLE':table(['Dimension','Contrast','Mean difference','95% interval','Raw p','Holm p'],
     [[r['module']+' '+r['dimension'],r['contrast'].replace(' minus ','-'),f"{r['mean_difference']:.4f}",
       f"[{r['ci95_low']:.4f}, {r['ci95_high']:.4f}]",f"{r['p_value']:.4f}",f"{r['holm_p_value']:.4f}"] for r in human['comparisons']])
}
p=OUT/'CHAPTER_4.md';content=p.read_text(encoding='utf-8')
for k,v in insert.items():content=content.replace('{{'+k+'}}',v)
assert '{{' not in content
p.write_text(content,encoding='utf-8')

def blocks(text):
    lines=text.splitlines();i=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r'[-: ]+',x) for x in cells):rows.append(cells)
                i+=1
            yield 'table',rows;continue
        if line.startswith('#'):
            level=len(line)-len(line.lstrip('#'));yield 'heading',(level,line[level:].strip());i+=1;continue
        if line.startswith('!['):
            match=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
            yield 'image',(match[1],match[2]);i+=1;continue
        if line.startswith('- '):yield 'bullet',line[2:];i+=1;continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','![','- ')):
            paragraph.append(lines[i].strip());i+=1
        yield 'paragraph',' '.join(paragraph)

styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='BodyDraft',fontName='Times-Roman',fontSize=11,leading=15,spaceAfter=8,allowWidows=0,allowOrphans=0))
styles.add(ParagraphStyle(name='TableDraft',fontName='Helvetica',fontSize=8.1,leading=10.5,spaceAfter=0))
styles.add(ParagraphStyle(name='CaptionDraft',fontName='Times-Italic',fontSize=9.5,leading=12,spaceAfter=10))
styles.add(ParagraphStyle(name='TitleDraft',fontName='Helvetica-Bold',fontSize=21,leading=26,spaceAfter=20,textColor=colors.HexColor('#163f50')))
for s in ['Heading1','Heading2','Heading3']:
    styles[s].fontName='Helvetica-Bold';styles[s].textColor=colors.HexColor('#163f50');styles[s].spaceBefore=12;styles[s].spaceAfter=8
    styles[s].keepWithNext=True

def inline(s):
    s=escape(s)
    s=re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',s)
    s=re.sub(r'`([^`]+)`',r'\1',s)
    return s

def pdf_elements(text):
    out=[]
    for kind,value in blocks(text):
        if kind=='heading':
            level,t=value;out.append(Paragraph(inline(t),styles['TitleDraft' if level==1 else 'Heading'+str(min(level,3))]))
        elif kind=='table':
            n=len(value[0]);widths=([135,55,90,188] if n==4 else [145,75,80,84,84] if n==5 else [85,48,68,119,74,74] if n==6 else [468/n]*n)
            rows=[[Paragraph(inline(c),styles['TableDraft']) for c in row] for row in value]
            t=Table(rows,colWidths=widths,repeatRows=1,hAlign='LEFT')
            t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eff2')),('VALIGN',(0,0),(-1,-1),'TOP'),
                ('LINEBELOW',(0,0),(-1,0),.6,colors.HexColor('#59727a')),('LINEBELOW',(0,-1),(-1,-1),.4,colors.grey),
                ('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
                ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f7f9fa')])]))
            out.extend([t,Spacer(1,8)])
        elif kind=='image':
            label,path=value;img=Image(str(OUT/path));img.drawHeight=img.imageHeight*468/img.imageWidth;img.drawWidth=468
            out.extend([img,Spacer(1,4)])
        else:
            sty='CaptionDraft' if re.match(r'^(Table|Figure) 4\.\d+\.',value) else 'BodyDraft'
            out.append(Paragraph(('&#8226; ' if kind=='bullet' else '')+inline(value),styles[sty]))
    grouped=[];i=0
    while i<len(out):
        if isinstance(out[i],(Table,Image)) and i+2<len(out) and isinstance(out[i+1],Spacer) and isinstance(out[i+2],Paragraph) and out[i+2].style.name=='CaptionDraft':
            grouped.append(KeepTogether(out[i:i+3]));i+=3
        else:grouped.append(out[i]);i+=1
    return grouped

story=[Paragraph('Thesis results and revision package',styles['TitleDraft']),
       Paragraph('Dictionary-Assisted Hybrid Retrieval-Augmented Generation Assistant for Code-Switched Local Government Services Inquiries in Davao City',styles['Heading2']),
       Spacer(1,18),Paragraph('Researcher review draft | 28 October 2026',styles['BodyDraft']),
       Paragraph('Prepared from archived evaluation records, the 20260923 manuscript, the two-module audit amendment and the Thesis Tracker. Tables and figures report existing results; no model or judge evaluation was rerun.',styles['BodyDraft']),
       Paragraph('Contains Chapters 4 and 5 drafts, Chapters 1-3 replacement passages, and an adviser/submission checklist. Editable-manuscript integration and the department template are deferred at the researcher\'s request. This is not an institution-approved final manuscript.',styles['BodyDraft']),
       Paragraph('Reading order',styles['Heading2'])]
for t in ['Chapter 4: Results and Discussion','Chapter 5: Summary, Conclusions and Recommendations','Chapters 1-3: Revision package','Adviser review and submission preparation']:story.append(Paragraph(t,styles['BodyDraft']))
files=['CHAPTER_4.md','CHAPTER_5.md','CHAPTERS_1_TO_3_REVISION_PACKAGE.md','ADVISER_REVIEW_AND_SUBMISSION.md']
for name in files:story.append(PageBreak());story.extend(pdf_elements((OUT/name).read_text(encoding='utf-8')))

def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#53636b'))
    canvas.drawString(72,36,'LGSDeliveryRAGAssistant | Researcher review draft | 28 October 2026')
    canvas.drawRightString(540,36,str(doc.page));canvas.restoreState()

SimpleDocTemplate(str(OUT/'THESIS_RESULTS_REVIEW.pdf'),pagesize=(612,792),rightMargin=72,leftMargin=72,topMargin=58,bottomMargin=56,
                  title='Thesis results and revision package',author='LGSDeliveryRAGAssistant research project').build(story,onFirstPage=footer,onLaterPages=footer)

# Portable fragments: plain UTF-8 LaTeX, no fabricated department template.
texdir=OUT/'latex';texdir.mkdir(exist_ok=True)
def tex_escape(s):
    chars={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    return ''.join(chars.get(c,c) for c in s.replace('**','').replace('`',''))
for file in files[:2]:
    ts=[]
    for kind,v in blocks((OUT/file).read_text(encoding='utf-8')):
        if kind=='heading':
            level,t=v;t=re.sub(r'^(Chapter [45] |[45]\.\d+(?:\.\d+)? )','',t)
            ts.append('\\'+{1:'chapter',2:'section',3:'subsection'}.get(level,'subsubsection')+'{'+tex_escape(t)+'}')
        elif kind=='table':
            n=len(v[0]);ts.append(r'{\small\begin{longtable}{@{}'+''.join('p{'+str(round((6.5-(n-1)*.16)/n,3))+'in}' for _ in range(n))+r'@{}}\toprule')
            ts.append(' & '.join(tex_escape(c) for c in v[0])+r' \\ \midrule\endhead')
            ts.extend(' & '.join(tex_escape(c) for c in row)+r' \\' for row in v[1:]);ts.append(r'\bottomrule\end{longtable}}')
        elif kind=='image':ts.append(r'\begin{center}\includegraphics[width=\textwidth]{../'+v[1]+r'}\end{center}')
        else:ts.append((r'\noindent\textbullet\ ' if kind=='bullet' else '')+tex_escape(v)+'\n')
    (texdir/(Path(file).stem.lower()+'.tex')).write_text('\n\n'.join(ts),encoding='utf-8')
(texdir/'preview_main.tex').write_text(r'''% Generic review wrapper only; not the department template.
\documentclass[12pt]{report}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[margin=1in]{geometry}
\usepackage{graphicx,longtable,booktabs,array}
\setlength{\emergencystretch}{3em}
\begin{document}
\setcounter{chapter}{3}
\input{chapter_4.tex}
\input{chapter_5.tex}
\end{document}
''',encoding='utf-8')
(texdir/'README.txt').write_text('LaTeX fragments prepared from the review drafts. The official template and source integration are deferred by the researcher. No TeX engine was available; these fragments have not been compiled. THESIS_RESULTS_REVIEW.pdf was rendered with ReportLab and is not a LaTeX compilation. When integrating, use the department template and verify all tables, figures, numbering and citations. Run the preview wrapper from this latex directory if a TeX engine is installed.\n',encoding='utf-8')
print('Filled five evidence tables; created review PDF and two LaTeX chapter fragments.')
