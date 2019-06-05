import re
import requests

from kubernetes import client
from kubernetes.client.apis import CoreV1Api, CustomObjectsApi

BASE = "harbor.humblelab.com/"

class ScanResult(object):

    def __init__(self, namespace, pod, container, image, severity, found):
        self.namespace = namespace
        self.pod = pod
        self.container = container
        self.image = image
        self.severity = severity
        self.found = found

def scan(resource):

    results = []
    core = client.CoreV1Api()
    custom = client.CustomObjectsApi()

    pods = core.list_pod_for_all_namespaces()
    for pod in pods.items:
        result = None
        for container in pod.spec.containers:
	    if container.image.startswith(BASE):
                path = re.sub(BASE, '', container.image)
                parts = path.split(':')
                if len(parts) == 1:
                    tag = 'latest'
                else:
                    tag = parts[1]
                image = parts[0]
                headers = {
                     "Content-Type": "application/json"
                }
                url = "https://%sapi/repositories/%s/tags/%s" % (BASE, image, tag)
                resp = requests.get(url, headers=headers)
                #print resp.json(indent=4)
		scan = resp.json()


                result = ScanResult(pod.metadata.namespace,
                                    pod.metadata.name,
                                    container.name,
                                    container.image,
                                    scan['scan_overview']['severity'],
                                    True)
            else:
                result = ScanResult(pod.metadata.namespace,
                                    pod.metadata.name,
                                    container.name,
                                    container.image,
                                    None,
                                    False)
        results.append(result)
    resource['status'] = {}
    resource['status']['results'] = [r.__dict__ for r in results]
    group, version = resource['apiVersion'].split('/')
    custom.patch_namespaced_custom_object(group, version, "default", "pilotscans", resource['metadata']['name'], resource)

       #print "CONTAINER IMAGE: %s NOT IN REGISTRY" % container.image
        
        #https://harbor.humblelab.com/api/repositories/library/cas-demo-frontend/tags?detail=1
