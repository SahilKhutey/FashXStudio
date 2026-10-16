from fastapi.dependencies.utils import get_parameterless_sub_dependant
from fastapi.routing import APIRoute

from fashx.main import app


def extract_routes(app_or_router, prefix="", inherited_deps=None):
    if inherited_deps is None:
        inherited_deps = []
    all_routes = []
    for r in app_or_router.routes:
        if isinstance(r, APIRoute):
            r.inherited_dependencies = list(inherited_deps)
            all_routes.append((prefix + r.path, r))
        elif "IncludedRouter" in type(r).__name__:
            p = prefix + getattr(r.include_context, "prefix", "")
            orig = getattr(r, "original_router", None)
            inc_deps = list(getattr(r.include_context, "dependencies", []) or [])
            if orig:
                all_routes.extend(extract_routes(orig, p, inherited_deps + inc_deps))
    return all_routes


if __name__ == "__main__":
    routes = extract_routes(app)
    routes.sort(key=lambda item: item[0])

    for path, r in routes:
        names, stack = [], [r.dependant]
        for dep in getattr(r, "inherited_dependencies", []):
            stack.append(get_parameterless_sub_dependant(depends=dep, path=path))
        while stack:
            d = stack.pop()
            if d.call is not None:
                names.append(getattr(d.call, "__name__", "?"))
            stack += d.dependencies
        params = [p.name for p in (r.dependant.path_params + r.dependant.query_params + r.dependant.body_params)]
        flag = "  <-- user in params" if any("user" in p for p in params) else ""
        methods = ",".join(sorted(r.methods - {"HEAD", "OPTIONS"}))
        print(f"{methods:6} {path:55} deps={sorted(set(names))}{flag}")
