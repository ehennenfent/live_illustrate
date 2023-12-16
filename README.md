# live_illustrate
ASR + LLM + Diffusion = ???

This project:
* Uses Whisper to transcribe live audio of a tabletop RPG session
* Uses ChatGPT to extract a description of the current setting from the transcript
* Uses Dall-e to draw the setting
* Uses Flask & HTMX to display a new image every few minutes

And like most AI projects, it simultaneously works better and worse than one might expect. 

### installation
```
pip install -e . 
pip install --index-url https://download.pytorch.org/whl/cu118 torch torchvision torchaudio  # https://pytorch.org/get-started/locally/
```

** You'll need an OpenAI API key, exposed via environment variable or in the `.env` file, like so: `OPENAI_API_KEY=<my_secret_api_key>`. **

With the default settings, it costs about $1/hour to run. 
