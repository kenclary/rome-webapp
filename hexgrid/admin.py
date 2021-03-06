# coding=utf-8
from django.contrib import admin
from gametex.models import GameTeXObject, GameTeXFieldValue
from hexgrid.models import Node, Item, Rumor, Character, GameDay, Secret, CharNodeWatch, CharNode, NodeEvent
from hexgrid.game_settings import PRICE_FIELD

class ItemAdmin(admin.ModelAdmin):
    """
    Admin for items for proper item card linking.
    """
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        """
        Filter item cards that have non-blank PRICE_FIELDs.
        """
        if db_field.name == 'item_card':
            kwargs['queryset'] = GameTeXObject.objects.filter(
                macro=GameTeXFieldValue.objects.filter(field__name=PRICE_FIELD)\
                .exclude(value=u'').values_list('object', flat=True))
        return super(ItemAdmin, self).formfield_for_foreignkey(db_field,
            request, **kwargs)

admin.site.register(Node)
admin.site.register(NodeEvent)
admin.site.register(Item, ItemAdmin)
admin.site.register(Rumor)
admin.site.register(Secret)
admin.site.register(Character)
admin.site.register(CharNode)
admin.site.register(CharNodeWatch)
admin.site.register(GameDay)