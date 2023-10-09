"""
These views do nothing other than provide members of the 'plain' BSCT template
set as default template names.
"""
import logging

from django.conf import settings
from django.core.exceptions import FieldDoesNotExist
from django.views import generic

from .templatetags.bscttags import get_headers

# Get the logger name from the user's settings.
logger_name = getattr(settings, "BSCT_LOGGER_NAME", "bsct")

logger = logging.getLogger(logger_name)


class CreateView(generic.CreateView):
    template_name = "bsct/plain/form.html"


class UpdateView(generic.UpdateView):
    template_name = "bsct/plain/form.html"


def authorized_fields(requested_fields, model):
    """Returns a list of fields that are authorized to be exposed to the user.

    Args:
        requested_fields (list): List of fields requested by the user.
        model (Model): Model to check for authorized fields.

    Returns:
        list: List of authorized fields.
    """

    # Get fields allowed with get_allowed_fields() classmethod.
    model_authorized_fields = model.get_allowed_fields()
    if model_authorized_fields == "__all__":
        model_authorized_fields = model._meta.get_fields()

    authorized_fields = []
    for field in requested_fields:
        if field in model_authorized_fields:
            # If the field is in the model's get_allowed_fields()
            authorized_fields.append(field)

        elif len(field.split("__")) > 1:
            # If the field is a related field with a field specified (e.g. 'tree__name')
            if field.split("__")[0] in model_authorized_fields:
                # If the related field is in the model's get_allowed_fields() (e.g. 'tree')
                try:
                    model._meta.get_field(
                        field.split("__")[0]
                    ).related_model._meta.get_field(field.split("__")[1]).name
                    authorized_fields.append(field)  # ?
                except FieldDoesNotExist:
                    pass
                except Exception as exception:
                    logger.error(
                        "An error occured while checking if %s exists : %s",
                        field.split("__"),
                        exception,
                    )

    return authorized_fields


class ListView(generic.ListView):
    template_name = "bsct/plain/list.html"

    def get_context_data(self, **kwargs):
        # Add headers for the table
        if self.model.__subclasses__():
            # The model has subclasses if it inherits from PolymorphicModel.
            headers = {}
            for subclass in self.model.__subclasses__():
                headers.update(get_headers(subclass))
        else:
            headers = get_headers(self.model)
        context = super(ListView, self).get_context_data(**kwargs)
        context.update({"headers": headers})
        context.update({"model": self.model._meta.verbose_name_plural})
        return context

    def get_queryset(self):
        allowed_fields = authorized_fields(
            [key for key in self.request.GET], self.model
        )
        params = {key: self.request.GET[key] for key in allowed_fields}
        # If the model has 'date_added', ordering by 'date_added' will be done.
        # If not, ordering by '-pk' will be done.
        if "date_added" in self.model._meta.get_fields():
            ordering = "-date_added"
        else:
            ordering = "id"
        return super().get_queryset().order_by(ordering).filter(**params)


class DetailView(generic.DetailView):
    template_name = "bsct/plain/detail.html"


class DeleteView(generic.DeleteView):
    template_name = "bsct/plain/confirm_delete.html"
