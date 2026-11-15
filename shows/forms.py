from django import forms

from .models import CollectionEntry
from .validation import NOTES_MAX_LENGTH


class TrackingForm(forms.ModelForm):
    """The My Tracking form. Validation comes from CollectionEntry.clean() (the shared rules)."""

    class Meta:
        model = CollectionEntry
        fields = ["status", "current_season", "current_episode", "rating", "notes"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "current_season": forms.NumberInput(attrs={"class": "form-control", "min": 1, "placeholder": "—", "inputmode": "numeric"}),
            "current_episode": forms.NumberInput(attrs={"class": "form-control", "min": 1, "placeholder": "—", "inputmode": "numeric"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 7, "maxlength": NOTES_MAX_LENGTH,
                                           "placeholder": "Theories, favourite episodes, where you left off…"}),
        }
        labels = {"current_season": "Season", "current_episode": "Episode"}
        # Django's own field checks run before CollectionEntry.clean(); give them the same
        # wording as shows.validation so the user sees one consistent message per rule.
        error_messages = {
            "current_season": {key: "Season must be a whole number of 1 or more." for key in ("invalid", "min_value")},
            "current_episode": {key: "Episode must be a whole number of 1 or more." for key in ("invalid", "min_value")},
            "rating": {key: "Rating must be a whole number from 1 to 5, or blank."
                       for key in ("invalid", "min_value", "max_value")},
            "notes": {"max_length": "Notes can be at most 2,000 characters (you entered %(show_value)s)."},
        }

    PROGRESS_FIELDS = ("current_season", "current_episode")

    def _update_errors(self, errors):
        """Skip shared-rule errors for fields whose own check already failed.

        Without this, "0" in Season would be reported twice (field check + shared rule).
        And because a rejected value never reaches the model, the shared rule would also
        claim the *other* progress field is missing.
        """
        if hasattr(errors, "error_dict"):
            progress_failed = any(field in self.errors for field in self.PROGRESS_FIELDS)
            for field in list(errors.error_dict):
                if field in self.errors or (progress_failed and field in self.PROGRESS_FIELDS):
                    del errors.error_dict[field]
            if not errors.error_dict:
                return
        super()._update_errors(errors)
