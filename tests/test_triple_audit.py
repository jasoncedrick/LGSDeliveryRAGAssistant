"""No model calls and no real rater evidence; check the versioned audit contract."""
import copy
import sys
import unittest
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_triple_audit import OUT, OLD, read, records, digest
from collect_triple_ratings import validate_export


class TripleAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = {r['answer_id']: r for r in read(OUT/'private/answer_key.json')}
        cls.archives = {c: {r['question_id']: r for r in records(c)} for c in 'ABC'}

    def test_counts_balance_and_verbatim_content(self):
        for module, count, configs in [('M1',40,'BC'),('M2',60,'ABC')]:
            positions = {}
            for n in range(1,4):
                packet = read(OUT/f'public/R{n:02d}-{module}/packet.json')
                self.assertEqual(len(packet['pairs']),count)
                counts = Counter()
                langs = Counter(p['language'] for p in packet['pairs'])
                self.assertEqual(set(langs.values()),{20})
                for p in packet['pairs']:
                    self.assertEqual(len(p['responses']),len(configs))
                    for j,r in enumerate(p['responses']):
                        k = self.key[r['answer_id']]
                        original = self.archives[k['configuration']][k['question_id']]
                        self.assertEqual(p['question'],original['question'])
                        expected = original['normalization']['normalized_query'] if module=='M1' else original['answer'] or ''
                        self.assertEqual(r['text'],expected)
                        if module=='M2':
                            self.assertEqual([s['text'] for s in r['passages']], [s['text'] for s in original['citations']])
                        counts[k['configuration'],j]+=1
                        positions.setdefault(r['answer_id'],[]).append(j)
                self.assertEqual(set(counts.values()),{20})
            if module=='M2':
                self.assertTrue(all(sorted(p)==[0,1,2] for p in positions.values()))

    def test_collector_rejects_wrong_scale_and_missing_scores(self):
        for module, maximum, count in [('M1',5,80),('M2',4,180)]:
            p=read(OUT/f'public/R01-{module}/packet.json')
            dims=['fidelity'] if module=='M1' else ['relevance','faithfulness']
            e={k:p[k] for k in ['schema_version','packet_id','rater_id','rubric_version','packet_version']}
            e.update(export_kind='final',ratings={})
            for pair in p['pairs']:
                for r in pair['responses']:
                    e['ratings'][r['answer_id']]={**{d:{'score':maximum} for d in dims}, 'note':'SYNTHETIC ONLY','flags':[],'updated_at':'2026-10-26T00:00:00Z'}
            self.assertEqual(len(validate_export(e,p)),count)
            for score in [None,0,maximum+1,True,'3']:
                bad=copy.deepcopy(e)
                next(iter(bad['ratings'].values()))[dims[0]]['score']=score
                with self.assertRaises(ValueError): validate_export(bad,p)
            bad=copy.deepcopy(e);bad['packet_version']='old'
            with self.assertRaises(ValueError): validate_export(bad,p)

    def test_pdf_bytes_and_registered_groups_preserved(self):
        self.assertEqual(digest(OLD/'private/selection_registration.json'),digest(OUT/'private/original_selection_registration.json'))
        for path in (OUT/'public/sources').glob('*.pdf'):
            self.assertEqual(digest(path),digest(OLD/'public/sources'/path.name))
        original=read(OLD/'private/selection_registration.json')
        self.assertEqual({r['group_id'] for r in self.key.values()},set(sum(original['selected_groups'].values(),[])))


if __name__=='__main__': unittest.main()
