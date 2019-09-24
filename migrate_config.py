#!/usr/bin/python

import json
import yaml
import os
import sys

# location of the configuration file
file = os.path.abspath(os.path.dirname(__file__))+"/config.json"
# destination directory where to store the converted configuration
config_dir = os.path.abspath(os.path.dirname(__file__))+"/config/"
# version of this script
version = "1.0"

print "myHouse2eGeoffrey Configuration Migration Utility v"+version
print ""
print "This script will convert a myHouse v2.4 configuration file into an eGeoffrey format"
print "Please place your config.json file into the directory where this script resides"
print "The new configuration will be created into "+config_dir
raw_input("Press Enter to continue...")
print ""
print "Notes:"

# save a file
def save_file(file, data, version=1):
    # convert to yaml
    content = yaml.safe_dump(data, default_flow_style=False)
    # recursively create directories if needed
    filename = os.path.basename(file)
    directories = os.path.dirname(file)
    if directories != "":
        path = config_dir+os.sep+directories
        if not os.path.exists(path):
            os.makedirs(path)
    # write the file
    file_path = config_dir+os.sep+file+"."+str(version)+".yml"
    f = open(file_path, "w")
    f.write(content)
    f.close()
    
# convert notification
def migrate_notification(new):
    # move global notification settings into "suppress" and convert the names
    for setting in ["min_severity", "mute_min_severity", "mute", "rate_limit"]:
        if setting in new:
            if "suppress" not in new: new["suppress"] = {}
            new_setting = setting
            if setting == "mute": new_setting = "timeframe"
            if setting == "mute_min_severity": new_setting = "timeframe_severity_exception"
            if setting == "rate_limit": new_setting = "rate_hour"
            if setting == "min_severity": new_setting = "severity_below"
            new["suppress"][new_setting] = new[setting]
            del new[setting]

# create destination directory if does not exist
if not os.path.isdir(config_dir): os.makedirs(config_dir)
              
# read the configuration file
if not os.path.exists(file): 
    print "Unable to read config.json from the current directory"
    sys.exit(1)
with open(file) as f: content = f.read()
old = json.loads(content)

# keep track of some items
lang = old["general"]["language"]
sections = old["gui"]["sections"]
formats = old["general"]["formats"]

# migrate the "house" file
new = {}
new["name"] = old["general"]["house_name"]
new["timezone"] = 2
new["units"] =  "imperial" if old["general"]["units"]["imperial"] else "metric"
new["language"] = old["general"]["language"]
new["latitude"] = old["general"]["latitude"]
new["longitude"] = old["general"]["longitude"]
save_file("house", new)

# keep track of latitude and longitude
latitude = new["latitude"]
longitude = new["longitude"]

# migrate the "gui/settings" file
new = {}
new["map_api_key"] = old["gui"]["maps"]["api_key"]
new["default_page"] = "overview/dashboard"
save_file("gui/settings", new)

# migrate "controller/db" file
new = {}
new = old["db"]
del new["enabled"]
del new["database_file"]
save_file("controller/db", new)

# migrate the "controller/alerter" file
new = {}
new["retention"] = old["alerter"]["data_expire_days"]
save_file("controller/alerter", new)

# migrate "output" configuration in individual modules
new = {}
new = old["output"]["email"]
del new["enabled"]
del new["debug"]
del new["alerts_digest"]
new["to"] = ",".join(new["to"])
migrate_notification(new)
print "\t- Manually add template to service/smtp"
save_file("notification/smtp", new)

new = {}
new = old["output"]["slack"]
del new["enabled"]
migrate_notification(new)
save_file("notification/slack", new)

new = {}
new = old["output"]["sms"]
del new["enabled"]
new["to"] = ",".join(new["to"])
migrate_notification(new)
save_file("notification/betamax_sms", new)

new = {}
new = old["output"]["audio"]
del new["enabled"]
if new["device"] == "": del new["device"]
migrate_notification(new)
save_file("notification/speaker", new)

new = {}
new = old["output"]["buzzer"]
del new["enabled"]
migrate_notification(new)
save_file("notification/buzzer_raspi", new)

new = {}
new = old["output"]["gsm_sms"]
del new["enabled"]
new["to"] = ",".join(new["to"])
migrate_notification(new)
save_file("notification/gsm_sms", new)

new = {}
new = old["output"]["gsm_call"]
del new["enabled"]
new["to"] = ",".join(new["to"])
migrate_notification(new)
save_file("notification/gsm_call", new)

