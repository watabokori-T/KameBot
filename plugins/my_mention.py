import os
import time
import picamera
import requests
import cv2
from datetime import datetime
from slackbot.bot import respond_to
import RPi.GPIO as GPIO
import time

TOKEN = 'xxxx-xxxxxxxxxxxx-xxxxxxxxxxxx-xxxxxxxxxxxxxxxxxxxxxxxx'

#写真を撮る
@respond_to('写真')
def takepicture_func(message):
    ImagePath = '/home/pi/ドキュメント/slackbot/kame.jpg'

    #写真の撮影(RaspberryPi)
    with picamera.PiCamera() as camera:
        camera.resolution = (1024, 768)
        camera.start_preview()
        #Camera warm-up time
        time.sleep(2)
        camera.capture(ImagePath)

    #画像のアップロード
    CHANNEL = 'xxxxxxxxx'
    TITLE = datetime(*time.localtime(os.path.getctime(ImagePath))[:6])
    files = {'file': open(ImagePath, 'rb')}
    param = {
        'token':TOKEN,
        'channels':CHANNEL,
        'filename':"kame.jpg",
        'initial_comment': "亀photo",'title': TITLE
    }
    requests.post(url="https://slack.com/api/files.upload",params=param, files=files)

#餌やる
@respond_to('餌')
def feed_func(message):
    #10秒GPIO21ONN
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(21, GPIO.OUT)
    GPIO.output(21, 1)
    #10秒待つ
    time.sleep(10)
    GPIO.output(21, 0)
    GPIO.cleanup()
    #返事
    message.reply('餌やっといたよ')

#capmovie
@respond_to(r'^cap\s+\S.*') #cap...
def cap_func(message):
    text = message.body['text']
    temp, word = text.split(None, 1) #temp:'cap',word:'...'

    ImagePath = '/home/pi/ドキュメント/slackbot/kamecap.mp4'

    cap = cv2.VideoCapture(0)
    fourcc = cv2.VideoWriter_fourcc('m','p','4','v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    size = (int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    out = cv2.VideoWriter('kamecap.mp4', fourcc, fps, size)

    #capture
    d = datetime.now()
    while(cap.isOpened()):
        ret, frame = cap.read()
        if ret == True:
            out.write(frame)
            #capture 5sec
            if(datetime.now() - d).seconds >= int(word):
                break
        else:
            break

    cap.release()
    out.release()
    cv2.destroyAllWindows()

    #movieアップロード
    CHANNEL = 'xxxxxxxxx'
    TITLE = datetime(*time.localtime(os.path.getctime(ImagePath))[:6])
    files = {'file': open(ImagePath, 'rb')}
    param = {
        'token':TOKEN,
        'channels':CHANNEL,
        'filename':"kamecap.mp4",
        'initial_comment': "亀movie",'title': TITLE
    }
    requests.post(url="https://slack.com/api/files.upload",params=param, files=files)

#cv,change detection
@respond_to('cv')
def cv_func(message):
    #change detection
    def difference(a, b):
        if(a < b):
            return b-a
        return a-b

    def dump(src, keep):
        os.system('clear')
        count = 0
        for y in range(0, 24):
            str = ''
            for x in range(0, 32):
                target = src[y*10][x*10]
                diff = difference(keep[y][x], target)
                if diff > 50:
                    str += '{:02} '.format(diff)
                    count += 1
                else:
                    str += '_ '
                keep[y][x] = target
            print(str)
        return count

    cap = cv2.VideoCapture(0)
    cap.set(3,320) #width
    cap.set(4,240) #hight
    cap.set(5,4) #fps

    keep = [[0] * 32 for i in range(24)]
    busy = True

    while(cap.isOpened()):
        ret, frame = cap.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        count = dump(gray, keep)

        print('{0} {1}'.format(count,busy))
        if busy and count==0:
            busy = False
        if busy == False and count > 5:
            busy = True
            message.reply('turtle moving') #reply

        if cv2.waitKey(1) != -1:
            cap.release()
            cv2.destroyAllWindows()
            break

        @respond_to('fin')
        def cvfin_func(message):
            cap.release()
            cv2.destroyAllWindows()
            #返事
            message.reply('cv fin')
