# Create your views here.
import json
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404, redirect
from hexgrid.models import Character
from hexgrid.views import gtc
from succession.models import Line
from territory.models import Unit, Faction, Territory, Action, GameBoard, validation_str, SPEC, SUPP, MOVE, BuildOrder
from territory.somalia import somaliax as somalia_pts


def get_orders(faction_code=None, turn=None):
    if not turn: turn=GameBoard.get_turn()
    actions = Action.objects.filter(turn=turn)
    if faction_code:
        actions = actions.filter(faction__code=faction_code)

    orders = {}

    for a in actions:
        orders[a.territory.code] = {
            'gm_str': str(a),
            'time': str(a.time),
            'str': a.p_str,
            'faction': a.faction.code,
            'turn': a.turn,
            'territory': a.territory.code,
            'type': a.type,
            'build': BuildOrder.objects.filter(territory=a.territory, turn=turn).exists(),
            'target': a.target.code,
            'special': a.special,
            'issuer': a.issuer.gto.name if a.issuer else None,
            'support_type': a.support_type,
            'support_to': a.support_to.code if a.support_to else None,
            'validation_level': validation_str(a.validation_level),
            'disband_priority': a.territory.unit.disband_priority if a.territory.has_unit else 0
        }
    return orders

@login_required()
def orders_json(request, faction_code=None, turn=None):
    context = {
        'orders': get_orders(faction_code, turn)
    }
    return HttpResponse(json.dumps(context), mimetype="application/json")

@login_required()
def overview(request, template="territory/territory.html"):
    somalia = ",".join(["[%s,%s]" % (x[0], x[1]) for x in Territory.convert_points(somalia_pts)])
    user = gtc(request)
    if not Line.objects.filter(lineorder__character=user).exclude(faction=None).exists():
        messages.error(request, "You're not a member of any wargame factions.")
        return redirect('/')
    try:
        faction = Line.objects.filter(lineorder__character=user).exclude(faction=None)[0].faction
    except IndexError:
        raise Http404
    #    units = Unit.live_units().filter(faction=faction)
    territories = Territory.objects.all()
    owned_terrs = faction.territory_set.all()
    builds = BuildOrder.objects.filter(faction=faction, turn=GameBoard.get_turn())
    context = {
        'faction': faction,
        'gameboard': GameBoard,
        'w_turn': GameBoard.get_turn(),
        'last_w_turn': GameBoard.get_turn()-1, #ugh
        'orders': json.dumps(get_orders(faction.code)),
        'builds': builds,
        'somalia': somalia,
        'territories': territories,
        'owned_terrs': owned_terrs
    }
    return render(request, template, context)


@login_required()
def gm_overview(request, template="territory/territory.html"):
    if not request.user.is_superuser: raise Http404
    somalia = ",".join(["[%s,%s]" % (x[0], x[1]) for x in Territory.convert_points(somalia_pts)])
    territories = Territory.objects.all()
    context = {
        'orders': json.dumps(get_orders()),
        'somalia': somalia,
        'gameboard': GameBoard,
        'w_turn': GameBoard.get_turn(),
        'last_w_turn': GameBoard.get_turn() - 1, #ugh
        'territories': territories,
    }
    return render(request, template, context)


@login_required()
def game_tick(request):
    if not request.user.is_superuser: raise Http404

    GameBoard.objects.get().execute_turn()
    messages.success(request, 'Done! It is now turn %s' % GameBoard.get_turn())

    return redirect(gm_overview)