# migrate "input" configuration in individual modules
new = {}
new = old["output"]["slack"]
save_file("interaction/slack", new)

new = {}
new["device"] = old["input"]["audio"]["device"]
new["engine"] = old["input"]["audio"]["engine"]
if new["device"] == "": del new["device"]
new["speaker"] = "speaker"
save_file("interaction/microphone", new)

# migrate "plugins" configuration in individual modules
new = {}
new = old["plugins"]["weatherchannel"]
del new["language"]
save_file("service/weatherchannel", new)

new = {}
new = old["plugins"]["messagebridge"]
if "enabled" in new: del new["enabled"]
save_file("service/messagebridge", new)

new = {}
new = old["plugins"]["rtl_433"]
if "enabled" in new: del new["enabled"]
save_file("service/rtl433", new)

new = {}
new = old["plugins"]["gpio"]
if "enabled" in new: del new["enabled"]
print "\t- GPIO service now uses BCM pin mode"

new = {}
new = old["plugins"]["mqtt"]
if "enabled" in new: del new["enabled"]
save_file("service/mqtt", new)

for gateway in old["plugins"]["mysensors"]["gateways"]:
    new = {}
    new = gateway
    del new["enabled"]
    filename = "service/mysensors_"+new["gateway_id"]
    print "\t- Configure a MySensors service with the following: EGEOFFREY_MODULES=service/mysensors_"+new["gateway_type"]+"=mysensors_"+new["gateway_id"]
    del new["gateway_id"]
    del new["gateway_type"]
    save_file(filename, new)

new = {}
new = old["plugins"]["bluetooth"]
if "enabled" in new: del new["enabled"]
save_file("service/bluetooth", new)
    
# migrate gui sections
c=1
for section in old["gui"]["sections"]:
    a = {}
    a["order"] = c
    a["text"] = section["display_name"][lang]
    save_file("gui/menu/"+section["section_id"]+"/_section", a)
    c=c+1

# keep track of all the groups and associated sensors
groups = {}
for module in old["modules"]:
    module_id = module["module_id"]
    if "sensors" in module:
        for sensor in module["sensors"]:
            if module_id+":"+sensor["group_id"] not in groups: groups[module_id+":"+sensor["group_id"]] = []
            groups[module_id+":"+sensor["group_id"]].append(sensor["sensor_id"])

