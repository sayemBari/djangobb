# -*- coding: utf-8
from __future__ import unicode_literals

import hashlib

from django import template
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import naturalday
from django.core.cache import cache
from django.urls import reverse
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from djangobb_forum import settings as forum_settings
from djangobb_forum.models import Report

register = template.Library()


# TODO:
# * rename all tags with forum_ prefix

@register.filter
def profile_link(user):
    uname = user.username if user else "NULL"
    data = '<a href="{hrefVal}">{uname}</a>'.format(
        hrefVal=reverse('djangobb:forum_profile', args=[uname]),
        uname=uname
    )
    return mark_safe(data)


@register.tag
def forum_time(parser, token):
    try:
        tag, time = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError('forum_time requires single argument')
    else:
        return ForumTimeNode(time)


class ForumTimeNode(template.Node):
    def __init__(self, time):
        self.time = template.Variable(time)

    def render(self, context):
        time = timezone.localtime(self.time.resolve(context))
        formatted_time = "{ndTime} {strTime}".format(ndTime=naturalday(time), strTime=time.strftime("%H:%M:%S"))
        formatted_time = mark_safe(formatted_time)
        return formatted_time


@register.simple_tag
def link(object, anchor=''):
    """
    Return A tag with link to object.
    """
    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    anchor = anchor or smart_text(object)
    return mark_safe('<a href="{url}">{text}</a>'.format(url=url, text=anchor))


@register.simple_tag
def lofi_link(object, anchor=''):
    """
    Return A tag with lofi_link to object.
    """

    url = hasattr(object, 'get_absolute_url') and object.get_absolute_url() or None
    anchor = anchor or smart_text(object)
    url_string = '<a href="{hrefVal}lofi/">{anchorVal}</a>'.format(hrefVal=url, anchorVal=escape(anchor))
    return mark_safe(s=url_string)


@register.filter
def has_unreads(topic, user):
    """
    Check if topic has messages which user didn't read.
    """
    if not user.is_authenticated() or (user.posttracking.last_read is not None
                                       and user.posttracking.last_read > topic.updated):
        return False
    else:
        if isinstance(user.posttracking.topics, dict):
            if topic and topic.last_post and topic.last_post_id > user.posttracking.topics.get(str(topic.id), 0):
                return True
            else:
                return False
        return True


@register.filter
def forum_unreads(forum, user):
    """
    Check if forum has topic which user didn't read.
    """
    if not user.is_authenticated():
        return False
    else:
        if isinstance(user.posttracking.topics, dict):
            topics = forum.topics.all().only('last_post')
            if user.posttracking.last_read:
                topics = topics.filter(updated__gte=user.posttracking.last_read)
            for topic in topics:
                if topic.last_post and topic.last_post_id > user.posttracking.topics.get(str(topic.id), 0):
                    return True
        return False


@register.filter
def forum_moderated_by(topic, user):
    """
    Check if user is moderator of topic's forum.
    """
    return user.is_superuser or user in topic.forum.moderators.all()


@register.filter
def forum_editable_by(post, user):
    """
    Check if the post could be edited by the user.
    """
    if user.is_superuser:
        return True
    if post.user == user:
        return True
    if user in post.topic.forum.moderators.all():
        return True
    return False


@register.filter
def forum_posted_by(post, user):
    """
    Check if the post is writed by the user.
    """
    return post.user == user


@register.filter
def forum_equal_to(obj1, obj2):
    """
    Check if objects are equal.
    """
    return obj1 == obj2


@register.filter
def forum_authority(user):
    posts = user.forum_profile.post_count
    static_url = settings.STATIC_URL
    if posts >= forum_settings.AUTHORITY_STEP_10:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote10.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_9:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote9.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_8:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote8.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_7:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote7.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_6:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote6.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_5:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote5.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_4:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote4.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_3:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote3.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_2:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote2.gif" alt="" />'.format(static_url=static_url))
    elif posts >= forum_settings.AUTHORITY_STEP_1:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote1.gif" alt="" />'.format(static_url=static_url))
    else:
        return mark_safe(
            '<img src="{static_url}djangobb_forum/img/authority/vote0.gif" alt="" />'.format(static_url=static_url))


@register.filter
def online(user):
    return cache.get('djangobb_user{user_id}'.format(user_id=user.id))


@register.filter
def attachment_link(attach):
    from django.template.defaultfilters import filesizeformat
    static_url = settings.STATIC_URL
    if attach.content_type in ['image/png', 'image/gif', 'image/jpeg']:
        img = '<img src="{static_url}djangobb_forum/img/attachment/image.png" alt="attachment" />'.format(
            static_url=static_url)
    elif attach.content_type in ['application/x-tar', 'application/zip']:
        img = '<img src="{static_url}djangobb_forum/img/attachment/compress.png" alt="attachment" />'.format(
            static_url=static_url)
    elif attach.content_type in ['text/plain']:
        img = '<img src="{static_url}djangobb_forum/img/attachment/text.png" alt="attachment" />'.format(
            static_url=static_url)
    elif attach.content_type in ['application/msword']:
        img = '<img src="{static_url}djangobb_forum/img/attachment/doc.png" alt="attachment" />'.format(
            static_url=static_url)
    else:
        img = '<img src="{static_url}djangobb_forum/img/attachment/unknown.png" alt="attachment" />'.format(
            static_url=static_url)
    attachment = '{img} <a href="{url}">{name}</a> ({size})'.format(
        img=img, url=attach.get_absolute_url(), name=attach.name, size=filesizeformat(attach.size))
    return mark_safe(attachment)


@register.simple_tag
def new_reports():
    return Report.objects.filter(zapped=False).count()


@register.simple_tag(takes_context=True)
def gravatar(context, email):
    if forum_settings.GRAVATAR_SUPPORT:
        if 'request' in context:
            is_secure = context['request'].is_secure()
        else:
            is_secure = False
        size = max(forum_settings.AVATAR_WIDTH, forum_settings.AVATAR_HEIGHT)
        url = 'https://secure.gravatar.com/avatar/{hash}?' if is_secure \
            else 'http://www.gravatar.com/avatar/{hash}?'
        url = url.format(hash=hashlib.md5(email.lower().encode('ascii')).hexdigest())
        url += urlencode({
            'size': size,
            'default': forum_settings.GRAVATAR_DEFAULT,
        })
        return url.replace('&', '&amp;')
    else:
        return ''


@register.simple_tag
def set_theme_style(user):
    if user.is_authenticated():
        selected_theme = user.forum_profile.theme
        theme_style = '<link rel="stylesheet" type="text/css" href="{static_url}djangobb_forum/themes/{theme}/style.css" />'
        return mark_safe(s=theme_style.format(static_url=settings.STATIC_URL, theme=selected_theme))
    else:
        theme_style = '<link rel="stylesheet" type="text/css" href="{static_url}djangobb_forum/themes/default/style.css" />'
        return mark_safe(s=theme_style.format(static_url=settings.STATIC_URL))


# http://stackoverflow.com/a/16609498
@register.simple_tag
def url_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return dict_.urlencode()
