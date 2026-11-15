from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from . import tvmaze


def home(request):
    """Public home page: a welcome hero for visitors, the personal home for users."""
    return render(request, "home.html")


@login_required
def discover(request):
    """Search TVmaze by title. A blank search shows guidance and never calls TVmaze."""
    raw_query = request.GET.get("q")
    query = (raw_query or "").strip()
    context = {"query": query, "results": [], "error": "", "blank_query": raw_query is not None and not query}
    if query:
        try:
            context["results"] = tvmaze.search_shows(query)
        except tvmaze.TVmazeError as error:
            context["error"] = str(error)
    return render(request, "shows/discover.html", context)


@login_required
def collection(request):
    """The user's collection (full filters, sorting and pagination come in Phase 7)."""
    return render(request, "shows/collection.html")
