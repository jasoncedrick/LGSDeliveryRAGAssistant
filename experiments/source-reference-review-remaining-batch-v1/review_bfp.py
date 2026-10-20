from review_helpers import *
review('SCENARIO-BFP-002',[
('For FSIC for Certificate of Occupancy and new/renewal business applications, the fee panel states FSIF is 15% of all fees charged by LGU/PEZA, not less than PHP500. It explicitly adds: if assessment from LGUs/PEZA is zero, FSIF is zero. Other fees apply if applicable under the cited RIRR provision. Do not omit the zero-assessment exception or narrow the base to LGU-only regulatory fees.',[(1,'For FSIC (Certificate of Occupancy)','Other fees')])],['Correct incomplete fee rule and include PEZA.','Old supporting IDs largely FSEC; map actual FSIF span including zero exception.','Remove unsolicited incomplete checklist from fee-focused answer. Matrix inspection separately confirms fire-insurance row not marked for Occupancy.'])
review('SCENARIO-BFP-003',[
('The BFP charter classifies Simple transactions as processed within 1 day, Complex within 3 days, and Highly Technical within 7 days. It directs readers to JMC2021-01 for classification coverage. The source says days, not working days, and identifies FIRE STATION/OSCP/BOSS.',[(1,'OFFICE FIRE STATION','TYPE OF TRANSACTION')])],['Replace wrong fee-block supporting IDs with classification passage.','Remove unsupported working-day and strict/statutory embellishments; preserve source terms.'])
review('SCENARIO-BFP-006',[
('The BFP public warning says it does not accredit or recommend any brand, store or distributor of fire extinguishers/fire-fighting equipment. Its warning prohibits personnel from selling or recommending a specific fire-extinguisher brand.',[(1,'PUBLIC WARNING','How to file a complaint'),(1,'WARNING: BFP PERSONNEL','REPORT SUCH IRREGULARITY')]),
('The image panel says portable fire extinguishers are regulated by DTI through BPS and that each type must comply with appropriate Philippine National Standards for product safety/reliability. This supports no BFP brand accreditation; it should not be expanded into a claim that any product is suitable regardless of type or hazard.',[(1,'Portable Fire Extinguishers are regulated','PARTS'),(1,'There are 4 types','Dry Chemical: PNS')])],['Main warning supported.','Add image-transcription evidence for selling prohibition and DTI/BPS/PNS claims absent from old IDs.'])
# Independent context-association record; no fresh reference replacement for already-reviewed BFP001/004/005.
context={'reviewer':'assistant','visual_sources':['BFP_matrix.png','BFP_fees.png','BFP_notes.png','BFP_class.png','BFP_warning.png'],'status':'context_associations_checked_with_limitations','associations':[
{'row':'Application form','mapping':'Fire Station: FSEC form for FSEC, FSIC form across FSIC columns. Unified form OSCP spans FSEC and Occupancy; BOSS spans business columns.'},
{'row':'Architectural through Fire Protection documents','mapping':'Eight dots under FSEC. Three-set side label covers documentary block including as-built row; label is separated from its context in corpus C052/C053.'},
{'row':'As-built plan together with building permit (If there is changes/','mapping':'Dots under Occupancy and all four business columns, not FSEC. Preserve exact truncated wording and prior reviewer interpretation separately.'},
{'row':'Copy of Fire Insurance, if any','mapping':'Dots under four business columns only; occupancy cell blank, not an exemption statement.'},
{'row':'Estimated value and valid PRC licenses','mapping':'FSEC only.'},
{'row':'OBO endorsement, completion certificate, occupancy assessment fee','mapping':'Occupancy column only. Side label If applied in Fire Station/Lone District Fire Office applies to this grouped section, which also includes subsequent business-document rows.'},
{'row':'Valid occupancy certificate','mapping':'New business WITH valid occupancy-stage FSIC only.'},
{'row':'BPLO assessment','mapping':'Four business columns.'},
{'row':'FSCR/FSCCR/FSMR','mapping':'FSCR FSEC; FSCCR Occupancy; FSMR new business WITHOUT valid occupancy-stage FSIC and both renewal columns. Conditional system-installation note applies.'},
{'row':'Hot works','mapping':'Per-project dot FSEC; annual dots both renewal columns. Preserve if required and accompanying timing text.'}],
'already_corrected_groups':['SCENARIO-BFP-001','SCENARIO-BFP-004','SCENARIO-BFP-005'],
'limitations':['Blank cells must not be converted into exemption statements.','Detached side labels at end of corpus page mean some retrieved chunks lack their applicability context; review confirmation does not certify retrieval completeness.','Any future source-representation repair must be versioned and rebuilt with matching indices. No corpus change in this batch.','Assistant comparison is not independent expert audit.'],
'manual_action_required_now':False}
write(ROOT/'bfp_context_associations.json',context)
