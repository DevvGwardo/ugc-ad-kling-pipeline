---
name: ugc-ad-kling-pipeline
description: Hosted-API counterpart to ugc-ad-video-pipeline. Same 8-step flow, but Steps 5–6 (frame + I2V) and optional VO/lipsync are replaced with KLing nodes — no 24GB VRAM required.
version: 1.0
tags: [video, ugc, ads, kling, comfyui, paid-api, pipeline]
---

# UGC Ad KLing Pipeline

Hosted-API counterpart to `ugc-ad-video-pipeline`. Same 8-step ad workflow, but Steps 5–6 (text-to-image + image-to-video) and lip-sync/VO are replaced with **KLing AI API nodes inside ComfyUI** — no 24GB VRAM required.

---

## 1. TL;DR — When to Use This vs. the FOSS Pipeline

| Factor | FOSS Pipeline | KLing Pipeline |
|--------|---------------|----------------|
| GPU needed? | 24GB+ VRAM (4090/A100) for wan2.1 I2V | ❌ None — KLing runs server-side |
| Cost per ad (gen) | ~$0.00 (electricity only) | ~$0.50–$1.50 per 5s clip (see pricing) |
| Commercial license | Depends on model (flux.1-dev = non-commercial) | ✅ KLing terms — check your use case |
| Quality ceiling | Good, but visible artifacts in complex motion | Higher — KLing v2-1 masters human motion, camera moves |
| Speed | 2-5 min per clip (queued on local GPU) | 30-90s per clip (queued on KLing servers) |
| Lip-sync / VO | bark/f5-tts + external tool | ✅ Built-in LipSync + TextToAudio nodes |
| Text in image | Unreliable with open models | ✅ KLing v2 handles text in image well |
| Video length | Up to 10s per clip (wan2.1) | 5s or 10s per clip (KLing I2V/T2V) |

**Decision rule:**
- Have a 4090 and need zero variable cost? → Use `ugc-ad-video-pipeline` (FOSS)
- Need commercial-grade quality, no GPU, or built-in lip-sync? → Use this skill
- Need both? → Use KLing for hero clips, FOSS for experimentation
- Budget ceiling: at ~$0.10–$0.25 per video generation, a 4-clip ad costs ~$0.40–$1.00

---

## 2. Setup

