'''
base.py - a base file where all the agents inherit from.
========================================================

Features:
    - 

'''

from typing import Optional,Tuple,List,Union
from pathlib import Path
import platform

class BaseConfig:
    _ROOT = Path(__file__).resolve().parents[4].absolute()
    def __init__(
        self
        ):pass 
    
    def check_and_convert(
        path : Union[str,Path],
        convert_to : type
    ):
        assert Path(path).exists() or path , "Hey! Path cannot be empty"
        if not isinstance(path,convert_to):
            convert_to(path)
        return path
    
    @staticmethod
    def confiig_venv(
        venv:str,
        path_type: Union[str,Path]
        ) -> Optional[Union[str,Path]]:
        
        assert Path(venv).exists(), 'This virtual environment does not exists. Please provide a correct venv path.'
        system_name = platform.system()
        base_path = BaseConfig._ROOT / "venvs/env/" / venv

        if system_name == 'Windows':
            return base_path / 'Scripts/python.exe'
        elif system_name == 'Darwin' or system_name == 'Linux' :
            return base_path / 'bin/python' 
        else:
            raise ValueError(f'Unsupported system type, {system_name} is not supported.')
    
    







        
