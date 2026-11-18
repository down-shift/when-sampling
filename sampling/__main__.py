import argparse
import json
from pathlib import Path
from .project import generate, verify, requests, digest, save
from .runner import run
from .analysis import analyze
from .evaluation import evaluation_lock


def main():
    p=argparse.ArgumentParser()
    p.add_argument('command',choices=['generate','verify','preview','run','analyze','freeze'])
    p.add_argument('--dataset',default='artifacts/dataset.json')
    p.add_argument('--split',choices=['development','evaluation'],default='development')
    p.add_argument('--dev-worlds',type=int,default=16)
    p.add_argument('--eval-worlds',type=int,default=64)
    p.add_argument('--dev-seed',type=int,default=1729)
    p.add_argument('--eval-seed',type=int,default=2718)
    p.add_argument('--order-seed',type=int,default=31415)
    p.add_argument('--repeat-worlds',type=int,default=2)
    p.add_argument('--world-limit',type=int)
    p.add_argument('--config',default='config.mock.json')
    p.add_argument('--output',default='artifacts/mock')
    p.add_argument('--live',action='store_true')
    p.add_argument('--dry-run',action='store_true')
    p.add_argument('--resume',action='store_true')
    p.add_argument('--plan', help='evaluation plan JSON used by freeze')
    p.add_argument('--lock', help='frozen evaluation lock file')
    args=p.parse_args()
    if args.command=='generate':
        if Path(args.dataset).exists():
            p.error('dataset exists; choose a new path rather than overwriting')
        data=generate(args.dev_worlds,args.eval_worlds,args.dev_seed,args.eval_seed)
        verify(data)
        save(args.dataset,data)
    data=json.loads(Path(args.dataset).read_text())
    if args.command in ('verify','generate'):
        verify(data)
        print('Verified dataset',digest(data))
        return
    original_hash=digest(data)
    if args.world_limit is not None:
        if args.world_limit<1:
            p.error('world-limit must be positive')
        data['splits'][args.split]=data['splits'][args.split][:args.world_limit]
    reqs,answers=requests(data,args.split,args.repeat_worlds,args.order_seed)
    context = dict(dataset_hash=original_hash, split=args.split, repeat_worlds=args.repeat_worlds,
                   order_seed=args.order_seed, world_limit=args.world_limit)
    if args.command == 'freeze':
        if args.split != 'evaluation' or args.world_limit is not None or not args.plan or not args.lock:
            p.error('freeze requires --split evaluation, --plan and --lock, with no --world-limit')
        try:
            plan = json.loads(Path(args.plan).read_text())
            config = json.loads(Path(args.config).read_text())
            lock = evaluation_lock(plan, config, context, reqs)
            with Path(args.lock).open('x') as file:
                json.dump(lock, file, indent=2, sort_keys=True)
                file.write('\n')
        except (OSError, ValueError) as exc:
            p.error(str(exc))
        print(f'Frozen {len(reqs)} evaluation requests in {args.lock}')
    elif args.command=='preview':
        print(json.dumps(dict(requests=len(reqs),maximum_http_attempts=len(reqs)*(json.loads(Path(args.config).read_text())['retry_limit']+1),dataset_hash=original_hash),indent=2))
        print(next(r['prompt'] for r in reqs if r['kind']=='primary'))
    elif args.command=='run':
        config=json.loads(Path(args.config).read_text())
        if args.live and args.split == 'evaluation':
            if not args.lock or args.world_limit is not None:
                p.error('live evaluation requires --lock and the full evaluation split')
            try:
                lock = json.loads(Path(args.lock).read_text())
                if lock != evaluation_lock(lock['plan'], config, context, reqs):
                    p.error('evaluation settings differ from the frozen lock')
            except (OSError, ValueError, KeyError) as exc:
                p.error(str(exc))
            context['evaluation_lock'] = lock
        print(f"Requests: {len(reqs)}; maximum attempts including retries: {len(reqs)*(config['retry_limit']+1)}")
        if not args.dry_run:
            run(reqs,answers,config,args.output,context,args.live,args.resume)
            save(Path(args.output)/'answers.private.json',answers)
    elif args.command=='analyze':
        manifest=json.loads((Path(args.output)/'manifest.json').read_text())
        if manifest['identity']['requests_hash']!=digest(reqs):
            p.error('analysis request settings do not match run')
        lock = manifest['identity'].get('evaluation_lock')
        if lock and lock != evaluation_lock(lock['plan'], manifest['config'], context, reqs):
            p.error('analysis settings differ from the frozen lock')
        analyze(args.output,answers)
        print(str(Path(args.output)/'report.md'))


if __name__=='__main__':
    main()