### 2.1 Install KLing ComfyUI Nodes

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/KwaiVGI/ComfyUI-KLingAI-API
cd ComfyUI-KLingAI-API
pip install -r requirements.txt
```

### 2.2 API Key

Get your API key from [Kling AI Dev Center](https://app.klingai.com/global/dev/document-api/quickStart/productIntroduction/overview).

Two options for configuring it:

**Option A — config.ini (recommended)** — edit `ComfyUI/custom_nodes/ComfyUI-KLingAI-API/config.ini`:

```ini
[API]
KLINGAI_API_ACCESS_KEY = your_access_key_here
KLINGAI_API_SECRET_KEY = your_secret_key_here
```

**Option B — pass into each Client node** (if you want to keep keys out of files).

### 2.3 Cost Note

KLing uses prepaid resource packs. Prices (approximate, subject to change — [check current pricing](https://klingai.com/dev-center)):

| Service | Standard (std) | Pro |
|---------|----------------|-----|
| Image Generation | ~$0.02–$0.05/image | — |
| Text-to-Video (5s) | ~$0.10–$0.20 | ~$0.25–$0.40 |
| Image-to-Video (5s) | ~$0.08–$0.15 | ~$0.20–$0.30 |
| Video Extend (5s) | ~$0.08–$0.15 | — |
| LipSync | ~$0.15–$0.30 | — |
| TextToAudio | ~$0.02–$0.05 | — |
| Video2Audio | ~$0.02–$0.05 | — |

**Per-ad estimate:** A 4-scene, 15-20s ad with lip-sync VO: **~$0.80–$2.00**.

### 2.4 Sanity Check

Restart ComfyUI, then check the node menu for a "KLingAI" category with these nodes:

```
KLingAIAPIClient
ImageGeneratorNode
Text2VideoNode
Image2VideoNode
VideoExtendNode
LipSyncNode (with LipSyncTextInputNode + LipSyncAudioInputNode)
EffectNode
ImageExpanderNode
Video2AudioNode
TextToAudioNode
PreviewVideo
PreviewAudio
```

Quick test — load this minimal workflow in ComfyUI:

```
[Client node] → [Text2Video node] → [PreviewVideo node]
```

Set the Text2Video prompt to "a clean app interface sliding into frame, modern SaaS aesthetic, smooth motion, 9:16" and run. If you get a video URL output, everything works.

---

## 3. Pattern → Production Mapping

Based on the 5 top-performing patterns from `may2026-niche-breakdowns.md` (see `ugc-ad-swipe-research/references/may2026-niche-breakdowns.md` for full research and source verification).

| # | Pattern | Best Niche | KLing Node Chain | Storyboard Template | Est. Cost / Ad |
|---|---------|-----------|------------------|--------------------|----------------|
| 1 | **Dollar + Timeframe Concrete Claim** | Fintech (expense trackers, tax apps, budgeting) | `ImageGen(9:16, kling-v2-1)` → `Image2Video(kling-v2-1-master, mode=std, duration=5)` → `PreviewVideo` | 4 scenes: (1) hook number card, (2) creator face with number overlay, (3) app UI screencap animated, (4) CTA card | $0.40–$0.80 |
| 2 | **Anti-Hook / Warning Angle** | SaaS, dev tools, fintech | `Text2Video(9:16, kling-v2-1-master, duration=5)` → `Text2Video(normal)` for product → `PreviewVideo` | 3 scenes: (1) warning text overlay on atmospheric video, (2) problem visualization, (3) solution product reveal | $0.30–$0.60 |
| 3 | **Income Threshold Callout** | Fintech (freelancers, 1099, Etsy) | `ImageGen(9:16, kling-v2-1)` → `Image2Video(kling-v2-1-master, duration=5)` → `LipSync(TextInput)` | 3 scenes: (1) threshold callout card, (2) creator talking to camera, (3) app demo + CTA | $0.50–$1.00 |
| 4 | **Confessional / "Nobody Told Me"** | Fintech, SaaS | `ImageGen(9:16, kling-v2-1)` → `Image2Video(mode=std, duration=5)` → `LipSync(TextInput)` | 3 scenes: (1) hook text card, (2) creator confessional talking head, (3) product reveal | $0.50–$1.00 |
| 5 | **Stakes / Fear (High-Stakes Reveal)** | Fintech (tax, compliance, debt) | `ImageGen(9:16, kling-v2-1)` → `Image2Video(mode=pro, duration=10)` → `LipSync(TextInput)` + `Video2Audio(sound_effect_prompt="tense dramatic music")` | 4 scenes: (1) fear hook card, (2) tense visualization, (3) relief pivot, (4) product + CTA | $0.80–$1.50 |

### Node Chain Legend

- **ImageGen** → KLingAIAPI:ImageGenerator — text-to-image, generates the starting frame
- **Text2Video** → KLingAIAPI:Text2Video — generates video directly from prompt (no starting image)
- **Image2Video** → KLingAIAPI:Image2Video — animates a starting frame into 5–10s video
- **LipSync** → KLingAIAPI:LipSync (+ LipSyncTextInputNode for text→speech)
- **Video2Audio** → KLingAIAPI:Video2Audio — adds sound effects / BGM to generated video
- **PreviewVideo** → KLingAIAPI:PreviewVideo — downloads the result

---

## 4. Three End-to-End Example Workflows

Each workflow below is self-contained. Feed the prompts into KLing nodes in ComfyUI (or use `scripts/storyboard_to_kling.py` to automate it).

### 4a. Dollar + Timeframe Concrete Claim (Fintech)

**Target audience:** Freelancers, side-hustlers, people who overspend
**Hook:** "I clawed back $4,217 in 90 days — here's how"

| # | Scene Type | Script Line | KLing Node | Prompt / Input | Duration |
|---|-----------|-------------|------------|----------------|----------|
| 1 | Hook card | "I clawed back $4,217 in 90 days" | `ImageGen(9:16, kling-v2-1)` | A bold financial infographic card, dark background with glowing green "$4,217 in 90 days" text centered, modern sleek aesthetic, app UI style, no people, 9:16 vertical | 0–2s (still frame) |
| 2 | Text overlay scene | "without cutting coffee" | `Image2Video(model=kling-v2-1-master, mode=std, duration=5)` | *Input image:* A cozy coffee shop table with a receipt and phone showing a budgeting app. *Prompt:* gentle steam rising from coffee cup, soft natural light, relaxed morning vibe, slight camera pan right | 2–7s |
| 3 | App reveal | "The app did the math for me" | `Image2Video(model=kling-v2-1-master, mode=std, duration=5)` | *Input image:* A smartphone screen showing an expense tracking dashboard with a green "+$4,217 saved" badge. *Prompt:* phone gently floating upward, UI elements subtly glowing, data points animating in sequence, smooth motion | 7–12s |
| 4 | CTA card | "Link in bio — no pressure" | `Text2Video(model=kling-v2-1-master, mode=std, aspect_ratio=9:16, duration=5)` | A minimalist end card with soft gradient background, elegant sans-serif text "Link in bio" at bottom, small "no pressure" above it, subtle particle background animation, warm inviting tone | 12–15s |

**ComfyUI graph walkthrough (node-by-node):**

```
Workflow: ugc_kling_dollar_timeframe.json

