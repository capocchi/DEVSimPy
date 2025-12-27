#!/usr/bin/env python
"""Test script to verify MQTT configuration loading"""
import os
import sys
import configparser
from pathlib import Path

# Add devsimpy to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def GetUserConfigDir():
    """Get user config directory"""
    config_dir = os.path.expanduser('~')
    return config_dir

def check_config():
    """Check if MQTT config exists and what it contains"""
    config_file = os.path.join(GetUserConfigDir(), '.devsimpy')
    
    print(f"Looking for config file at: {config_file}")
    print(f"Config file exists: {os.path.exists(config_file)}")
    
    if os.path.exists(config_file):
        print(f"Config file size: {os.path.getsize(config_file)} bytes")
        print("\nConfig file contents:")
        with open(config_file, 'r') as f:
            contents = f.read()
            print(contents)
        
        print("\n\nParsing with configparser:")
        cfg = configparser.ConfigParser()
        cfg.read(config_file)
        
        print(f"Sections found: {cfg.sections()}")
        
        if cfg.has_section('BROKER_MQTT'):
            print("\nBROKER_MQTT section found!")
            print("Options in BROKER_MQTT:")
            for key, value in cfg.items('BROKER_MQTT'):
                print(f"  {key} = {value}")
        else:
            print("\nNo BROKER_MQTT section found")
    else:
        print("Config file does not exist yet")

if __name__ == '__main__':
    check_config()
