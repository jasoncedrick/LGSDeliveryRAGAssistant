"""Create an auditable held-out/resume adapter of the unchanged legacy scorer."""
import difflib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def adapted(source):
    replacements = [
        ('"""Offline local RAGAS scoring of archived development interactions; no serving filter."""',
         '"""Registered held-out RAGAS scoring; same metrics and legacy prompts, explicit nulls."""'),
        ("or output.exists():raise ValueError('Use experiment names and fresh output')", ":raise ValueError('Use experiment names')"),
        ("if protocol.get('held_out_accessed') is not False:raise ValueError('Only development archives accepted')",
         "validate_final_source(source, protocol, args)"),
        ('    output.mkdir()\n', '    output.mkdir(exist_ok=True)\n'),
        ("    current_record_id=None\n", "    current_record_id=None\n"),
        ("'scope':'Offline archived development evaluation; no runtime filtering or final benchmark claims'",
         "'scope':'Registered held-out A/B/C evaluation; no runtime filtering or test-guided tuning'"),
        ("'max_retries':0,'held_out_accessed':False", "'max_retries':0,'held_out_accessed':True"),
        ('    scored=[]\n    for r in selected:\n',
         "    scored=json.loads((output/'scores.json').read_text(encoding='utf-8')) if (output/'scores.json').exists() else []\n"
         "    completed={r['record_id'] for r in scored}\n"
         "    attempted=set()\n"
         "    if (output/'judge_calls.jsonl').exists():\n"
         "        attempted={json.loads(line)['record_id'] for line in (output/'judge_calls.jsonl').read_text(encoding='utf-8').splitlines() if json.loads(line).get('event')=='judge_prompt'}\n"
         "    for r in selected:\n"
         "        if r['record_id'] in completed:continue\n"),
        ("        if r.get('status')!='ANSWERED' or not r.get('answer') or not reference:",
         "        if r['record_id'] in attempted:\n"
         "            item.update(status='SCORING_ERROR',scores={m:None for m in args.metrics},error='Interrupted judge attempt preserved; no automatic retry')\n"
         "        elif r.get('status')!='ANSWERED' or not r.get('answer') or not reference:"),
        ('Generation K and configuration are recorded in the source protocol; development scoring is not frozen held-out evaluation or independent expert certification.',
         'Generation K, configuration and freeze are registered; automated judge scores are not independent expert certification.'),
    ]
    for before, after in replacements:
        if source.count(before) != 1:
            raise ValueError('Unexpected legacy scorer structure: ' + before[:65])
        source = source.replace(before, after, 1)
    insertion = '''
def validate_final_source(source, protocol, args):
    registration=ROOT/'experiments/t07-final-evaluation-v1'
    if source.parent!=registration or source.name not in ('A','B','C'):
        raise ValueError('Only the registered final A/B/C archive is accepted')
    if protocol.get('held_out_accessed') is not True or protocol.get('freeze') is not True:
        raise ValueError('Final source must carry its registered freeze')
    if args.context_precision_v2 or args.record_id or args.judge_output_tokens!=4096 or args.judge_timeout!=600:
        raise ValueError('Use the registered evaluator/settings and complete configuration')
    if not args.strict_metric_json or not args.strict_recall_json or args.strict_faithfulness_json:
        raise ValueError('Evaluator flags differ from registered legacy protocol')
    if args.metrics!=['faithfulness','context_precision','context_recall','answer_relevancy']:
        raise ValueError('Score all registered metrics in order')
    manifest=json.loads((registration/'execution_manifest.json').read_text(encoding='utf-8'))
    seal=json.loads((registration/'execution_manifest.seal.json').read_text(encoding='utf-8'))
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    if digest(registration/'execution_manifest.json')!=seal['sha256']:
        raise ValueError('Execution registration seal changed')
    for name,value in manifest['execution_code_hashes'].items():
        if digest(ROOT/name)!=value:raise ValueError('Frozen execution code changed: '+name)
    archive=source/args.archive_file
    if digest(archive)!=json.loads((source/'archive_seal.json').read_text(encoding='utf-8'))['sha256']:
        raise ValueError('Final generation archive changed')

'''
    source = source.replace('def main(args):\n', insertion + 'def main(args):\n', 1)
    before = "    write=lambda name,value:(output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')"
    after = """    def write(name,value):
        if name=='protocol.json' and (output/name).exists():
            if json.loads((output/name).read_text(encoding='utf-8'))!=value:raise ValueError('Cannot resume changed scoring protocol')
            return
        temporary=output/(name+'.tmp')
        temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
        temporary.replace(output/name)"""
    assert source.count(before) == 1
    return source.replace(before, after, 1)


if __name__ == '__main__':
    original = (ROOT / 'scripts/score_development_ragas.py').read_text(encoding='utf-8')
    final = adapted(original)
    compile(final, 'score_final_ragas.py', 'exec')
    target = ROOT / 'scripts/score_final_ragas.py'
    assert not target.exists(), 'Preserve existing final scorer.'
    target.write_text(final, encoding='utf-8')
    diff = ''.join(difflib.unified_diff(original.splitlines(True), final.splitlines(True), fromfile='legacy_development_scorer', tofile='registered_final_scorer'))
    (ROOT / 'experiments/t07-final-evaluation-v1/scorer_adapter.diff').write_text(diff, encoding='utf-8')
    print('Final scorer adapter compiled; metric prompts/calculations unchanged. No inference performed.')