[KLingAIAPIClient] → access_key="", secret_key="", area="global"
  │
  ├── [ImageGeneratorNode] → model=kling-v2-1, prompt="..."
  │   └── image → [PreviewVideo] → download as scene1.png
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   ├── image ← scene1.png (pass the generated image)
  │   └── prompt="..."
  │       └── url → [PreviewVideo] → save as clip1.mp4
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   ├── image ← scene2_image.png (pre-generated product screenshot)
  │   └── prompt="..."
  │       └── url → [PreviewVideo] → save as clip2.mp4
  │
  └── [Text2VideoNode] → model=kling-v2-1-master, mode=std, aspect_ratio=9:16, duration=5
      └── prompt="..."
          └── url → [PreviewVideo] → save as clip3.mp4
```

**Final ffmpeg stitch:**

```bash
# Stitch clips
ffmpeg -i clip1.mp4 -i clip2.mp4 -i clip3.mp4 -filter_complex \
  "[0:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[s0]; \
   [1:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[s1]; \
   [2:v]scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2[s2]; \
   [s0][s1][s2]concat=n=3:v=1:a=0" \
  -c:v libx264 -crf 18 -preset medium ugc_dollar_timeframe_raw.mp4

# Add captions (see Section 5 for caption commands)
```

---

### 4b. Humblebrag Origin Story (Dev Tools)

**Target audience:** Solo devs, indie hackers, startup engineers
**Hook:** "I'm not a designer. But I accidentally shipped a full app in 48 hours."

| # | Scene | Script | Node | Prompt | Dur |
|---|-------|--------|------|--------|-----|
| 1 | Hook card | "I'm not a designer." | `ImageGen(9:16, kling-v2-1)` | A messy desk with code editor visible on a laptop, coffee mug, sticky notes everywhere. Hacker/maker aesthetic, warm lighting, slightly chaotic, 9:16 vertical | 0–2s |
| 2 | Origin reveal | "But I shipped a full app in 48 hours" | `Image2Video(model=kling-v2-1-master, mode=std, duration=5)` | *Input:* The laptop screen close-up showing code with a "Deployed!" green banner. *Prompt:* code slowly scrolling, green checkmark animation subtly glowing, slight camera zoom in, sense of accomplishment | 2–7s |
| 3 | The tool | "Here's exactly how" | `Image2Video(model=kling-v2-1-master, mode=pro, duration=10)` | *Input:* Split screen — left side shows messy terminal/spreadsheets, right side shows clean [[PRODUCT]] dashboard. *Prompt:* left side gently fading to dust particles, right side brightening, smooth crossfade from chaos to order, cinematic | 7–17s |
| 4 | CTA | "Try it — link in bio" | `Text2Video(model=kling-v2-1-master, mode=std, aspect_ratio=9:16, duration=5)` | Dev-themed end card, dark mode, subtle animated grid background, "Try it" in mono font at center, "link in bio" at bottom, binary particles floating upward | 17–20s |

**Key KLing params for this workflow:**

```
Scene 2: cfg_scale=0.7 (lower for more free motion), camera_control_type="simple", camera_control_config="zoom", camera_control_value=1.0
Scene 3: mode="pro", duration=10, cfg_scale=0.5
```

---

### 4c. Side-by-Side Chaos vs. Order (SaaS)

**Target audience:** Task management/app productivity switchers
**Hook:** Left = chaotic spreadsheets, Right = clean [[PRODUCT]] dashboard

| # | Scene | Script | Node | Prompt | Dur |
|---|-------|--------|------|--------|-----|
| 1 | Hook | Side-by-side grid — chaos left, order right | `ImageGen(9:16, kling-v2-1)` | Split screen design, left half: chaotic messy desk with 47 sticky notes, tangled cables, stressed energy, warm orange tones. Right half: clean minimalist desk with one monitor, calm blue tones. Contrasting halves, 9:16 vertical | 0–2s |
| 2 | Problem close-up | "This was me last month" | `Image2Video(model=kling-v2-1-master, mode=std, duration=5)` | *Input:* Close-up of the chaotic left half from above — papers, post-its, coffee rings. *Prompt:* papers slightly rustling, chaotic energy, slight handheld camera feel, tight framing | 2–7s |
| 3 | Solution reveal | "Now my dashboard looks like this" | `Image2Video(model=kling-v2-1-master, mode=std, duration=5)` | *Input:* Clean [[PRODUCT]] dashboard on a laptop screen, organized kanban columns, green checkmarks. *Prompt:* dashboard UI gracefully fading in, data cards sliding into place, smooth professional motion, satisfying order | 7–12s |
| 4 | CTA | "Stop the chaos → link in bio" | `Text2Video(model=kling-v2-1-master, mode=std, aspect_ratio=9:16, duration=5)` | Split screen ending — left side rapidly collapsing/organizing into right side, clean final frame with soft CTA text, "Stop the chaos" in bold, "link in bio" subtle below | 12–15s |

---

## 5. Reusable Storyboard Schema + Automation Script

### Storyboard Template

Create a file like `storyboards/my_ugc_ad.yaml` using this schema:

```yaml
# Storyboard schema for KLing UGC ad generation
# Fill this in, then run: python scripts/storyboard_to_kling.py storyboards/my_ugc_ad.yaml

