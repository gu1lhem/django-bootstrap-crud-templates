import logging
from typing import Dict, List

from django.conf import settings
from django.db import models
from django.template import Library

from django.urls.exceptions import NoReverseMatch

# Get the logger name from the user's settings.
logger_name = getattr(settings, "BSCT_LOGGER_NAME", "bsct")

logger = logging.getLogger(logger_name)

register = Library()

@register.filter(name="get_class_name")
def get_class_name(value):
    """
    Return the class name of an object.
    Source: https://stackoverflow.com/a/14291795
    """
    try:
        return value.__class__._meta.verbose_name
    except Exception:
        return value.__class__.__name__

@register.simple_tag
def get_verbose_name(instance):
    """
    Returns the verbose name for a model.
    """
    return instance._meta.verbose_name


@register.simple_tag
def get_verbose_name_plural(instance):
    """
    Returns the verbose pluralized name for a model.
    """
    return instance._meta.verbose_name_plural


# Pagination Helpers
# -------------------------


@register.simple_tag
def append_querystring(request, exclude=None):
    """
    Returns the query string for the current request, minus the GET parameters
    included in the `exclude`.
    """
    exclude = exclude or ["page"]

    if request and request.GET:
        amp = "&amp;"
        return amp + amp.join(
            ["%s=%s" % (k, v) for k, v in request.GET.items() if k not in exclude]
        )

    return ""


# Filters
# -------------------------


@register.filter
def get_detail(instance):
    """
    Returns a dictionary of the models fields and values.

    If the method '<field>_detail' or verbose_name is defined, its value is used as the
    displayed value for the field.
    """

    # Get fields allowed with get_allowed_fields_details() classmethod.
    allowed_fields = instance.get_allowed_fields_details()
    if allowed_fields == "__all__":
        fields = instance._meta.get_fields()
    else:
        fields = [f for f in instance._meta.get_fields() if f.name in allowed_fields]

    details = {}

    # Get fields that are in a foreign key relation.
    fk_fields = [f for f in allowed_fields if "__" in f]
    for fk_field in fk_fields:
        try:
            # Get the field name and the related model.
            model_name, field_name = fk_field.split("__")
            # Get the related model.
            related_model = getattr(instance, model_name)
            # Get the related model's field.
            related_field = getattr(related_model, field_name)
            details[field_name] = str(related_field)

        except Exception as exception:
            logger.warning("Error getting related field %s: %s", fk_field, exception)

    for field in fields:
        try:
            # Get information about the field.
            detail_method = getattr(instance, f"get_{field.name}_detail", None)
            if detail_method:
                details[detail_method] = detail_method(*{instance})

            verbose = getattr(field, "verbose_name", None)
            value = getattr(instance, field.name, None)

            display_method = getattr(instance, "get_%s_display" % field.name, None)
            render = getattr(instance, "get_%s_render" % field.name, None)
            if display_method:
                value = display_method()
            elif render:
                value = f"<div class={render()}>{value}</div>"

            elif field.get_internal_type() == "DateTimeField":
                value = value.strftime("%Y-%m-%d %H:%M:%S")

            elif field.is_relation:
                
                relation_verbose = getattr(field.related_model._meta, "verbose_name")
                if getattr(field, "multiple", False):
                    # If the field is a relation to a many-to-many field

                    # Get the related objects and generate links.
                    rset = getattr(instance, "%s_set" % field.name)
                    value = []
                    for i in rset.all():
                        try:
                            value.append(f"<a href={i.get_absolute_url()}>{i}</a>")
                        except NoReverseMatch:
                            value.append(str(i).strip('<>'))

                    # Try to get the plural verbose name of the related model if any,
                    # and if there is multiple relations.
                    if rset.count() > 1 and getattr(
                        field.related_model._meta, "verbose_name_plural"
                    ):
                        relation_verbose = getattr(
                            field.related_model._meta, "verbose_name_plural"
                        )
                else:
                    # If the field is a relation to a ForeignKey (one-to-many) field
                    foreign_key_element = getattr(instance, "%s" % field.name)
                    if hasattr(foreign_key_element, "get_absolute_url"):
                        ref_url = foreign_key_element.get_absolute_url()
                        value = f"<a href='{ref_url}'>{value}</a>"
                    else:
                        value = str(foreign_key_element)

            # If the value is 'None', we want to display '-' instead.
            if value is None or (type(value) is str and value.endswith("None")):
                value = "-"

            # Now, add the field to the details dictionary.
            if field.is_relation:
                if relation_verbose:
                    details[relation_verbose] = value
                else:
                    details[field.name] = value
            elif verbose:
                # Classic field with verbose_name
                if field.__class__ is models.FileField:
                    # URL to the file
                    details[verbose] = f"<a href='{value.url}'>{value}</a>"
                else:
                    details[verbose] = value
            else:
                details[field.name] = value

        except Exception as exception:
            logger.warning("Error getting field %s: %s (%s)", field, exception, exception.__class__)
    return details


def get_allowed_fields(instance: models.Model) -> List[str]:
    """Returns allowed fields for a model.

    Args:
        instance (Model): instance to look for allowed fields.

    Returns:
        list: list of allowed fields.
    """

    if hasattr(instance, "get_allowed_fields_list"):
        allowed_fields = instance.get_allowed_fields_list()
    else:
        # Get fields allowed with get_allowed_fields_details() classmethod.
        allowed_fields = instance.get_allowed_fields()

    if allowed_fields == "__all__":
        # All fields, ignoring many-to-many fields
        return [
            f for f in instance._meta.get_fields() if not getattr(f, "multiple", False)
        ]
    else:
        return [
            f
            for f in instance._meta.get_fields()
            if f.name in allowed_fields and not getattr(f, "multiple", False)
        ]


