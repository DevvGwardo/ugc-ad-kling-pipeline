#!/usr/bin/env python3
"""
storyboard_to_kling.py — Drive KLing AI API from a storyboard YAML.

Reads a storyboard YAML, generates each scene via ComfyUI (KLing nodes),
downloads the clips, and stitches them into a final UGC ad video.

Usage:
    python storyboard_to_kling.py storyboards/my_ugc_ad.yaml

Requires:
    - ComfyUI running (default: http://127.0.0.1:8188)
    - ComfyUI-KLingAI-API installed
    - KLing API key in config.ini
    - pip install pyyaml requests
"""

import os
import sys
import json
import time
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    print("Install pyyaml: pip install pyyaml")
    sys.exit(1)

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)


# ─── Configuration ───────────────────────────────────────────────────────────

COMFYUI_HOST = os.environ.get("COMFYUI_HOST", "http://127.0.0.1:8188")
OUTPUT_DIR = Path("./ugc_output").resolve()
SCENE_DIR = OUTPUT_DIR / "scenes"


# ─── ComfyUI API helpers ─────────────────────────────────────────────────────


def queue_prompt(workflow: dict) -> str:
    """Queue a workflow and return the prompt_id. Workaround for 'prompt' key."""
    resp = requests.post(
        f"{COMFYUI_HOST}/prompt",
        json={"prompt": workflow},
        timeout=30,
    )
    if resp.status_code != 200:
        print(f"  ERROR queueing: HTTP {resp.status_code}: {resp.text[:300]}")
        resp.raise_for_status()
    return resp.json()["prompt_id"]


