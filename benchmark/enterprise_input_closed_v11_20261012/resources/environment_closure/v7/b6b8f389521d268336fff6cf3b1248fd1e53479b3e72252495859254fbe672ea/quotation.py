"""Generate parameterized project quotations with Decimal receipts and formulas."""
import argparse, json
from pathlib import Path
from decimal import Decimal, ROUND_HALF_UP
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

def generate(data,out):
    cents=lambda x:x.quantize(Decimal('0.01'),rounding=ROUND_HALF_UP)
    factor=Decimal(str(data['factor']));base=Decimal(str(data['base_total']))
    if not factor.is_finite() or factor<=0 or not base.is_finite() or base<0:raise ValueError('Invalid price or factor')
    if not data.get('source') or not data.get('items'):raise ValueError('Actual source and line items required')
    items=[]
    for item in data['items']:
        quantity=Decimal(str(item['quantity']));unit=Decimal(str(item['unit_price']))
        if not quantity.is_finite() or not unit.is_finite() or quantity<0 or unit<0 or not item.get('source'):
            raise ValueError('Line items need valid nonnegative numbers and evidence')
        amount=cents(quantity*unit);items.append((item,quantity,unit,amount,cents(amount*factor)))
    if sum((x[3] for x in items),Decimal(0))!=cents(base):raise ValueError('Line item base prices do not equal contract base_total')
    target=cents(base*factor);delta=target-sum((x[4] for x in items),Decimal(0))
    adjustments=[Decimal(0)]*len(items)
    remaining=delta
    if remaining>0:
        index=max(range(len(items)),key=lambda i:items[i][4])
        adjustments[index]=remaining;remaining=Decimal(0)
    elif remaining<0:
        for index in range(len(items)-1,-1,-1):
            deduction=min(items[index][4],-remaining)
            adjustments[index]=-deduction;remaining+=deduction
            if remaining==0:break
    assert remaining==0,'Cannot allocate rounding without a negative line'
    wb=Workbook();sheet=wb.active;sheet.title='报价明细'
    sheet.append([data.get('title','项目报价')]);sheet.append(['币种',data.get('currency','CNY'),'原价',float(base),'倍率',float(factor),'金额来源',data['source']])
    headers=['分类','模块','功能/交付描述','数量','原单价','基础金额','倍率后金额','舍入调整','报价金额','来源']
    sheet.append(headers)
    receipt=[]
    for i,(item,q,u,amount,adjusted) in enumerate(items,4):
        correction=adjustments[i-4]
        sheet.append([item.get('category',''),item.get('module',''),item['description'],float(q),float(u),float(amount),float(adjusted),float(correction),f'=G{i}+H{i}',item['source']])
        receipt.append(dict(description=item['description'],base_amount=str(amount),multiplied_amount=str(adjusted),rounding_adjustment=str(correction),final_amount=str(adjusted+correction)))
    last=sheet.max_row;sheet.append(['合计','','','','',f'=SUM(F4:F{last})',f'=SUM(G4:G{last})',f'=SUM(H4:H{last})',f'=SUM(I4:I{last})'])
    sheet.freeze_panes='D4';sheet.auto_filter.ref=f'A3:J{last}'
    for cell in sheet[3]:cell.font=Font(bold=True,color='FFFFFF');cell.fill=PatternFill('solid',fgColor='215B75')
    for r in sheet.iter_rows(min_row=4):
        for c in r:
            c.alignment=Alignment(vertical='top',wrap_text=True)
            if c.column in (5,6,7,8,9):c.number_format='#,##0.00'
    for i,width in enumerate([18,22,58,12,16,16,16,16,16,55],1):sheet.column_dimensions[get_column_letter(i)].width=width
    sources=wb.create_sheet('核算与来源');sources.append(['字段','值']);sources.append(['原合同总价',float(base)]);sources.append(['当轮倍率',float(factor)]);sources.append(['报价总价',float(target)]);sources.append(['金额来源',data['source']]);sources.append(['舍入说明','各行四舍五入到分，在非负约束下按反向条目分摊总价舍入差额'])
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True);wb.save(out)
    result=dict(base_total=str(cents(base)),factor=str(factor),quotation_total=str(target),rounding_adjustment=str(delta),currency=data.get('currency','CNY'),items=receipt,output=str(out),requires_formula_recalculation=True)
    out.with_suffix('.calculation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');p.add_argument('--out',required=True);a=p.parse_args()
    print(json.dumps(generate(json.loads(Path(a.input).read_text('utf-8-sig')),a.out),ensure_ascii=False))
if __name__=='__main__':main()
