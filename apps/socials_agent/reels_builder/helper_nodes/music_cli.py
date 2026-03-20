'''
music_cli.py

>>> Features :
        - Lets you choose the music for your video.
        - Lets you download any music you want to add to your video.
        - Lets you automate your music selection process.
        - Lets you add music to your video.
        - Lets you set the volume of the music.
        - Automatically sets the music duration accordingly to the video length.

>>> Usage :
        - python music_cli.py --download <music url> //lets you download music 
        - python music_cli.py --show_list   // returns list of music
        - python music_cli.py --download <music url> --add <video_path> // add the music to the video
        - python music_cli.py --download <music url> --add <video_path> --set_volume <100.0> // add the music to the video with set volume

>>> Example :
        $ python music_cli.py --download https://www.youtube.com/watch?v=dQw4w9WgXcQ --add "D:\neural_citadel\apps\socials_agent\reels_builder\output\video.mp4" --set_volume 100.0

'''        

from pathlib import Path
import sys
import gc
_ROOT = Path(__file__).resolve().parents[4]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from apps.socials_agent.reels_builder.agents.base import ConfigPlatform
from configs.paths import MUSIC_DIR,PREDOWNLOADED_MIXER_SONGS
from typing import Optional,Literal,List,Union,Dict,Tuple,Callable,ModuleType
from dataclasses import dataclass
import importlib.util
import subprocess
import argparse
import secrets
import yt_dlp
import json
import re

# class LazyLoader:
#     def __init__(self,module_name):
#         """Initializes the proxy without loading the module."""
#         self.module_name = module_name
#         self.module = None
        
#     def _load_module(self):
#         """Loads the module if it is not already loaded."""
#         self.module = importlib.import_module(self.module_name) if self.module is None else self.module
#         return self.module

#     def __getattr__(self, name):
#         """Delegates attribute access to the module."""
#         if self.module is None:
#             self._load_module()
#         return getattr(self.module, name)

#     def _unload_module(self):
#         """Unloads the module if it is loaded."""
#         if self.module:
#             del self.module
#             self.module = None
#             if self.module_name in sys.modules:
#                 del sys.modules[self.module_name]
#             submodules = [mod for mod in sys.modules if mod.startswith(f"{self.module_name}.")]
#             for sub in submodules:
#                 del sys.modules[sub]
#             gc.collect()
    
    # def __del__(self):
    #     self._unload_module()


def lazy_loader(module_name:str)->ModuleType:
    '''
    >>> lazy loading modules for speed and performance optization.
    '''
    spec = importlib.util.find_spec(module_name)
    assert module_name is not None,"Calling Lazy Loader without a function is not allowed."
    assert spec is not None,"Module not found."
    # if spec is None:
    #     raise ImportError(f"Module {module_name} not found.")
    # if module_name is None:
    #     raise ValueError("Module name cannot be None.")
    loader = importlib.util.LazyLoader(spec.loader)
    spec.loader = loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    loader.exec_module(module)
    return module

