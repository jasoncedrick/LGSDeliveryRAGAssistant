"""Versioned adviser amendment: reuse the registered sample and archived A/B/C outputs."""
import copy
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from prepare_expert_audit import ROOT, FINAL, OUT as OLD, read, write, digest, rank, records, verify_frozen

OUT = ROOT / 'experiments/t08-t09-expert-audit-v2-triple'
STATEMENT = 'This normalized query preserves the meaning, intent, and explicit details of the original query'


def template(module):
    t = (ROOT / 'audit_ui/packet.html').read_text(encoding='utf-8')
    t = t.replace('1?4', '1-4')
    t = t.replace('grid-template-columns:1fr 1fr;gap:20px;align-items:start',
                  'grid-template-columns:repeat(3,minmax(0,1fr));gap:15px;align-items:start')
    t = t.replace('@media(max-width:850px)', '@media(max-width:1100px)')
    t = t.replace('Two anonymous responses', 'Anonymous outputs')
    t = t.replace('schema_version:2', 'schema_version:3').replace('s.schema_version!==2', 's.schema_version!==3')
    t = t.replace('j===0?"left":"right"', '["X","Y","Z"][j]')
    t = t.replace('side===0?"Response X":"Response Y"', '"Response "+["X","Y","Z"][side]')
    t = t.replace('n+" / 120 responses complete"', 'n+" / "+allAnswers.size+" outputs complete"')
    t = t.replace('(i+1)+" / 60"', '(i+1)+" / "+packet.pairs.length')
    t = t.replace('n<=60', 'n<=packet.pairs.length').replace('%60', '%packet.pairs.length')
    t = t.replace('"Rater "+packet.rater_id+" · 60 queries · 120 responses · offline"',
                  '"Rater "+packet.rater_id+" | "+packet.module+" | "+packet.pairs.length+" queries | "+allAnswers.size+" outputs | offline"')
    t = t.replace('packet.rater_id+"-final-', 'packet.rater_id+"-"+packet.module+"-final-')
    t = t.replace('packet.rater_id+"-backup-', 'packet.rater_id+"-"+packet.module+"-backup-')
    t = t.replace('Take a break after every 20 queries.', 'Complete 15 queries per session. Download a backup and take a mandatory break of at least 10 minutes between sessions. Follow the five-session schedule in START_HERE.txt.')
    t = t.replace('function navigate(i){state.position=i;',
                  'function navigate(i){if(i>state.position&&i%packet.block_size===0&&!confirm("Session boundary: download a backup and take a mandatory break of at least 10 minutes. Have you taken your break?"))return;state.position=i;')
    if module == 'M1':
        start = t.index('<details class="instructions"')
        end = t.index('</details>', start) + len('</details>')
        guide = '<details class="instructions" open><summary>Module 1: normalization fidelity</summary><p>Compare each normalized output with the original query. Rate each output independently; equal scores are allowed. Do not rate the answer to the service question.</p><p><strong>'+STATEMENT+'</strong></p><p>1 = Strongly Disagree; 2 = Disagree; 3 = Neither Agree nor Disagree; 4 = Agree; 5 = Strongly Agree.</p><p>Check meaning, intent, service, actor/direction, numbers and explicit conditions. Record concerns in notes. Scores start blank; drafts may remain incomplete. Consult the facilitator if evidence is insufficient; do not guess a score. Final submission requires every rating.</p><p>Download a backup at breaks. Work independently. Complete this module before opening Module 2.</p></details>'
        t = t[:start] + guide + t[end:]
        t = t.replace('const dimensions=["relevance","faithfulness"];', 'const dimensions=["fidelity"];')
        t = t.replace('d.score<=4', 'd.score<=5')
        t = t.replace('relevance:{score:null},faithfulness:{score:null},', 'fidelity:{score:null},')
        t = t.replace('[1,2,3,4].forEach', '[1,2,3,4,5].forEach')
        t = t.replace('d==="relevance"?"Answer Relevance":"Factual Faithfulness"', json.dumps(STATEMENT))
        t = t.replace('relevance_score:v.relevance.score,\n faithfulness_score:v.faithfulness.score,', 'fidelity_score:v.fidelity.score,')
        t = t.replace('q.append(sources);', '')
        t = t.replace('card.append(passages);', '')
        t = t.replace('"Response "+["X","Y","Z"][side]', '"Normalized query "+["X","Y"][side]')
        t = t.replace('Evidence notes / document and page references', 'Meaning, intent and detail notes')
        t = t.replace('Rubric: manuscript Chapter 3, Table 2.', 'Scale: adviser amendment, Module 1 (five-point agreement).')
        t = t.replace('Complete 15 queries per session.', 'Session 1: complete 40 query comparisons, with a mandatory break after query 20.')
        t = t.replace('repeat(3,minmax(0,1fr))', 'repeat(2,minmax(0,1fr))')
    return t


