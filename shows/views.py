from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import services, tvmaze
from .models import CollectionEntry, Show


def home(request):
    """Public home page: a welcome hero for visitors, the personal home for users."""
    return render(request, "home.html")


def saved_entries_by_tvmaze_id(user, tvmaze_ids):
    """Map TVmaze IDs to the user's entries, for marking shows already saved."""
    entries = CollectionEntry.objects.filter(user=user, show__tvmaze_id__in=tvmaze_ids).select_related("show")
    return {entry.show.tvmaze_id: entry for entry in entries}


@login_required
def discover(request):
    """Search TVmaze by title. A blank search shows guidance and never calls TVmaze."""
    raw_query = request.GET.get("q")
    query = (raw_query or "").strip()
    context = {"query": query, "results": [], "error": "", "blank_query": raw_query is not None and not query}
    if query:
        try:
            shows = tvmaze.search_shows(query)
        except tvmaze.TVmazeError as error:
            context["error"] = str(error)
        else:
            saved = saved_entries_by_tvmaze_id(request.user, [show["tvmaze_id"] for show in shows])
            context["results"] = [{"show": show, "entry": saved.get(show["tvmaze_id"])} for show in shows]
    return render(request, "shows/discover.html", context)


def _safe_next(request, fallback):
    """The POSTed 'next' URL if it points back into this site, otherwise the fallback."""
    next_url = request.POST.get("next", "")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()},
                                                    require_https=request.is_secure()):
        return next_url
    return fallback


@login_required
@require_POST
def add_to_collection(request):
    """Save a TVmaze show to the user's collection. Only `tvmaze_id` is read from the form."""
    fallback = reverse("shows:discover")
    try:
        tvmaze_id = int(request.POST.get("tvmaze_id", ""))
        if tvmaze_id < 1:
            raise ValueError
    except ValueError:
        messages.error(request, "That show couldn't be saved: its TVmaze ID is missing or invalid.")
        return redirect(_safe_next(request, fallback))

    try:
        entry = services.save_show_to_collection(request.user, tvmaze_id)
    except services.AlreadySaved as already:
        messages.info(request, str(already))
        return redirect(f"{reverse('shows:detail', args=[tvmaze_id])}?tab=tracking")
    except tvmaze.ShowNotFound:
        messages.error(request, "TVmaze has no show with that ID, so nothing was saved.")
        return redirect(_safe_next(request, fallback))
    except tvmaze.TVmazeError as error:
        messages.error(request, f"The show wasn't saved. {error}")
        return redirect(_safe_next(request, fallback))

    messages.success(request, f"Saved {entry.show.name} to your collection as Plan to Watch.")
    return redirect(f"{reverse('shows:detail', args=[tvmaze_id])}?tab=tracking")


@login_required
def show_detail(request, tvmaze_id):
    """A show's details page. (Phase 4b: saved shows from local data; Phase 5 adds the rest.)"""
    show = Show.objects.filter(tvmaze_id=tvmaze_id).first()
    if show is None:
        raise Http404("Show not found")
    entry = CollectionEntry.objects.filter(user=request.user, show=show).first()
    return render(request, "shows/show_detail.html", {"show": show, "entry": entry})


@login_required
def collection(request):
    """The user's collection (full filters, sorting and pagination come in Phase 7)."""
    return render(request, "shows/collection.html")
