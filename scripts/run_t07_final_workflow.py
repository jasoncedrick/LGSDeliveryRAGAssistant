"""One local queue: final A/B/C generation -> legacy RAGAS -> CSV/report."""
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'experiments/t07-final-evaluation-v1'


def main():
    fd = os.open(OUT / 'workflow.lock', os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.write(fd, str(os.getpid()).encode())
    os.close(fd)
    def run(stage, command):
        (OUT / 'workflow_progress.json').write_text(json.dumps(dict(stage=stage, status='RUNNING')), encoding='utf-8')
        with (OUT / 'workflow.log').open('a', encoding='utf-8') as log:
            log.write('\nSTAGE ' + stage + '\n')
            log.flush()
            result = subprocess.run([sys.executable, '-u', '-B'] + command, cwd=ROOT,
                                    stdout=log, stderr=subprocess.STDOUT, env=dict(os.environ, RAGAS_DO_NOT_TRACK='true'))
        if result.returncode:
            raise RuntimeError(stage + ' stopped; preserve logs, do not silently retry completed attempts.')
        print(stage + ' completed', flush=True)
    try:
        run('GENERATION', ['scripts/run_t07_final_abc.py'])
        run('RETRIEVAL_CSV', ['scripts/export_t07_final_metrics.py'])
        for config in 'ABC':
            run('RAGAS_' + config, ['scripts/score_final_ragas.py', '--input-name', 't07-final-evaluation-v1',
                '--input-subdir', config, '--output-name', f't07-final-ragas-{config.lower()}-v1',
                '--metrics', 'faithfulness', 'context_precision', 'context_recall', 'answer_relevancy',
                '--strict-metric-json', '--strict-recall-json', '--judge-output-tokens', '4096', '--judge-timeout', '600'])
            run('CSV_AFTER_' + config, ['scripts/export_t07_final_metrics.py'])
        (OUT / 'workflow_progress.json').write_text(json.dumps(dict(stage='COMPLETE', status='EXECUTION_AND_EXPORT_COMPLETE_WITH_DECLARED_LIMITATIONS')), encoding='utf-8')
        print('T07 execution and CSV export finished; inspect T07_EXECUTION_REPORT.txt and missing-score denominators.', flush=True)
    except Exception as error:
        (OUT / 'workflow_progress.json').write_text(json.dumps(dict(stage='STOPPED', status='NOT_COMPLETE', error=str(error))), encoding='utf-8')
        raise
    finally:
        (OUT / 'workflow.lock').unlink()


if __name__ == '__main__':
    main()
