#!/usr/bin/env python3
"""Check bounded TLA+ models, source agreement, and executable boundary probes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'verification'
JAR_SHA = '936a262061c914694dfd669a543be24573c45d5aa0ff20a8b96b23d01e050e88'
AREAS = {
    'bridge': ('ExportBridge', 'ExportContract', []),
    'references': ('ReferenceLifetime', 'BorrowedReferenceContract', ['UnchangedReferenceIsLive','UnchangedReferenceNeverAliases']),
    'example': ('ExampleFlow', 'SuccessfulRunCloses', ['EveryExitExplicitlyCloses']),
    'observer': ('Observer', 'ObserverReleasesResources', ['ReadHasDeadline']),
    'pipeline': ('CheckPipeline', 'CheckPipelineContract', []),
}


def run(args, *, cwd=None, env=None, timeout=30):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'Command failed ({result.returncode}): {args}\n{result.stdout}')
    return result.stdout


def toolchain():
    cached_java = Path.home()/'.cache/bend-window-ref-verification/java/bin/java'
    java = os.environ.get('JAVA') or shutil.which('java') or (str(cached_java) if cached_java.exists() else None)
    if not java:
        raise RuntimeError('Install Java 11 or later, or set JAVA to its executable. Validated with Temurin 21.0.8+9.')
    jar = Path(os.environ.get('TLA2TOOLS', str(Path.home()/'.cache/bend-window-ref-verification/tla2tools-1.7.4.jar')))
    if not jar.exists():
        jar.parent.mkdir(parents=True, exist_ok=True)
        # Verify before publishing the download to the shared cache.
        with tempfile.TemporaryDirectory(dir=jar.parent) as tmp:
            download = Path(tmp)/'tlc.jar'
            urllib.request.urlretrieve('https://github.com/tlaplus/tlaplus/releases/download/v1.7.4/tla2tools.jar', download)
            if hashlib.sha256(download.read_bytes()).hexdigest() != JAR_SHA:
                raise RuntimeError('TLC download checksum mismatch')
            download.replace(jar)
    if hashlib.sha256(jar.read_bytes()).hexdigest() != JAR_SHA:
        raise RuntimeError('Use the checksum-pinned TLC 1.7.4 jar')
    return java, jar


def check_model(model, rule, output, *, mutated=None):
    java, jar = toolchain()
    with tempfile.TemporaryDirectory(prefix='winref-tlc-') as tmp:
        scratch = Path(tmp)
        text = (HERE/'models'/f'{model}.tla').read_text() if mutated is None else mutated
        (scratch/f'{model}.tla').write_text(text)
        (scratch/f'{model}.cfg').write_text(f'SPECIFICATION Spec\nINVARIANT {rule}\n')
        result = subprocess.run([str(java),'-XX:+UseParallelGC','-cp',str(jar),'tlc2.TLC','-workers','1','-seed','1','-fp','0','-config',f'{model}.cfg',model],cwd=scratch,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60)
        output.mkdir(parents=True,exist_ok=True)
        (output/f'{model}-{rule}.out').write_text(result.stdout)
        violated = re.search(r'Invariant (\w+) is violated',result.stdout)
        if violated and violated.group(1) == rule:
            status = 'counterexample'
        elif result.returncode == 0 and 'No error has been found' in result.stdout:
            status = 'verified'
        else:
            raise RuntimeError(f'TLC did not finish {model}/{rule}:\n{result.stdout}')
        count = re.search(r'([\d,]+) distinct states found',result.stdout)
        return {'model':model,'rule':rule,'status':status,'states':int(count.group(1).replace(',','')) if count else None}


def probes(area, source):
    p = HERE/'probes'
    with tempfile.TemporaryDirectory(prefix='winref-probe-') as tmp:
        scratch = Path(tmp)
        logs = []
        if area in {'bridge','references'}:
            for unsupported in [False, True] if area == 'bridge' else [False]:
                exe = scratch/('unsupported' if unsupported else 'bridge')
                flags = ['-U__linux__','-DUNSUPPORTED'] if unsupported else []
                logs.append(run(['clang','-std=c11','-Wno-unused-function',*flags,'-I',source,p/'bridge.c','-o',exe]))
                logs.append(run([exe]))
        if area == 'bridge':
            logs.append(run(['node',p/'javascript.mjs',source/'winref.js']))
        if area == 'references':
            logs.append(run(['bend',HERE/'PROOF.bend']))
            logs.append(run([sys.executable,p/'reference.py',source/'winref.bend']))
        if area == 'example':
            compiled = scratch/'export.js'
            logs.append(run(['bend',source/'examples/export.bend','-o',compiled]))
            logs.append(run(['node',p/'example.mjs',compiled]))
        if area == 'observer':
            logs.append(run([sys.executable,p/'observer.py',source/'scripts/check_x11.py']))
            logs.append(run([sys.executable,p/'blocked_read.py',source/'scripts/check_x11.py']))
        if area == 'pipeline':
            logs.append(run([sys.executable,p/'pipeline.py',source/'scripts/check.sh']))
        return ''.join(logs)


def source_matches(areas):
    manifest = json.loads((HERE/'coverage.json').read_text())
    stale = []
    for area in areas:
        for filename, sha in manifest['subsystems'][area]['sources'].items():
            path = ROOT/filename
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != sha:
                stale.append(filename)
    if stale:
        raise RuntimeError('Covered source changed: '+', '.join(sorted(set(stale)))+'. Review the model mapping and run with --review-source; update coverage.json only after review.')


def mutations(areas, output):
    # Each change is applied to a disposable COPY of the actual source.
    variants = {
        'bridge': [('winref.c','XSync(win->dpy, False);','XSync(win->dpy, 1);'),('winref.c','io_tup(e, f[0],','io_tup(e, 0,'),('winref.js','io_tup(window,','io_tup(null,')],
        'references': [('winref.bend','type WindowRef is Data:','type WindowRef is Type:'),('winref.c','(u32)win->win);','(u32)win->win + 1);')],
        'example': [('examples/export.bend','    Window.close(window)','    IO.pure(Unit, Unit{})')],
        'observer': [('scripts/check_x11.py','                x11.XFree(name)','                pass'),('scripts/check_x11.py','            process.kill()','            pass')],
        'pipeline': [('scripts/check.sh',"trap 'rm -rf \"$build_dir\"' EXIT", "trap ':' EXIT"),('scripts/check.sh','set -euo pipefail','set -uo pipefail')],
    }
    model_variants = {
        'bridge': ('owner\' = owner','owner\' = "lost"'),
        'references': ("ref' = 7", "ref' = 8"),
        'example': ("explicitlyClosed' = TRUE", "explicitlyClosed' = FALSE"),
        'observer': ("display' = FALSE", "display' = TRUE"),
        'pipeline': ("temporary' = FALSE", "temporary' = TRUE"),
    }
    results = []
    files = ['winref.bend','winref.c','winref.js','LAWS.bend','PROOF.bend','examples/export.bend','scripts/check_x11.py','scripts/check.sh']
    for area in areas:
        for number,(filename,before,after) in enumerate(variants[area]):
            with tempfile.TemporaryDirectory(prefix='winref-mutation-') as tmp:
                scratch = Path(tmp)
                for file in files:
                    target = scratch/file
                    target.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(ROOT/file,target)
                path = scratch/filename
                original = path.read_text()
                if before not in original: raise RuntimeError(f'Mutation no longer applies: {filename}: {before}')
                path.write_text(original.replace(before,after))
                try: probes(area,scratch)
                except RuntimeError as exc:
                    (output/f'mutation-{area}-{number}.out').write_text(str(exc))
                    results.append({'subsystem':area,'source':filename,'mutation':before+' -> '+after,'detected':True})
                else: raise RuntimeError(f'Probe MISSED mutation in {filename}: {before}')
        model,rule,_ = AREAS[area]
        before,after = model_variants[area]
        text = (HERE/'models'/f'{model}.tla').read_text()
        assert before in text
        result = check_model(model,rule,output/'model-mutations',mutated=text.replace(before,after))
        if result['status'] != 'counterexample': raise RuntimeError(f'Model mutation missed: {model}')
        results.append({'subsystem':area,'model':model,'rule':rule,'detected':True})
        print(f'{area}: source mutations and model mutation detected')
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('subsystem',choices=['all',*AREAS],nargs='?',default='all')
    parser.add_argument('--out',type=Path,default=HERE/'results')
    parser.add_argument('--mutations',action='store_true',help='also prove checks fail on disposable source and model mutations')
    parser.add_argument('--review-source',action='store_true',help='run while reviewing changed source; does not update the coverage record')
    parser.add_argument('--regression',action='store_true',help='accept only the explicitly recorded diagnostic counterexamples; keep reporting them')
    args = parser.parse_args()
    areas = list(AREAS) if args.subsystem == 'all' else [args.subsystem]
    if not args.review_source: source_matches(areas)
    if run(['bend','version']).strip() != 'bend 2.0.40':
        raise RuntimeError('Verification adapters require Bend 2.0.40; review them before using another compiler')
    args.out.mkdir(parents=True,exist_ok=True)
    records = []
    for area in areas:
        model,rule,diagnostics = AREAS[area]
        log = probes(area,ROOT)
        (args.out/f'{area}-source.out').write_text(log)
        result = check_model(model,rule,args.out)
        records.append(result)
        if result['status'] != 'verified': raise RuntimeError(f'Contract failed: {rule}; read the TLC trace')
        print(f'{area}: {rule} verified; source probes passed')
        for diagnostic in diagnostics:
            result = check_model(model,diagnostic,args.out)
            records.append(result)
            print(f'  DIAGNOSTIC {diagnostic}: {result["status"]}')
            if result['status'] != 'counterexample':
                raise RuntimeError(f'Diagnostic changed: {diagnostic}; review model and baseline, do not silently accept it')
    mutation_results = mutations(areas,args.out) if args.mutations else []
    report = {'source_commit':json.loads((HERE/'coverage.json').read_text())['sync_commit'],'tlc':'1.7.4','checks':records,'mutations':mutation_results}
    (args.out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    findings = any(record['status']=='counterexample' for record in records)
    print('Contracts verified; diagnostic counterexamples remain.' if findings else 'Contracts verified.')
    return 1 if findings and not args.regression else 0

if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError,subprocess.TimeoutExpired) as exc:
        print(str(exc),file=sys.stderr)
        sys.exit(2)
