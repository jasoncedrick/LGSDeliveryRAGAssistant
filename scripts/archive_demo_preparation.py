"""Preserve untracked work and inventory the historical checkouts; never delete."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path

ROOT = Path('D:/thesis')
DEST = ROOT / 'conversation-backups/adviser-preparation-20261111'
DEST.mkdir(exist_ok=False)
receipts = []
for name in ['LGSDeliveryRAGAssistant-clean', 'LGSDeliveryRAGAssistant-main',
             'LGSDeliveryRAGAssistant-main-integration-20261020']:
    repo = ROOT / name
    cmd = ['git', '-c', f'safe.directory={repo.as_posix()}', '-C', str(repo)]
    def git(*args):
        return subprocess.check_output(cmd + list(args)).decode('utf-8')
    files = [f for f in git('ls-files', '--others', '--exclude-standard', '-z').split('\0')
             if f and (repo / f).is_file()]
    receipt = dict(path=str(repo), branch=git('branch', '--show-current').strip(),
                   head=git('rev-parse', 'HEAD').strip(), status=git('status', '--short'), files=[])
    if files:
        target = DEST / (name + '-untracked.zip')
        with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
            for relative in files:
                data = (repo / relative).read_bytes()
                archive.writestr(relative, data)
                receipt['files'].append(dict(path=relative, bytes=len(data),
                                            sha256=hashlib.sha256(data).hexdigest()))
        with zipfile.ZipFile(target) as archive:
            assert archive.testzip() is None
        receipt['backup'] = str(target)
        receipt['backup_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    (DEST / (name + '-tracked.patch')).write_text(git('diff', 'HEAD', '--binary'), encoding='utf-8')
    receipts.append(receipt)
(DEST / 'inventory.json').write_text(json.dumps(receipts, indent=2), encoding='utf-8')
print('Preserved', sum(len(r['files']) for r in receipts), 'untracked files; originals unchanged.')