def build():
    checked = verify_frozen()
    if (OUT / 'public').exists():
        raise FileExistsError('Preserve existing release; do not rebuild over issued packets.')
    reg = read(OLD / 'private/selection_registration.json')
    archives = {c: {r['question_id']: r for r in records(c)} for c in 'ABC'}
    differences = []
    allowed = {'ranking_metrics','ground_truth_chunk_ids','relevance_mapping_status','unresolved_legacy_ids'}
    for old in read(OLD / 'private/original_selected_records.json'):
        current = archives[old['configuration']][old['question_id']]
        changed = {k for k in set(old)|set(current) if old.get(k) != current.get(k)}
        if changed - allowed:
            raise ValueError('Archived audit content changed: '+str(changed))
        if changed:
            differences.append(dict(configuration=old['configuration'],question_id=old['question_id'],fields=sorted(changed)))
    groups = set(sum(reg['selected_groups'].values(), []))
    queries = sorted(q for q, r in archives['A'].items() if r['question_group_id'] in groups)
    code_queries = [q for q in queries if archives['A'][q]['language'] != 'english']
    assert len(queries) == 60 and len(code_queries) == 40
    old_packet = read(OLD / 'public/R01/packet.json')
    common = {p['query_id']: p for p in old_packet['pairs']}
    links = {s['document']: s['href'].split('#')[0] for p in old_packet['pairs'] for s in p['common_sources']}
    for p in old_packet['pairs']:
        for r in p['responses']:
            for s in r['passages']:
                links[s['document']] = s['href'].split('#')[0]
    shutil.copytree(OLD / 'public/sources', OUT / 'public/sources')
    mapping = []
    for module, qs, configs in [('M1', code_queries, 'BC'), ('M2', queries, 'ABC')]:
        items = {}
        for q in qs:
            a = archives['A'][q]
            qid = ('NQ-' if module == 'M1' else 'Q-') + rank('query-id', q)[:12]
            base = common['Q-' + rank('query-id', q)[:12]]
            item = {k: copy.deepcopy(base[k]) for k in ['question', 'language', 'category', 'common_sources']}
            item['query_id'] = qid
            item['answers'] = {}
            for c in configs:
                r = archives[c][q]
                assert r['question'] == a['question']
                if module == 'M1':
                    assert r['normalization']['status'] == 'SUCCESS'
                    text = r['normalization']['normalized_query']
                    assert isinstance(text, str) and text.strip()
                    passages = []
                else:
                    text = r['answer'] or ''
                    passages = [dict(document=p['file_source'], pdf_page=int(p['pdf_relative_page']),
                                     printed_page=p.get('source_page'), label=p['citation'], text=p['text'],
                                     href=links[p['file_source']]+'#page='+str(p['pdf_relative_page'])) for p in r['citations']]
                aid = ('N-' if module == 'M1' else 'R-') + rank('answer-id', q+'|'+c)[:16]
                item['answers'][c] = dict(answer_id=aid, text=text, passages=passages)
                mapping.append(dict(module=module, answer_id=aid, question_id=q, group_id=a['question_group_id'], configuration=c))
            items[q] = item
        positions = {q: i for i, q in enumerate(sorted(qs, key=lambda q: rank('triple-side-'+module, q)))}
        t = template(module)
        (ROOT / 'audit_ui' / (module.lower()+'_packet.html')).write_text(t, encoding='utf8')
        for n in range(3):
            rater = f'R{n+1:02d}'
            pairs = []
            for q in sorted(qs, key=lambda q: rank('triple-order-'+module+rater, q)):
                rotation = (positions[q]+n) % len(configs)
                order = configs[rotation:] + configs[:rotation]
                pairs.append({k: v for k, v in items[q].items() if k != 'answers'} |
                             {'responses': [items[q]['answers'][c] for c in order]})
            payload = dict(schema_version=3, rubric_version='normalization-fidelity-agreement-v1' if module=='M1' else 'chapter3-table2-v1',
                           rater_id=rater, module=module, block_size=20 if module=='M1' else 15,
                           packet_version='t08-t09-v3-triple', pairs=pairs)
            payload['packet_id'] = hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            folder = OUT / 'public' / (rater+'-'+module)
            write(folder / 'packet.json', payload)
            (folder / 'index.html').write_text(t.replace('__PACKET_JSON__', json.dumps(payload, ensure_ascii=False).replace('<', '\\u003c')), encoding='utf8')
    write(OUT / 'private/answer_key.json', mapping)
    shutil.copyfile(OLD / 'private/selection_registration.json', OUT / 'private/original_selection_registration.json')
    write(OUT / 'protocol_amendment.json', dict(date='2026-10-26', authority='User-supplied adviser mandate and explicit confirmation',
          formal_scoring_started=False, statement=STATEMENT, original_sample_preserved=True,
          module1=dict(queries=40, outputs_per_rater=80, records_three_raters=240, scale=[1,2,3,4,5]),
          module2=dict(queries=60, outputs_per_rater=180, records_three_raters=540, dimensions=2, scale=[1,2,3,4]),
          manuscript_change='Section 3.2.9 amendment required; original PDF remains unchanged.',
          selection_timing=reg['timing'], tracker_tab='Thesis Tracker'))
    write(OUT / 'private/provenance.json', dict(frozen_files_checked=checked,
          prior_archive_hashes=reg['archive_hashes'], selected_record_label_differences=differences,
          content_check='All selected A/B fields identical except explicitly listed retrieval-label metadata; no text regenerated.',
          archive_hashes={c: digest(FINAL/c/'interactions.jsonl') for c in 'ABC'},
          original_selection_sha256=digest(OLD/'private/selection_registration.json'),
          references=read(OLD/'methodology_snapshot.json')))
    package()


def package():
    for n in range(1,4):
        rater = f'R{n:02d}'
        dest = OUT / 'distribution' / (rater+'-two-module-audit.zip')
        dest.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(dest, 'w', zipfile.ZIP_DEFLATED) as z:
            for folder in ['sources',rater+'-M1',rater+'-M2']:
                for p in sorted((OUT/'public'/folder).rglob('*')):
                    if p.is_file(): z.write(p,p.relative_to(OUT/'public'))
            if (OUT/'START_HERE.txt').exists(): z.write(OUT/'START_HERE.txt','START_HERE.txt')
    write(OUT/'private/release_manifest.json', {str(p.relative_to(OUT)):digest(p) for d in ['public','distribution'] for p in sorted((OUT/d).rglob('*')) if p.is_file()})
    print(OUT)


if __name__ == '__main__':
    build()
