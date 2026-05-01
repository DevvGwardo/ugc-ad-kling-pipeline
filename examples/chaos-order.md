# Side-by-Side Chaos vs. Order — SaaS

**Hook:** Left = chaotic spreadsheets, Right = clean [[PRODUCT]] dashboard

## Target Audience
Task management/app productivity switchers

## KLing Node Chain
`ImageGen(9:16)` → `Image2Video(std, 5s)` → `Image2Video(std, 5s)` → `Text2Video(std, 5s)`

## Storyboard

| # | Scene | Script | KLing Mode | Prompt | Dur |
|---|-------|--------|-----------|--------|-----|
| 1 | Hook | Side-by-side — chaos vs order | ImageGen | Split screen: left = chaotic desk with 47 sticky notes, tangled cables, warm orange tones. Right = clean desk with one monitor, calm blue tones. Contrasting halves, 9:16 | 0–2s |
| 2 | Problem | "This was me last month" | Image2Video | *Frame:* Close-up of chaotic left half — papers, post-its, coffee rings. *Motion:* papers slightly rustling, chaotic energy, handheld camera feel, tight framing | 2–7s |
| 3 | Solution | "Now my dashboard looks like this" | Image2Video | *Frame:* Clean [[PRODUCT]] dashboard on laptop, organized kanban, green checkmarks. *Motion:* UI fading in, data cards sliding into place, smooth satisfying order | 7–12s |
| 4 | CTA | "Stop the chaos → link in bio" | Text2Video | Split screen ending — left side collapsing/organizing into right, clean final frame, "Stop the chaos" bold, "link in bio" subtle | 12–15s |

## ComfyUI Node Walkthrough

```
[KLingAIAPIClient] → area="global"
  │
  ├── [ImageGeneratorNode] → model=kling-v2-1, aspect_ratio=9:16
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   └── cfg_scale=0.5
  │
  ├── [Image2VideoNode] → model=kling-v2-1-master, mode=std, duration=5
  │   └── cfg_scale=0.5
  │
  └── [Text2VideoNode] → model=kling-v2-1-master, duration=5, aspect_ratio=9:16
```