ad:
  product_name: "[[PRODUCT_NAME]]"
  niche: "fintech | dev-tools | saas | productivity"
  pattern_slug: "dollar-timeframe | anti-hook | income-threshold | confessional | stakes-fear | humblebrag | chaos-order"
  target_audience: "freelancers / solo devs / small biz owners / etc."
  hook_copy: "The headline hook text that appears in scene 1"

scenes:
  - id: hook
    script: "The exact line to display/speak"
    duration_secs: 2
    kling_mode: "imagegen"                 # imagegen | text2video | image2video
    kling_model: "kling-v2-1"              # for imagegen
    image_prompt: "Detailed prompt for the image"
    motion_prompt: ""                      # only for image2video
    aspect_ratio: "9:16"
    camera_control:
      type: "None"                         # None | simple | down_back | forward_up | right_turn_forward | left_turn_forward
      config: "horizontal"                 # horizontal | vertical | pan | tilt | roll | zoom
      value: 0.5
    cfg_scale: 0.5
    text_overlay: ""                       # bold text to overlay on this scene
    reference_image: ""                    # path to pre-existing image (optional)

  - id: problem
    script: "The problem statement"
    duration_secs: 5
    kling_mode: "image2video"
    kling_model: "kling-v2-1-master"
    image_prompt: "Generate this frame first, then animate"
    motion_prompt: "What motion to add — smooth camera pan, gentle zoom..."
    aspect_ratio: "9:16"
    mode: "std"                            # std | pro
    duration: "5"                          # 5 | 10
    cam_type: "None"
    cam_config: "zoom"
    cam_value: 1.0
    cfg_scale: 0.5
    text_overlay: ""

  - id: solution
    script: "The product reveal moment"
    duration_secs: 5
    kling_mode: "image2video"
    kling_model: "kling-v2-1-master"
    image_prompt: "[[PRODUCT]] interface screenshot — clean, modern"
    motion_prompt: "UI gracefully fading in, smooth professional motion"
    aspect_ratio: "9:16"
    mode: "pro"
    duration: "5"
    cam_type: "simple"
    cam_config: "zoom"
    cam_value: 0.5
    cfg_scale: 0.5
    text_overlay: ""

  - id: cta
    script: "Link in bio — soft close"
    duration_secs: 3
    kling_mode: "text2video"
    kling_model: "kling-v2-1-master"
    image_prompt: ""
    motion_prompt: ""
    aspect_ratio: "9:16"
    mode: "std"
    duration: "5"
    cam_type: "None"
    cam_config: ""
    cam_value: 0.0
    cfg_scale: 0.5
    text_overlay: "Link in bio — no pressure"

