def nav_active(request):
    """Tell the nav bar which link to highlight.

    Watching and Completed are the collection page with a status filter, so the
    status query parameter decides which of the three collection links is active.
    """
    match = getattr(request, "resolver_match", None)
    name = match.view_name if match else ""
    if name == "home":
        active = "home"
    elif name == "shows:discover":
        active = "discover"
    elif name == "shows:collection":
        status = request.GET.get("status", "")
        active = {"watching": "watching", "completed": "completed"}.get(status, "collection")
    else:
        active = ""
    return {"nav_active": active}
