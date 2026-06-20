from .float_preview import (
    V3_AVAILABLE,
    FloatPreviewNode,
    FP_CLASS_MAPPINGS,
    FP_DISPLAY_NAME_MAPPINGS,
)
from .scheduler import (
    SchedulerNode,
    SCHED_CLASS_MAPPINGS,
    SCHED_DISPLAY_NAME_MAPPINGS,
)
from .ksampler_presets import register_ksampler_presets

if V3_AVAILABLE:
    from typing_extensions import override
    from comfy_api.latest import ComfyExtension, io

    class MohseniKitExtension(ComfyExtension):
        @override
        async def on_load(self):
            register_ksampler_presets()

        @override
        async def get_node_list(self) -> list[type[io.ComfyNode]]:
            return [FloatPreviewNode, SchedulerNode]

    async def comfy_entrypoint() -> MohseniKitExtension:
        return MohseniKitExtension()

    __all__ = ["comfy_entrypoint"]
else:
    register_ksampler_presets()

    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

    NODE_CLASS_MAPPINGS.update(FP_CLASS_MAPPINGS)
    NODE_CLASS_MAPPINGS.update(SCHED_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(FP_DISPLAY_NAME_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(SCHED_DISPLAY_NAME_MAPPINGS)

    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
