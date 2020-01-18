from django.contrib.syndication.views import Feed, FeedDoesNotExist
from django.db.models import Q
from django.http import Http404
from django.urls import reverse
from django.utils.feedgenerator import Atom1Feed
from django.utils.translation import ugettext_lazy as _

from djangobb_forum.models import Post, Topic, Forum, Category


class ForumFeed(Feed):
    feed_type = Atom1Feed

    def link(self, request, *args, **kwargs):
        return reverse('djangobb:index')

    @staticmethod
    def item_guid(obj):
        return str(obj.id)

    @staticmethod
    def item_pubdate(obj):
        return obj.created

    @staticmethod
    def item_author_name(self, item):
        return item.user.username


class LastPosts(ForumFeed):
    title = _('Latest posts on forum')
    description = _('Latest posts on forum')
    title_template = 'djangobb_forum/feeds/posts_title.html'
    description_template = 'djangobb_forum/feeds/posts_description.html'

    def get_object(self, request, *args, **kwargs):
        user_groups = request.user.groups.all()
        if request.user.is_anonymous:
            user_groups = []
        allow_forums = Forum.objects.filter(
            Q(category__groups__in=user_groups) |
            Q(category__groups__isnull=True)).order_by("-updated")
        return allow_forums

    @staticmethod
    def items(allow_forums):
        _items = Post.objects.filter(topic__forum__in=allow_forums).order_by('-created')
        return _items[:15] if _items.exists() else _items.none()


class LastTopics(ForumFeed):
    title = _('Latest topics on forum')
    description = _('Latest topics on forum')
    title_template = 'djangobb_forum/feeds/topics_title.html'
    description_template = 'djangobb_forum/feeds/topics_description.html'

    def get_object(self, request, *args, **kwargs):
        user_groups = request.user.groups.all()
        if request.user.is_anonymous:
            user_groups = []
        allow_forums = Topic.objects.filter(
            Q(topic__forum__category__groups__in=user_groups) |
            Q(topic__forum__category__groups__isnull=True)).order_by("-updated")
        return allow_forums

    @staticmethod
    def items(allow_forums):
        _items = Topic.objects.filter(topic__forum__in=allow_forums).order_by('-created')
        return _items[:15] if _items.exists() else _items.none()


class LastPostsOnTopic(ForumFeed):
    title_template = 'djangobb_forum/feeds/posts_title.html'
    description_template = 'djangobb_forum/feeds/posts_description.html'

    def get_object(self, request, *args, **kwargs):
        try:
            topic = Topic.objects.get(id=kwargs.get("topic_id"))
            if topic.forum.category.has_access(user=request.user):
                return topic
            else:
                raise Http404
        except Exception as exp:
            raise Http404

    @staticmethod
    def title(obj):
        return _('Latest posts on {title} topic'.format(title=obj.name))

    def link(self, request, *args, **kwargs):
        obj = self.get_object(request=request, *args, **kwargs)
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return _('Latest posts on {description} topic'.format(description=obj.name))

    def items(self, obj):
        try:
            return Post.objects.filter(topic__id=obj.id).order_by('-created')[:15]
        except Exception as exp:
            return Post.objects.none()


class LastPostsOnForum(ForumFeed):
    title_template = 'djangobb_forum/feeds/posts_title.html'
    description_template = 'djangobb_forum/feeds/posts_description.html'

    def get_object(self, request, *args, **kwargs):
        try:
            forum = Forum.objects.get(id=kwargs.get("forum_id"))
            if forum.category.has_access(user=request.user):
                return forum
            else:
                raise Http404
        except Exception as exp:
            raise Http404

    def title(self, obj):
        return _('Latest posts on {title} forum'.format(title=obj.name))

    def link(self, request, *args, **kwargs):
        obj = self.get_object(request=request, *args, **kwargs)
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return _('Latest posts on {description} forum'.format(description=obj.name))

    def items(self, obj):
        try:
            return Post.objects.filter(topic__forum__id=obj.id).order_by('-created')[:15]
        except Exception as exp:
            return Post.objects.none()


class LastPostsOnCategory(ForumFeed):
    title_template = 'djangobb_forum/feeds/posts_title.html'
    description_template = 'djangobb_forum/feeds/posts_description.html'

    def get_object(self, request, *args, **kwargs):
        try:
            category = Category.objects.get(id=kwargs.get("category_id"))
            if category.has_access(user=request.user):
                return category
            else:
                raise Http404
        except Exception as exp:
            raise Http404

    def title(self, obj):
        return _('Latest posts on {title} category'.format(title=obj.name))

    def description(self, obj):
        return _('Latest posts on {description} category'.format(description=obj.name))

    def items(self, obj):
        try:
            return Post.objects.filter(topic__forum__category__id=obj.id).order_by('-created')[:15]
        except Exception as exp:
            return Post.objects.none()
