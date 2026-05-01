# Dollar + Timeframe Concrete Claim — Fintech

**Hook:** "I clawed back $4,217 in 90 days — here's how"

## Target Audience
Freelancers, side-hustlers, people who overspend

## KLing Node Chain
`ImageGen(9:16, kling-v2-1)` → `Image2Video(kling-v2-1-master, std, 5s)` → `Image2Video(kling-v2-1-master, std, 5s)` → `Text2Video(kling-v2-1-master, std, 5s)`

## Storyboard

| # | Scene | Script | KLing Mode | Prompt | Dur |
|---|-------|--------|-----------|--------|-----|
| 1 | Hook card | "I clawed back $4,217 in 90 days" | ImageGen | A bold financial infographic card, dark background with glowing green "$4,217 in 90 days" text centered, modern sleek aesthetic, app UI style, 9:16 vertical | 0–2s |
| 2 | Scene | "without cutting coffee" | Image2Video | *Frame:* Cozy coffee shop table with receipt and phone showing budgeting app. *Motion:* gentle steam rising, soft natural light, relaxed vibe, slight camera pan right | 2–7s |
| 3 | App reveal | "The app did the math for me" | Image2Video | *Frame:* Smartphone screen with expense dashboard, green "+$4,217 saved" badge. *Motion:* phone floating upward, UI subtly glowing, data animating in sequence | 7–12s |
| 4 | CTA | "Link in bio — no pressure" | Text2Video | Minimalist end card, soft gradient, elegant "Link in bio" at bottom, subtle particle background | 12–15s |

## ComfyUI Node Walkthrough

```
[KLingAIAPIClient] → area="global"
  │
  ├── [ImageGeneratorNode] → model=kling-v2-1, aspect_ratio=9:16
  │   └── ──→ [PreviewVideo] → scene_01.png
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   ├── image ← scene_01.png
  │   └── prompt="gentle steam rising from coffee cup..."
  │       └── ──→ [PreviewVideo] → clip_01.mp4
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   ├── image ← (product screenshot)
  │   └── prompt="phone floating upward, UI glowing..."
  │       └── ──→ [PreviewVideo] → clip_02.mp4
  │
  └── [Text2VideoNode] → model=kling-v2-1-master, duration=5, aspect_ratio=9:16
      └── prompt="minimalist end card..."
          └── ──→ [PreviewVideo] → clip_03.mp4
```

## ffmpeg Stitch

```bash
ffmpeg -i clip_01.mp4 -i clip_02.mp4 -i clip_03.mp4 \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0" \
  -c:v libx264 -crf 18 -preset medium ugc_dollar_timeframe.mp4
```
