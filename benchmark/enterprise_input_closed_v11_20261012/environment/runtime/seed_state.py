"""Concrete synthetic account background from human input only, never old AI.

These records make reads/searches operate on actual state. Their values are
experimental inputs, not reconstructed mail, dates, messages, or task answers.
"""
from datetime import datetime, timedelta, timezone
import hashlib
import re

SCHEMA='synthetic-enterprise-services-v1'
TZ=timezone(timedelta(hours=8))

def build_state(session_id, human_texts, candidates, knowledge=()):
    texts=list(human_texts)
    # Background objects may be named in later human requests, but no AI text or
    # derived task output is admitted. Names are not complete future prompts.
    evidence='\n'.join(texts)
    first=texts[0] if texts else ''
    dated=re.search(r'20\d\d-\d\d-\d\d',first)
    try:
        anchor=datetime.fromisoformat(dated[0]).replace(tzinfo=TZ) if dated else datetime(2026,10,8,tzinfo=TZ)
    except ValueError:
        anchor=datetime(2026,10,8,tzinfo=TZ)
    names=[]
    for expression in [r'[「《“\"]([^」》”\"\n]{2,55})[」》”\"]',r'([\u4e00-\u9fff]{2,16}(?:公司|科技|医疗|集团|大学|学院|医院|项目))',r'([A-Za-z][A-Za-z0-9_-]{2,30})',r'([^\s，。；：:]{2,40}\.(?:docx|xlsx|pdf|pptx|md|csv))']:
        for term in re.findall(expression,evidence):
            if term.startswith(('sk-','eyJ')):continue
            if term not in names and term not in {'Mon','Tue','Wed','Thu','Fri','Sat','Sun','GMT'}:
                names.append(term)
    names=names[:18]
    related='、'.join(names) if names else '项目需求、费用核对与会议安排'
    available=set(candidates)
    state={'schema':SCHEMA,'synthetic':True,'session_id':session_id,
           'knowledge':list(knowledge),'mail':[],'calendar':[],'messages':[],
           'provenance':{'policy':'human_text_and_named_objects_only_no_historical_ai',
             'human_text_sha256':hashlib.sha256(evidence.encode()).hexdigest(),
             'historical_equivalence':False,'reference_date':anchor.isoformat(),
             'date_policy':'first_human_explicit_date_else_fixed_experiment_date',
             'background_objects':names,'external_delivery':False}}
    scenarios=[
        ('项目需求与验收范围确认','项目经理','产品负责人',
         '本期先完成核心流程与数据导入，验收包含字段完整性、错误处理和导出可读性。请在周三需求会前确认职责及验收样例。'),
        ('采购报价与交货安排','供应商联络人','采购团队',
         '本批报价为人民币36,800元（含税），交期为确认订单后10个工作日，质保12个月。附件规格中的接口和温度要求待双方确认后冻结。'),
        ('会议通知与议程','项目秘书','参会团队',
         '本次会议议程为上周事项跟进、客户需求差异确认、交期风险及下周责任分工。会议室为三层301，支持远程参加。'),
        ('合同版本与待确认事项','法务联络人','业务负责人',
         '当前版本保留付款节点、交付标准、质保及双方签字页。请核对主体名称和对接人，版本变更应保留修订记录。'),
        ('费用申请与票据补充','行政团队','申请人',
         '本次申请含交通680元、住宿两晚共960元、餐费160元，合计1,800元。需补行程日期、发票及审批记录；这些是本实验账户的合成票据数据。'),
        ('客户沟通记录与下次跟进','客户联络人','客户成功团队',
         '客户优先关注部署时间、数据留存、接口兼容和售后响应。计划下周安排演示，会前提供规格差异表，现阶段不作已验收承诺。')]
    if 'mail' in available:
        for i in range(18):
            subject,sender,recipient,body=scenarios[i%len(scenarios)]
            date=anchor+timedelta(days=-(i//3),hours=9+i%7)
            state['mail'].append({'id':f'inbox-{i+1:03d}','subject':subject+'｜'+(names[i%len(names)] if names else '企业项目'),
              'from':sender+' <contact'+str(i+1)+'@synthetic.invalid>','to':[recipient+' <team@synthetic.invalid>'],
              'body':body+'\n相关项目或资料：'+related+'。\n此邮件为当前会话隔离的合成账户记录。',
              'folder':'inbox','read':i%3!=0,'received_at':date.isoformat(),'created_at':date.isoformat(),
              'synthetic':True,'external_delivery':False,'attachments':[]})
    if 'calendar' in available:
        for i in range(7):
            start=anchor+timedelta(days=i-2,hours=10 if i%2==0 else 14)
            state['calendar'].append({'id':f'event-background-{i+1:03d}',
              'title':['项目例会','客户需求确认','交付与风险复盘'][i%3]+'｜'+(names[i%len(names)] if names else '企业协同'),
              'start':start.isoformat(),'end':(start+timedelta(minutes=60)).isoformat(),
              'location':['三层301会议室','线上会议','二层讨论室'][i%3],
              'attendees':['项目经理','产品负责人','业务代表'],'description':'讨论'+related+'，记录决策与责任分工。',
              'synthetic':True,'created_at':anchor.isoformat()})
    if 'messaging' in available or 'messages' in available:
        for i in range(12):
            state['messages'].append({'id':f'message-background-{i+1:03d}','channel':'项目协同群',
              'sender':['项目经理','采购联络人','行政联络人'][i%3],
              'body':scenarios[i%len(scenarios)][3]+'相关资料：'+related+'。',
              'created_at':(anchor+timedelta(days=-(i//4),hours=9+i%4)).isoformat(),
              'synthetic':True,'external_delivery':False,'status':'synthetic_existing_message'})
    return state
