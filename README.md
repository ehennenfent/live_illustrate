# TTRPG live_illustrate
ASR + LLM + Diffusion = ???

This project:
* Uses Whisper to transcribe live audio of a tabletop RPG session
* Uses ChatGPT to extract a description of the current setting from the transcript
* Uses Dall-e to draw the setting
* Uses Flask & HTMX to display a new image every few minutes

And like most AI projects, it simultaneously works better and worse than one might expect. 
The images generated are never a perfect rendition of what's going on, but are almost _too_ good to be just ambient background flavor.

## Demo Reel

Some scenes from our party's first trial session:

![image](https://github.com/ehennenfent/live_illustrate/assets/7294647/3525a789-2f07-4b76-b704-bb163b5d6a9e)
The party enjoys dinner together on the deck of the _Daydream_. No one's quite sure where the other ship came from, but it looks nice.

![image](https://github.com/ehennenfent/live_illustrate/assets/7294647/ea25229d-ace4-409f-a4b9-5f6a86921f27)
The party sails the _Daydream_ through a narrow canal in a swamp, searching for the hidden pirate city of Siren's Cove. 
Perhaps they should ask the barrel people for directions. 

![image](https://github.com/ehennenfent/live_illustrate/assets/7294647/f1c381f4-22b8-49bf-ba29-e7e550045e5c)
The party eavesdrops on a red-haired gnome and a halfling in a Siren's Cove tavern who are plotting to steal a competitor's shipping manifest.
Pay no attention to the faces of the other patrons. 

![image](https://github.com/ehennenfent/live_illustrate/assets/7294647/0af383e8-5276-47ce-9ed1-6385348398c9)
The party seeks further gossip at a luxe brothel called _The Rich Dagger_, guarded by a Goliath bouncer and famed for its perplexing architecture. 

## Installation
```
pip install -e . 
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision torchaudio  # https://pytorch.org/get-started/locally/
```

**You'll need an OpenAI API key, exposed via environment variable or in the `.env` file, like so: `OPENAI_API_KEY=<my_secret_api_key>`.**

With the default settings, it costs about $1/hour to run. You can lower the cost by reducing the size of the generated images, or 
increasing the interval between them. 
