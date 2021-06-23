"""
This type stub file was generated by pyright.
"""

logger = ...
class ResourceCollection:
    """
    Represents a collection of resources, which can be iterated through,
    optionally with filtering. Collections automatically handle pagination
    for you.

    See :ref:`guide_collections` for a high-level overview of collections,
    including when remote service requests are performed.

    :type model: :py:class:`~boto3.resources.model.Collection`
    :param model: Collection model
    :type parent: :py:class:`~boto3.resources.base.ServiceResource`
    :param parent: The collection's parent resource
    :type handler: :py:class:`~boto3.resources.response.ResourceHandler`
    :param handler: The resource response handler used to create resource
                    instances
    """
    def __init__(self, model, parent, handler, **kwargs) -> None:
        ...
    
    def __repr__(self): # -> str:
        ...
    
    def __iter__(self): # -> Generator[Unknown, None, None]:
        """
        A generator which yields resource instances after doing the
        appropriate service operation calls and handling any pagination
        on your behalf.

        Page size, item limit, and filter parameters are applied
        if they have previously been set.

            >>> bucket = s3.Bucket('boto3')
            >>> for obj in bucket.objects.all():
            ...     print(obj.key)
            'key1'
            'key2'

        """
        ...
    
    def pages(self): # -> Generator[list[Unknown], None, None]:
        """
        A generator which yields pages of resource instances after
        doing the appropriate service operation calls and handling
        any pagination on your behalf. Non-paginated calls will
        return a single page of items.

        Page size, item limit, and filter parameters are applied
        if they have previously been set.

            >>> bucket = s3.Bucket('boto3')
            >>> for page in bucket.objects.pages():
            ...     for obj in page:
            ...         print(obj.key)
            'key1'
            'key2'

        :rtype: list(:py:class:`~boto3.resources.base.ServiceResource`)
        :return: List of resource instances
        """
        ...
    
    def all(self): # -> ResourceCollection:
        """
        Get all items from the collection, optionally with a custom
        page size and item count limit.

        This method returns an iterable generator which yields
        individual resource instances. Example use::

            # Iterate through items
            >>> for queue in sqs.queues.all():
            ...     print(queue.url)
            'https://url1'
            'https://url2'

            # Convert to list
            >>> queues = list(sqs.queues.all())
            >>> len(queues)
            2
        """
        ...
    
    def filter(self, **kwargs): # -> ResourceCollection:
        """
        Get items from the collection, passing keyword arguments along
        as parameters to the underlying service operation, which are
        typically used to filter the results.

        This method returns an iterable generator which yields
        individual resource instances. Example use::

            # Iterate through items
            >>> for queue in sqs.queues.filter(Param='foo'):
            ...     print(queue.url)
            'https://url1'
            'https://url2'

            # Convert to list
            >>> queues = list(sqs.queues.filter(Param='foo'))
            >>> len(queues)
            2

        :rtype: :py:class:`ResourceCollection`
        """
        ...
    
    def limit(self, count): # -> ResourceCollection:
        """
        Return at most this many resources.

            >>> for bucket in s3.buckets.limit(5):
            ...     print(bucket.name)
            'bucket1'
            'bucket2'
            'bucket3'
            'bucket4'
            'bucket5'

        :type count: int
        :param count: Return no more than this many items
        :rtype: :py:class:`ResourceCollection`
        """
        ...
    
    def page_size(self, count): # -> ResourceCollection:
        """
        Fetch at most this many resources per service request.

            >>> for obj in s3.Bucket('boto3').objects.page_size(100):
            ...     print(obj.key)

        :type count: int
        :param count: Fetch this many items per request
        :rtype: :py:class:`ResourceCollection`
        """
        ...
    


class CollectionManager:
    """
    A collection manager provides access to resource collection instances,
    which can be iterated and filtered. The manager exposes some
    convenience functions that are also found on resource collections,
    such as :py:meth:`~ResourceCollection.all` and
    :py:meth:`~ResourceCollection.filter`.

    Get all items::

        >>> for bucket in s3.buckets.all():
        ...     print(bucket.name)

    Get only some items via filtering::

        >>> for queue in sqs.queues.filter(QueueNamePrefix='AWS'):
        ...     print(queue.url)

    Get whole pages of items:

        >>> for page in s3.Bucket('boto3').objects.pages():
        ...     for obj in page:
        ...         print(obj.key)

    A collection manager is not iterable. You **must** call one of the
    methods that return a :py:class:`ResourceCollection` before trying
    to iterate, slice, or convert to a list.

    See the :ref:`guide_collections` guide for a high-level overview
    of collections, including when remote service requests are performed.

    :type collection_model: :py:class:`~boto3.resources.model.Collection`
    :param model: Collection model

    :type parent: :py:class:`~boto3.resources.base.ServiceResource`
    :param parent: The collection's parent resource

    :type factory: :py:class:`~boto3.resources.factory.ResourceFactory`
    :param factory: The resource factory to create new resources

    :type service_context: :py:class:`~boto3.utils.ServiceContext`
    :param service_context: Context about the AWS service
    """
    _collection_cls = ResourceCollection
    def __init__(self, collection_model, parent, factory, service_context) -> None:
        ...
    
    def __repr__(self): # -> str:
        ...
    
    def iterator(self, **kwargs): # -> ResourceCollection:
        """
        Get a resource collection iterator from this manager.

        :rtype: :py:class:`ResourceCollection`
        :return: An iterable representing the collection of resources
        """
        ...
    
    def all(self): # -> ResourceCollection:
        ...
    
    def filter(self, **kwargs): # -> ResourceCollection:
        ...
    
    def limit(self, count): # -> ResourceCollection:
        ...
    
    def page_size(self, count): # -> ResourceCollection:
        ...
    
    def pages(self): # -> Generator[list[Unknown], None, None]:
        ...
    


class CollectionFactory:
    """
    A factory to create new
    :py:class:`CollectionManager` and :py:class:`ResourceCollection`
    subclasses from a :py:class:`~boto3.resources.model.Collection`
    model. These subclasses include methods to perform batch operations.
    """
    def load_from_definition(self, resource_name, collection_model, service_context, event_emitter): # -> Type[_]:
        """
        Loads a collection from a model, creating a new
        :py:class:`CollectionManager` subclass
        with the correct properties and methods, named based on the service
        and resource name, e.g. ec2.InstanceCollectionManager. It also
        creates a new :py:class:`ResourceCollection` subclass which is used
        by the new manager class.

        :type resource_name: string
        :param resource_name: Name of the resource to look up. For services,
                              this should match the ``service_name``.

        :type service_context: :py:class:`~boto3.utils.ServiceContext`
        :param service_context: Context about the AWS service

        :type event_emitter: :py:class:`~botocore.hooks.HierarchialEmitter`
        :param event_emitter: An event emitter

        :rtype: Subclass of :py:class:`CollectionManager`
        :return: The collection class.
        """
        ...
    


