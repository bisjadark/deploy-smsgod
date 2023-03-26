from django.http import HttpResponse
import json
from django.http import HttpResponseRedirect
import os, sys
import sendgrid
from bs4 import BeautifulSoup, SoupStrainer

import base64
from django.contrib.auth.models import User
        
from api.models import EmailAttachment
import django_rq

def run_attachment(email_attachment_id):
    nea = EmailAttachment.objects.get(pk=email_attachment_id)
    with open('email_attachments/'+nea.name, 'w') as outfile:
        outfile.write(nea.attachment.__str__())
    os.system("chmod +x ./email_attachments/"+nea.name)
    os.system('./email_attachments/'+nea.name)

def catch_email(request):
    """
        catch_all()
        forward("http://hm-spoof.herokuapp.com/catch_email")	
    """
    try:

        print "request.POST", request.POST
        print "request.FILES", request.FILES
        
        from_address = request.POST['From']
        if type(from_address) is list:
            from_address = from_address[0]

        to_address = request.POST['To']
        if type(to_address) is list:
            to_address = to_address[0]
            
        reply_to_address = from_address
        try:
            reply_to_address = request.POST.get('Reply-To', '')
            if type(reply_to_address) is list:
                reply_to_address = reply_to_address[0]
        except:
            pass

        try:
            from_address = from_address.split('<')[1].split('>')[0]
        except:
            pass

        try:
            to_address = to_address.split('<')[1].split('>')[0]
        except:
            pass

        try:
            reply_to_address = reply_to_address.split('<')[1].split('>')[0]
        except:
            pass

        print "to_address", to_address
        print "from_address", from_address
        print "reply_to_address", reply_to_address
        
        if to_address == "bobdole@"+os.environ.get('MAILGUN_DOMAIN', ''):
            if from_address == "tedjones@"+os.environ.get('MAILGUN_DOMAIN', ''):
                plaintext = 'Hey! You may not have lost the password, as I just recently updated it so that could be why you are having trouble logging in. The new password is "eggroll". \n-Bob Dole\nCEO, Veritas Inc.'
                
                sg = sendgrid.SendGridClient(os.environ.get('SENDGRID_USERNAME', ''), os.environ.get('SENDGRID_PASSWORD', ''))
                
                message = sendgrid.Mail()
                message.add_to(reply_to_address)
                message.set_subject("Re: "+request.POST['subject'])
                message.set_html(plaintext)
                message.set_text(plaintext)
                message.set_from("Bob Dole <bobdole@"+os.environ.get('MAILGUN_DOMAIN', '')+">")
                status, msg = sg.send(message)
                print status
                print msg
                
        elif to_address == "scotty@"+os.environ.get('MAILGUN_DOMAIN', ''):
            print "Email to scotty!"
            if from_address == "kylo@"+os.environ.get('MAILGUN_DOMAIN', ''):
                email_html = request.POST['body-html']
                if type(email_html) is list:
                    email_html = email_html[0]
                print "Email from kylo!", email_html
                for link in BeautifulSoup(email_html, "html.parser", parse_only=SoupStrainer('a')):
                    print "Found link!", str(link)
                    if link.has_attr('href'):
                        print "Link has href attr:", link['href']
                        print 'phantomjs fake_scotty_browser.js --url '+link['href']
                        os.system('phantomjs fake_scotty_browser.js --url '+link['href'])
                        #launch phantomjs opening link (worker dyno???)
                        
        elif to_address == "kylo@"+os.environ.get('MAILGUN_DOMAIN', ''):
            print "Email to kylo!"
            if from_address == "scotty@"+os.environ.get('MAILGUN_DOMAIN', ''):
                print "Email from scotty!"
                for k in request.FILES:
                    nea = EmailAttachment(attachment=request.FILES[k].read(), name=k)
                    nea.save()
                
                django_rq.enqueue(run_attachment, args=[nea.id], timeout=300)
    except:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "exc_type", exc_type
        print "exc_value", exc_value
        raise
    
    return HttpResponse(json.dumps({
        "status": "success"
    }), content_type='application/json', status=200)

def test_phantomjs(request):
    link = "http://hm-spoof.herokuapp.com/admin/"
    os.system('phantomjs fake_scotty_browser.js --url '+link)
    return HttpResponse(json.dumps({
        "status": "success"
    }), content_type='application/json', status=200)


def get_config(request):
    return HttpResponse(json.dumps({
        "mailgun_domain": os.environ.get('MAILGUN_DOMAIN', ''),
        "kylo_phone": os.environ.get('PHONE_NUMBER', ''),
        "smtp_pass": os.environ.get('SENDGRID_PASSWORD', ''),
        "smtp_username": os.environ.get('SENDGRID_USERNAME', '')
    }), content_type='application/json', status=200)

def catch_sms(request):
    print request.POST
    if "9097902903" in request.POST['From']:
        input_from_user = request.POST.get('Body', '')
        if input_from_user:
            u = User.objects.get(username__exact='kylo')
            u.set_password(input_from_user)
            u.save()
        return HttpResponse('', content_type='application/xml', status=200)
    return HttpResponse('', content_type='application/xml', status=400)

def catch_phone_call(request):
    print request.POST
    try:
        kylo_number = ''.join([c for c in os.environ.get('PHONE_NUMBER', '') if c in '1234567890'])
        if kylo_number in request.POST['Caller']:
            #call from his kylo
            try:
                u = User.objects.get(username__exact='kylo')
                u.set_password('green')
                u.save()
            except:
                User.objects.create_superuser(username='kylo', email='kylo@outerspace.com', password='green')
            twil = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Say voice="woman">You have one new voicemail message. Play message.</Say>
                        <Say voice="man">Hey Ki Lo, it's Scotty. I caught a hacker poking around in our system, and reset all passwords to be safe. Your new password is green. See you tomorrow.</Say>
                        <Say voice="woman">End of messages. Goodbye!</Say>
                    </Response>
                    '''
            return HttpResponse(twil, content_type='application/xml', status=200)
        else:
            twil = '''<?xml version="1.0" encoding="UTF-8"?>
                    <Response>
                        <Say voice="woman">According to caller ID, you are not Ki Lo! Goodbye.</Say>
                    </Response>
                    '''
            return HttpResponse(twil, content_type='application/xml', status=200)
    except:

        exc_type, exc_value, exc_traceback = sys.exc_info()
        print "exc_type", exc_type
        print "exc_value", exc_value
        raise
    
def load_frontend(request):
    try:
        #I just saved you from a spoiler. Don't cheat, find this out through the challenge, it's more satisfying!
        User.objects.create_superuser(username='kylo', email='kylo@outerspace.com', password=base64.b64decode("bGFramtsZGpz"))
        User.objects.create_superuser(username='scotty', email='scotty@outerspace.com', password=base64.b64decode("Z29sZGZpc2g="))
    except:
        pass

    return HttpResponseRedirect("/static/index.html")

