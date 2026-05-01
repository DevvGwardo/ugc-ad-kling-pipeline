# Humblebrag Origin Story — Dev Tools

**Hook:** "I'm not a designer. But I accidentally shipped a full app in 48 hours."

## Target Audience
Solo devs, indie hackers, startup engineers

## KLing Node Chain
`ImageGen(9:16)` → `Image2Video(std, 5s, zoom cam)` → `Image2Video(pro, 10s, crossfade)` → `Text2Video(std, 5s)`

## Storyboard

| # | Scene | Script | KLing Mode | Prompt | Dur |
|---|-------|--------|-----------|--------|-----|
| 1 | Hook | "I'm not a designer." | ImageGen | Messy desk with code editor on laptop, coffee mug, sticky notes everywhere. Hacker/maker aesthetic, warm lighting, slightly chaotic, 9:16 vertical | 0–2s |
| 2 | Origin | "But I shipped a full app in 48 hours" | Image2Video | *Frame:* Laptop screen close-up showing code with "Deployed!" green banner. *Motion:* code slowly scrolling, green checkmark glowing, slight zoom in. *(cam: simple/zoom=1.0)* | 2–7s |
| 3 | Tool | "Here's exactly how" | Image2Video | *Frame:* Split screen — messy terminal left, clean [[PRODUCT]] dashboard right. *Motion:* Left fading to dust, right brightening, smooth crossfade. *(mode=pro, duration=10)* | 7–17s |
| 4 | CTA | "Try it — link in bio" | Text2Video | Dark mode end card, animated grid background, "Try it" in mono font, binary particles floating upward | 17–20s |

## ComfyUI Node Walkthrough

```
[KLingAIAPIClient] → area="global"
  │
  ├── [ImageGeneratorNode] → model=kling-v2-1, aspect_ratio=9:16
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   ├── camera_control_type="simple", camera_control_config="zoom", camera_control_value=1.0
  │   └── cfg_scale=0.7
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=pro, duration=10
  │   └── cfg_scale=0.5
  │
  └── [Text2VideoNode] → model=kling-v2-1-master, duration=5, aspect_ratio=9:16
```
