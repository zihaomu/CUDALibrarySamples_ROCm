#!/usr/bin/env python3
"""Generate explicit schemas for attempts, route registry and sample work coverage."""
from experiment import ROOT,write,OUTCOMES
base={'$schema':'https://json-schema.org/draft/2020-12/schema','type':'object'}
def record(required,properties):return dict(base,required=required,properties=properties)
string={'type':'string','minLength':1}
attempt=record(['schema_version','experiment_id','sample_id','case_id','batch_id','backend','started_at_utc','experiment_outcome','eligible_for_sample_pass'],
 {'schema_version':{'const':1},'experiment_id':string,'sample_id':string,'case_id':string,'batch_id':string,'backend':string,
  'started_at_utc':{'type':'string','format':'date-time'},'finished_at_utc':{'type':['string','null']},
  'experiment_outcome':{'enum':sorted(OUTCOMES)},
  'eligible_for_sample_pass':{'const':False}})
task=record(['sample_id','source','primary_phase','baseline_status','state','retry_condition'],
 {'sample_id':string,'source':string,'primary_phase':{'enum':['R1','R2','R3','R4','R5','R6','R7','R8']},
  'baseline_status':{'enum':['PASSED','PARTIAL','FAILED','UNSUPPORTED']},'state':string,'retry_condition':string})
schemas={'experiment':attempt,
 'tasks':record(['schema_version','tasks'],{'schema_version':{'const':1},'tasks':{'type':'array','minItems':639,'maxItems':639,'items':task}}),
 'libraries':record(['schema_version','libraries','modules'],{'schema_version':{'const':1},'libraries':{'type':'array','items':record(['id','status','qualified_samples'],{'id':string,'status':string,'qualified_samples':{'type':'array','items':string}})},'modules':{'type':'object','minProperties':30,'maxProperties':30}}),
 'backend-routes':record(['schema_version','routes'],{'schema_version':{'const':1},'routes':{'type':'array','minItems':639,'maxItems':639,'items':record(['sample_id','route_id','status','implementation','candidate_libraries'],{'sample_id':string,'route_id':string,'status':string,'implementation':{'type':['string','null']},'candidate_libraries':{'type':'array'}})}})}
for name,schema in schemas.items():write(ROOT/'migration/moat/schema'/(name+'.schema.json'),schema)
print('Generated',len(schemas),'schemas')
