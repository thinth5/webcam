import torch

model = torch.hub.load('ultralytics/yolov5', 'yolov5n')

import pyttsx3

engine = pyttsx3.init()
voices = engine.getProperty('voices')
engine.setProperty('voice', 'english')
engine.setProperty('rate', engine.getProperty('rate') - 50)

import cv2
import time

from kivy.app import App
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

WINDOW_SIZE = 10

Builder.load_string('''
<DetectLayout>:
    orientation: 'vertical'

    KivyCamera:
        id: camera
        resolution: (640, 480)
        detect: False
        green_mode: False
        show_fps: False
        fps: '0'
''')

class DetectLayout(BoxLayout):

    def capture(self):
        '''
        Function to capture the images and give them the names
        according to their captured time and date.
        '''
        camera = self.ids['camera']
        timestr = time.strftime("%Y%m%d_%H%M%S")
        filename = 'IMG_{}.png'.format(timestr)
        camera.export_to_png(filename)
        print("Captured as {}".format(filename))


class KivyCamera(Image):

    def __init__(self, fps=30, **kwargs):
        super(KivyCamera, self).__init__(**kwargs)
        self.capture = cv2.VideoCapture(0)
        Clock.schedule_interval(self.update, 1.0 / fps)
        self.actual_fps = []

    def frame_to_texture(self, frame):
        # convert it to texture
        buf1 = cv2.flip(frame, 0)
        buf = buf1.tostring()
        image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        return image_texture

    def update(self, dt):
        cap = cv2.VideoCapture(0)
        ret, frame = self.capture.read()
        if not ret:
            return
        result = model (frame)
        df = result.pandas().xyxy[0]

        textToSpeech = ""
        for ind in df.index:
            x1, y1 = int(df['xmin'][ind]),int (df['ymin'][ind])
            x2, y2 = int(df ['xmax'][ind]),int(df['ymax'][ind])
            label = df['name'][ind]
            conf = df['confidence'][ind]
            text = label + ' ' + str(conf.round(decimals= 2))
            cv2.rectangle(frame, (x1, y1), (x2,y2), (0,255,0),2)
            cv2.putText(frame, text,(x1,y1-5), cv2.FONT_HERSHEY_PLAIN, 2,(0,255,0),2)
            textToSpeech += label

        engine.say(textToSpeech)
        engine.runAndWait()
        # display image from the texture
        self.texture = self.frame_to_texture(frame)


class CamApp(App):

    def build(self):
        self.layout = DetectLayout()
        return self.layout

    def on_stop(self):
        #without this, app will not exit even if the window is closed
        self.layout.ids['camera'].capture.release()


if __name__ == '__main__':
    CamApp().run()