def poll_history(prompt_id: str, timeout: int = 300, interval: int = 3) -> dict:
    """Block until the workflow finishes, return its history entry."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(
                f"{COMFYUI_HOST}/history/{prompt_id}",
                timeout=10,
            )
            if resp.status_code == 200:
                data = resp.json()
                if prompt_id in data:
                    return data[prompt_id]
        except requests.RequestException:
            pass
        time.sleep(interval)
    raise TimeoutError(f"Prompt {prompt_id} did not finish in {timeout}s")


def extract_outputs(history: dict) -> list[dict]:
    """Extract {filename, type, url} from completed workflow history."""
    results = []
    outputs = history.get("outputs", {})
    for node_id, node_out in outputs.items():
        # ComfyUI saved images
        for key in ("images", "videos"):
            for item in node_out.get(key, []):
                results.append({
                    "filename": item["filename"],
                    "subfolder": item.get("subfolder", ""),
                    "type": item.get("type", "output"),
                    "url": None,
                })
        # KLing nodes return URLs in UI output
        ui_urls = node_out.get("video_url", [])
        if isinstance(ui_urls, list):
            for url in ui_urls:
                if isinstance(url, str) and url.startswith("http"):
                    results.append({
                        "filename": url.split("/")[-1],
                        "subfolder": "",
                        "type": "url",
                        "url": url,
                    })
    return results


def download_comfyui_output(item: dict, dest_dir: Path) -> Path:
    """Download a single output item and return its local path."""
    dest_dir.mkdir(parents=True, exist_ok=True)

    if item["url"]:
        resp = requests.get(item["url"], timeout=120)
        resp.raise_for_status()
        fpath = dest_dir / item["filename"]
        fpath.write_bytes(resp.content)
        return fpath
    else:
        # ComfyUI local output
        view_url = (
            f"{COMFYUI_HOST}/view"
            f"?filename={item['filename']}"
            f"&subfolder={item['subfolder']}"
            f"&type={item['type']}"
        )
        resp = requests.get(view_url, timeout=120)
        resp.raise_for_status()
        fpath = dest_dir / item["filename"]
        fpath.write_bytes(resp.content)
        return fpath


# ─── Workflow builders ───────────────────────────────────────────────────────


def build_workflow(scene: dict, scene_index: int) -> dict:
    """Build a ComfyUI workflow dict for one scene.

    Returns a flat dict of {node_id: node_spec}. KLing nodes are connected by
    passing client output from the first node.
    """
    mode = scene["kling_mode"]
    aspect = scene.get("aspect_ratio", "9:16")
    prompt = scene.get("image_prompt", "")
    motion = scene.get("motion_prompt", "")
    duration = scene.get("duration", "5")
    kling_mode = scene.get("mode", "std")
    cfg = scene.get("cfg_scale", 0.5)
    cam_type = scene.get("cam_type", "None")
    cam_config = scene.get("cam_config", "")
    cam_value = scene.get("cam_value", 0.5)
    kling_model = scene.get("kling_model", "kling-v2-1")

    workflow = {}

    # KLing client (reads keys from config.ini)
    workflow["client"] = {
        "class_type": "KLingAIAPIClient",
        "inputs": {
            "access_key": "",
            "secret_key": "",
            "poll_interval": 1,
            "area": "global",
        }
    }

    if mode == "imagegen":
        # Generate still frame → preview/download
        workflow["gen"] = {
            "class_type": "ImageGeneratorNode",
            "inputs": {
                "client": ["client", 0],
                "model": kling_model,
                "prompt": prompt,
                "negative_prompt": "",
                "image_num": 1,
                "aspect_ratio": aspect,
                "resolution": "1k",
            }
        }
        # Save to output
        workflow["save"] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": ["gen", 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }

    elif mode == "text2video":
        workflow["gen"] = {
            "class_type": "Text2VideoNode",
            "inputs": {
                "client": ["client", 0],
                "model": kling_model,
                "prompt": prompt,
                "negative_prompt": "",
                "cfg_scale": cfg,
                "mode": kling_mode,
                "aspect_ratio": aspect,
                "duration": duration,
            }
        }
        # Add camera control if configured
        if cam_type != "None":
            workflow["gen"]["inputs"]["camera_control_type"] = cam_type
            if cam_type == "simple":
                workflow["gen"]["inputs"]["camera_control_config"] = cam_config
                workflow["gen"]["inputs"]["camera_control_value"] = cam_value

        workflow["save"] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": ["gen", 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }

    elif mode == "image2video":
        # Step 1: Generate the starting image
        workflow["img"] = {
            "class_type": "ImageGeneratorNode",
            "inputs": {
                "client": ["client", 0],
                "model": kling_model,
                "prompt": prompt,
                "negative_prompt": "",
                "image_num": 1,
                "aspect_ratio": aspect,
                "resolution": "1k",
            }
        }
        # Step 2: Animate it
        motion_prompt = motion or f"{prompt}, smooth motion, cinematic"
        workflow["vid"] = {
            "class_type": "Image2VideoNode",
            "inputs": {
                "client": ["client", 0],
                "model": kling_model,
                "image": ["img", 0],
                "prompt": motion_prompt,
                "mode": kling_mode,
                "duration": duration,
                "cfg_scale": cfg,
            }
        }
        if cam_type != "None":
            workflow["vid"]["inputs"]["camera_control_type"] = cam_type
            if cam_type == "simple":
                workflow["vid"]["inputs"]["camera_control_config"] = cam_config
                workflow["vid"]["inputs"]["camera_control_value"] = cam_value

        workflow["save"] = {
            "class_type": "PreviewVideo",
            "inputs": {
                "video_url": ["vid", 0],
                "filename_prefix": f"scene_{scene_index:02d}",
                "save_output": True,
            }
        }

    else:
        raise ValueError(f"Unknown kling_mode: {mode}")

    return workflow


# ─── Scene generation ────────────────────────────────────────────────────────


def generate_scene(scene: dict, scene_index: int) -> Path | None:
    """Generate one scene from the storyboard via ComfyUI + KLing.

    Returns the path to the downloaded video file, or None on failure.
    """
    scene_id = scene.get("id", f"scene_{scene_index}")
    mode = scene["kling_mode"]

    print(f"  Building workflow ({mode})...")
    workflow = build_workflow(scene, scene_index)

    print(f"  Queueing on ComfyUI ({COMFYUI_HOST})...")
    prompt_id = queue_prompt(workflow)
    print(f"  Prompt ID: {prompt_id}")

    print(f"  Waiting for completion...")
    history = poll_history(prompt_id)

    outputs = extract_outputs(history)
    if not outputs:
        print(f"  WARNING: No output files. Workflow may have failed.")
        # Print errors from history
        node_errors = history.get("status", {}).get("messages", [])
        for msg in node_errors:
            print(f"    Node msg: {msg}")
        return None

    # Download all outputs, return the first video
    for item in outputs:
        dest = download_comfyui_output(item, SCENE_DIR)
        print(f"  Saved: {dest}")
        # Return the first (main output) — but prefer .mp4
        if item["filename"].endswith((".mp4", ".webm", ".gif")):
            return dest

    # If no video found, return first image
    for item in outputs:
        dest = SCENE_DIR / item["filename"]
        if dest.exists():
            return dest

    return None


# ─── FFmpeg stitching ────────────────────────────────────────────────────────


def stitch_clips(clip_paths: list[Path], output: Path):
    """Concatenate video clips with ffmpeg."""
    if not clip_paths:
        print("  No clips to stitch.")
        return

    concat_file = OUTPUT_DIR / "_concat.txt"
    with open(concat_file, "w") as f:
        for p in clip_paths:
            f.write(f"file '{p.absolute()}'\n")

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_file),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "medium",
        "-pix_fmt", "yuv420p",
        str(output),
    ]
    print(f"  Stitching: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if result.returncode != 0:
        print(f"  ffmpeg stderr: {result.stderr[:500]}")
        raise RuntimeError(f"ffmpeg failed with code {result.returncode}")

    print(f"  ✅ Stitched {len(clip_paths)} clips -> {output}")


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
    output = storyboard.get("output", {})
    voiceover = storyboard.get("voiceover", {})

    if not scenes:
        print("Error: No scenes defined in storyboard")
        sys.exit(1)

    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    SCENE_DIR.mkdir(parents=True, exist_ok=True)

    print(f"╔══════════════════════════════════════════╗")
    print(f"║  UGC Ad — KLing Pipeline                  ║")
    print(f"╠══════════════════════════════════════════╣")
    print(f"║  Product: {ad.get('product_name', 'Untitled'):32s}║")
    print(f"║  Pattern: {ad.get('pattern_slug', 'N/A'):32s}║")
    print(f"║  Hook:    {ad.get('hook_copy', 'N/A'):32s}║")
    print(f"║  Scenes:  {len(scenes):32d}║")
    print(f"╚══════════════════════════════════════════╝")
    print()

    # Generate each scene
    clip_files = []
    for i, scene in enumerate(scenes):
        scene_id = scene.get("id", f"scene_{i+1}")
        print(f"─── [{i+1}/{len(scenes)}] {scene_id} ───")
        result = generate_scene(scene, i + 1)
        if result:
            clip_files.append(result)
            print()
        else:
            print(f"  ⚠️  Scene {scene_id} failed\n")

    # Stitch
    final_name = output.get("filename", "ugc_ad_final.mp4")
    final_path = OUTPUT_DIR / final_name

    if len(clip_files) == len(scenes):
        print(f"🎯 All {len(scenes)} scenes generated successfully.")
        stitch_clips(clip_files, final_path)
        print(f"\n✅ Final ad: {final_path}")
    elif clip_files:
        print(f"⚠️  Generated {len(clip_files)}/{len(scenes)} scenes.")
        stitch_clips(clip_files, final_path)
        print(f"\n⚠️  Partial ad (missing scenes): {final_path}")
    else:
        print("❌ No clips generated. Check ComfyUI + KLing config.")

    # Print summary
    print()
    print(f"📁 Scene clips:  {SCENE_DIR}/")
    print(f"📁 Final video:  {final_path}")
    print(f"📄 Storyboard:   {yaml_path.resolve()}")
    print()
    print(f"Next: caption with whisper + ffmpeg (see ugc-ad-video-pipeline Step 8)")


if __name__ == "__main__":
    main()
