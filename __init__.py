# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

import podcastparser as pp
import urllib
from urllib.request import Request

from mycroft.skills.core import intent_file_handler
from mycroft.skills.common_play_skill import CommonPlaySkill, CPSMatchLevel
from mycroft.skills.audioservice import AudioService
from mycroft.util.parse import fuzzy_match

__author__ = 'jamespoole'


class PodcastSkill(CommonPlaySkill):
    def __init__(self):
        super(PodcastSkill, self).__init__(name="PodcastSkill")
        self.process = None
        self.user_agent = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11'
        self.state = 'idle'

    def initialize(self):
        # Setup handlers for playback control messages
        self.add_event('mycroft.audio.service.next', self.next)
        self.add_event('mycroft.audio.service.prev', self.previous)
        self.add_event('mycroft.audio.service.pause', self.pause)
        self.add_event('mycroft.audio.service.resume', self.resume)
        self.audio_service = AudioService(self.bus)


### BEGIN PLAYBACK SPECIFIC FUNCTIONS 

    def CPS_match_query_phrase(self, phrase):
        self.log.debug("phrase {}".format(phrase))

        data = None
        best_index = -1
        best_confidence = 0.0

        if 'podcast' in phrase.lower():
            bonus = 0.1
        else:
            bonus = 0

        podcast_names = [self.settings["nameone"], self.settings["nametwo"], self.settings["namethree"]]
        podcast_urls = [self.settings["feedone"], self.settings["feedtwo"], self.settings["feedthree"]]

        # fuzzy matching
        for index, name in enumerate(podcast_names):
            confidence = min(fuzzy_match(name.lower(), phrase.lower()) + bonus,
                             1.0)
            if confidence > best_confidence:
                best_index = index
                best_confidence = confidence
            self.log.debug("index {}, name {}, confidence {}".format(index, name, confidence))

        # check for exact match
        data = self.chosen_podcast(phrase, podcast_names, podcast_urls)

        if data:
            confidence = CPSMatchLevel.EXACT
        elif best_index >= 0:
            data = podcast_urls[best_index]
            if best_confidence > 0.9:
                confidence = CPSMatchLevel.EXACT
            elif best_confidence > 0.6:
                confidence = CPSMatchLevel.TITLE
            elif best_confidence > 0.1:
                confidence = CPSMatchLevel.CATEGORY
            else:
                confidence = CPSMatchLevel.GENERIC

        self.log.info("phrase: {} confidence: {} data: {}".format(phrase,
                                                                  confidence,
                                                                  data))
        return phrase, confidence, data

    def CPS_start(self, phrase, data):
            self.log.info("CPS_start phrase: {} data: {}".format(phrase, data))
            parsed_feed = pp.parse(data, urllib.request.urlopen(Request(data,
                            data=None, headers={'User-Agent': self.user_agent}))
                          )

            # try and parse the rss feed, some are incompatible
            try:
                episodes = parsed_feed["episodes"]
                urls = [o["enclosures"][0]["url"] for o in episodes]
                titles = [o["title"] for o in episodes]
            except:
                self.speak_dialog('badrss')

            self.titles = titles
            self.current_index = 0
            self.speak(titles[0], wait=True)
            self.audio_service.play(urls)

    def chosen_podcast(self, utter, podcast_names, podcast_urls):
        for index, name in enumerate(podcast_names):
            # skip if podcast slot left empty
            if not name:
                continue
            if name.lower() in utter.lower():
                listen_url = podcast_urls[index]
                break
        else:
            listen_url = ""
        return listen_url

    def pause(self):
        self.log.info("Pause called")
        self.log.info('Audio service status: ''{}'.format(self.audio_service.track_info()))


    def resume(self):
        self.log.info("Resume called")
        self.log.info('Audio service status: ''{}'.format(self.audio_service.track_info()))



    def next(self):
        self.log.info("Next called")
        self.log.info('Audio service status: ''{}'.format(self.audio_service.track_info()))
        if self.audio_service.is_playing:
            if(self.current_index == 0):
                self.speak("You are listening to the latest episode", wait=True)
                return False
            else:
                self.current_index = self.current_index - 1
                self.speak(self.titles[self.current_index], wait=True)

    def previous(self):
        self.log.info("Prev called")
        self.log.info('Audio service status: ''{}'.format(self.audio_service.track_info()))
        if self.audio_service.is_playing:
            if(self.current_index == len(self.titles)-1):
                self.speak("No more episodes avaliable", wait=True)
            else:
                self.current_index = self.current_index + 1
                self.speak(self.titles[self.current_index], wait=True)

### END PLAYBACK SPECIFIC FUNCTIONS 


    @intent_file_handler('LatestEpisodes.intent')
    def handle_latest_episodes_intent(self, message):
        self.enclosure.mouth_think()

        podcast_names = [self.settings["nameone"], self.settings["nametwo"], self.settings["namethree"]]
        podcast_urls = [self.settings["feedone"], self.settings["feedtwo"], self.settings["feedthree"]]

        new_episodes = []
        for index, url in enumerate(podcast_urls):
            # skip if url slot left empty
            if not url:
                continue
            parsed_feed = pp.parse(podcast_urls[index],
                                urllib.request.urlopen(Request(podcast_urls[index], data=None, headers={'User-Agent': self.user_agent})))
            last_episode = (parsed_feed['episodes'][0]['title'])
            new_episodes.append(last_episode)

            # skip if i[0] slot left empty
        elements = [": ".join(i) for i in zip(podcast_names, new_episodes) if i[0]]
        response = {'episodes': ", ".join(elements[:-2] + [" and ".join(elements[-2:])])}
        self.speak_dialog("latestEpisodes", data=response)

    @intent_file_handler('LatestEpisode.intent')
    def handle_latest_episode_intent(self, message):
        utter = message.data['utterance']
        self.enclosure.mouth_think()

        podcast_names = [self.settings["nameone"], self.settings["nametwo"], self.settings["namethree"]]
        podcast_urls = [self.settings["feedone"], self.settings["feedtwo"], self.settings["feedthree"]]
        
        found = False
        # check if the user specified a podcast to check for a new podcast
        for index, name in enumerate(podcast_names):
            # skip if podcast slot left empty
            if not name:
                continue
            if name.lower() in utter.lower():
                parsed_feed = pp.parse(podcast_urls[index],
                                urllib.request.urlopen(Request(podcast_urls[index], data=None, headers={'User-Agent': self.user_agent})))
                last_episode = (parsed_feed['episodes'][0]['title'])
                response = {'podcast': name, 'episode': last_episode}
                self.speak_dialog("latestEpisode", data=response)
                found = True
                break

        if(not found):
            self.speak_dialog("nopodcastfound")


    def stop(self):
        if self.audio_service.is_playing:
            self.audio_service.stop()
            self.state = 'idle'
            return True
        else:
            return False

    def shutdown(self):
        if self.state != 'idle':
            self.audio_service.stop()


def create_skill():
    return PodcastSkill()