@login_required()
def submit_build(request):
    context = {}
    try:
        if request.method == 'POST':
            f = Faction.objects.get(code=request.POST.get('build_f_id'))
            if request.POST.get('build_t1') and request.POST.get('build_t1') == request.POST.get('build_t2'):
                raise Exception("Can't build two units in the same territory!")
            if BuildOrder.objects.filter(turn=GameBoard.get_turn, faction=f).exists():
                bos = BuildOrder.objects.filter(turn=GameBoard.get_turn(), faction=f)
                bos.delete()
            if request.POST.get('build_t1'):
                build_terr_1 = Territory.objects.get(code=request.POST.get('build_t1'))
                BuildOrder.objects.create(faction=f, territory=build_terr_1, turn=GameBoard.get_turn())
            if request.POST.get('build_t2'):
                build_terr_2 = Territory.objects.get(code=request.POST.get('build_t2'))
                BuildOrder.objects.create(faction=f, territory=build_terr_2, turn=GameBoard.get_turn())
            context['status'] = 'iconized icon-ok-circle'
            context['message'] = 'Build orders accepted'
    except Exception, e:
        context['status'] = 'iconized icon-error'
        context['message'] = 'Server error: %s %s' % (e.message, type(e))
    return HttpResponse(json.dumps(context), mimetype="application/json")

@login_required()
def submit_order(request):
    context = {}
    try:
        if request.method == 'POST':
            print request.POST
            if request.POST.get('gm_sekrit', False):
                c = None
            else:
                c = Character.objects.get(id=request.POST.get('u_id'))
            t = Territory.objects.get(code=request.POST.get('t_id'))
            f = Faction.objects.get(name=request.POST.get('f_id'))
            if t.owner != f:
                context['status'] = 'iconized icon-error'
                context['message'] = "Can't issue order for territory not yours"
                return HttpResponse(json.dumps(context), mimetype="application/json")

            created = False
            try:
                a = Action.objects.get(territory=t, faction=f, turn=GameBoard.get_turn())
            except Action.DoesNotExist:
                a = Action(territory=t, faction=f, turn=GameBoard.get_turn())
                created = True
            if not created:
                if a.issuer and f.rank(a.issuer) < f.rank(c):
                    context['status'] = 'iconized icon-error'
                    context['message'] = "Can't change an order from someone who outranks you!"
                    return HttpResponse(json.dumps(context), mimetype="application/json")

            a.type = request.POST.get('order_type')
            if c:
                a.issuer = c

            if a.type == MOVE:
                a.target = Territory.objects.get(code=request.POST.get('move_to'))
            elif a.type == SUPP:
                a.support_type = request.POST.get('support_type')
                if a.support_type == MOVE:
                    a.target = Territory.objects.get(code=request.POST.get('support_from'))
                    a.support_to = Territory.objects.get(code=request.POST.get('support_to'))
                else:
                    a.target = Territory.objects.get(code=request.POST.get('support_to'))
            elif a.type == SPEC:
                a.special = request.POST.get('special')
            else:
                a.target = None
            try:
                a.save()
            except Action.InvalidMoveError, e:
                context['status'] = 'iconized icon-error'

                context['message'] = 'Invalid move: %s ' % e.message
                return HttpResponse(json.dumps(context), mimetype="application/json")
            context['order'] = str(a)
            if created:
                context['message'] = 'Order created'
            else:
                context['status'] = 'iconized icon-ok-circle'
                context['message'] = 'Order accepted'

    except ValidationError, e:
        context['status'] = 'iconized icon-error'
        context['message'] = 'Invalid move: %s' % str(e.message_dict)
    except Exception, e:
        context['status'] = 'iconized icon-error'
        context['message'] = 'Server error: %s %s' % (e.message, type(e))
    return HttpResponse(json.dumps(context), mimetype="application/json")

def set_disband_priority(request):
    context = {}
    try:
        if request.method == 'POST':
            print request.POST
            territory = Territory.objects.get(code=request.POST.get('db_t_id'))
            unit = Unit.objects.get(territory=territory)
            priority = int(request.POST.get('disband_priority'))
            unit.disband_priority = priority
            unit.save()
            context['status'] = 'iconized icon-ok-circle'
            context['message'] = 'OK'
    except Exception, e:
        context['status'] = 'iconized icon-error'
        context['message'] = 'Server error: %s %s' % (e.message, type(e))

    return HttpResponse(json.dumps(context), mimetype="application/json")