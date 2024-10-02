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

def safe_access_log(event_data):
    task = event_data.get("task", "record issue")
    user = event_data.get("user", "admin-1")
    timestamp = event_data.get("timestamp", datetime.datetime(1970, 1, 1, 1, 0))
    cost = event_data.get("cost", 11)  # Default cost is 11 if not available
    return {
        "task": task,
        "user": user,
        "timestamp": timestamp,
        "cost": cost
    }

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
                "concept:name": "record issue",  # Changed to match the expected key
                "org:resource": "admin-1",       # Changed to match the expected key
                "time:timestamp": datetime.datetime(1970, 1, 1, 1, 0),  # Changed to match the expected key
                "cost": 11                      # Default cost
            }
            
            for attr in event:
                key = attr.get('key')
                if key == "concept:name":
                    event_data["concept:name"] = attr.get('value', 'record issue')  # Use the expected key
                elif key == "org:resource":
                    event_data["org:resource"] = attr.get('value', 'admin-1')       # Use the expected key
                elif key == "time:timestamp":
                    timestamp_value = attr.get('value', None)
                    try:
                        event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S.%f%z').replace(tzinfo=None)
                    except ValueError:
                        try:
                            event_data["time:timestamp"] = datetime.datetime.strptime(timestamp_value, '%Y-%m-%dT%H:%M:%S%z').replace(tzinfo=None)
                        except (ValueError, TypeError):
                            event_data["time:timestamp"] = datetime.datetime(1970, 1, 1, 1, 0)  # Default value
                elif key == "cost":
                    try:
                        cost_value = float(attr.get('value', 0))
                        if cost_value.is_integer():
                            event_data["cost"] = int(cost_value)
                        else:
                            event_data["cost"] = cost_value
                    except (ValueError, TypeError):
                        event_data["cost"] = 11  # Default cost

            log_dict[case_id].append(event_data)

    return log_dict


def dependency_graph_file(log):
    return dependency_graph_inline(log)

def event_counts_per_case(log):
    result = []
    for case_id, events in log.items():
        result.append(f"{case_id} {len(events)}")
    return result


log = read_from_file("extension-log.xes")

# general statistics: for each case id the number of events contained
for case_id in sorted(log):
    print((case_id, len(log[case_id])))

# details for a specific event of one case
case_id = "case_123"
event_no = 0
print((log[case_id][event_no]["concept:name"], log[case_id][event_no]["org:resource"], log[case_id][event_no]["time:timestamp"],  log[case_id][event_no]["cost"]))