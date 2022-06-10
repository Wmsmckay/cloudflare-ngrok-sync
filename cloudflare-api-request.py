from datetime import datetime
import requests
import json
import variables
import os



zoneName = os.getenv("ZONE")
cloudflare_auth_email = os.getenv("CLOUDFLARE_AUTH_EMAIL")
cloudflare_auth_key = os.getenv("CLOUDFLARE_AUTH_KEY")
mcSrvRecord = os.getenv("MC_SRV_RECORD")
mcCnameRecord = os.getenv("MC_CNAME_RECORD")


url = 'https://api.cloudflare.com/client/v4/zones'
headers = {
    'Accept': 'application/json',
    'X-Auth-Email': cloudflare_auth_email,
    'X-Auth-Key': cloudflare_auth_key
}


def main():
    # print(f"Running script at {datetime.now()}")
    zoneId = getZoneId()
    if zoneId:
        ngrokAddr = getNgrokTunnelInfo()
        mcSrvRecordId = findDnsRecordId(zoneId, mcSrvRecord)
        mcCnameRecordId = findDnsRecordId(zoneId, mcCnameRecord)

        # print(mcSrvRecordId, mcCnameRecordId)

        # check that the ngrok address is the same as the DNS entry on cloudflare

        if isPublicUrlSame(mcSrvRecordId, mcCnameRecordId, zoneId, ngrokAddr) == False:
            # change it
            updateEntries(zoneId, mcCnameRecordId, mcSrvRecordId, ngrokAddr)
    # print(f"Completed at {datetime.now()}\n")


def getZoneId():
    try:
        req = requests.get(url, headers=headers)
        data = req.json()
        if data["result"][0]["name"] == zoneName:
            return data["result"][0]["id"]
        else:
            print("No Zone by that name")
    except:
        print("Error getting Zone ID")


def getDnsRecordInfo(zoneId, recordId):
    try:
        endpoint = f"{url}/{zoneId}/dns_records/{recordId}"
        req = requests.get(url=endpoint, headers=headers)
        data = req.json()
        return data
    except:
        print("Error getting DNS record info")


def findDnsRecordId(zoneId, recordInfo):
    try:
        endpoint = f"{url}/{zoneId}/dns_records"
        req = requests.get(url=endpoint, headers=headers)
        data = req.json()
        for i in data["result"]:
            if i["name"] == recordInfo[0] and i["type"] == recordInfo[1]:
                return i["id"]
    except:
        print("Error finding DNS record by ID")


def getNgrokTunnelInfo():
    try:
        req = requests.get("http://10.0.0.16:34040/api/tunnels")
        data = req.json()
        addr = data["tunnels"][0]["public_url"]
        url = addr[6::].split(":", 1)[0]
        port = int(addr.split(":", 2)[2])
        return [url, port]
    except:
        print("Error getting Ngrok tunnel info")


def isPublicUrlSame(SrvRecordId, CnameRecordId, zoneId, ngrok):
    try:
        mcsrvInfo = getDnsRecordInfo(zoneId, SrvRecordId)
        mcSrvPort = mcsrvInfo["result"]["data"]["port"]
        mcCnameInfo = getDnsRecordInfo(zoneId, CnameRecordId)
        mcCnameUrl = mcCnameInfo["result"]["content"]

        # print(type(mcSrvPort), type(ngrok[1]))
        if mcCnameUrl == ngrok[0] and mcSrvPort == ngrok[1]:
            return True

        print(f"Ngrok info:     \t{mcCnameUrl}:{mcSrvPort}")
        print(f"Cloudflare info:\t{ngrok[0]}:{ngrok[1]}")
        return False
    except:
        print("Error checking if URLs are the same.")


def changeSrvRecord(zoneId, id, newPort):
    try:
        endpoint = f"{url}/{zoneId}/dns_records/{id}"
        body = {
            "type": "SRV",
            "name": f"_minecraft._tcp.mc.{zoneName}",
            "proxied": False,
            "ttl": 1,
            "content": f"0\t{newPort}\tmc.{zoneName}",
            "data": {
                    "name": f"mc.{zoneName}",
                    "port": newPort,
                    "priority": 0,
                    "proto": "_tcp",
                    "service": "_minecraft",
                    "target": f"mc.{zoneName}",
                    "weight": 0
            }
        }

        req = requests.put(url=endpoint, headers=headers,
                           data=json.dumps(body))
        data = req.json()
    except:
        print("Error changing SRV Record.")


def changeCnameRecord(zoneId, id, newContent):
    try:
        endpoint = f"{url}/{zoneId}/dns_records/{id}"

        body = {
            "type": "CNAME",
            "proxied": False,
            "ttl": 1,
            "name": f"mc.{zoneName}",
            "content": newContent
        }

        req = requests.put(url=endpoint, headers=headers,
                           data=json.dumps(body))
        data = req.json()
    except:
        print("Error Changing the CNAME record.")


def updateEntries(zoneId, mcCnameId, mcSrvId, ngrok):
    try:
        changeCnameRecord(zoneId, mcCnameId, ngrok[0])
        changeSrvRecord(zoneId, mcSrvId, ngrok[1])
        print("Successfully updated")
    except:
        print("There was an ERROR!!!")


main()
