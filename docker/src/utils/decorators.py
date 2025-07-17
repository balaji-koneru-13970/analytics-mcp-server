from ZA_Config import ZA_Config
from mcp_instance import mcp
from functools import wraps

def with_dynamic_doc(doc_template: str):
    """
    Decorator to dynamically set the docstring of a function based on a template.
    The template can include placeholders for the function name and other parameters.
    """
    def decorator(func):
        func.__doc__ = doc_template.format(
            PRODUCT_NAME=ZA_Config.PRODUCT_NAME,
            PRODUCT_VERSION=ZA_Config.PRODUCT_VERSION,
            function_name=func.__name__
        )
        return func
    return decorator