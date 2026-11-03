import sys,json
sys.path.insert(0,'/home/lookup07/lookup-preview-0.2.1-1793721877/lookup-source')
from lookup import platform,app
from unittest.mock import Mock
env=platform.session_env()
value=platform.read_primary(env) or ''
source=app.Source(env)
monitor=platform.Monitor('probe',0,0,1280,800,1)
snapshot=Mock(point=(360,262),monitor=monitor,available=(0,0,1280,800))
first=source.freeze(snapshot);second=source.freeze(snapshot)
assert value and source.consumed==' '.join(value.split())
assert first.mode==second.mode=='ocr'
print(json.dumps({'primary_chars':len(value),'contains_reported_advertisement':'Agensi.io' in value,'first_mode':first.mode,'second_mode':second.mode}))
