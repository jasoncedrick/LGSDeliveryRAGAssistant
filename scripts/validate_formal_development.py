"""Conservative source-span remapping of development references; never opens held-out data."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
import argparse
import unicodedata
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def tokens(text):
    text=''.join(' ' if unicodedata.category(c).startswith('P') else c for c in text)
    return re.findall(r'[a-z0-9]+',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower())


def occurrences(haystack,needle):
    if not needle:return []
    return [i for i in range(len(haystack)-len(needle)+1) if haystack[i:i+len(needle)]==needle]


def span_occurrences(haystack,needle):
    """Legacy splitter may cut the first/last word; interior words must match exactly."""
    exact=occurrences(haystack,needle)
    if exact or len(needle)<3:return exact
    return [i for i in range(len(haystack)-len(needle)+1)
            if haystack[i].endswith(needle[0]) and haystack[i+len(needle)-1].startswith(needle[-1])
            and haystack[i+1:i+len(needle)-1]==needle[1:-1]]


def main(output_name='t06-formal-development-validation-v1'):
    source=ROOT/'data/benchmark_scenarios_dev.json'
    legacy=ROOT/'data/eboss_corpus_chunks_v1.json'
    artifacts=ROOT/'experiments/chapter3-table-repaired-development-v1'
    if Path(output_name).name!=output_name:raise ValueError('Use experiment directory name')
    output=ROOT/'experiments'/output_name
    if output.exists():raise ValueError('Preserve prior validation')
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    groups=read(source);old={c['chunk_id']:c for c in read(legacy)}
    pages=read(artifacts/'source_pages.json');chunks=read(artifacts/'corpus.json')
    assert len(groups)==30 and len({g['group_id'] for g in groups})==30
    assert all(g['split']=='development' and set(g['queries'])=={'english','taglish','bislish'} for g in groups)
    assert all(isinstance(q,str) and q.strip() for g in groups for q in g['queries'].values())
    assert len({q for g in groups for q in g['queries'].values()})==90
    counts=Counter(g['pillar'] for g in groups);assert len(counts)==5 and set(counts.values())=={6}
    output.mkdir()
    write=lambda name,v:(output/name).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    write('development_groups.snapshot.json',groups)
    mappings=[];derived=[]
    for g in groups:
        mapped=[];references=[]
        for cid in g['ground_truth_chunk_ids']:
            item={'legacy_chunk_id':cid}
            if cid not in old:
                item.update(status='MISSING_LEGACY_ID');references.append(item);continue
            previous=old[cid]
            candidates=[p for p in pages if p['file_source']==previous['file_source'] and p['pdf_relative_page']==previous['pdf_relative_page']]
            if len(candidates)!=1:
                item.update(status='SOURCE_PAGE_NOT_UNIQUE');references.append(item);continue
            page=candidates[0];needle=tokens(previous['text_content']);hay=tokens(page['text'])
            if needle and str(page.get('source_page'))==needle[0]:needle=needle[1:]
            positions=span_occurrences(hay,needle)
            item.update(source_page_id=page['source_page_id'],pdf_relative_page=page['pdf_relative_page'],
                        printed_page=page['source_page'],legacy_text=previous['text_content'])
            if len(positions)!=1:
                item.update(status='MANUAL_SPAN_REVIEW_REQUIRED',exact_span_matches=len(positions))
            else:
                # Map only new chunks containing an exact contiguous segment of the verified source span.
                # Tokens are lexical audit tokens, not embedding tokens; 120/20 chunks remain untouched.
                start=positions[0];end=start+len(needle);new_ids=[]
                for c in chunks:
                    if c['source_page_id']!=page['source_page_id']:continue
                    ct=tokens(c['text_content']);spots=span_occurrences(hay,ct)
                    if len(spots)==1 and min(end,spots[0]+len(ct))>max(start,spots[0]):new_ids.append(c['chunk_id'])
                if not new_ids:item.update(status='MANUAL_CHUNK_MAPPING_REQUIRED')
                else:item.update(status='EXACT_LEXICAL_SOURCE_SPAN_MAPPED',new_chunk_ids=new_ids,source_lexical_token_span=[start,end]);mapped.extend(new_ids)
            references.append(item)
        valid=all(r['status']=='EXACT_LEXICAL_SOURCE_SPAN_MAPPED' for r in references)
        mappings.append({'group_id':g['group_id'],'references':references,'all_references_mapped':valid,
                         'reference_answer_semantic_validation':'not established by lexical mapping'})
        derived.append({**g,'legacy_ground_truth_chunk_ids':g['ground_truth_chunk_ids'],
                        'ground_truth_chunk_ids':list(dict.fromkeys(mapped)) if valid else [],
                        'mapping_status':'PROVISIONAL_EXACT_SPAN_MAPPING' if valid else 'BLOCKED_PENDING_SOURCE_REVIEW'})
    write('source_reference_mapping.json',mappings);write('development_groups.derived.json',derived)
    report={'groups':30,'queries':90,'pillars':dict(counts),'language_variants':['english','taglish','bislish'],
            'legacy_reference_count':sum(len(g['ground_truth_chunk_ids']) for g in groups),
            'reference_status_counts':dict(Counter(r['status'] for g in mappings for r in g['references'])),
            'groups_fully_mapped':sum(g['all_references_mapped'] for g in mappings),
            'blocked_group_ids':[g['group_id'] for g in mappings if not g['all_references_mapped']],
            'semantic_answer_validation':'Manual source comparison still needed; exact old-span presence does not prove reference-answer completeness.',
            'policy':'No page-wide or nearest-neighbour gold-ID substitution; incomplete group mappings withheld from ranking metrics.',
            'normalization':'Punctuation/whitespace canonicalization; only first/last word fragments allowed, all interior words must match exactly.',
            'original_development_file_modified':False,'held_out_accessed':False,
            'input_hashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [source,legacy,artifacts/'source_pages.json',artifacts/'corpus.json']}}
    write('summary.json',report)
    write('hashes.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.is_file()})
    print(json.dumps({k:v for k,v in report.items() if k!='input_hashes'},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-name',default='t06-formal-development-validation-v1');main(p.parse_args().output_name)
