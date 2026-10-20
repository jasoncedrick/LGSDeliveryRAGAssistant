"""Predeclare source-grounded development controls before evaluator calls."""
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.offline_judge_grounding import VERSION,INSTRUCTION
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 out=ROOT/'experiments/context-precision-calibration-v1';out.mkdir(exist_ok=True)
 if (out/'controls.json').exists():print('Existing declared controls preserved');return
 source=ROOT/'experiments/t06-formal-development-validation-v4/development_groups.derived.json';groups=json.loads(source.read_text(encoding='utf-8'));assert len(groups)==30 and all(g['split']=='development' for g in groups)
 corpus=ROOT/'experiments/chapter3-table-repaired-development-v1/corpus.json';chunks={r['chunk_id']:r for r in json.loads(corpus.read_text(encoding='utf-8'))};groups={g['group_id']:g for g in groups}
 plan=[
 ('SCENARIO-BB-001',[
 ('DEV120-BB-PDF0002-C002',1,'Lists new-application form and location-map requirements explicitly.'),
 ('DEV120-BB-PDF0002-C003',1,'Lists employee certification, DTI and SEC documents; partial checklist evidence is useful.'),
 ('DEV120-BB-PDF0001-C001',0,'Office cover contains no required documents.'),
 ('DEV120-BB-PDF0002-C001',0,'Service introduction describes pre-assessment but lists no document requirement requested by the question.')]),
 ('SCENARIO-CTO-003',[
 ('DEV120-CTO-PDF0036-C001',1,'States Basic Real Property Tax rate of 1.5 percent of assessed value.'),
 ('DEV120-CTO-PDF0036-C002',1,'States the 1 percent SEF levy and assessed-value base; includes Basic RPT rate.'),
 ('DEV120-CTO-PDF0001-C001',0,'Office cover contains no RPT or SEF rates.'),
 ('DEV120-CTO-PDF0031-C001',0,'Book-registration workflow and processing minutes do not state the requested RPT/SEF rates.')]),
 ('SCENARIO-OCBO-006',[
 ('DEV120-OCBO-PDF0103-C002',1,'States CTC owner/representative identification, SPA, and affidavit-of-loss requirements.'),
 ('DEV120-OCBO-PDF0104-C002',1,'Explicitly states PHP50 per document, one copy, for the CTC service.'),
 ('DEV120-OCBO-PDF0001-C001',0,'Office cover gives no CTC fees or requirements.'),
 ('DEV120-OCBO-PDF0002-C001',0,'Building-permit issuance scope and application letter are a different service, not the CTC-of-lost-permit checklist.')]),
 ('SCENARIO-CPDO-003',[
 ('DEV120-CPDO-PDF0022-C001',1,'States zoning percentage and filing fees for agricultural/residential categories.'),
 ('DEV120-CPDO-PDF0022-C002',1,'States commercial/industrial filing fee of PHP300 per application.'),
 ('DEV120-CPDO-PDF0001-C001',0,'Office cover provides no zoning or filing charges.'),
 ('DEV120-CPDO-PDF0019-C001',0,'Service heading and scope identify the clearance but state no requested zoning rate or filing charge.')]),
 ('SCENARIO-BFP-002',[
 ('DEV120-BFP-PDF0001-C019',1,'Explicit FSIC occupancy/business fee applicability, FSIF 15 percent base and PHP500 minimum.'),
 ('DEV120-BFP-PDF0001-C020',1,'FSIF sample calculation, minimum and explicit zero-assessment exception.'),
 ('DEV120-BFP-PDF0001-C006',0,'Maintenance-report description contains no FSIF fee, minimum or zero exception.'),
 ('DEV120-BFP-PDF0001-C041',0,'Matrix report/application mappings contain no FSIF calculation, minimum or zero exception.')])]
 cases=[]
 for gid,specs in plan:
  group=groups[gid]
  for language,question in group['queries'].items():
   for i,(cid,label,rationale) in enumerate(specs,1):
    c=chunks[cid];pdf=ROOT/'data/raw_charters'/c['file_source'];assert sha(pdf)==c['pdf_sha256']
    cases.append({'case_id':f'{gid}-{language}-CONTROL{i}','group_id':gid,'pillar':group['pillar'],'language':language,'question':question,'reference_answer':group['ground_truth_reference_answer'],'chunk_id':cid,'context':c['text_content'],'expected_verdict':str(label),'label_basis':rationale,'source_pdf':c['file_source'],'pdf_relative_page':c['pdf_relative_page'],'source_pdf_sha256':c['pdf_sha256'],'annotation_status':'ASSISTANT_SOURCE_COMPARED_CALIBRATION_LABEL_NOT_INDEPENDENT_EXPERT_GOLD'})
 assert len(cases)==60 and len({r['case_id'] for r in cases})==60
 (out/'controls.json').write_text(json.dumps(cases,ensure_ascii=False,indent=2),encoding='utf-8')
 (out/'candidate_instruction.txt').write_text(INSTRUCTION,encoding='utf-8')
 protocol={'scope':'Offline evaluator calibration only; no pipeline, benchmark, reference or retrieval modifications','held_out_accessed':False,'freeze':False,'cases':60,'offices':5,'languages':3,'controls_per_office_language':4,'positives_per_cell':2,'negatives_per_cell':2,'source_groups_sha256':sha(source),'corpus_sha256':sha(corpus),'controls_sha256':sha(out/'controls.json'),'candidate_instruction_version':VERSION,'candidate_instruction_sha256':sha(out/'candidate_instruction.txt'),'source_review':'Original PDF hashes checked for every control; source passages and prior reviewed reference maps compared before declaring labels.','judge_versions':['Original RAGAS 0.1.5 Context Precision prompt plus existing strict JSON format contract','Same RAGAS prompt with evidence-grounding instruction appended, requiring verbatim context evidence for positive verdicts'],'expected_labels_not_sent_to_judge':True,'raw_outputs_preserved':True,'invalid_output_policy':'Missing/invalid, never relabeled zero. Quote mismatch is a contract failure, not proof the context is irrelevant.','classification_policy':'Useful evidence for at least one requested fact is positive; mere topic/office overlap without requested facts is negative. Partial answers are not penalized as irrelevant.','review_policy':'Report FP/FN, format/evidence failures and valid coverage separately by office/language. No automatic promotion or statistical certification based on this small reused development calibration set.','supplemental_engineering_scope':'Calibration labels and evidence-quote validator are development diagnostics, not new manuscript performance metrics. Any revised judge must later rescore baseline and candidate with identical settings.','methodology':'20260923.pdf PDF24-25,31-34: offline evaluation, 15-cell Context Precision objective, development-only tuning and freeze before held-out testing.','tracker':'Thesis Tracker main tab requirements archived in t06-formal-development-validation-v4/methodology_and_tracker.json; no workbook changes.'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8');print('Declared 60 controls, 30 positive and 30 negative, before new judge calls',flush=True)
if __name__=='__main__':main()
