# Cat Man — image generation (Google Gemini / nano banana)

Generates every story image straight to disk via the Gemini API.

## One-time setup
1. Get a free API key: https://aistudio.google.com/apikey
2. Paste it into the project-root file `Cat\.env`:
   ```
   GEMINI_API_KEY=your_key_here
   ```
3. Install the libraries:
   ```
   cd Cat\game\tools
   pip install -r requirements.txt
   ```

## Generate
```
cd Cat\game\tools

python generate_images.py --pages 1        # test: just page 1 (3 images)
python generate_images.py                  # the whole book (60 images)
```
Options: `--pages 1-5` or `--pages 3,7,12`, `--overwrite`, `--no-refs`.

## Where images land
`Cat\game\assets\scenes\book2\`
- `b2_p01_correct.jpg`, `b2_p01_trapA.jpg`, `b2_p01_trapB.jpg`, ...  (game-ready 1000x750)
- `raw\` — the full-resolution originals

## How it works
- `book2_prompts.json` holds all 60 scenes (a shared `style_header` + one `scene`
  line each) plus per-scene character `refs` (the cutouts in `game\assets\`) so
  Cat Man, the raccoon, the weasel and the baker pig stay on-model.
- Edit the JSON to tweak any scene; re-run with `--overwrite` to regenerate.
- Cost is roughly 4 cents per image (~$2.50 for the whole book).
- For Book 3 later: make `book3_prompts.json` the same way and run
  `python generate_images.py --prompts book3_prompts.json`.
