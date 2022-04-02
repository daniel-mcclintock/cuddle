import hug
import peewee
from playhouse.shortcuts import model_to_dict

FIELD_TO_TYPE = {peewee.AutoField: int}
PAGINATION_SIZE_LIMITS = (10, 100)


def clamp(value, smallest, largest):
    return max(smallest, min(value, largest))


def get_pagination_values(**kwargs):
    return (
        int(kwargs.get("page", 1)),
        clamp(
            int(kwargs.get("page_size", PAGINATION_SIZE_LIMITS[0])),
            *PAGINATION_SIZE_LIMITS,
        ),
    )


def Cuddle(model):
    """Decorator that provides Hug API functionality to a PeeWee class."""
    api = hug.route.API(model.__module__)
    base_url = f"/{model.__name__.lower()}"
    primary_key_name = model._meta.primary_key.name
    primary_key_type = FIELD_TO_TYPE[model._meta.primary_key.__class__]
    non_primary_fields = (
        field
        for (field, field_object) in model._meta.fields.items()
        if not field_object.primary_key
    )
    all_fields = (primary_key_name,) + tuple(non_primary_fields)

    base_url_by_primary_key = base_url + (
        "/{" f"{primary_key_name}:{primary_key_type.__name__}" "}"
    )

    @api.get(
        base_url_by_primary_key,
        parameters=("response", primary_key_name),
        # TODO: type annotations
    )
    def _get_by_primary_key(response, **kwargs):
        primary_key = kwargs[primary_key_name]
        try:
            return model_to_dict(model.get(primary_key), recurse=False)
        except model.DoesNotExist:
            response.status = hug.HTTP_404
            return hug.HTTP_404

    @api.delete(
        base_url_by_primary_key,
        parameters=("response", primary_key_name),
        # TODO: type annotations
    )
    def _del_by_primary_key(response, **kwargs):
        primary_key = kwargs[primary_key_name]
        try:
            model.get(primary_key).delete()
            return hug.HTTP_200
        except model.DoesNotExist:
            response.status = hug.HTTP_404
            return hug.HTTP_404

    @api.put(
        base_url_by_primary_key,
        parameters=("response", *all_fields),
        # TODO: type annotations
    )
    def _update_by_primary_key(response, **kwargs):
        primary_key = kwargs[primary_key_name]
        update = model.update(**kwargs).where(
            getattr(model, primary_key_name) == primary_key
        )
        update.execute()
        return model_to_dict(model.get(primary_key), recurse=False)

    @api.post(
        base_url,
        parameters=("response", *non_primary_fields)
        # TODO: type annotations
    )
    def _create(response, **kwargs):
        instance = model(**kwargs)
        instance.save()
        return model_to_dict(instance, recurse=False)

    @api.get(
        f"{base_url}/query",
        parameters=("response", *non_primary_fields),
        defaults={field: None for field in non_primary_fields},
        # TODO: type annotations
    )
    def _query(response, **kwargs):
        page, page_size = get_pagination_values(**kwargs)
        query = model.select()

        param_query_string = []

        for field, value in kwargs.items():
            if field not in ["response", "page", "page_size"]:
                param_query_string.append(f"{field}={value}")
                query = query.where(getattr(model, field) == value)

        query = query.offset((page - 1) * page_size)
        query = query.limit(page_size)

        results = [model_to_dict(m, recurse=False) for m in query]

        # TODO: clamp pages and validate totals
        param_query_string = "&".join(param_query_string)
        page_prev = (
            f"{base_url}/query?{param_query_string}&page={page-1}&page_size={page_size}"
            if page > 1
            else None
        )
        page_next = (
            f"{base_url}/query?{param_query_string}&page={page+1}&page_size={page_size}"
            if len(results) == page_size or page < 1
            else None
        )

        return {
            "total": len(results),
            "results": results,
            "page": page,
            "page_size": page_size,
            "page_prev": page_prev,
            "page_next": page_next,
        }

    return model
