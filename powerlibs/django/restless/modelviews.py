from copy import copy

from django.forms.models import modelform_factory

from .views import Endpoint
from .http import HttpError, Http200, Http201

from .models import serialize

__all__ = ['ListEndpoint', 'DetailEndpoint']


def _get_form(form, model):
    from django import VERSION

    if VERSION[:2] >= (1, 8):
        def mf(model):
            return modelform_factory(model, fields='__all__')
    else:
        mf = modelform_factory

    if form:
        return form
    elif model:
        return mf(model)
    else:
        raise NotImplementedError('Form or Model class not specified')


def method(the_real_method):
    def new_method(self, *args, **kwargs):
        if the_real_method.__name__.upper() not in self.methods:
            raise HttpError(405, 'Method Not Allowed')
        return the_real_method(self, *args, **kwargs)


class ListEndpoint(Endpoint):
    """
    List :py:class:`restless.views.Endpoint` supporting getting a list of
    objects and creating a new one. The endpoint exports two view methods by
    default: get (for getting the list of objects) and post (for creating a
    new object).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have a list
    (and/or create) endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for creating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.
    """

    model = None
    form = None
    methods = ['GET', 'POST']

    def get_query_set(self, request, *args, **kwargs):
        """Return a QuerySet that this endpoint represents.

        If `model` class attribute is set, this method returns the `all()`
        queryset for the model. You can override the method to provide custom
        behaviour. The `args` and `kwargs` parameters are passed in directly
        from the URL pattern match.

        If the method raises a :py:class:`restless.http.HttpError` exception,
        the rest of the request processing is terminated and the error is
        immediately returned to the client.
        """

        if self.model:
            return self.model.objects.all()
        else:
            raise HttpError(404, 'Resource Not Found')

    @staticmethod
    def serialize(objs):
        """Serialize the objects in the response.

        By default, the method uses the :py:func:`restless.models.serialize`
        function to serialize the objects with default behaviour. Override the
        method to customize the serialization.
        """

        return serialize(objs)

    @method
    def get(self, request, *args, **kwargs):
        """Return a serialized list of objects in this endpoint."""

        qs = self.get_query_set(request, *args, **kwargs)
        return self.serialize(qs)

    @method
    def post(self, request, *args, **kwargs):
        """Create a new object."""

        if isinstance(request.data, (list, tuple)):
            # TODO: atomic transaction!
            for entry in request.data:
                new_request = copy(request)
                new_request.POST = entry
                new_request.data = entry
                ret = self.post(new_request, *args, **kwargs)
                if not isinstance(ret, (Http201, Http200)):
                    return ret  # TODO: rollback transaction!
            return Http201({})

        Form = _get_form(self.form, self.model)
        form = Form(entry or None, request.FILES)
        if not form.is_valid():
            raise HttpError(400, 'Invalid Data', errors=form.errors)
        obj = form.save()
        return Http201(self.serialize(obj))


class DetailEndpoint(Endpoint):
    """
    Detail :py:class:`restless.views.Endpoint` supports getting a single
    object from the database (HTTP GET), updating it (HTTP PUT) and deleting
    it (HTTP DELETE).

    The only required configuration for the endpoint is the `model`
    class attribute, which should be set to the model you want to have the
    detail endpoints for.

    You can also provide a `form` class attribute, which should be the
    model form that's used for updating the model. If not provided, the
    default model class for the model will be created automatically.

    You can restrict the HTTP methods available by specifying the `methods`
    class variable.

    """
    model = None
    form = None
    lookup_field = 'pk'
    methods = ['GET', 'PUT', 'PATCH', 'DELETE']

    def get_instance(self, request, *args, **kwargs):
        """Return a model instance represented by this endpoint.

        If `model` is set and the primary key keyword argument is present,
        the method attempts to get the model with the primary key equal
        to the url argument.

        By default, the primary key keyword argument name is `pk`. This can
        be overridden by setting the `lookup_field` class attribute.

        You can override the method to provide custom behaviour. The `args`
        and `kwargs` parameters are passed in directly from the URL pattern
        match.

        If the method raises a :py:class:`restless.http.HttpError` exception,
        the rest of the request processing is terminated and the error is
        immediately returned to the client.
        """

        if self.model and self.lookup_field in kwargs:
            try:
                return self.model.objects.get(**{
                    self.lookup_field: kwargs.get(self.lookup_field)
                })
            except self.model.DoesNotExist:
                raise HttpError(404, 'Resource Not Found')
        else:
            raise HttpError(404, 'Resource Not Found')

    def serialize(self, obj):
        """Serialize the object in the response.

        By default, the method uses the :py:func:`restless.models.serialize`
        function to serialize the object with default behaviour. Override the
        method to customize the serialization.
        """

        return serialize(obj)

    @method
    def get(self, request, *args, **kwargs):
        """Return the serialized object represented by this endpoint."""

        return self.serialize(self.get_instance(request, *args, **kwargs))

    @method
    def patch(self, request, *args, **kwargs):
        """Update the object represented by this endpoint."""

        instance = self.get_instance(request, *args, **kwargs)

        for key, value in request.data.items():
            setattr(instance, key, value)

        instance.save()

        return Http200(self.serialize(instance))

    @method
    def put(self, request, *args, **kwargs):
        """Update the object represented by this endpoint."""

        Form = _get_form(self.form, self.model)
        instance = self.get_instance(request, *args, **kwargs)
        form = Form(request.data or None, request.FILES, instance=instance)
        if form.is_valid():
            obj = form.save()
            return Http200(self.serialize(obj))
        raise HttpError(400, 'Invalid data', errors=form.errors)

    @method
    def delete(self, request, *args, **kwargs):
        """Delete the object represented by this endpoint."""

        instance = self.get_instance(request, *args, **kwargs)
        instance.delete()
        return {}
