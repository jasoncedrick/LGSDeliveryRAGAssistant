"""Create a source-grounded employee meeting packet without model calls."""
from pathlib import Path
import fitz, json, hashlib, re
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/employee-annotation-meeting-v1'
OUT.mkdir(parents=True,exist_ok=True)
pages=[
('Employee briefing','Research annotation partnership', '''
<p class="lead">We are requesting your service expertise to check whether a research assistant gives useful answers that are supported by Davao City Citizens' Charter documents.</p>
<p><b>Study</b><br>Dictionary-Assisted Hybrid Retrieval-Augmented Generation Assistant for Code-Switched Local Government Services Inquiries in Davao City</p>
<p><b>Researchers</b><br>Christian Mari B. Civiles, Juniel Francis Lae A. Portillo, and Jason Cedrick P. Rabanes<br>Ateneo de Davao University</p>
<h2>What the assistant does</h2>
<p>A citizen asks a service question in English, Tagalog or Bislish. The assistant searches a prepared collection of official charter passages and uses the retrieved evidence to generate a cited answer. We are studying whether it understands these questions and answers them accurately. This is a research prototype.</p>
<h2>The help we are requesting</h2>
<ul><li>Help identify qualified domain experts familiar with the services covered by the study and fluent in the three study languages.</li>
<li>Review prepared reference passages and flag unclear wording, table relationships, or source-version issues through a documented source-review process.</li>
<li>Independently rate anonymous answers for <b>Answer Relevance</b> and <b>Factual Faithfulness</b>, using the supplied rubric.</li></ul>
<h2>Services covered</h2>
<p>Business Bureau; City Treasurer's Office; Office of the City Building Official; City Planning and Development Office; and Bureau of Fire Protection.</p>
<p>Please help us confirm the correct office contacts, including whether a separate referral is needed for BFP. We should also confirm that each proposed expert can assess the full range of services required by the study.</p>
<h2>What we hope to agree on today</h2>
<p>An appropriate contact or endorsement route, possible expert participants, access to the correct public charter versions, and a practical schedule for orientation and independent review. Participation and any institutional requirements will be discussed before formal collection.</p>
<p class="small">Meeting date and venue __________________________<br>Researcher contact ______________________________</p>
'''),
('Employee briefing','What expert review involves','''
<p class="lead">You will score each anonymous answer independently. We are evaluating the assistant's output, not employee performance.</p>
<h2>Planned workload in the manuscript</h2>
<table><tr><th>Review unit</th><th>Planned amount</th></tr>
<tr><td>Scenario groups selected for expert audit</td><td>20 groups, four per service category</td></tr>
<tr><td>Language variants</td><td>Three per group, giving 60 questions</td></tr>
<tr><td>Anonymous answers</td><td>Two per question, giving 120 answers per expert</td></tr>
<tr><td>Panel</td><td>Three independent experts, each reviewing all 120 answers</td></tr>
<tr><td>Scores</td><td>Two scores per answer, each from 1 to 4</td></tr></table>
<p>Across three experts this gives 360 answer reviews and 720 score values when complete. We will measure the time needed in a pilot before committing to a formal session duration. Separate blocks and breaks can be arranged.</p>
<h2>What you will receive</h2>
<ol><li>The original citizen question and verified reference material with official page citations.</li>
<li>Anonymous system answers and the source passages actually retrieved for each answer.</li>
<li>Two separate scoring controls, space for an evidence note, and an option to flag an item that cannot be judged from the supplied evidence.</li></ol>
<h2>How to review</h2>
<p>Read the question, compare each answer with the evidence, and score the two dimensions separately. Identify the claim or source passage behind an error flag. Equal scores for the two answers are allowed.</p>
<p>During formal scoring, work independently. System identities, automated scores, and other experts' scores will be hidden. Please do not try to infer a system's identity.</p>
<h2>If the source is unclear</h2>
<p>Flag the specific passage rather than guessing. If current office practice differs from the archived charter, record that difference and identify a separately documented source if available. A source clarification and an answer-quality rating are different records.</p>
<p class="small">The team will agree on procedures for contradictory evidence, clarification responses, incomplete answers, and missing ratings before formal collection.</p>
'''),
('Employee handout','Scoring guide and practice','''
<p>Give each answer two separate scores. Fluency, length, or a printed citation alone does not establish correctness.</p>
<table><tr><th>Score</th><th>Answer Relevance</th><th>Factual Faithfulness</th></tr>
<tr><td>1</td><td>Does not address the inquiry or answers a different question.</td><td>Main answer is unsupported or contradicts the official charter.</td></tr>
<tr><td>2</td><td>Addresses part of the inquiry but misses the primary procedural need.</td><td>Some claims are supported, but there is a major error in a fee, requirement, or office.</td></tr>
<tr><td>3</td><td>Addresses the main inquiry with limited minor omissions.</td><td>Main claims are supported, with minor imprecisions that do not alter the procedure.</td></tr>
<tr><td>4</td><td>Directly and comprehensively addresses all parts of the inquiry.</td><td>All factual claims are supported and traceable to official documents.</td></tr></table>
<p class="small">Condensed from manuscript Table 2, printed page 30, PDF page 35.</p>
<h2>Fictional practice only</h2>
<p><b>This example is invented. It is not a Davao City service or an actual system output. Practice scores will not enter the study dataset.</b></p>
<p><b>Question</b><br>Where do I submit a new vendor-registration application, what documents do I need, and what is the fee?</p>
<p><b>Training source</b><br>Submit a completed application form and one photocopy of a valid ID to the Vendor Services Desk. The application fee is PHP 120. [Training Charter, page 1]</p>
<p><b>Anonymous answer X</b><br>Submit to the Vendor Services Desk. Bring a completed application form and one photocopy of a valid ID. The fee is PHP 120. [Training Charter, page 1]</p>
<p><b>Anonymous answer Y</b><br>Submit to the Vendor Services Desk. Bring a completed application form and one photocopy of a valid ID. The fee is PHP 500. [Training Charter, page 1]</p>
<p><b>Circle one value for each dimension</b><br>X relevance: 1 / 2 / 3 / 4 &nbsp;&nbsp; X faithfulness: 1 / 2 / 3 / 4<br>Y relevance: 1 / 2 / 3 / 4 &nbsp;&nbsp; Y faithfulness: 1 / 2 / 3 / 4</p>
<p>Evidence note ___________________________________________________<br>________________________________________________________________</p>
'''),
('Researcher use only','How to lead the first meeting','''
<p class="lead">Use this meeting to explain the task and establish cooperation. Schedule formal blind rating after the study pipeline and review instructions are ready.</p>
<h2>A simple opening you can read</h2>
<p>“Good morning, and thank you for meeting with us. We are developing a research assistant for questions about local government services, including questions written in English, Tagalog and Bislish. It searches Citizens' Charter passages before producing an answer. We need service experts to help us check whether its answers address the citizen's question and are supported by the documents. Today, we would like to explain the review task, demonstrate one fictional example, and ask about the appropriate participants and process for working with your office.”</p>
<h2>Suggested first meeting agenda</h2>
<table><tr><th>Time</th><th>What to present</th></tr>
<tr><td>0 to 3 minutes</td><td>Research purpose and the specific request for expert help</td></tr>
<tr><td>3 to 7 minutes</td><td>Citizen question, source evidence, and anonymous answer example</td></tr>
<tr><td>7 to 12 minutes</td><td>Two scoring dimensions and independent fictional practice</td></tr>
<tr><td>12 to 20 minutes</td><td>Participants, office coverage, workload, source versions and access route</td></tr>
<tr><td>20 to 25 minutes</td><td>Confirm the next contact, required documents and tentative schedule</td></tr></table>
<h2>What to bring</h2>
<ul><li>Employee pages 1 to 3 of this packet and the manuscript rubric.</li>
<li>A short school or adviser introduction and any request letter your institution requires. Fill in verified contacts before sharing.</li>
<li>A readable public charter page to explain what source evidence looks like.</li>
<li>A way to take meeting notes. A static fictional demonstration works even without the model server.</li></ul>
<h2>After the independent practice</h2>
<p>Discuss the evidence rather than asking participants to match a preferred score. Suggested training anchors: X relevance 4 and faithfulness 4; Y relevance 4 and faithfulness 2 because the fee is wrong. Confirm this distinction during orientation before freezing the scoring instructions.</p>
<p class="small">Keep this page separate from the employee handout. Do not show suggested scores before independent practice. Actual formal ratings must not be coached.</p>
'''),
('Researcher use only','Decisions and follow through','''
<h2>Questions to settle with the office</h2>
<ol><li>Who can authorize or coordinate participation, and is a formal endorsement needed?</li>
<li>Which experts have service-domain knowledge and fluency in all three study languages? Can each cover the full audit, or is an adviser-approved panel adjustment needed?</li>
<li>Which public charter versions should support the reference evidence, and who can provide documented clarification for ambiguous wording?</li>
<li>What session format, equipment, location, breaks and availability are practical?</li>
<li>What participant information, permission, confidentiality and acknowledgement arrangements should be settled through the institution before formal rating?</li></ol>
<h2>Record before leaving</h2>
<p>Office or contact channel __________________________________________<br>Required endorsement or introduction _______________________________<br>Possible panel and service coverage __________________________________<br>Preferred schedule and session format _______________________________<br>Source documents or clarification follow-up __________________________<br>Next action and responsible person __________________________________</p>
<h2>Before formal annotation begins</h2>
<p>Complete development evaluation, register the frozen pipeline, and generate the final held-out outputs. Preselect the balanced expert-audit subset without choosing cases by answer quality. Prepare verified references, actual retrieved evidence, anonymous answer IDs and randomized presentation.</p>
<p>Keep the identity mapping separate. Document who is blinded in practice. Agree on missing-evidence and failed-output handling, pilot the workload, and finalize participant arrangements and the rubric before collecting independent ratings. Include all scheduled cases and retain unfavorable outcomes.</p>
<h2>Methodology and task alignment</h2>
<p>Chapter 3.2.9, PDF pages 34 to 36, establishes the evidence records, expert panel, blinded review, two 1 to 4 scores, and inter-rater reliability assessment. Its reliability threshold is a target to evaluate, not a result to promise.</p>
<p>The existing T08 to T12 preparation materials map the next work to audit-packet preparation, rubric/interface preparation, independent sessions, agreement analysis and paired comparison. This meeting supports recruitment and preparation; it does not complete those tasks.</p>
<p>The meeting agenda, time blocks and administrative questions in this packet are preparation suggestions. The source-review role should be documented separately from final blind scoring. If the same employees perform both roles, record that overlap and any implications for independence with the adviser.</p>
<p class="small">Sources: 20260923.pdf, PDF pages 1 and 34 to 36; existing FACILITATOR_GUIDE.txt and MOCK_RATER_HANDOUT.txt in experiments/t08-t12-rater-preparation. The facilitator guide records alignment to the Thesis Tracker main tab, T08 to T12. No tracker status has been changed. Prepared 19 October 2026.</p>
''')]
css='''body{font-family:Arial,sans-serif;font-size:10.6pt;line-height:1.30;color:#171717} h1{font-size:23pt;line-height:1.1;margin:6pt 0 13pt;color:black} h2{font-size:12pt;margin:14pt 0 5pt;color:black} p{margin:0 0 9pt} .lead{font-size:12pt;line-height:1.35} .eyebrow{font-size:9pt;color:#555} .small{font-size:8.7pt;color:#444} ul,ol{margin:4pt 0 10pt;padding-left:19pt} li{margin-bottom:6pt} table{border-collapse:collapse;width:100%;font-size:9.3pt;margin:7pt 0 11pt} td,th{border:0.6pt solid #d9d9d9;padding:7pt;text-align:left;vertical-align:middle} th{background:#e6edf2;color:black}'''
doc=fitz.open();alltext=[];qa=[]
for i,(label,title,body) in enumerate(pages,1):
 page=doc.new_page(width=595.28,height=841.89)
 html=f'<div class="eyebrow">DAVAO CITY SERVICE INQUIRIES STUDY &nbsp; | &nbsp; {label.upper()}</div><h1>{title}</h1>'+body
 spare,scale=page.insert_htmlbox(fitz.Rect(47,43,548,789),html,css=css,scale_low=1)
 if spare<0:raise RuntimeError(f'Page {i} overflows; simplify rather than shrink')
 page.insert_text((47,815),'Employee annotation meeting packet  |  19 October 2026',fontsize=8,color=(.35,.35,.35))
 page.insert_text((515,815),f'{i} / {len(pages)}',fontsize=8,color=(.35,.35,.35))
 qa.append({'page':i,'remaining_height':spare,'scale':scale})
 alltext.append(title+'\n'+re.sub('<[^>]+>',' ',body).replace('&nbsp;',' '))
pdf=OUT/'Davao_City_Employee_Annotation_Meeting_Packet.pdf';doc.save(pdf)
(OUT/'meeting_packet_editable.txt').write_text('\n\n'.join(alltext),encoding='utf-8')
images=OUT/'qa';images.mkdir(exist_ok=True)
for i,page in enumerate(doc):page.get_pixmap(matrix=fitz.Matrix(1.25,1.25)).save(images/f'page-{i+1}.png')
sources=[Path(r'D:\thesis\20260923.pdf'),ROOT/'experiments/t08-t12-rater-preparation/FACILITATOR_GUIDE.txt',ROOT/'experiments/t08-t12-rater-preparation/MOCK_RATER_HANDOUT.txt']
(OUT/'provenance.json').write_text(json.dumps({'sources':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},'pdf_pages_inspected':[1,34,35,36],'content_policy':'Administrative proposals labeled; no held-out query records accessed; no research task completion asserted','layout':qa},indent=2),encoding='utf-8')
print(pdf);print(json.dumps(qa))
