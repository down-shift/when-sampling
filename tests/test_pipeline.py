import json
import tempfile
import unittest
from pathlib import Path
from sampling.project import generate, verify, requests, truth
from sampling.runner import parse, run
from sampling.analysis import analyze


class ScientificChecks(unittest.TestCase):
    def test_all_worlds(self):
        data=generate()
        self.assertEqual(verify(data),240)
        for worlds in data['splits'].values():
            for w in worlds:
                self.assertEqual(truth(w,'F'),truth(w,'S'))

    def test_strict_parser(self):
        def raw(s,finish='stop'):
            return dict(choices=[dict(finish_reason=finish,message=dict(content=s))])
        for text,status in [('75','invalid_schema'),('{"posterior_h_a":75}','out_of_range'),('Here is 0.75','malformed_json'),('{"posterior_h_a":true}','invalid_schema'),('{"posterior_h_a":NaN}','malformed_json'),('{"posterior_h_a":0.5,"posterior_h_a":0.6}','malformed_json')]:
            self.assertEqual(parse(raw(text),'primary')[0],status)
        self.assertEqual(parse(raw('{}','length'),'primary')[0],'truncation')
        self.assertEqual(parse({'choices':[{'message':{'refusal':'no'}}]},'primary')[0],'refusal')

    def test_mock_resume_and_analysis(self):
        data=generate(2,2)
        reqs,answers=requests(data,'development',1)
        config=json.loads(Path('config.mock.json').read_text())
        with tempfile.TemporaryDirectory() as directory:
            run(reqs,answers,config,directory,{},False)
            before=(Path(directory)/'responses.jsonl').read_bytes()
            run(reqs,answers,config,directory,{},False,True)
            self.assertEqual(before,(Path(directory)/'responses.jsonl').read_bytes())
            report=analyze(directory,answers,bootstrap=100)
            self.assertTrue(report['synthetic'])
            self.assertEqual(report['metrics']['invariance_absolute']['mean'],0)
            self.assertEqual(report['metrics']['primary_posterior_mae:F']['mean'],0)
            self.assertEqual(len(reqs),42)


if __name__=='__main__':
    unittest.main()

class HandChecks(unittest.TestCase):
    def test_hand_example_and_edges(self):
        from fractions import Fraction as Q
        from sampling.oracle import analytic, enumerated, likelihood, terminal, enumerate_outcomes
        pi,pa,pb=Q(1,2),Q(3,4),Q(1,4)
        self.assertEqual(analytic('HHT',pi,pa,pb),Q(3,4))
        self.assertEqual(enumerated('HHT',pi,pa,pb,'S',3,a=4,b=1),Q(3,4))
        self.assertEqual(analytic('HHT',pi,pa,pb,Q(1,4),Q(3,4)),Q(1,2))
        self.assertEqual(analytic('HHT',pi,pa,pb,Q(1,3),Q(1,3)),Q(3,4))
        self.assertEqual(analytic('HHT',1-pi,pb,pa),1-analytic('HHT',pi,pa,pb))
        self.assertFalse(terminal('HTH',4,1,3))
        with self.assertRaises(ValueError):
            enumerated('HTH',pi,pa,pb,'S',3,a=4,b=1)
        with self.assertRaises(ValueError):
            analytic('H',pi,Q(0),Q(0))
        for x in ('HHT','HTH'):
            self.assertTrue(terminal(x,4,4,3))
        self.assertEqual(likelihood('HHT',pa),likelihood('HTH',pa))
        dist=enumerate_outcomes(pa,3,'R',q=Q(1,4))
        self.assertEqual(dist['NO_REPORT'],Q(3,4))
        self.assertEqual(sum(dist.values()),1)

class AdapterChecks(unittest.TestCase):
    def test_http_payload_and_raw_response(self):
        import io
        from unittest.mock import patch
        data=generate(1,1)
        reqs,answers=requests(data,'development',0)
        reqs=reqs[:1]
        config=json.loads(Path('config.mock.json').read_text())
        config['adapter']='http'
        raw=dict(model='returned-test-model',choices=[dict(finish_reason='stop',message=dict(content='{"posterior_h_a":0.5}'))])
        sent=[]
        def fake(request,timeout):
            sent.append(json.loads(request.data))
            return io.BytesIO(json.dumps(raw).encode())
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ',{'SAMPLING_API_KEY':'test-secret'}), patch('urllib.request.urlopen',side_effect=fake):
            run(reqs,answers,config,directory,{},live=True)
            self.assertEqual(set(sent[0]),{'model','messages','max_tokens','temperature'})
            self.assertEqual(sent[0]['messages'],[dict(role='user',content=reqs[0]['prompt'])])
            for p in Path(directory).iterdir():
                self.assertNotIn('test-secret',p.read_text())
            row=json.loads((Path(directory)/'responses.jsonl').read_text())
            self.assertEqual(row['raw'],raw)
            self.assertEqual(row['returned_model'],'returned-test-model')

class LocalServingChecks(unittest.TestCase):
    def test_local_no_auth_and_template_settings(self):
        import io
        from unittest.mock import patch
        data=generate(1,1)
        reqs,answers=requests(data,'development',0)
        config=json.loads(Path('config.local.json').read_text())
        seen=[]
        def fake(request,timeout):
            self.assertNotIn('Authorization',request.headers)
            seen.append(json.loads(request.data))
            return io.BytesIO(b'{"model":"Qwen/Qwen3-4B","choices":[{"finish_reason":"stop","message":{"content":"{\\"posterior_h_a\\":0.5}"}}]}')
        with tempfile.TemporaryDirectory() as directory, patch('urllib.request.urlopen',side_effect=fake):
            run(reqs[:1],answers,config,directory,{},True)
        self.assertEqual(seen[0]['chat_template_kwargs'],{'enable_thinking':False})
        self.assertEqual(seen[0]['max_tokens'],128)
        self.assertEqual(seen[0]['temperature'],0)

    def test_decoding_cannot_replace_message(self):
        data=generate(1,1)
        reqs,answers=requests(data,'development',0)
        config=json.loads(Path('config.mock.json').read_text())
        config['decoding']['messages']=[]
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            run(reqs[:1],answers,config,directory,{})
