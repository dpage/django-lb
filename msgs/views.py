from django.shortcuts import redirect, render
from django.core.paginator import Paginator

from .models import Msg


def index(request):
    # Save any new message that has been submitted, and display the archive
    if request.method == 'POST' and \
            request.POST.get("msg") is not None and \
            request.POST.get("msg") != '':
        new_msg = Msg(msg_text=request.POST.get("msg"))
        new_msg.save()

        return redirect('archive')

    # Failed submission?
    warning = ''
    if request.method == 'POST':
        warning = "The message submitted was empty! Please try again."

    # No new message - get the latest
    latest_msg = Msg.objects.order_by('-msg_time')[:1]

    if len(latest_msg) == 0:
        msg = "There are no messages to display."
        time = "N/A"
    else:
        msg = latest_msg[0].msg_text
        time = latest_msg[0].msg_time

    context = {
        'text': msg,
        'time': time,
        'warning': warning
    }

    return render(request, 'msgs/index.html', context)


def archive(request):
    msgs = Msg.objects.order_by('-msg_time')

    paginator = Paginator(msgs, 10)

    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'msgs/archive.html', {'msgs': page_obj})
