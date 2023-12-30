# TTRPG live_illustrate
ASR + LLM + Diffusion = ???

This project:
* Uses [Whisper](https://github.com/openai/whisper) to transcribe live audio of a tabletop RPG session
* Uses [GPT-3.5](https://platform.openai.com/docs/guides/text-generation) to extract a description of the current setting from the transcript
* Uses [DALL-E](https://platform.openai.com/docs/guides/images) to draw the setting
* Uses [Flask](https://flask.palletsprojects.com) & [HTMX](https://htmx.org) to display a new image every few minutes

And like most AI projects, it simultaneously works better and worse than one might expect. 
The images generated are usually an amusingly flawed rendition of what's going on, but are almost _too_ good to be just ambient background flavor.

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
I recommend installing in a [virtual environment](https://docs.python.org/3/library/venv.html). 

```
# From PyPI:
pip install live-illustrate

# Or for hacking:
git clone git@github.com:ehennenfent/live_illustrate.git
cd live_illustrate
pip install -e ".[dev]"
```

Whisper will be _much_ faster if you use a cuda-enabled pytorch build. I recommend installing this manually afterwards.
```
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision torchaudio  # https://pytorch.org/get-started/locally/
```

**You'll need an OpenAI API key, exposed via environment variable or in the `.env` file, like so: `OPENAI_API_KEY=<my_secret_api_key>`.**

With the default settings, it costs about $1/hour to run. You can lower the cost by reducing the size of the generated images, or 
increasing the interval between them. 

### Running
Once installed, run the `illustrate` command line tool, which will automatically start recording with your default microphone.
A `data\` directory will be created containing the generated images and transcripts, and a web server will start on `localhost:8080` to display the generated images. 

A few words about the most important command line options:
* `--wait_minutes`: This controls how frequently the tool draws an image, which directly translates into how expensive it is
to run. The default of 7.5 minutes seems to work well for our campaign.
* `--max_context`: Each interval, the tool looks back at the transcript and collects up to `max_context` tokens to send to GPT3. 
It will get as close as possible, so some of these tokens may come from _before_ the previous image was generated. GPT can be 
a bit slow about summarizing large amounts of text, so be careful about making this too large. The default of 2000 tokens seems
to correspond _very_ roughly to about ten minutes of conversation from one of our sessions, but YMMV. 
* `--persistence_of_memory` When summarizing long conversations, the LLM can seem to get "stuck" on the first setting described.
This argument controls what fraction of the previous context is retained each time an image is generated. The default setting of 0.2
may lead to some discontinuity if your party is in one place for a long time. 

Optionally, it's possible to upload generated images to a Discord server automatically by configuring a [Discord webhook](https://support.discord.com/hc/en-us/articles/228383668) and supplying the URL in the `DISCORD_WEBHOOK` environment variable.
