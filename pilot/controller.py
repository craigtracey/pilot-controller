import logging
import pprint

try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from threading import Thread

from kubernetes import client, config, watch

from pilot.scanner import scan

LOG = logging.getLogger(__name__)


def handle_updates(event_queue):
    while True:
        event = event_queue.get()
        LOG.info("Processinng update for %s", pprint.pprint(event))
        if event['type'] == 'ADDED':
            scan(event['object'])


def run_controller(args):

    try:
        config.load_incluster_config()
    except Exception as e:
        LOG.warning("Failed to load in-cluster config. "
                    "Trying environment. Error: %s", e)
        config.load_kube_config()

    crds = client.CustomObjectsApi()
    crds.api_client.configuration.debug = args.debug 

    event_queue = Queue()
    update_thread = Thread(target=handle_updates, args=(event_queue,))
    update_thread.daemon = True
    update_thread.start()

    LOG.debug("Starting watch loop")

    synced = False
    while True:
        samples = crds.list_namespaced_custom_object("harbor.vmware.com",
                                                     "v1", "default", "pilotscans")
        if not synced:
            print "not synced, so sync state nnow"
            synced = True

        resource_version = int(samples['metadata']['resourceVersion'])
        LOG.debug("Max resource version: %d", resource_version)

        crd_watch = watch.Watch()
        crd_watch.resource_version = resource_version

        stream = crd_watch.stream(
            crds.list_namespaced_custom_object,
            "harbor.vmware.com",
            "v1",
            "default",
            "pilotscans",
            resource_version=resource_version)

        LOG.debug("Received stream data from API server.")
        for event in stream:
            LOG.debug("Putting event on queue: %s" % pprint.pformat(event))
            event_queue.put(event)
            resource_version = int(
                event['object']['metadata']['resourceVersion'])
            crd_watch.resource_version = resource_version
