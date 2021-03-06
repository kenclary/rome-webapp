#coding=utf-8
"""
URL patterns for hexgrid.
"""
from django.conf.urls import patterns, url

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'hexgrid.views.home', name='home'),
    url(r'^node/(\d+)/$', 'hexgrid.views.node', name='node'),
    url(r'^password/(\d+)/$', 'hexgrid.views.node_password', name='node_password'),
    url(r'^unlock/(\d+)/(\d+)/$', 'hexgrid.views.unlock', name='unlock'),
    url(r'^watch/(\d+)/$', 'hexgrid.views.watch', name='watch'),
    url(r'^unwatch/(\d*)/(\d+)/$', 'hexgrid.views.unwatch', name='unwatch'),
    url(r'^buy/(\d+)/(\d+)/$', 'hexgrid.views.buy', name='buy'),
    url(r'^bid/(\d+)/(\d+)/$', 'hexgrid.views.bid', name='bid'),
    url(r'^disguise/$', 'hexgrid.views.toggle_disguise', name='toggle_disguise'),

    url(r'^map/$', 'hexgrid.views.node_map', name='map'),

)