# migrate user's content
module_count = 0
calendars = []
services={}
for module in old["modules"]:
    module_id = module["module_id"]
    # migrate each sensor
    if "sensors" in module:
        for sensor in module["sensors"]:
            s = {}
            if "display_name" in sensor: s["description"] = sensor["display_name"][lang]
            if not sensor["enabled"]: s["disabled"] = True
            s["format"] = formats[sensor["format"]]["type"]
            if s["format"] ==  "": s["format"] = sensor["format"]
            s["unit"] = formats[sensor["format"]]["suffix"]
            if s["unit"] == "": del s["unit"]
            if "summarize" in sensor and sensor["summarize"]["avg"] and "min_max" in sensor["summarize"] and sensor["summarize"]["min_max"]:
                s["calculate"] = "avg_min_max"
            if "summarize" in sensor and sensor["summarize"]["avg"] and "sum" in sensor["summarize"] and sensor["summarize"]["sum"]:
                s["calculate"] = "sum"
            if "retention" in sensor and "realtime_count" in sensor["retention"]:
                s["retain"] = "single_value"
            else: s["retain"] = "history"
            # migrate the plugin mapping to the associated service
            if "plugin" in sensor:
                s["service"] = {}
                s["service"]["name"] = sensor["plugin"]["plugin_name"]
                s["service"]["configuration"] = sensor["plugin"]
                if sensor["plugin"]["plugin_name"] == "wunderground":
                    s["service"]["name"] = "openweathermap"
                    s["service"]["configuration"]["request"] = s["service"]["configuration"]["measure"]
                    del s["service"]["configuration"]["measure"]
                    s["service"]["configuration"]["latitude"] = latitude
                    s["service"]["configuration"]["longitude"] = longitude
                    print "\t- Sensor "+module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]+" is using the wunderground plugin which is no longer supported. Replacing with 'openweathermap' service"
                if sensor["plugin"]["plugin_name"] == "weatherchannel":
                    s["service"]["configuration"]["request"] = s["service"]["configuration"]["measure"]
                    del s["service"]["configuration"]["measure"]
                if sensor["plugin"]["plugin_name"] == "mysensors":
                    s["service"]["name"] = "mysensors_"+s["service"]["configuration"]["gateway_id"]
                    del s["service"]["configuration"]["gateway_id"]
                if sensor["plugin"]["plugin_name"] == "rtl_433":
                    filter = ""
                    for key, value in sensor["plugin"]["search"].iteritems():
                        if filter == "": filter = key+"="+value
                        else: filter = filter+"&"+key+"="+value
                    s["service"]["configuration"]["filter"] = filter
                    del s["service"]["configuration"]["search"]
                if "polling_interval" in sensor["plugin"]:
                    s["service"]["schedule"] = {}
                    s["service"]["schedule"]["trigger"] = "interval"
                    s["service"]["schedule"]["minutes"] = sensor["plugin"]["polling_interval"]
                    s["service"]["mode"] = "active"
                else: s["service"]["mode"] = "passive"
                if "queue_size" in sensor["plugin"]:
                    s["service"]["mode"] = "actuator"
                del s["service"]["configuration"]["plugin_name"]
                if "polling_interval" in s["service"]["configuration"]: del s["service"]["configuration"]["polling_interval"]
                if "cache_expire_min" in s["service"]["configuration"]: del s["service"]["configuration"]["cache_expire_min"]
                if s["service"]["name"] not in services: services[s["service"]["name"]] = 0
                services[s["service"]["name"]] = services[s["service"]["name"]]+1
            save_file("sensors/"+module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"], s)
            if "series" in sensor:
                for series in sensor["series"]:
                    if "series_id" in series and series["series_id"] == "sum": 
                        print "\t- Manually set 'series: sum' to every widget where "+module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]+" is used"
                    if "type" in series and series["type"] == "bar":
                        print "\t- Manually set 'style: bar' to every widget where "+module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]+" is used"
            if sensor["format"] == "calendar":
                calendars.append(module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"])
    
    # migrate the rules
    if "rules" in module:
        for rule in module["rules"]:
            s = {}
            if "display_name" in rule: s["text"] = rule["display_name"][lang]
            if "for" in rule:
                s["for"] = []
                for f in rule["for"]: s["for"].append(f.replace(":", "/"))
            if not rule["enabled"]: s["disabled"] = True
            s["conditions"] = []
            s["conditions"].append(rule["conditions"])
            s["severity"] = rule["severity"]
            if rule["run_every"] == "minute":
                s["schedule"] = {}
                s["schedule"]["trigger"] = "interval"
                s["schedule"]["minutes"] = 1
            if rule["run_every"] == "5 minutes":
                s["schedule"] = {}
                s["schedule"]["trigger"] = "interval"
                s["schedule"]["minutes"] = 5
            if rule["run_every"] == "hour":
                s["schedule"] = {}
                s["schedule"]["trigger"] = "interval"
                s["schedule"]["hours"] = 1
            if rule["run_every"] == "day":
                s["schedule"] = {}
                s["schedule"]["trigger"] = "interval"
                s["schedule"]["days"] = 1
            for definition in rule["definitions"]:
                value = rule["definitions"][definition]
                if ":" in str(value) or "%i%" in str(value):
                    if "variables" not in s: s["variables"] = {}
                    split = value.split(",")
                    out = ""
                    if len(split) == 4:
                       out = split[3].upper()+" " 
                    if split[1] != "-1" or split[2] != "-1": out = out + split[1]+","+split[2]+" "
                    out = out + split[0].replace(":", "/")
                    if out in calendars: out = "SCHEDULE "+out
                    s["variables"][definition] = out
                else:
                    if "constants" not in s: s["constants"] = {}
                    s["constants"][definition] = value
            if "actions" in rule:
                s["actions"] = []
                for a in rule["actions"]:
                    split = a.split(",")
                    if split[0] == "set" or split[0] == "send": split[0] = "SET"
                    s["actions"].append(split[0]+" "+split[1].replace(":", "/")+" "+split[2])
            if "schedule" in s:
                s["type"] = "recurrent"
            else:
                s["type"] = "on_demand"
            save_file("rules/"+module_id+"/"+rule["rule_id"], s)
     
    # migrate the widgets
    if "widgets" in module:
        menu = {}
        menu["text"] = module["display_name"][lang]
        menu["icon"] = module["icon"].replace("fa-","")
        menu["page"] = module["section_id"]+"/"+module_id
        menu["order"] = module_count
        save_file("gui/menu/"+module["section_id"]+"/"+module_id, menu)
        rows = []
        for r in module["widgets"]:
            row = {}
            columns = []
            row[""] = columns
            rows.append(row)
            for w in r:
                s = {}
                s["title"] = w["display_name"][lang]
                s["size"] = w["size"]
                for l in w["layout"]:
                    if l["type"] == "sensor_group_summary":
                        s["widget"] = "summary"
                        s["sensors"] = []
                        for sensor_id in groups[l["group"]]:
                            s["sensors"].append(l["group"].replace(":","/")+"/"+sensor_id)
                        break
                    elif l["type"] == "sensor_group_timeline":
                        s["widget"] = "timeline"
                        s["sensors"] = []
                        for sensor_id in groups[l["group"]]:
                            if "exclude" in l and l["group"]+":"+sensor_id in l["exclude"]: continue
                            s["sensors"].append(l["group"].replace(":","/")+"/"+sensor_id)                
                        if l["timeframe"] == "recent": s["group_by"] = "hour"
                        if l["timeframe"] == "history": s["group_by"] = "day"
                        if l["timeframe"] == "forecast": 
                            s["group_by"] = "day"
                            s["timeframe"] = "next_7_days"
                        break 
                    elif l["type"] == "chart_short_inverted" or l["type"] == "chart_short":
                        s["widget"] = "timeline"
                        s["sensors"] = []
                        s["sensors"].append(l["sensor"].replace(":","/"))
                        if l["timeframe"] == "recent": s["group_by"] = "hour"
                        if l["timeframe"] == "history": s["group_by"] = "day"
                        if l["timeframe"] == "forecast": 
                            s["group_by"] = "day"
                            s["timeframe"] = "next_7_days"
                        break 
                    elif l["type"] == "image":
                        s["widget"] = "image"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "current_measure":
                        s["widget"] = "value"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "checkbox":
                        s["widget"] = "control"
                        s["sensor"] = l["sensor"].replace(":","/")
                        if "send" in l or "send_on" in l: print "\t- Manually fix checkbox with send: "+w["widget_id"]
                        break
                    elif l["type"] == "input":
                        s["widget"] = "input"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "separator":
                        break
                    elif l["type"] == "button":
                        s["widget"] = "button"
                        s["actions"] = []
                        for action in l["actions"]:
                            split = action.split(",")
                            if split[0] == "send":
                                a = split[1].split("/")
                                a1 = a[0]+"/"+a[1]+"/"+a[2]
                                s["actions"].append("SET "+a1)
                        break
                    elif l["type"] == "calendar":
                        s["widget"] = "calendar"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "map":
                        s["widget"] = "map"
                        if "tracking" in l: s["tracking"] = l["tracking"]
                        s["sensors"] = []
                        for sensor_id in groups[l["group"]]:
                            if "exclude" in l and l["group"]+":"+sensor_id in l["exclude"]: continue
                            s["sensors"].append(l["group"].replace(":","/")+"/"+sensor_id)             
                        if l["timeframe"] == "recent": s["group_by"] = "hour"
                        if l["timeframe"] == "history": s["group_by"] = "day"
                        if l["timeframe"] == "forecast": 
                            s["group_by"] = "day"
                            s["timeframe"] = "next_7_days"
                        break
                    elif l["type"] == "table":
                        s["widget"] = "table"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "data":
                        s["widget"] = "text"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "current_header" and len(w["layout"]) == 1:
                        s["widget"] = "value"
                        s["sensor"] = l["sensor"].replace(":","/")
                        break
                    elif l["type"] == "current_header" and len(w["layout"]) > 1:
                        continue
                    elif l["type"] == "alerts":
                        break
                    elif l["type"] == "configuration":
                        break
                    else: 
                        print "unknown type "+l["type"]+": "+w["widget_id"]       
                columns.append(s)
        # write the content of the page
        save_file("gui/pages/"+module["section_id"]+"/"+module_id, rows)
    module_count = module_count +1

print "\t- Rules' variable placeholders do not add anymore the unit of the measure which has to be made added manually"
print "\t- Configuration of all the services, notifications and interactions have been migrated; however ensure you install through egeoffrey-cli only those actually used by at least one sensor"
print "\t- The following services (and associated number of sensors) are in use:"
for service in services:
    print "\t"+service+": "+str(services[service])
print ""
print "DONE!"
