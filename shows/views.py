from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import services, tvmaze
from .forms import TrackingForm
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


TABS = {"tracking": "MY TRACKING", "suggested": "SUGGESTED", "extras": "EXTRAS"}


@login_required
def show_detail(request, tvmaze_id):
    """A show's details page.

    Saved shows (a local Show row) render from the database. Any other show is fetched
    live from TVmaze and displayed, but never written to the database. Extras (seasons
    and cast) are fetched from TVmaze only when that tab is opened.
    """
    show = Show.objects.filter(tvmaze_id=tvmaze_id).first()
    entry = CollectionEntry.objects.filter(user=request.user, show=show).first() if show else None

    tabs = ["tracking", "suggested", "extras"] if entry else ["suggested", "extras"]
    tab = request.GET.get("tab")
    if tab not in tabs:
        tab = tabs[0]

    extras, extras_error = None, ""
    if show is None:
        try:
            if tab == "extras":
                show, extras = tvmaze.get_show_and_extras(tvmaze_id)  # one request for both
            else:
                show = tvmaze.get_show(tvmaze_id)
        except tvmaze.ShowNotFound:
            raise Http404("TVmaze has no show with that ID.")
        except tvmaze.TVmazeError as error:
            return render(request, "shows/show_unavailable.html", {"error": str(error), "tvmaze_id": tvmaze_id}, status=503)
    elif tab == "extras":
        try:
            extras = tvmaze.get_extras(tvmaze_id)
        except tvmaze.TVmazeError as error:
            extras_error = str(error)

    return render(request, "shows/show_detail.html",
                  _detail_context(request, show, entry, tab, tabs, extras=extras, extras_error=extras_error))


def _detail_context(request, show, entry, tab, tabs, extras=None, extras_error="", form=None):
    context = {
        "show": show,
        "entry": entry,
        "tab": tab,
        "tabs": [(key, TABS[key]) for key in tabs],
        "extras": extras,
        "extras_error": extras_error,
    }
    if tab == "tracking":
        context["form"] = form or TrackingForm(instance=entry)
    if tab == "suggested":
        suggestions = services.suggested_shows(_value(show, "tvmaze_id"), _value(show, "genres"))
        saved = saved_entries_by_tvmaze_id(request.user, [s.tvmaze_id for s in suggestions])
        context["suggestions"] = [{"show": s, "entry": saved.get(s.tvmaze_id)} for s in suggestions]
    return context


def _value(show, name):
    return show.get(name) if isinstance(show, dict) else getattr(show, name)


def _tracking_url(entry):
    return f"{reverse('shows:detail', args=[entry.show.tvmaze_id])}?tab=tracking"


@login_required
def update_entry(request, entry_id):
    """Save the My Tracking form. Only the owner's entries can be found (others get 404)."""
    entry = get_object_or_404(CollectionEntry.objects.select_related("show"), pk=entry_id, user=request.user)
    if request.method != "POST":
        return redirect(_tracking_url(entry))
    form = TrackingForm(request.POST, instance=entry)
    if form.is_valid():
        form.save()
        messages.success(request, f"Saved your tracking for {entry.show.name}.")
        return redirect(_tracking_url(entry))
    # Re-render the page with the errors and the user's input. The page header uses a fresh
    # copy of the entry, because an invalid form has already changed `entry` in memory.
    saved_entry = CollectionEntry.objects.select_related("show").get(pk=entry.pk)
    context = _detail_context(request, saved_entry.show, saved_entry, "tracking",
                              ["tracking", "suggested", "extras"], form=form)
    return render(request, "shows/show_detail.html", context, status=400)


@login_required
def delete_entry(request, entry_id):
    """GET shows a confirmation page; POST removes the entry (the shared Show row stays)."""
    entry = get_object_or_404(CollectionEntry.objects.select_related("show"), pk=entry_id, user=request.user)
    if request.method == "POST":
        name = entry.show.name
        entry.delete()
        messages.success(request, f"Removed {name} from your collection.")
        return redirect("shows:collection")
    return render(request, "shows/confirm_delete.html", {"entry": entry, "show": entry.show})


@login_required
def collection(request):
    """The user's collection (full filters, sorting and pagination come in Phase 7)."""
    return render(request, "shows/collection.html")
