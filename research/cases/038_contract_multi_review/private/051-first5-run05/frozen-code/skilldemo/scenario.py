"""Observable synthetic scenario, not a quality benchmark."""
import time
import uuid

def scenario(loop, actor='alice', review=False):
    if loop.agent.mode != 'replay': raise ValueError('合成示例仅允许在replay模式运行')
    with loop.store.tx() as db:
        existing = loop.store.get(db, 'scenario', 'example-' + actor)
        if existing:
            return existing['result']
    session = 'scenario-' + uuid.uuid4().hex[:10]
    def turn(text, skills=None): return loop.chat(actor, session, text, skills or [])
    turn('你好')
    turn('整理销售周报，必须先核对金额单位，再扣除退款并汇总收入')
    loop.tick(time.time() + max(loop.settle_seconds, loop.idle_seconds) + 1)
    first = loop.discover(actor)[0]
    loop.generate(actor, first['id'])
    skill = loop.accept(actor, first['id'])
    turn('新任务：整理下一期销售周报', [skill['id']])
    loop.tick(time.time() + max(loop.settle_seconds, loop.idle_seconds) + 1)
    loop.discover(actor)
    turn('不对，跨期退款必须单独列出，不能计入本期收入')
    loop.tick(time.time() + max(loop.settle_seconds, loop.idle_seconds) + 1)
    update = loop.discover(actor)[0]
    loop.generate(actor, update['id'])
    skill = loop.accept(actor, update['id'])
    submission = loop.submit(actor, update['id'])
    if review:
        shared = loop.review('reviewer', submission['id'], True)
        loop.chat('bob', 'scenario-bob-' + uuid.uuid4().hex[:8], '整理销售报告，必须核对退款', [shared['id']])
    result = {'session': session, 'skill': skill['id'], 'submission': submission['id']}
    with loop.store.tx() as db:
        loop.store.put(db, 'scenario', {'id': 'example-' + actor, 'owner': actor, 'result': result})
    return result
