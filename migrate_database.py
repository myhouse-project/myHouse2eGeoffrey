#!/usr/bin/python

import redis
import json
import os
import sys

# location of the configuration file
file = os.path.abspath(os.path.dirname(__file__))+"/config.json"
# version of this script
version = "1.0"

print "myHouse2eGeoffrey Database Migration Utility v"+version
print ""
print "This script will convert a myHouse v2.4 database into the eGeoffrey format"
print "Please place your config.json file into the directory where this script resides"
raw_input("Press Enter to continue...")

# load config file
if not os.path.exists(file): 
    print "Unable to read config.json from the current directory"
    sys.exit(1)
with open(file) as f: content = f.read()
old = json.loads(content)

# read database configuration. New db will be written at old_db +1
hostname = old["db"]["hostname"]
port = old["db"]["port"]
source_db = old["db"]["database"]
destination_db = source_db+1
# database location override
#hostname = "pi"
#destination_db = 4

print "The database #"+str(source_db)+" at "+hostname+":"+str(port)+" will be migrated on the same host into database #"+str(destination_db)
print "To override, please uncomment 'hostname' and 'destination_db' under 'database location override' at the beginning of this script"
raw_input("Press Enter to continue...")
print ""

# connect to the source and destination db
source_db = redis.StrictRedis(host=hostname, port=port, db=source_db)
destination_db = redis.StrictRedis(host=hostname, port=port, db=destination_db)
# clean up destination db
destination_db.flushdb()

# migrate a key
def migrate(source_db, destination_db, old_key, new_key):
    print "\t"+old_key+" -> "+new_key
    if not source_db.exists(old_key):
        print "\tWARNING: "+old_key+" does not exists"
        return
    data = source_db.dump(old_key)
    destination_db.restore(new_key, 0, data)

# migrate alerts
print "Migrating alerts:"
for severity in ["info","warning","alert"]:
    migrate(source_db, destination_db, "myHouse:_alerts_:"+severity, "eGeoffrey/alerts/"+severity)

# migrate sensors
count = 0
for module in old["modules"]:
    module_id = module["module_id"]
    if "sensors" in module:
        for sensor in module["sensors"]:
            # define old and new key
            old_key_base = "myHouse:"+module_id+":"+sensor["group_id"]+":"+sensor["sensor_id"]
            new_key_base = "eGeoffrey/sensors/"+module_id+"/"+sensor["group_id"]+"/"+sensor["sensor_id"]
            print "Migrating "+old_key_base+":"
            # get all the stats associated to a key
            old_keys = source_db.keys(old_key_base+":*")
            if source_db.exists(old_key_base): old_keys.append(old_key_base)
            # for each key, migrate it
            for old_key in old_keys:
                if old_key.endswith(":rate"): continue
                new_key = new_key_base+old_key.replace(old_key_base, "").replace(":","/")
                migrate(source_db, destination_db, old_key, new_key)
                count = count+1

print "Migrated "+str(count)+" keys"
