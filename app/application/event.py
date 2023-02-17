event_cb = {}


def process_event(event):
    if event in event_cb:
        cb = event_cb[event]
        cb[0](cb[1])


def subscribe_event(event, cb, opaque):
    event_cb[event] = (cb, opaque)
    return True
