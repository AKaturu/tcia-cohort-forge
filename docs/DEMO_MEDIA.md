# Demo Media

The repository demo assets are public-workflow illustrations. They do not call the live TCIA API and do not include downloaded DICOM files.

## Files

- `docs/assets/demo.gif` - README animation
- `docs/assets/demo.mp4` - downloadable demo clip
- `docs/assets/demo-poster.png` - static preview frame

## Regenerate

```bash
python -m pip install -e ".[media]"
python scripts/generate_demo_media.py
```

The generator creates a three-step guided walkthrough of collection discovery, cohort filtering, and manifest-oriented downloads. The GIF is the inline GitHub preview; the MP4 is the full browser-playable clip.