def get_headers(instance: models.Model) -> Dict[str, str]:
    """Returns headers for a model.

    Args:
        instance (Model): instance to look for headers.

    Returns:
        dict: dictionary of headers.
    """
    headers = {}

    for field in get_allowed_fields(instance):
        if field.__class__ is models.TextField:
            continue  # TextFields are not displayed in the list view.

        try:
            detail_method = getattr(instance, "get_%s_detail" % field.name, None)(
                *{instance}
            )
        except Exception:
            detail_method = None
        verbose = getattr(field, "verbose_name", None)
        if field.is_relation:
            relation_verbose = getattr(field.related_model._meta, "verbose_name")
            # If the field is a relation to a ForeignKey (one-to-many) field
            if relation_verbose:
                headers[field.__str__()] = relation_verbose
            else:
                headers[field.__str__()] = field.name
        elif detail_method:
            headers[field.__str__()] = detail_method
        elif verbose:
            headers[field.__str__()] = verbose
        else:
            headers[field.__str__()] = field.name

    return headers


@register.filter
def get_list_headers(instances: List[models.Model]) -> Dict[str, str]:
    """Returns headers for a list of models.

    Args:
        instances (List[Model]): list of instances to look for headers.

    Returns:
        dict: dictionary of headers.
    """
    headers = {}
    [headers.update(get_headers(instance)) for instance in instances]
    return headers


@register.filter
def get_list_detail(instance):
    """
    Returns a dictionary of the models fields and values.

    If the method '<field>_detail' or verbose_name is defined, its value is used as the
    displayed value for the field.
    """

    details = {}

    for field in get_allowed_fields(instance):
        try:
            if field.__class__ is models.TextField:
                continue  # TextFields are not displayed in the list view.

            try:
                detail_method = getattr(instance, "get_%s_detail" % field.name, None)(
                    *{instance}
                )
            except Exception:
                detail_method = None
            verbose = getattr(field, "verbose_name", None)
            value = getattr(instance, field.name, None)

            display_method = getattr(instance, "get_%s_display" % field.name, None)
            if display_method:
                value = display_method()

            render = getattr(instance, "get_%s_render" % field.name, None)
            if render:
                value = f"<div class={render()}>{value}</div>"
            if field.get_internal_type() == "DateTimeField":
                value = value.strftime("%Y-%m-%d %H:%M:%S")
            if field.is_relation:
                relation_verbose = getattr(field.related_model._meta, "verbose_name")
                # If the field is a relation to a ForeignKey (one-to-many) field
                ref_url = getattr(instance, "%s" % field.name).get_absolute_url()
                value = f"<a href='{ref_url}'>{value}</a>"
                if relation_verbose:
                    details[field.__str__()] = value

                else:
                    details[field.__str__()] = value
            elif detail_method:
                details[field.__str__()] = detail_method
            elif verbose:
                # Classic field with verbose_name
                if field.__class__ is models.FileField:
                    # URL to the file
                    details[field.__str__()] = f"<a href='{value.url}'>{value}</a>"
                else:
                    details[field.__str__()] = value
            else:
                details[field.__str__()] = value

            if value is None:
                details[field.__str__()] = ""
        except Exception:
            pass
    return details


def is_field_m2m_cascade(field):
    """
    Returns True if the field is a ManyToManyField and the 'on_delete' is set to CASCADE.
    """
    if field.is_relation:  # if field is a relation (FK, M2M)
        if getattr(
            field, "multiple", False
        ):  # If the field is a relation to a many-to-many field
            if field.on_delete == models.CASCADE:  # if on_delete is CASCADE
                return True
    return False


@register.filter(name="dict_key")
def dict_key(d, k):
    """Returns the given key from a dictionary.
    https://stackoverflow.com/questions/19745091/accessing-dictionary-by-key-in-django-template/51090108#51090108
    """
    try:
        return d[k]
    except KeyError:
        return ""


@register.filter
def get_delete_detail(instance):
    """
    Returns a dictionary of the models FK and M2M relationships fields and values.
    """
    fields = instance._meta.get_fields()
    details = {}

    for field in fields:  # loop through model instance fields
        if is_field_m2m_cascade(
            field
        ):  # if field is a ManyToManyField and on_delete is CASCADE

            rset = getattr(instance, "%s_set" % field.name)  # set of related objects
            value = []

            for child_instance in rset.all():  # loop through related objects
                child_set = []
                child_fields = (
                    child_instance._meta.get_fields()
                )  # get fields of related object
                for (
                    child_field
                ) in child_fields:  # loop through child model instance fields

                    if is_field_m2m_cascade(
                        child_field
                    ):  # if child field is a ManyToManyField and on_delete is CASCADE
                        child_rset = getattr(
                            child_instance, "%s_set" % child_field.name
                        )  # set of related objects

                        [
                            child_set.append(
                                f"<a href='{c.get_absolute_url()}'>{c}</a>"
                            )
                            for c in child_rset.all()
                        ]  # loop through related objects
                        # we store the instances

                value.append(
                    f"<a href='{child_instance.get_absolute_url()}'>{child_instance}</a><ul>{''.join([f'<li>{c}</li>' for c in child_set])}</ul>"
                )

            # handle verbose_name if it is defined
            relation_verbose = getattr(field.related_model._meta, "verbose_name")
            if relation_verbose:
                details[relation_verbose] = value
            else:
                details[field.name] = value

    return details
