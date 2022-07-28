from pygame import mixer

class Sound:
    def __init__(self):
        self._kick = mixer.Sound("sound/kick.mp3")
        self._goalPostHit = mixer.Sound("sound/post_hit.mp3")

        self.sounds = [self._kick, self._goalPostHit]
    
    def toggleMute(self):
        for sound in self.sounds:
            sound.set_volume(1.0 - sound.get_volume())
    
    def kick(self):
        self._kick.play()
        
    def goalPostHit(self):
        self._goalPostHit.play()