# Audio / voiceover (optional)
voiceover:
  enabled: false
  mode: "lipsync"                         # lipsync | text2audio
  voice_id: "Sunny"                       # see KLing node for full voice list
  voice_language: "en"
  voice_speed: 1.0

# Output
output:
  filename: "ugc_ad_final.mp4"
  caption_style: "white_black_stroke"     # see ugc-ad-video-pipeline for caption formats
  caption_position: "upper_third"
```

### Automation Script: `scripts/storyboard_to_kling.py`

This script reads the storyboard YAML and drives the KLing API through ComfyUI to generate each scene, then stitches them.

```python
#!/usr/bin/env python3
"""
storyboard_to_kling.py — Drive KLing AI API from a storyboard YAML.

Usage:
    python storyboard_to_kling.py storyboards/my_ugc_ad.yaml

Requires:
    - ComfyUI with ComfyUI-KLingAI-API installed
    - KLing API key in ComfyUI-KLingAI-API/config.ini
    - The storyboard YAML file
"""

import os
import sys
import yaml
import json
import time
import requests
import subprocess
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────────────────────

# ComfyUI server — change if running remotely
COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188")

# Output directory for generated clips
OUTPUT_DIR = Path("./ugc_output").resolve()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── ComfyUI API helpers ─────────────────────────────────────────────────────