class MusicHelper:
    '''
    >>>  Features : 
            - Lets you check if the music file is present in the server or not.
            - Lets you download the music.
    '''

    def __init__(self):
        '''Initializes the MusicHelper class.'''
        self.music_dir = MUSIC_DIR
        
    def _is_music_available(
        self,
        name:Optional[str] = None,
        url:Optional[str] = None
    ) -> Tuple[bool,Optional[Path]]:
        '''
        >>>  usage :
                - Lets you check if the file is present already in the server or not
                - Internally lets you save time by not downloading the same file again
        '''

        song_name = None
        if not name and not url: 
            return (False, None)
        if name : song_name = name.split(".")[0] if '.' in name else name
        elif url:
            sanitized_name = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
            song_name = sanitized_name.group(1) if sanitized_name else None
            if song_name:
                if any(char in song_name for char in ['\\','/','|']):
                    sanitized_name = re.search(r"(?:v=|youtu\.be/|embed/|shorts/|/v/|^)([a-zA-Z0-9_-]{11})", url)
                    song_name = sanitized_name.group(1) if sanitized_name else None
        
        if song_name:
            search_song = next(self.music_dir.rglob(f"*{song_name}*"),None) # Added (*song_name*) wildcards to search for any file name.
            if search_song:
                return (True,search_song.absolute())  
        return (False,None)

    def _get_video_duration(
        self,
        video_path:Union[str,Path],
        debug:bool = False
    )->Optional[float]:   

        '''
        >>> usage :
             - lets you get the video time to adjust it accordingly to the music.
        '''
        if isinstance(video_path,str):
            video_path = Path(video_path)
        # assert video_path.exists(), f"Video file {video_path} does not exist."
        if not video_path.exists(): raise FileNotFoundError(f"Video file {video_path} does not exist.")
        mpy = lazy_loader("moviepy.video.io.VideoFileClip")
        clip = None
        try:
            clip = mpy.VideoFileClip(str(video_path))
            duration = clip.duration
            
        except Exception as e:
            if debug:
                import traceback
                print(traceback.format_exc())
            return None
        else:
            return duration
        finally:
            if clip is not None: clip.close()

    def _download_music(
        self,
        url:str,
        debug:bool = False,
        download_dir:Optional[Union[str,Path]] = None
    )->Optional[Path]:
        '''
        >>> usage :
             - lets you download the music from the given url.
        '''
        if not url : raise ValueError("URL cannot be None.")
        is_available, file_path = self._is_music_available(url=url)
        if is_available:
            return file_path
        
        
        if isinstance(download_dir,str):
            download_dir = Path(download_dir)
            if not download_dir.exists(): download_dir.mkdir(parents=True, exist_ok=True)
        if download_dir is None:
            download_dir = self.music_dir
        
        try:

            with yt_dlp.YoutubeDL({
                'format': 'bestaudio/best',
                'outtmpl': str(download_dir / '%(title)s_[%(id)s].%(ext)s'),
                'default_search': 'ytsearch',
                'quiet': not debug,
                'no_warnings': not debug,
            }) as ydl:            
                info_dict = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info_dict)
                return Path(filename)

        except Exception as e:
            if debug:
                import traceback
                print(traceback.format_exc())
            return None

class MusicAgent:
    def __init__(self,load_moviepy = False):
        self.music_dir = MUSIC_DIR
        self.predownloaded_mixer_songs = PREDOWNLOADED_MIXER_SONGS
        self.mpv  = None 
        if self.load_moviepy:
            self.mpv = lazy_loader("moviepy.video.io.VideoFileClip")

    def show_template(
        self,
        paths_format: Literal['List','json'],
        debug:bool = False
    ) -> Union[str, List[Path]]:
        directory = self.music_dir
        place_holder = list(directory.iterdir())
        if paths_format == 'List':
            return place_holder
        else:
            return json.dumps([str(i) for i in place_holder],indent=4)
    
    def show_predownloaded_template(
        self,
        paths_format: Literal['List','json'],
        debug:bool = False
    ) -> Union[str, List[Path]]:
        """
        >>> usage :
             - lets you see the predownloaded mixer songs.
        """
        directory = self.predownloaded_mixer_songs
        place_holder = list(directory.iterdir())
        if paths_format == 'List':
            return place_holder
        else:
            return json.dumps([str(i) for i in place_holder],indent=4)
    
    def get_video_time(
        self,
        video_path: Union[Path,str],
        debug: bool = False
    ) ->float :
        #  assert self.mpv is not None,'Moviepy is not loaded.'
        try:
            if self.mpv is None:
                self.mpv = lazy_loader("moviepy.video.io.VideoFileClip")
        except Exception as e:
            import traceback
            print(f'Error occured : {traceback}')

    
        
    

        




        
    
    


    





