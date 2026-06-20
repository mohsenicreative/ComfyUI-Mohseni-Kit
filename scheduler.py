import torch  # type: ignore

try:
    from comfy_api.latest import io  # type: ignore

    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False


def _karras_polynomial(n, sigma_min, sigma_max, rho=7.0, **kwargs):
    ramp = torch.linspace(0, 1, n)
    min_inv_rho = sigma_min ** (1.0 / rho)
    max_inv_rho = sigma_max ** (1.0 / rho)
    sigmas = (max_inv_rho + ramp * (min_inv_rho - max_inv_rho)) ** rho
    return torch.cat([sigmas, sigmas.new_zeros([1])])


SCHEDULERS = {
    "karras_polynomial": _karras_polynomial,
}

SCHEDULER_NAMES = list(SCHEDULERS.keys())


def build_sigmas(model, scheduler, steps, denoise, rho, sigma_max=0.0, sigma_min=0.0):
    if denoise <= 0.0:
        return torch.FloatTensor([])

    total_steps = steps
    if denoise < 1.0:
        total_steps = int(steps / denoise)

    model_sampling = model.get_model_object("model_sampling")
    s_min = sigma_min if sigma_min > 0.0 else float(model_sampling.sigma_min)
    s_max = sigma_max if sigma_max > 0.0 else float(model_sampling.sigma_max)

    func = SCHEDULERS[scheduler]
    sigmas = func(total_steps, s_min, s_max, rho=rho).cpu()

    return sigmas[-(steps + 1):]


# --- Custom Node Definition ---
if V3_AVAILABLE:

    class SchedulerNode(io.ComfyNode):
        @classmethod
        def define_schema(cls):
            return io.Schema(
                node_id="MohseniScheduler",
                display_name="📈 Mohseni Scheduler",
                category="⚡ Mohseni Kit/Sampling",
                inputs=[
                    io.Model.Input("model"),
                    io.Combo.Input("scheduler", options=SCHEDULER_NAMES),
                    io.Int.Input("steps", default=20, min=1, max=10000),
                    io.Float.Input(
                        "denoise", default=1.0, min=0.0, max=1.0, step=0.01
                    ),
                    io.Float.Input("rho", default=7.0, min=1.0, max=30.0, step=0.1),
                    io.Float.Input(
                        "sigma_max",
                        default=0.0,
                        min=0.0,
                        max=1000.0,
                        step=0.01,
                        optional=True,
                    ),
                    io.Float.Input(
                        "sigma_min",
                        default=0.0,
                        min=0.0,
                        max=1000.0,
                        step=0.01,
                        optional=True,
                    ),
                ],
                outputs=[io.Sigmas.Output("SIGMAS")],
            )

        @classmethod
        def execute(
            cls,
            model,
            scheduler,
            steps,
            denoise,
            rho,
            sigma_max=0.0,
            sigma_min=0.0,
        ):
            sigmas = build_sigmas(
                model, scheduler, steps, denoise, rho, sigma_max, sigma_min
            )
            return io.NodeOutput(sigmas)

else:

    class SchedulerNode:
        @classmethod
        def INPUT_TYPES(cls):
            return {
                "required": {
                    "model": ("MODEL",),
                    "scheduler": (SCHEDULER_NAMES,),
                    "steps": ("INT", {"default": 20, "min": 1, "max": 10000}),
                    "denoise": (
                        "FLOAT",
                        {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.01},
                    ),
                    "rho": (
                        "FLOAT",
                        {"default": 7.0, "min": 1.0, "max": 30.0, "step": 0.1},
                    ),
                },
                "optional": {
                    "sigma_max": (
                        "FLOAT",
                        {"default": 0.0, "min": 0.0, "max": 1000.0, "step": 0.01},
                    ),
                    "sigma_min": (
                        "FLOAT",
                        {"default": 0.0, "min": 0.0, "max": 1000.0, "step": 0.01},
                    ),
                },
            }

        RETURN_TYPES = ("SIGMAS",)
        FUNCTION = "execute"
        CATEGORY = "⚡ Mohseni Kit/Sampling"

        def execute(
            self,
            model,
            scheduler,
            steps,
            denoise,
            rho,
            sigma_max=0.0,
            sigma_min=0.0,
        ):
            sigmas = build_sigmas(
                model, scheduler, steps, denoise, rho, sigma_max, sigma_min
            )
            return (sigmas,)


# --- Register Custom Node ---
if V3_AVAILABLE:
    SCHED_CLASS_MAPPINGS = {}
    SCHED_DISPLAY_NAME_MAPPINGS = {}
else:
    SCHED_CLASS_MAPPINGS = {"MohseniScheduler": SchedulerNode}
    SCHED_DISPLAY_NAME_MAPPINGS = {"MohseniScheduler": "📈 Mohseni Scheduler"}
