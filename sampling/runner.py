import concurrent.futures
import datetime
import json
import math
import os
import random
import subprocess
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from fractions import Fraction
from .project import digest, save


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def parse(raw, kind):
    if not isinstance(raw, dict):
        return 'malformed_response', None
    choices = raw.get('choices', [])
    if not choices:
        return 'malformed_response', None
    choice = choices[0]
    message = choice.get('message', {})
    if message.get('refusal') or choice.get('finish_reason') == 'content_filter':
        return 'refusal', None
    if choice.get('finish_reason') == 'length':
        return 'truncation', None
    content = message.get('content')
    def unique(pairs):
        d = {}
        for k,v in pairs:
            if k in d:
                raise ValueError('duplicate key')
            d[k] = v
        return d
    try:
        value = json.loads(content, object_pairs_hook=unique, parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (TypeError, ValueError):
        return 'malformed_json', None
    keys = {'likelihood_h_a','likelihood_h_b'} if kind == 'extraction' else {'posterior_h_a'}
    if not isinstance(value,dict) or set(value) != keys or any(type(v) not in (int,float) for v in value.values()):
        return 'invalid_schema', None
    if any(not math.isfinite(v) or not 0 <= v <= 1 for v in value.values()):
        return 'out_of_range', None
    return 'ok', value


def run(reqs, answers, config, directory, context, live=False, resume=False):
    out = Path(directory)
    if config['max_requests'] < len(reqs):
        raise ValueError(f"request count {len(reqs)} exceeds max_requests")
    if config['concurrency'] < 1 or config['retry_limit'] < 0 or config['timeout'] <= 0:
        raise ValueError('invalid runner limits')
    if live and config['adapter'] != 'http':
        raise ValueError('live requires adapter=http')
    if not live and config['adapter'] != 'mock':
        raise ValueError('HTTP requires --live')
    allowed = {'temperature', 'top_p', 'seed', 'frequency_penalty', 'presence_penalty', 'chat_template_kwargs'}
    if set(config['decoding']) - allowed:
        raise ValueError('unsupported decoding fields')
    source_hash = digest({str(p):p.read_text() for p in sorted(Path('sampling').glob('*.py'))})
    protocol_hash = digest(Path('protocol.md').read_text())
    identity = dict(context, config_hash=digest(config), requests_hash=digest(reqs), source_hash=source_hash, protocol_hash=protocol_hash, live=live)
    manifest = out/'manifest.json'
    if manifest.exists():
        if not resume:
            raise ValueError('run exists; use --resume')
        old = json.loads(manifest.read_text())
        if old['identity'] != identity:
            raise ValueError('resume identity mismatch')
    else:
        if resume:
            raise ValueError('cannot resume absent run')
        out.mkdir(parents=True,exist_ok=True)
        revision = subprocess.run(['git','rev-parse','HEAD'],capture_output=True,text=True).stdout.strip() or None
        save(manifest,dict(identity=identity,config=config,started=now(),revision=revision,synthetic=not live))
        save(out/'requests.json',reqs)
    path = out/'responses.jsonl'
    completed = {}
    if path.exists():
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if row['id'] in completed:
                raise ValueError('duplicate completed request')
            completed[row['id']] = row
    lock = threading.Lock()
    def append(filename, row):
        with lock:
            with (out/filename).open('a') as f:
                f.write(json.dumps(row,allow_nan=False)+'\n')
                f.flush()
                os.fsync(f.fileno())
    def execute(req):
        payload = dict(model=config['model'],messages=[dict(role='user',content=req['prompt'])],max_tokens=config['max_output_tokens'],**config['decoding'])
        # Only explicitly allowlisted request fields are sent; answers never enter payload.
        raw = None
        status = 'transport_failure'
        for attempt in range(config['retry_limit']+1):
            started = now()
            retry = False
            if not live:
                target = answers[req['id']]
                keys = ('likelihood_h_a','likelihood_h_b') if req['kind']=='extraction' else ('posterior_h_a',)
                content = json.dumps({k:float(Fraction(target[k])) for k in keys})
                raw = dict(model='synthetic-oracle-mock',choices=[dict(finish_reason='stop',message=dict(content=content))])
                error = None
            else:
                key_env = config.get('api_key_env')
                key = os.environ.get(key_env) if key_env else None
                if key_env and not key:
                    raise ValueError('configured API key environment variable is unset')
                headers = {'Content-Type': 'application/json'}
                if key:
                    headers['Authorization'] = 'Bearer ' + key
                request = urllib.request.Request(config['endpoint'],data=json.dumps(payload).encode(),headers=headers)
                try:
                    with urllib.request.urlopen(request,timeout=config['timeout']) as response:
                        body = response.read().decode()
                    try:
                        raw = json.loads(body)
                    except ValueError:
                        raw = {'unparsed_body':body}
                    error = None
                except urllib.error.HTTPError as exc:
                    # Do not persist headers or error bodies that may contain credentials.
                    error = dict(type='http',code=exc.code)
                    retry = exc.code == 429 or 500 <= exc.code < 600
                except (urllib.error.URLError,TimeoutError,OSError):
                    error = dict(type='transport')
                    retry = True
            append('attempts.jsonl',dict(id=req['id'],attempt=attempt,started=started,finished=now(),raw=raw,error=error,requested_model=config['model'],decoding=config['decoding'],max_output_tokens=config['max_output_tokens']))
            if error is None:
                status, parsed = parse(raw,req['kind'])
                break
            parsed = None
            status = 'rate_limit_failure' if error.get('code')==429 else 'transport_failure'
            if not retry or attempt == config['retry_limit']:
                break
            time.sleep(min(2**attempt,16))
        row = dict(id=req['id'],status=status,parsed=parsed,raw=raw,finished=now(),requested_model=config['model'],returned_model=raw.get('model') if isinstance(raw,dict) else None)
        append('responses.jsonl',row)
    with concurrent.futures.ThreadPoolExecutor(max_workers=config['concurrency']) as pool:
        list(pool.map(execute,[r for r in reqs if r['id'] not in completed]))
    save(out/'completion.json',dict(finished=now(),requests=len(reqs)))
