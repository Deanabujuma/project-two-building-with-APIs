from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import queries, services, tvmaze
from .forms import TrackingForm
from .models import CollectionEntry, Show


HOME_RECENT_LIMIT = 10


def home_context(user):
    """The personal home page: one featured show and four rows, all from the user's entries.

    The hero features the most recently updated Watching entry, falling back to the most
    recently updated entry of any status. Continue Tracking lists the other Watching entries.
    """
    by_updated = list(queries.order_entries(queries.collection_entries(user), "-updated_at"))
    featured = next((e for e in by_updated if e.status == "watching"), by_updated[0] if by_updated else None)
    by_created = sorted(by_updated, key=lambda e: e.created_at, reverse=True)
    rows = [
        {"key": "continue", "title": "Continue Tracking", "sub": "Watching, most recently updated", "wide": True,
         "entries": [e for e in by_updated if e.status == "watching" and e != featured]},
        {"key": "watchlist", "title": "My Watchlist", "sub": "Plan to Watch", "wide": False,
         "entries": [e for e in by_updated if e.status == "plan_to_watch"]},
        {"key": "recent", "title": "Recently Added", "sub": "Newest saves first", "wide": False,
         "entries": by_created[:HOME_RECENT_LIMIT]},
        {"key": "completed", "title": "Completed Shows", "sub": "", "wide": False,
         "entries": [e for e in by_updated if e.status == "completed"]},
    ]
    return {"featured": featured, "rows": [row for row in rows if row["entries"]]}


def home(request):
    """Public home page: a welcome hero for visitors, the personal home for users."""
    context = home_context(request.user) if request.user.is_authenticated else {}
    return render(request, "home.html", context)


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


COLLECTION_PAGE_SIZE = 12

# Web sort options -> the shared ordering values the API also accepts.
WEB_SORTS = [
    ("-updated", "Recently updated", "-updated_at"),
    ("title", "Title (A–Z)", "show__name"),
    ("-rating", "My rating (high–low)", "-rating"),
]
DEFAULT_SORT = "-updated"


@login_required
def collection(request):
    """My Collection: status chips, title search, sort and 12-per-page pagination.

    Every option lives in the URL, so a view can be bookmarked. Owner scoping, the status
    filter and ordering come from shows.queries, the same code the API uses.
    """
    status_values = {value for value, _ in CollectionEntry.Status.choices}
    status = request.GET.get("status", "")
    status = status if status in status_values else ""
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", DEFAULT_SORT)
    sort_map = {key: ordering for key, _, ordering in WEB_SORTS}
    sort = sort if sort in sort_map else DEFAULT_SORT

    entries = queries.collection_entries(request.user, status)
    if q:
        entries = entries.filter(show__name__icontains=q)  # titles only; the API also searches notes
    entries = queries.order_entries(entries, sort_map[sort])
    page = Paginator(entries, COLLECTION_PAGE_SIZE).get_page(request.GET.get("page"))

    counts = dict(CollectionEntry.objects.filter(user=request.user).values_list("status").annotate(n=Count("pk")))
    total_saved = sum(counts.values())

    def url_with(**changes):
        """This page's URL with some parameters changed; empty and default values are left out."""
        params = {"status": status, "q": q, "sort": sort, **changes}
        if params["sort"] == DEFAULT_SORT:
            params["sort"] = ""
        query = urlencode({key: value for key, value in params.items() if value})
        return reverse("shows:collection") + (f"?{query}" if query else "")

    chips = [{"value": "", "label": "All", "count": total_saved, "url": url_with(status="")}]
    chips += [{"value": value, "label": label, "count": counts.get(value, 0), "url": url_with(status=value)}
              for value, label in CollectionEntry.Status.choices]

    titles = {"watching": "Watching", "completed": "Completed"}
    context = {
        "page": page,
        "chips": chips,
        "status": status,
        "status_label": dict(CollectionEntry.Status.choices).get(status, ""),
        "q": q,
        "sort": sort,
        "sorts": [(key, label) for key, label, _ in WEB_SORTS],
        "total_saved": total_saved,
        "page_title": titles.get(status, "My Collection"),
        "page_links": [(number, url_with(page=number)) for number in page.paginator.page_range],
        "prev_url": url_with(page=page.previous_page_number()) if page.has_previous() else "",
        "next_url": url_with(page=page.next_page_number()) if page.has_next() else "",
        "clear_url": reverse("shows:collection"),
    }
    return render(request, "shows/collection.html", context)
