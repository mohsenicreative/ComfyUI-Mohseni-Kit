import torch  # type: ignore

from .scheduler import _karras_polynomial, apply_shift

KSAMPLER_PRESETS = {
    "mohseni_compose": {"rho": 0.5, "shift": 3.0},
    "mohseni_detail": {"rho": 7.0, "shift": 1.0},
}

_patched = False


def _preset_sigmas(model_sampling, scheduler_name, steps):
    cfg = KSAMPLER_PRESETS[scheduler_name]
    s_min = float(model_sampling.sigma_min)
    s_max = float(model_sampling.sigma_max)
    body = _karras_polynomial(steps, s_min, s_max, rho=cfg["rho"])
    body = apply_shift(body, s_min, s_max, cfg.get("shift", 1.0))
    return torch.cat([body, body.new_zeros([1])])


def register_ksampler_presets():
    global _patched
    if _patched:
        return

    try:
        import comfy.samplers as samplers
    except Exception:
        return

    try:
        original = samplers.calculate_sigmas

        def calculate_sigmas(model_sampling, scheduler_name, steps):
            if scheduler_name in KSAMPLER_PRESETS:
                return _preset_sigmas(model_sampling, scheduler_name, steps)
            return original(model_sampling, scheduler_name, steps)

        samplers.calculate_sigmas = calculate_sigmas

        targets = [getattr(samplers, "SCHEDULER_NAMES", None)]
        ksampler = getattr(samplers, "KSampler", None)
        if ksampler is not None:
            targets.append(getattr(ksampler, "SCHEDULERS", None))

        for names in targets:
            if isinstance(names, list):
                for name in KSAMPLER_PRESETS:
                    if name not in names:
                        names.append(name)

        _patched = True
        print(
            f"[Mohseni Kit] Registered KSampler scheduler presets: "
            f"{', '.join(KSAMPLER_PRESETS)}"
        )
    except Exception as e:
        print(f"[Mohseni Kit] KSampler presets unavailable, skipping: {e}")
