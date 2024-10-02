import datetime
import xml.etree.ElementTree as ET
from collections import defaultdict

def log_as_dictionary(log):
    log_dict = defaultdict(list)
    lines = log.strip().split("\n")
    
    for line in lines:
        if line.strip():
            parts = line.split(";")
            if len(parts) == 4:
                task, case_id, user, timestamp = parts
                log_dict[case_id].append({
                    "task": task,
                    "user": user,
                    "timestamp": datetime.datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                })
    
    return log_dict

def dependency_graph_inline(log):
    dep_graph = defaultdict(lambda: defaultdict(int))
    
    for case_id, events in log.items():
        sorted_events = sorted(events, key=lambda x: x["timestamp"])
        
        for i in range(len(sorted_events) - 1):
            task_1 = sorted_events[i]["task"]
            task_2 = sorted_events[i + 1]["task"]
            if task_1 != task_2:  
                dep_graph[task_1][task_2] += 1
    
    return dep_graph

def read_from_file(filename):
    tree = ET.parse(filename)
    root = tree.getroot()

    namespace = {'xes': 'http://www.xes-standard.org/'}
    log_dict = defaultdict(list)

    for trace in root.findall('xes:trace', namespace):
        case_id = None
        for trace_attr in trace.findall('xes:string', namespace):
            if trace_attr.get('key') == 'concept:name':
                case_id = trace_attr.get('value')
                break
        
        if case_id is None:
            continue

        for event in trace.findall('xes:event', namespace):
            event_data = {
                "concept:name": "record issue",  
                "org:resource": "admin-1",       
                "time:timestamp": datetime.datetime(1970, 1, 1, 1, 0),  
                "cost": 11                      
            }
            
            for attr in event:
                key = attr.get('key')
                if key == "concept:name":
                    event_data["concept:name"] = attr.get('value', 'record issue')
                elif key == "org:resource":
                    event_data["org:resource"] = attr.get('value', 'admin-1')
                elif key == "time:timestamp":
                    timestamp_value = attr.get('value', None)
                    try:
                        event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=None)
                    except ValueError:
                        try:
                            event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                        except ValueError:
                            event_data["time:timestamp"] = datetime.datetime(1970, 1, 1, 1, 0)
                elif key == "cost":
                    try:
                        cost_value = float(attr.get('value', 0))
                        event_data["cost"] = int(cost_value) if cost_value.is_integer() else cost_value
                    except (ValueError, TypeError):
                        event_data["cost"] = 11

            log_dict[case_id].append(event_data)

    return log_dict

def dependency_graph_file(log):
    dep_graph = defaultdict(lambda: defaultdict(int))
    
    for case_id, events in log.items():
        sorted_events = sorted(events, key=lambda x: x["time:timestamp"])
        
        for i in range(len(sorted_events) - 1):
            task_1 = sorted_events[i]["concept:name"]
            task_2 = sorted_events[i + 1]["concept:name"]
            if task_1 != task_2:  
                dep_graph[task_1][task_2] += 1
    
    return dep_graph
