# ⚡ ComfyUI Mohseni Kit

A collection of professional custom nodes for **ComfyUI**, focused on precise sampling control and a smoother preview workflow.

## Nodes

| Node | Category | Purpose |
|---|---|---|
| 📈 Mohseni Scheduler | `⚡ Mohseni Kit / Sampling` | Karras polynomial sigma scheduler tuned for two-stage sampling |
| 🖼️ Float Preview | `⚡ Mohseni Kit / Image` | Floating, always-on-top image preview window |

---

## 📈 Mohseni Scheduler

A custom **sigma scheduler** that outputs a `SIGMAS` curve using **Karras polynomial spacing** with a tunable shape. It is built for **two-stage sampling** — a composition/color pass followed by a detailing pass — letting the same formula bias steps toward either end of the noise range.

> **Output:** `SIGMAS` — connect it to `SamplerCustom` / `SamplerCustomAdvanced` (with a `KSamplerSelect`), not the standard `KSampler`.

### Parameters

| Parameter | Description | Typical |
|---|---|---|
| `scheduler` | Spacing formula. Currently `karras_polynomial` (extensible). | — |
| `steps` | Sampling steps for this stage. | 15–30 |
| `denoise` | `1.0` starts from pure noise; lower values start partway down the curve. | detail: 0.35–0.5 |
| `rho` | Curve shape. **< 1 = composition** (steps held high), `1` = linear, **> 1 = detail** (steps packed low). | compose 0.4–0.8 / detail 7–15 |
| `shift` | Adds high-noise step density on top of `rho` (resolution-aware). `1.0` = off. | compose 2–4 / detail 1.0 |
| `sigma_max` | Top of the noise range. `0` = auto from model. | 0 |
| `sigma_min` | Bottom of the noise range. `0` = auto from model. | 0 |

### Why polynomial spacing

Composition and color form at **high noise**; fine detail forms at **low noise**. `rho` decides where the steps are spent:

- **Composition** — `rho` below `1` (e.g. `0.6`) holds steps in the high-noise band; add `shift` `2–4` for more resolution there.
- **Detail** — `rho` of `7–15` concentrates steps in the low-noise band, which adds detail far more cleanly than exponential spacing.

### Two-stage detailing recipe

| | Pass 1 — composition | Pass 2 — detail |
|---|---|---|
| `steps` | 24 | 18 |
| `denoise` | 1.0 | 0.45 |
| `rho` | 0.6 | 10.0 |
| `shift` | 3.0 | 1.0 |
| `sigma_max` / `sigma_min` | 0 / 0 | 0 / 0 |

Per pass, wire `Mohseni Scheduler → SamplerCustom (sigmas)` and `KSamplerSelect → SamplerCustom (sampler)`. Pass 1 runs on an empty latent (`add_noise` on); feed its `LATENT` into Pass 2 (`add_noise` on), then `VAE Decode`.

> **Tip:** for a detail pass without splitting, use `denoise 1.0` with `sigma_max ≈ 2.5` and `sigma_min 0` to keep the whole schedule in the low-noise band.

### KSampler dropdown presets

Two fixed presets are added to the standard `KSampler` scheduler dropdown automatically:

- `mohseni_compose` — composition-weighted (`rho 0.5`, `shift 3`)
- `mohseni_detail` — detail-weighted (`rho 7`)

They are fixed-value (no live controls) — use the node to tune, the presets for speed. On an incompatible ComfyUI build they are skipped without affecting the rest of the kit.

---

## 🖼️ Float Preview

A floating, resizable, always-on-top image preview window that lives **outside** the ComfyUI interface — ideal for multi-monitor setups.

### Features

- Live preview that updates as the workflow runs
- Batch support — scroll through multiple images
- Save to disk or copy to clipboard
- Always-on-top toggle and free window dragging
- Persistent window size, position, and state across sessions
- Keyboard shortcuts and a right-click menu

### Controls

| Action | Description |
|---|---|
| ← / ↑ | Previous image |
| → / ↓ | Next image |
| Ctrl + T | Toggle always on top |
| Ctrl + C | Copy current image to clipboard |
| Ctrl + S | Save current image (PNG / JPEG) |
| Esc | Close the window |
| Right click | Open the context menu |

Connect any `IMAGE` output to the node and run the workflow; the window appears and tracks new outputs.

---

## 📥 Installation

### ComfyUI Manager

Search for **ComfyUI Mohseni Kit** in ComfyUI Manager, click **Install**, then restart ComfyUI.

### Manual

```bash
cd ComfyUI/custom_nodes
git clone https://github.com/mohsenicreative/ComfyUI-Mohseni-Kit
```

Restart ComfyUI. Dependencies are installed automatically; if needed, install them manually:

```bash
pip install PyQt6 ftfy psutil
```

---

## 📜 License

Licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**.

- Credit the original author: **Mohammadreza Mohseni**.
- Modifications must be shared under the same license.
- Commercial use is allowed with attribution.

Full text: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)

---

## 📬 Contact

[Mohammadreza Mohseni](https://bio.mohseni.info)
