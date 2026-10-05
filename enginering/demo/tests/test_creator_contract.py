import unittest
from skilldemo.creator import verify_files
from skilldemo.runtime import HEADINGS


def files(extra=''):
    text='---\nname: contract-review\ndescription: 按当前立场审阅协议。\n---\n'
    text+='## 确认立场\n<!-- SKILLSLOOP_METHOD:m1 -->\n先向用户确认当前代表的合同立场。\n'
    text+='当用户没有明确立场时，先询问而不猜测。\n完成前检查记录中已经明确当前立场。\n'+extra
    text+='\n## 市场信息\n'+'\n'.join('### '+h+'\n用于本次合同审阅流程。' for h in HEADINGS)
    return [{'path':'SKILL.md','content':text}]


class CreatorContractTests(unittest.TestCase):
    def test_nested_resource_can_reference_package_root(self):
        package=files('\n[参考](references/note.md)\n')
        package.append({'path':'references/note.md','content':'[返回](../SKILL.md#确认立场)\n'})
        self.assertEqual(verify_files(package,['m1'])['status'],'PASS')

    def test_escape_and_pseudo_uri_rejected(self):
        for target in ('../outside.md','../../outside.md','file:///C:/secret.txt',
                       'javascript:alert','data:text/plain,secret','//server/share','%2e%2e/outside.md',
                       '%66ile:///C:/secret.txt','..%5csecret.txt'):
            with self.subTest(target=target),self.assertRaises(ValueError):
                verify_files(files('\n[链接]('+target+')\n'),['m1'])

    def test_marker_only_is_not_coverage(self):
        package=files()
        package[0]['content']=package[0]['content'].replace(
            '先向用户确认当前代表的合同立场。\n当用户没有明确立场时，先询问而不猜测。\n完成前检查记录中已经明确当前立场。\n','')
        with self.assertRaisesRegex(ValueError,'marker'):verify_files(package,['m1'])

    def test_coverage_requires_actual_action_condition_and_check_quotes(self):
        methods=[{'id':'m1','action':'确认任务中的审阅身份','conditions':['缺少立场时应澄清'],
                  'completionCheck':'立场已明确'}]
        coverage=[{'methodId':'m1','file':'SKILL.md',
                   'actionQuote':'先向用户确认当前代表的合同立场。',
                   'conditionQuotes':['当用户没有明确立场时，先询问而不猜测。'],
                   'completionCheckQuote':'完成前检查记录中已经明确当前立场。'}]
        result=verify_files(files(),['m1'],methods=methods,coverageManifest=coverage)
        self.assertEqual(result['methodCoverage'][0]['status'],'CONTENT_ANCHORED')
        self.assertEqual(result['semanticValidation'],'NOT_INDEPENDENTLY_VERIFIED')
        with self.assertRaises(ValueError):verify_files(files(),['m1'],methods=methods)
        with self.assertRaises(ValueError):verify_files(files(),['m1'],methods=methods,
            coverageManifest=[{**coverage[0],'actionQuote':'这个动作并未写到实际的文件内容中'}])
        with self.assertRaises(ValueError):verify_files(files(),['m1'],methods=methods,
            coverageManifest=[{**coverage[0],'conditionQuotes':[]}])


if __name__=='__main__':unittest.main()