def queue_workflow(workflow_json: dict) -> str:
    """Queue a workflow JSON on ComfyUI and return the prompt_id."""
    resp = requests.post(
        f"{COMFYUI_HOST}/prompt",
        json={"prompt": workflow_json},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["prompt_id"]


def poll_completion(prompt_id: str, timeout: int = 300, poll_interval: int = 5) -> dict:
    """Poll until the prompt finishes. Returns the history entry."""
    start = time.time()
    while time.time() - start < timeout:
        resp = requests.get(
            f"{COMFYUI_HOST}/history/{prompt_id}",
            timeout=10,
        )
        if resp.status_code == 200 and prompt_id in resp.json():
            return resp.json()[prompt_id]
        time.sleep(poll_interval)
    raise TimeoutError(f"Prompt {prompt_id} did not finish within {timeout}s")


def get_output_filenames(history: dict) -> list[str]:
    """Extract saved filenames from a completed workflow history entry."""
    outputs = history.get("outputs", {})
    filenames = []
    for node_id, node_output in outputs.items():
        if "videos" in node_output:
            for video in node_output["videos"]:
                filenames.append(video.get("filename", ""))
        if "images" in node_output:
            for img in node_output["images"]:
                filenames.append(img.get("filename", ""))
        # Some KLing nodes return video_url in UI
        if "video_url" in node_output:
            filenames.extend(node_output["video_url"])
    return [f for f in filenames if f]


def download_file(url: str, dest: Path) -> Path:
    """Download a file from ComfyUI output or direct URL."""
    if not url.startswith("http"):
        # ComfyUI internal output path
        url = f"{COMFYUI_HOST}/view?filename={url}&type=output"
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    dest.write_bytes(resp.content)
    return dest


# ─── Workflow builders ───────────────────────────────────────────────────────


def make_kling_client_node(access_key: str = "", secret_key: str = "") -> tuple[str, dict]:
    """Build a KLingAIAPIClient node. Returns (node_id, node_json)."""
    return "client", {
        "class_type": "KLingAIAPIClient",
        "inputs": {
            "access_key": access_key,
            "secret_key": secret_key,
            "poll_interval": 1,
            "area": "global",
        }
    }


def make_imagegen_node(
    client_id: str,
    prompt: str,
    model: str = "kling-v2-1",
    aspect_ratio: str = "9:16",
    resolution: str = "1k",
) -> tuple[str, dict]:
    """Build an ImageGeneratorNode. Returns (node_id, node_json)."""
    return "imagegen", {
        "class_type": "ImageGeneratorNode",
        "inputs": {
            "client": [client_id, 0],
            "model": model,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "resolution": resolution,
            "negative_prompt": "",
            "image_num": 1,
        }
    }


def make_image2video_node(
    client_id: str,
    prompt: str,
    model: str = "kling-v2-1-master",
    mode: str = "std",
    duration: str = "5",
    aspect_ratio: str = "9:16",
    cfg_scale: float = 0.5,
) -> tuple[str, dict]:
    """Build an Image2VideoNode. Returns (node_id, node_json)."""
    return "i2v", {
        "class_type": "Image2VideoNode",
        "inputs": {
            "client": [client_id, 0],
            "model": model,
            "prompt": prompt,
            "mode": mode,
            "duration": duration,
            "cfg_scale": cfg_scale,
        },
        "_meta": {"prompt_aspect_ratio": aspect_ratio}
    }


def make_text2video_node(
    client_id: str,
    prompt: str,
    model: str = "kling-v2-1-master",
    mode: str = "std",
    duration: str = "5",
    aspect_ratio: str = "9:16",
    cfg_scale: float = 0.5,
) -> tuple[str, dict]:
    """Build a Text2VideoNode. Returns (node_id, node_json)."""
    return "t2v", {
        "class_type": "Text2VideoNode",
        "inputs": {
            "client": [client_id, 0],
            "model": model,
            "prompt": prompt,
            "mode": mode,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "cfg_scale": cfg_scale,
        }
    }


def make_lipsync_text_node(
    text: str,
    voice_id: str = "Sunny",
    voice_language: str = "en",
    voice_speed: float = 1.0,
) -> tuple[str, dict]:
    """Build a LipSyncTextInputNode. Returns (node_id, node_json)."""
    return "lipsync_input", {
        "class_type": "LipSyncTextInputNode",
        "inputs": {
            "text": text,
            "voice_id": voice_id,
            "voice_language": voice_language,
            "voice_speed": voice_speed,
        }
    }


def make_preview_video_node(sources: list) -> tuple[str, dict]:
    """Build a PreviewVideo node. First source is the video input."""
    return "preview", {
        "class_type": "PreviewVideo",
        "inputs": {
            "video_url": sources[0] if len(sources) == 1 else sources,
            "filename_prefix": "ugc_kling",
            "save_output": True,
        }
    }


# ─── Scene generator ─────────────────────────────────────────────────────────


def generate_scene(scene: dict, client_id: str, scene_index: int) -> Path:
    """Generate a single scene from the storyboard using KLing nodes.

    Returns the path to the downloaded video file.
    """
    mode = scene.get("kling_mode", "image2video")
    prompt = scene.get("image_prompt", "")
    motion = scene.get("motion_prompt", "")
    aspect = scene.get("aspect_ratio", "9:16")

    workflow = {}

    # Always add client
    cid, client_node = make_kling_client_node()
    workflow[cid] = client_node

    if mode == "imagegen":
        # Generate a still frame (used as a 2s hold)
        nid, node = make_imagegen_node(client_id, prompt,
                                       aspect_ratio=aspect)
        workflow[nid] = node
        # We need a PreviewVideo to output
        vid = "preview"
        workflow[vid] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": [nid, 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }
    elif mode == "text2video":
        nid, node = make_text2video_node(
            client_id, prompt,
            aspect_ratio=aspect,
            duration=scene.get("duration", "5"),
            mode=scene.get("mode", "std"),
            cfg_scale=scene.get("cfg_scale", 0.5),
        )
        workflow[nid] = node
        vid = "preview"
        workflow[vid] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": [nid, 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }
    elif mode == "image2video":
        # Need to generate the starting image first
        ignid, ignode = make_imagegen_node(
            client_id, prompt,
            aspect_ratio=aspect,
        )
        workflow[ignid] = ignode

        # Now animate it
        motion_prompt = motion or f"{prompt}, smooth motion, cinematic"
        nid, node = make_image2video_node(
            client_id, motion_prompt,
            mode=scene.get("mode", "std"),
            duration=scene.get("duration", "5"),
            cfg_scale=scene.get("cfg_scale", 0.5),
        )
        # Connect the imagegen output to the image input
        # KLing I2V node expects image at index 1 (optional)
        node["inputs"]["image"] = [ignid, 0]
        workflow[nid] = node

        vid = "preview"
        workflow[vid] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": [nid, 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }
    else:
        raise ValueError(f"Unknown kling_mode: {mode}")

    # Queue and poll
    print(f"  Queuing scene {scene_index} ({mode})...")
    prompt_id = queue_workflow(workflow)
    print(f"  Prompt ID: {prompt_id}, waiting...")
    history = poll_completion(prompt_id)

    # Get output
    filenames = get_output_filenames(history)
    if not filenames:
        print(f"  WARNING: No output files for scene {scene_index}. History: {json.dumps(history, indent=2)[:500]}")
        return None

    # Download
    for fname in filenames:
        dest = OUTPUT_DIR / f"scene_{scene_index:02d}_{fname}"
        if fname.startswith("http"):
            download_file(fname, dest)
            print(f"  Downloaded: {dest}")
            return dest
        else:
            # ComfyUI local output
            url = f"{COMFYUI_HOST}/view?filename={fname}&type=output"
            result = download_file(url, dest)
            print(f"  Downloaded: {dest}")
            return result

    return None


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    if len(sys.argv) < 2:
        print("Usage: python storyboard_to_kling.py <storyboard.yaml>")
        sys.exit(1)

    yaml_path = Path(sys.argv[1])
    if not yaml_path.exists():
        print(f"Error: {yaml_path} not found")
        sys.exit(1)

    with open(yaml_path) as f:
        storyboard = yaml.safe_load(f)

    ad = storyboard.get("ad", {})
    scenes = storyboard.get("scenes", [])
    output_cfg = storyboard.get("output", {})
    voiceover = storyboard.get("voiceover", {})

    print(f"🎬 Generating UGC Ad: {ad.get('product_name', 'Untitled')}")
    print(f"   Pattern: {ad.get('pattern_slug', 'N/A')}")
    print(f"   Target:  {ad.get('target_audience', 'N/A')}")
    print(f"   Hook:    {ad.get('hook_copy', 'N/A')}")
    print(f"   Scenes:  {len(scenes)}")
    print()

    # Generate each scene
    clip_files = []
    for i, scene in enumerate(scenes):
        print(f"[Scene {i+1}/{len(scenes)}] {scene.get('id', 'unnamed')}")
        result = generate_scene(scene, "client", i + 1)
        if result:
            clip_files.append(result)
        print()

    if len(clip_files) < len(scenes):
        print("⚠️  Some scenes failed to generate. Proceeding with available clips.")

    # Stitch with ffmpeg
    if clip_files:
        final_output = OUTPUT_DIR / output_cfg.get("filename", "ugc_ad_final.mp4")
        _stitch_with_ffmpeg(clip_files, final_output)
        print(f"\n✅ Final ad: {final_output}")
        print(f"   Scene clips in: {OUTPUT_DIR}/")
    else:
        print("❌ No clips generated.")


def _stitch_with_ffmpeg(clip_files: list[Path], output: Path):
    """Concatenate video clips with ffmpeg."""
    # Create concat file
    concat_path = OUTPUT_DIR / "_concat_list.txt"
    with open(concat_path, "w") as f:
        for clip in clip_files:
            f.write(f"file '{clip.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_path),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        str(output),
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    print(f"   🎞 Stitched {len(clip_files)} clips -> {output}")


if __name__ == "__main__":
    main()
```

---

## 6. Assembly + Captions

This step is **identical** to Steps 7–8 of the FOSS pipeline. Do not reinvent.

See `ugc-ad-video-pipeline` skill for:

- **Step 7 (Assemble & Edit):** ffmpeg concat, kdenlive/shotcut GUI editing, losslesscut trimming, moviepy programmatic editing
- **Step 8 (Auto-Captions):** whisper → .srt → ffmpeg burn-in with white text + black stroke

Quick-reference for caption burn-in (from the FOSS skill):

```bash
# Generate captions
whisper ugc_ad_final.mp4 --model small --output_dir ./captions

# Burn into video
ffmpeg -i ugc_ad_final.mp4 -vf \
  "subtitles=./captions/ugc_ad_final.srt:force_style='FontName=Arial-Bold,FontSize=24,PrimaryCol=&H00FFFFFF,OutlineCol=&H00000000,BorderStyle=3,Outline=1,Shadow=1,MarginV=40'" \
  -c:a copy ugc_ad_captioned.mp4
```

---

## 7. Pitfalls & Guardrails

### 7.1 KLing License Terms vs. Flux.1-dev

| Model | License | Can I use for commercial ads? |
|-------|---------|-------------------------------|
| flux.1-dev | Non-commercial (research only) | ❌ No |
| flux.1-schnell | Apache 2.0 | ✅ Yes |
| **KLing API** | **KLing terms of service** | **⛑ Check your use case** — KLing allows commercial use but requires attribution in some plans. See [KLing Terms](https://klingai.com/terms). |
| kling-v2-1 | API service (pay-per-use) | ✅ Generally yes for SaaS/fintech UGC ads, but verify your API plan |

### 7.2 FTC AI-Disclosure Rule (Fintech)

Per `may2026-niche-breakdowns.md` production notes:

> **AI-generated creator avatars must be labeled in fintech verticals**

This means:
- If you use KLing's LipSync on a generated character face and the video looks like a real person talking, **you must disclose it's AI-generated** in the fintech vertical
- Recommended disclosure: overlay "AI-generated" text in the first 3 seconds, or in the caption
- The FTC considers this a "material connection" disclosure — same as influencer sponsorship tags

**Safe approach:** "AI-generated" badge at bottom of frame during the hook section, white text with black stroke, 2px font, lasts 2 seconds. Does not affect ad performance (users don't care, but FTC does).

### 7.3 When to Fall Back to Local Flux/Wan2.1

Use the FOSS pipeline (`ugc-ad-video-pipeline`) when:

- **Cost ceiling hit:** You need 50+ ad variations per day. At ~$1.00/ad, that's $1,500/mo. Local generation on a 4090 is $0/ad (electricity only).
- **Throughput bottleneck:** KLing queue times increase during peak hours. If you need 10+ ads/hour, local GPU wins.
- **Experimental / iterative:** Making 50 prompt tweaks to nail a shot? Do it locally with flux.1-schnell, then render the final with KLing.
- **No API key:** Self-explanatory.

**Decision matrix:**

```
Need 1-10 ads/week?    → KLing pipeline
Need 10+ ads/day?      → FOSS pipeline (owned GPU)
Need quality > speed?  → KLing (pro mode)
Need speed > quality?  → FOSS (schnell + wan2.1)
Compliance requires local-only? → FOSS pipeline
```

### 7.4 Hook Placement: First 3s Rule

From `may2026-niche-breakdowns.md` production notes:

> **First 3 seconds are everything — 90% of success is determined here**

When designing your KLing workflow:

- Scene 1 (the hook card) should be ≤2 seconds with the hook copy visible immediately
- KLing Text2Video has a ~1s startup delay before motion starts — for the hook scene, consider using ImageGen (static frame) instead of Text2Video, so the hook text is immediately readable
- For Image2Video scenes with text overlay, place the text in the **upper third** of the 9:16 frame (thumbnails cut the bottom)

### 7.5 KLing API Gotchas

- **Rate limits:** KLing API has rate limits per key. If generating 5+ clips simultaneously, stagger requests by 2-3 seconds
- **Polling:** The ComfyUI node polls every `poll_interval` seconds. Set to 1-2s for faster feedback
- **Area setting:** Use `area="global"` for non-China accounts. The `"china"` setting routes through different endpoints
- **Video URLs expire:** KLing returns temporary download URLs. Download immediately via PreviewVideo node
- **Model choice for ads:** `kling-v2-1-master` gives best text rendering and motion quality. Use `kling-v1-6` for faster/cheaper iteration
- **Duration limits:** Max 5s for `mode="std"`, max 10s for `mode="pro"`. For longer clips, use `VideoExtendNode` to chain
- **Camera control:** `camera_control_type="simple"` + `camera_control_config="zoom"` with `camera_control_value=0.3–1.0` gives natural product reveals. Higher values = more aggressive motion

### 7.6 Image Quality

- KLing v2-1 renders text in images better than flux.1-dev. For ad cards with dollar amounts or hook copy, prefer ImageGen directly over overlaying text in post
- For "app screenshot" frames, use a real screenshot as a reference image with `image_reference="subject"` and `image_fidelity=0.7` to get the exact UI layout while KLing regenerates the background/environment
- For "creator face" shots, consider KLing's LipSync — it can animate a still portrait into a talking head with natural lip movement, saving you from filming VO sync

### 7.7 Script Dependencies

The `storyboard_to_kling.py` script requires:
- `pip install pyyaml requests`
- ComfyUI running at the configured host
- ComfyUI-KLingAI-API installed

---

## Quick-Start Checklist

1. [ ] Install KLing ComfyUI nodes
2. [ ] Set KLing API keys in `config.ini`
3. [ ] Restart ComfyUI, check KLingAI category exists
4. [ ] Pick a pattern from Section 3
5. [ ] Fill in the storyboard YAML template (Section 5)
6. [ ] Run `python scripts/storyboard_to_kling.py storyboards/my_ad.yaml`
7. [ ] Review scene outputs in `ugc_output/`
8. [ ] Stitch + caption with ffmpeg (Section 6)
9. [ ] Disclose AI generation for fintech (Section 7)
