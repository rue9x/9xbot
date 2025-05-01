import time
import obsws_python as obs
import os

import json
from dotenv import load_dotenv
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')

OBS_HOST = os.getenv('OBS_HOST')
OBS_PORT = os.getenv('OBS_PORT')
OBS_PASSWORD = os.getenv('OBS_PASSWORD') # Replace with your actual OBS password

def connect(host=OBS_HOST,port=OBS_PORT,password=OBS_PASSWORD,timeout=3):
    try:
        cl = obs.ReqClient(host=OBS_HOST, port=OBS_PORT, password=OBS_PASSWORD,timeout=3)
        return cl
    except Exception as e:
        raise ValueError(f"Error connecting to OBS: {e}")
    
def get_scene_item_id(client, scene_name, source_name):
    items = client.get_scene_item_list(scene_name).scene_items
    for item in items:
        if item['sourceName'] == source_name:
            return item['sceneItemId']
    raise ValueError(f"Source '{source_name}' not found in scene '{scene_name}'")

def get_current_scene_name(client):
    try:
        sn = client.get_current_program_scene().current_program_scene_name
        return sn
    except Exception as e:
        raise ValueError(f"Error getting current scene name: {e}")
       
def set_source_enabled(client,scene,source_name,enabled=True):
    try:
        cl.set_scene_item_enabled(scene,source_name,enabled=enabled)
        return enabled
    except Exception as e:
        raise ValueError(f"Error setting object visibility: {e}")

def test_flicker(cl):
    scene_name = get_current_scene_name(cl)
    source_name = 'PythonImg'
    source_id = get_scene_item_id(cl,scene_name,source_name)
    set_source_enabled(cl,scene_name,source_id,enabled=True)
    time.sleep(1)
    set_source_enabled(cl,scene_name,source_id,enabled=False)
    time.sleep(1)
    set_source_enabled(cl,scene_name,source_id,enabled=True)
    time.sleep(1)
    set_source_enabled(cl,scene_name,source_id,enabled=False)
    time.sleep(1)
    set_source_enabled(cl,scene_name,source_id,enabled=True)
    time.sleep(1)

if __name__ == "__main__":
    cl = connect()
    test_flicker(cl)