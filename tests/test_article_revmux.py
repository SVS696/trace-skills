"""Behavioral tests for the pool-free authoring / ordinary-revmux protocol."""
import argparse
import json
import unittest
from scripts import caseflow
import test_caseflow as fixtures


class ArticleRevmuxTests(unittest.TestCase):
    setUp = fixtures.CaseFlowTests.setUp
    tearDown = fixtures.CaseFlowTests.tearDown
    write = fixtures.CaseFlowTests.write
    submit_stage_one = fixtures.CaseFlowTests.submit_stage_one
    prepare_review = fixtures.CaseFlowTests.prepare_review
    write_review_adjudication = fixtures.CaseFlowTests.write_review_adjudication

    def args(self, **values):
        return argparse.Namespace(case_root=self.case_root, **values)

    def modern_review(self):
        self.prepare_review()
        payload = caseflow.load_case(self.case_root)
        payload['review_protocol'] = 'article-revmux'
        caseflow.save_case(self.case_root, payload, 'test_protocol')

    def review(self, name, findings=None, target='article.md#RULE-1', degraded=False):
        payload = caseflow.load_case(self.case_root)
        findings = findings or []
        receipt = self.write('reviews/'+name+'.json', json.dumps({
            'schema': 1, 'article_sha256': payload['article']['sha256'],
            'sources': {'ids':['logic'], 'expected':1, 'reported':1,
                        'degraded':['logic'] if degraded else []},
            'findings': findings, 'open_questions': []}))
        kwargs = {'receipt': str(receipt)}
        if findings:
            kwargs['adjudication_report'] = str(self.write_review_adjudication(
                receipt, accepted={f['id'] for f in findings}))
            pool = self.write('diffs/'+name+'.json', json.dumps({'schema':1,'stage':4,
                'items':[{'id':'D4-001','source_finding_id':findings[0]['id'],
                          'target':target,'change':'Correct the article rule',
                          'reason':'Reviewed rule is wrong','status':'open'}]}))
            kwargs['diff_pool'] = str(pool)
        return caseflow.command_record_review(self.args(**kwargs))

    def record_stage_one(self, open_inputs=None):
        self.submit_stage_one()
        caseflow.command_open_stitch(self.args())
        report = self.write('stitches/stage-01.json', json.dumps({
            'schema':1,'stage':1,'status':'ready','open_inputs':open_inputs or []}))
        return caseflow.command_record_stitch(self.args(report=str(report)))

    def test_authoring_stage_needs_no_pool_or_verification(self):
        self.assertEqual(self.record_stage_one()['state'], 'ready')
        payload=caseflow.load_case(self.case_root)
        self.assertIsNone(payload['stages']['1']['diff_pool'])
        self.assertEqual(payload['review_protocol'],'article-revmux')
        self.assertEqual(caseflow.command_advance(self.args())['stage'],2)

    def test_unresolved_content_cannot_be_registered_ready(self):
        with self.assertRaisesRegex(caseflow.CaseFlowError,'open_inputs'):
            self.record_stage_one(['Which actor can approve?'])

    def test_article_changes_after_stitch_require_new_registration(self):
        self.record_stage_one()
        self.write('articles/stage-01.md','silently changed article')
        with self.assertRaisesRegex(caseflow.CaseFlowError,'changed after registration'):
            caseflow.command_advance(self.args())

    def test_context_contains_rules_and_reports_missing_source(self):
        rule=self.write('project-rule.md','project requirement')
        missing=self.case_root/'unavailable-source.md'
        result=caseflow.command_context(self.args(block='ARTICLE',lane=None,
            project_rule=[str(rule)],source=[str(missing)]))
        self.assertIn(str(rule.resolve()),result['read_set'])
        self.assertIn(str(missing.resolve()),result['missing_required'])

    def test_review_pool_cannot_target_only_intermediate_file(self):
        self.modern_review()
        with self.assertRaisesRegex(caseflow.CaseFlowError,'final article'):
            self.review('wrong-target',[{'id':'f1','severity':'major','sources':['logic']}],
                        target='blocks/B01/stage-02.md#RULE-1')

    def test_source_only_change_cannot_be_applied(self):
        self.modern_review()
        self.review('first',[{'id':'f1','severity':'major','sources':['logic']}])
        self.write('blocks/B01/stage-02.md','fixed source')
        receipt=self.write('applied.txt','source corrected')
        with self.assertRaisesRegex(caseflow.CaseFlowError,'intermediate-only'):
            caseflow.command_resolve_review(self.args(item='D4-001',receipt=str(receipt)))

    def test_next_ordinary_review_confirms_article_fix(self):
        self.modern_review()
        self.review('first',[{'id':'f1','severity':'major','sources':['logic']}])
        article=self.write('article.md','# RULE-1\nCorrected rule\n')
        receipt=self.write('applied.txt','fixed RULE-1 in article')
        caseflow.command_resolve_review(self.args(item='D4-001',receipt=str(receipt)))
        with self.assertRaisesRegex(caseflow.CaseFlowError,'ordinary revmux'):
            caseflow.command_verify_review(self.args(item='D4-001',receipt=str(receipt),result='pass'))
        caseflow.command_article_updated(self.args(article=str(article)))
        self.assertEqual(self.review('retry',degraded=True)['state'],'revmux_pending')
        pool=json.loads((self.case_root/'diffs/first.json').read_text())
        self.assertEqual(pool['items'][0]['status'],'applied')
        self.assertEqual(self.review('second')['state'],'spec_ready')
        pool=json.loads((self.case_root/'diffs/first.json').read_text())
        self.assertEqual(pool['items'][0]['status'],'verified')
        self.assertEqual(pool['items'][0]['verification_receipt']['kind'],'ordinary-revmux')
        self.assertEqual(caseflow.command_status(self.args())['review_cycles_used'],2)

    def test_stale_application_receipt_does_not_authorize_later_article(self):
        self.modern_review()
        self.review('first',[{'id':'f1','severity':'major','sources':['logic']}])
        article=self.write('article.md','fixed rule')
        receipt=self.write('applied.txt','first correction')
        caseflow.command_resolve_review(self.args(item='D4-001',receipt=str(receipt)))
        article.write_text('different article after receipt')
        with self.assertRaisesRegex(caseflow.CaseFlowError,'receipt does not match'):
            caseflow.command_article_updated(self.args(article=str(article)))

    def test_four_authoring_stages_reach_ordinary_review_without_pools(self):
        self.record_stage_one()
        caseflow.command_advance(self.args())
        for stage in (2, 3, 4):
            status=caseflow.command_status(self.args())
            article=self.write(f'articles/stage-{stage:02d}.md', '# US-1\nComplete article\n')
            for block in status['required_blocks']:
                self.write(f'method-basis/stage-{stage:02d}-{block}.md','method')
                artifact=article if block == 'ARTICLE' else self.write(f'blocks/{block}/stage-{stage:02d}.md','contribution')
                caseflow.command_submit_block(self.args(stage=stage,block=block,artifact=str(artifact)))
            caseflow.command_open_stitch(self.args())
            report=self.write(f'stitches/stage-{stage:02d}.json',json.dumps({
                'schema':1,'stage':stage,'status':'ready','open_inputs':[]}))
            caseflow.command_record_stitch(self.args(report=str(report),article=str(article)))
            caseflow.command_advance(self.args())
        caseflow.command_finalize_article(self.args(article=str(article)))
        self.assertEqual(self.review('clean')['state'],'spec_ready')
        payload=caseflow.load_case(self.case_root)
        self.assertTrue(all(not record['diff_pool'] for record in payload['stages'].values()))

    def test_correction_cannot_invent_an_unreviewed_finding(self):
        self.modern_review()
        self.review('first',[{'id':'f1','severity':'major','sources':['logic']}])
        item=self.write('new-item.json',json.dumps({'id':'D4-002','target':'article.md#new',
            'change':'Unreviewed change','reason':'Found while editing','status':'open'}))
        with self.assertRaisesRegex(caseflow.CaseFlowError,'next ordinary revmux'):
            caseflow.command_append_review_item(self.args(item_file=str(item)))

    def test_fresh_init_rejects_pre_review_pool(self):
        self.case_root = self.root / 'new-case'
        payload = caseflow.command_init(self.args(template=self.template, brief=self.brief,
            decision=self.decision, plan=self.plan, article_id='CASE-1'))
        self.assertEqual(payload['review_protocol'], 'article-revmux')
        self.submit_stage_one()
        caseflow.command_open_stitch(self.args())
        report=self.write('stitches/legacy.md','legacy integration')
        pool=self.write('diffs/premature.json',json.dumps({'schema':1,'stage':1,
            'deferred_inputs':[],'items':[]}))
        with self.assertRaisesRegex(caseflow.CaseFlowError,'only from revmux findings'):
            caseflow.command_record_stitch(self.args(report=str(report),diff_pool=str(pool)))
