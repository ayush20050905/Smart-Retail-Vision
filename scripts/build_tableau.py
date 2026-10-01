"""Generate Tableau starter workbook; desktop verification still required."""
import copy
import csv
from pathlib import Path
import xml.etree.ElementTree as E
import zipfile
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'tableau'; out.mkdir(exist_ok=True)
fields=next(csv.reader((ROOT/'data/demo/minute_metrics.csv').open()))
strings={'run_id','source_type','store_id','camera_id'}
reals={'observed_seconds','person_seconds','queue_person_seconds','alert_seconds'}
def dtype(f): return 'string' if f in strings else 'datetime' if f=='minute' else 'date' if f=='date' else 'real' if f in reals else 'integer'
r=E.Element('workbook',{'source-platform':'win','version':'9.0','xmlns:user':'http://www.tableausoftware.com/xml/user'})
E.SubElement(r,'preferences'); E.SubElement(r,'style-theme',name='clean')
dsources=E.SubElement(r,'datasources'); name='textscan.retailflow'
ds=E.SubElement(dsources,'datasource',caption='RetailFlow minute metrics',inline='true',name=name,version='9.0')
conn=E.SubElement(ds,'connection',{'class':'textscan','directory':'../data/demo','filename':'minute_metrics.csv','password':'','server':''})
rel=E.SubElement(conn,'relation',name='minute_metrics#csv',table='[minute_metrics#csv]',type='table')
cols=E.SubElement(rel,'columns',{'character-set':'UTF-8','header':'yes','locale':'en_US','separator':','})
for i,f in enumerate(fields): E.SubElement(cols,'column',datatype=dtype(f),name=f,ordinal=str(i))
meta=E.SubElement(conn,'metadata-records')
for i,f in enumerate(fields):
    m=E.SubElement(meta,'metadata-record',{'class':'column'})
    for tag,value in [('remote-name',f),('remote-type',{'string':'129','datetime':'135','date':'133','real':'5','integer':'20'}[dtype(f)]),('local-name',f'[{f}]'),('parent-name','[minute_metrics#csv]'),('remote-alias',f),('ordinal',str(i)),('local-type',dtype(f)),('aggregation','Count' if dtype(f)=='string' else 'Year' if dtype(f) in ('date','datetime') else 'Sum'),('contains-null','true')]: E.SubElement(m,tag).text=value
E.SubElement(ds,'aliases',enabled='yes'); columns={}
for f in fields:
    dim=dtype(f) in ('string','date','datetime') or f=='hour'
    columns[f]=E.SubElement(ds,'column',datatype=dtype(f),name=f'[{f}]',role='dimension' if dim else 'measure',type='nominal' if dtype(f)=='string' else 'ordinal' if dim else 'quantitative')
calcs={
 'Average Visible People':'IF SUM([observed_seconds]) > 0 THEN SUM([person_seconds])/SUM([observed_seconds]) END',
 'Average Queue Length':'IF SUM([observed_seconds]) > 0 THEN SUM([queue_person_seconds])/SUM([observed_seconds]) END',
 'Queue Alert Time Fraction':'IF SUM([observed_seconds]) > 0 THEN SUM([alert_seconds])/SUM([observed_seconds]) END',
 'Daily Entries LOD':'{ FIXED [store_id], [date] : SUM([entries]) }'}
for f,formula in calcs.items():
    columns[f]=E.SubElement(ds,'column',datatype='real',name=f'[{f}]',role='measure',type='quantitative')
    E.SubElement(columns[f],'calculation',{'class':'tableau','formula':formula})
works=E.SubElement(r,'worksheets')
sheets=[('Entry Crossings','entries','Sum','sum','Bar'),('Exit Crossings','exits','Sum','sum','Bar'),('Visible People','Average Visible People','User','usr','Line'),('Queue Length','Average Queue Length','User','usr','Line'),('Queue Alerts','queue_alerts','Sum','sum','Bar')]
for title,field,deriv,token,mark in sheets:
    ws=E.SubElement(works,'worksheet',name=title); table=E.SubElement(ws,'table'); view=E.SubElement(table,'view')
    sources=E.SubElement(view,'datasources'); E.SubElement(sources,'datasource',caption='RetailFlow minute metrics',name=name)
    deps=E.SubElement(view,'datasource-dependencies',datasource=name)
    for col in columns.values(): deps.append(copy.deepcopy(col))
    x='[none:minute:qk]'; y=f'[{token}:{field}:qk]'
    E.SubElement(deps,'column-instance',column='[minute]',derivation='None',name=x,pivot='key',type='quantitative')
    E.SubElement(deps,'column-instance',column=f'[{field}]',derivation=deriv,name=y,pivot='key',type='quantitative')
    E.SubElement(view,'aggregation',value='true')
    E.SubElement(table,'style')
    panes=E.SubElement(table,'panes'); pane=E.SubElement(panes,'pane')
    pv=E.SubElement(pane,'view'); E.SubElement(pv,'breakdown',value='auto')
    E.SubElement(pane,'mark',{'class':mark})
    ps=E.SubElement(pane,'style'); rule=E.SubElement(ps,'style-rule',element='mark'); E.SubElement(rule,'format',attr='mark-color',value='#168a78')
    E.SubElement(table,'rows').text=f'[{name}].{y}'; E.SubElement(table,'cols').text=f'[{name}].{x}'
dashboards=E.SubElement(r,'dashboards'); dash=E.SubElement(dashboards,'dashboard',name='RetailFlow - SYNTHETIC DEMO')
E.SubElement(dash,'style'); E.SubElement(dash,'size',{'maxheight':'800','maxwidth':'1200','minheight':'800','minwidth':'1200'})
zones=E.SubElement(dash,'zones')
for i,title in enumerate(['Entry Crossings','Visible People','Queue Length','Queue Alerts']):
    E.SubElement(zones,'zone',{'h':'50000','w':'50000','x':str((i%2)*50000),'y':str((i//2)*50000),'id':str(i+1),'name':title})
windows=E.SubElement(r,'windows',{'saved-dpi-scale-factor':'1.0','source-height':'1000'})
for title,*_ in sheets:
    win=E.SubElement(windows,'window',{'class':'worksheet','name':title}); E.SubElement(win,'viewpoint',name=title)
E.SubElement(windows,'window',{'class':'dashboard','name':'RetailFlow - SYNTHETIC DEMO'})
E.SubElement(r,'thumbnails'); E.indent(r)
E.ElementTree(r).write(out/'RetailFlow.twb',encoding='utf-8',xml_declaration=True)
conn.set('directory','Data')
with zipfile.ZipFile(out/'RetailFlow_Demo.twbx','w',zipfile.ZIP_DEFLATED) as z:
    z.writestr('RetailFlow.twb',E.tostring(r,encoding='utf-8',xml_declaration=True))
    z.write(ROOT/'data/demo/minute_metrics.csv','Data/minute_metrics.csv')
print('Created Tableau starter workbooks.')
