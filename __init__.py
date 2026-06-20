from .float_preview import V3_AVAILABLE

if V3_AVAILABLE:
    from .float_preview import comfy_entrypoint

    __all__ = ["comfy_entrypoint"]
else:
    from .float_preview import FP_CLASS_MAPPINGS, FP_DISPLAY_NAME_MAPPINGS

    NODE_CLASS_MAPPINGS = {}
    NODE_DISPLAY_NAME_MAPPINGS = {}

    NODE_CLASS_MAPPINGS.update(FP_CLASS_MAPPINGS)
    NODE_DISPLAY_NAME_MAPPINGS.update(FP_DISPLAY_NAME_MAPPINGS)

    __all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
