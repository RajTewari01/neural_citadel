'''
base.py - a base file where all the agents inherit from.
========================================================

Features:
    - 

'''
from typing import Tuple,Dict,List,Literal,Optional,Union
import subprocess,sys,os,json,shutil,secrets
from pathlib import Path
import importlib
import platform


class ConfigPlatform:

    _ROOT = Path(__file__).resolve().parents[4]

    @staticmethod
    def config_venv(venv:str)->Path:
        system_name = platform.system()
        base_path = ConfigPlatform._ROOT / "venvs/env/" / venv
        if system_name == "Windows":
            return base_path / "Scripts/python.exe"
        elif system_name == "Linux" or system_name == "Darwin":
            return base_path / "bin/python"
        else:
            raise ValueError(f"Unsupported system: {system_name}")
    
    def get_secret_key(
        self,
        key_name:str,
        path:Optional[Union[str,Path]] = None
        ) -> str :

        key_path = Path(__file__).resolve().parents[4] / "D:/neural_citadel/configs/secrets/socials.env"
        assert key_name , "Hey provide a correct api key to fetch."
        if path:
           assert Path(path).exists(),"Hey provide a correct path."
           key_path = path
        
        from dotenv import dotenv_values
        return dotenv_values.get(key_name,"Not found!")

        
           
        
        


         

    
    

