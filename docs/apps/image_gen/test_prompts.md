# Test Prompts - ALL Pipelines

Run from `d:\neural_citadel`

---

## PIPELINES WITH --type

### ANIME (7 models)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "beautiful anime girl" --style anime --type meinamix --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime girl photo style" --style anime --type novaporn --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime warrior red eyes" --style anime --type bloodorangemix --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime witch dark forest" --style anime --type abyssorangemix --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "creepy anime ghost girl" --style anime --type eerieorangemix --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime knight fantasy RPG" --style anime --type azovya --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime girl shiny latex" --style anime --type shiny_sissy --open --aspect portrait --add_details
```

### CAR (11 LoRAs)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "sports car drawing" --style car --type sketch --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "luxury sedan highway" --style car --type sedan --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "vintage 1960s car" --style car --type retro --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "McLaren speedtail" --style car --type speedtail --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "Formula 1 racing" --style car --type f1 --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "Mazda MX5 Miata" --style car --type mx5 --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "modern SUV showroom" --style car --type autohome --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "taxi city street" --style car --type amsdr --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "Mazda RX7 FD3S drifting" --style car --type rx7 --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "train locomotive" --style car --type jetcar --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "sports motorcycle" --style car --type motorbike --open --aspect landscape --add_details
```

### DRAWING (4 models)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "giraffe sunset watercolor" --style drawing --type rachel_walker --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "anime girl sketch pixiv" --style drawing --type matcha_pixiv --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "surreal floating islands" --style drawing --type pareidolia --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "chinese mountains scroll" --style drawing --type chinese_ink --open --aspect landscape --add_details
```

### HYPERREALISTIC (5 models)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "beautiful woman portrait" --style hyperrealistic --type realistic_vision --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "woman in summer dress" --style hyperrealistic --type dreamshaper --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "detailed face portrait freckles" --style hyperrealistic --type neverending --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "clean digital portrait" --style hyperrealistic --type digital --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "dramatic lighting portrait" --style hyperrealistic --type typhoon --open --aspect portrait --add_details
```

### ETHNICITY (5 models)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "beautiful woman portrait" --style ethnicity --type asian --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "woman in traditional saree" --style ethnicity --type indian --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "model with blue eyes" --style ethnicity --type russian --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "blonde woman portrait" --style ethnicity --type european --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "woman in silk qipao" --style ethnicity --type chinese --open --aspect portrait --add_details
```

### PAPERCUT (2 models)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "dragon in layered paper art" --style papercut --type midjourney --open --aspect normal --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "cute cat origami style" --style papercut --type papercutcraft --open --aspect normal --add_details
```

### DIFCONSISTENCY (3 modes - defaults to photo)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "burger food photography" --style difconsistency --type photo --open --aspect normal --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "watch macro extreme detail" --style difconsistency --type detail --open --aspect normal --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "cyborg portrait" --style difconsistency --type raw --open --aspect portrait --add_details
```

---

## PIPELINES WITH AUTO-DETECTION (no --type)

### NSFW (auto-detects model from keywords)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "amateur instagram photo" --style nsfw --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "reddit gonewild selfie" --style nsfw --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "futanari woman" --style nsfw --open --aspect portrait --add_details
```

### HORROR (auto-detects shot type from prompt)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "vampire close-up portrait" --style horror --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "terrifying demon corridor" --style horror --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "abandoned asylum room" --style horror --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "blood moon forest wide panorama" --style horror --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "werewolf attacking dynamic action" --style horror --open --aspect landscape --add_details
```

### ZOMBIE (auto-detects from prompt)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "rotting zombie close-up portrait" --style zombie --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "two zombies hospital" --style zombie --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "zombie horde attacking city wide" --style zombie --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "chinese qing dynasty zombie talisman" --style zombie --open --aspect portrait --add_details
```

### GHOST (auto-detects shot type)
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "ethereal ghost woman floating in haunted mansion" --style ghost --open --aspect portrait --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "spectral apparition in dark cemetery wide shot" --style ghost --open --aspect landscape --add_details
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "translucent spirit close-up face" --style ghost --open --aspect portrait --add_details
```

---

## NO SUBTYPES

### CLOSEUP_ANIME
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "magical girl glowing eyes" --style closeup_anime --open --aspect portrait --add_details
```

### SPACE
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "colorful nebula stars galaxy" --style space --open --aspect landscape --add_details
```

### DIFFUSIONBRUSH
```bash
d:\neural_citadel\venvs\env\image_venv\Scripts\python.exe -m apps.image_gen.runner "fantasy warrior armor digital art" --style diffusionbrush --open --aspect portrait --add_details
```
