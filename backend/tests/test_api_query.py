import urllib.request
import json
import sys

def test():
    url_planner = 'http://127.0.0.1:8000/api/test/planner'
    data = json.dumps({'user_query': 'what happened in venzuela'}).encode('utf-8')
    req = urllib.request.Request(url_planner, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            planner_res = json.loads(response.read().decode())
            print('PLANNER OUTPUT:')
            print(json.dumps(planner_res.get('planner'), indent=2))
            
            print('\n--- INITIAL SEARCH CONTEXT RETRIEVED ---')
            print(planner_res.get('initial_search_context', 'None found'))
            print('----------------------------------------\n')
            
            url_orch = 'http://127.0.0.1:8000/api/test/orchestrator'
            orch_data = json.dumps({
                'user_query': 'what happened in venzuela', 
                'planner': planner_res.get('planner')
            }).encode('utf-8')
            req_orch = urllib.request.Request(url_orch, data=orch_data, headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req_orch) as response_orch:
                orch_res = json.loads(response_orch.read().decode())
                print('\nORCHESTRATOR OUTPUT:')
                print(json.dumps(orch_res, indent=2))
    except Exception as e:
        print('Error:', e)
        if hasattr(e, 'read'):
            print(e.read().decode())

if __name__ == '__main__':
    test()
