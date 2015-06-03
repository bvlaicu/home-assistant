"""
homeassistant.components.media_player.chromecast
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Provides functionality to interact with Cast devices on the network.

WARNING: This platform is currently not working due to a changed Cast API
"""
import logging

try:
    import pychromecast
    import pychromecast.controllers.youtube as youtube
except ImportError:
    pychromecast = None

from homeassistant.const import (
    STATE_PLAYING, STATE_PAUSED, STATE_IDLE, STATE_OFF,
    STATE_UNKNOWN)

from homeassistant.components.media_player import (
    MediaPlayerDevice,
    SUPPORT_PAUSE, SUPPORT_VOLUME_SET, SUPPORT_VOLUME_MUTE,
    SUPPORT_YOUTUBE,
    SUPPORT_TURN_ON, SUPPORT_TURN_OFF,
    SUPPORT_PREVIOUS_TRACK, SUPPORT_NEXT_TRACK)

CAST_SPLASH = 'https://home-assistant.io/images/cast/splash.png'


# pylint: disable=unused-argument
def setup_platform(hass, config, add_devices, discovery_info=None):
    """ Sets up the cast platform. """
    logger = logging.getLogger(__name__)

    if pychromecast is None:
        logger.error((
            "Failed to import pychromecast. Did you maybe not install the "
            "'pychromecast' dependency?"))

        return False

    if discovery_info:
        hosts = [discovery_info[0]]

    else:
        hosts = (host_port[0] for host_port
                 in pychromecast.discover_chromecasts())

    casts = []

    for host in hosts:
        try:
            casts.append(CastDevice(host))
        except pychromecast.ChromecastConnectionError:
            pass

    add_devices(casts)


class CastDevice(MediaPlayerDevice):
    """ Represents a Cast device on the network. """

    def __init__(self, host):
        self.cast = pychromecast.Chromecast(host)
        self.youtube = youtube.YouTubeController()
        self.cast.register_handler(self.youtube)

        self.cast.socket_client.receiver_controller.register_status_listener(
            self)
        self.cast.socket_client.media_controller.register_status_listener(self)

        self.cast_status = self.cast.status
        self.media_status = self.cast.media_controller.status

    """Entity properties and methods"""

    @property
    def should_poll(self):
        return False

    @property
    def name(self):
        """ Returns the name of the device. """
        return self.cast.device.friendly_name

    """MediaPlayerDevice properties and methods"""

    @property
    def state(self):
        """ State of the player. """
        media_controller = self.cast.media_controller

        if media_controller.is_playing:
            return STATE_PLAYING
        elif media_controller.is_paused:
            return STATE_PAUSED
        elif media_controller.is_idle:
            return STATE_IDLE
        elif self.cast.is_idle:
            return STATE_OFF
        else:
            return STATE_UNKNOWN

    @property
    def volume_level(self):
        """ Volume level of the media player (0..1). """
        if self.cast_status is None:
            return None
        else:
            return self.cast_status.volume_level

    @property
    def is_volume_muted(self):
        """ Boolean if volume is currently muted. """
        if self.cast_status is None:
            return None
        else:
            return self.cast_status.volume_muted

    @property
    def media_content_id(self):
        """ Content ID of current playing media. """
        if self.media_status is None:
            return None
        else:
            return self.media_status.content_id

    @property
    def media_content_type(self):
        """ Content type of current playing media. """
        return None

    @property
    def media_duration(self):
        """ Duration of current playing media in seconds. """
        if self.media_status is None:
            return None
        else:
            return self.media_status.duration

    @property
    def media_image_url(self):
        """ Image url of current playing media. """
        return self.cast.media_controller.thumbnail

    @property
    def media_title(self):
        """ Title of current playing media. """
        return self.cast.media_controller.title

    @property
    def media_artist(self):
        """ Artist of current playing media. (Music track only) """
        return None

    @property
    def media_album(self):
        """ Album of current playing media. (Music track only) """
        return None

    @property
    def media_track(self):
        """ Track number of current playing media. (Music track only) """
        return None

    @property
    def media_series_title(self):
        """ Series title of current playing media. (TV Show only)"""
        return None

    @property
    def media_season(self):
        """ Season of current playing media. (TV Show only) """
        return None

    @property
    def media_episode(self):
        """ Episode of current playing media. (TV Show only) """
        return None

    @property
    def app_id(self):
        """  ID of the current running app. """
        return self.cast.app_id

    @property
    def app_name(self):
        """  Name of the current running app. """
        return self.cast.app_display_name

    @property
    def supported_media_commands(self):
        """ Flags of media commands that are supported. """
        return SUPPORT_PAUSE | SUPPORT_VOLUME_SET | SUPPORT_VOLUME_MUTE | \
            SUPPORT_TURN_ON | SUPPORT_TURN_OFF | SUPPORT_PREVIOUS_TRACK | \
            SUPPORT_NEXT_TRACK

    @property
    def device_state_attributes(self):
        """ Extra attributes a device wants to expose. """
        return None

    def turn_on(self):
        """ Turns on the ChromeCast. """
        # The only way we can turn the Chromecast is on is by launching an app
        if not self.cast.status or not self.cast.status.is_active_input:
            if self.cast.app_id:
                self.cast.quit_app()

            self.cast.play_media(
                CAST_SPLASH, pychromecast.STREAM_TYPE_BUFFERED)


    def turn_off(self):
        """ Service to exit any running app on the specimedia player ChromeCast and
        shows idle screen. Will quit all ChromeCasts if nothing specified.
        """
        self.cast.quit_app()

    def mute_volume(self, mute):
        """ mute the volume. """
        self.cast.set_volume_muted(mute)

    def set_volume_level(self, volume):
        """ set volume level, range 0..1. """
        self.cast.set_volume(volume)

    def media_play(self):
        """ Send play commmand. """
        self.cast.media_controller.play()

    def media_pause(self):
        """ Send pause command. """
        self.cast.media_controller.pause()

    def media_previous_track(self):
        """ Send previous track command. """
        self.cast.media_controller.rewind()

    def media_next_track(self):
        """ Send next track command. """
        self.cast.media_controller.skip()

    def media_seek(self, position):
        """ Seek the media to a specific location. """
        self.case.media_controller.seek(position)

    def play_youtube(self, media_id):
        """ Plays a YouTube media. """
        self.youtube.play_video(media_id)

    """implementation of chromecast status_listener methods"""

    def new_cast_status(self, status):
        """ Called when a new cast status is received. """
        self.cast_status = status
        self.update_ha_state()

    def new_media_status(self, status):
        """ Called when a new media status is received. """
        self.media_status = status
        self.update_ha_state()