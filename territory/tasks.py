from datetime import datetime
from django.utils.timezone import now
from consortium.consortium import send_mail
from hexgrid.models import GameDay
from celery.schedules import crontab
from celery.task import periodic_task
from territory.models import GameBoard

__author__ = 'cternus'

@periodic_task(run_every=crontab(minute='0', hour='19'))
def day_phase():
    # if now().time().hour < 18 or now().time().hour > 19: return "Wrongly fired"
    g = GameBoard.objects.get()
    s = g.execute_turn(string=True)
    send_mail("[Consortium] Day phase complete", "Day phase successful at %s\n%s" % (datetime.now(), s), 'consortium-gms@cternus.net',
          ['ternus@cternus.net'], fail_silently=True)

@periodic_task(run_every=crontab(minute='0', hour='23'))
def night_phase():
    # if now().time().hour < 22: return "Wrongly fired"
    g = GameBoard.objects.get()
    s = g.execute_turn(string=True)
    send_mail("[Consortium] Night phase complete", "Night phase successful at %s\n%s" % (datetime.now(), s), 'consortium-gms@cternus.net',
          ['ternus@cternus.net'], fail_silently=True)